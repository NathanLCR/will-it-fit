#!/usr/bin/env python3
"""Run a test set against an OpenAI-compatible endpoint; write raw results to results/<setup>/<set-stem>.jsonl."""
import argparse, datetime, hashlib, json, re, subprocess, sys, time, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from prompts import build_answer_prompt
from tagparser import TagStreamParser

ROOT = Path(__file__).resolve().parent.parent
SAMPLING = {k: v for k, v in json.load(open(Path(__file__).parent / "sampling.json")).items() if not k.startswith("_")}
THINK_RE = re.compile(r"<think>.*?</think>", re.S)


def strip_think(t):
    t = THINK_RE.sub("", t or "")
    if "</think>" in t: t = t.split("</think>", 1)[1]  # template opened the block itself
    return t.split("<think>")[0].strip()


class ThinkFilter:
    """Streaming version of strip_think: drops <think>...</think>, holds back partial markers."""
    def __init__(self): self.buf, self.inside = "", False
    def feed(self, chunk):
        self.buf += chunk; out = ""
        while True:
            tag = "</think>" if self.inside else "<think>"
            i = self.buf.find(tag)
            if i >= 0:
                if not self.inside: out += self.buf[:i]
                self.buf, self.inside = self.buf[i + len(tag):], not self.inside
                continue
            keep = next((k for k in range(len(tag) - 1, 0, -1) if self.buf.endswith(tag[:k])), 0)
            if not self.inside: out += self.buf[:len(self.buf) - keep]
            self.buf = self.buf[len(self.buf) - keep:]
            return out


def post(args, body, stream=False):
    body["chat_template_kwargs"] = {"enable_thinking": args.think == "on"}
    body.update(args.sampling)  # vendor sampling, top-level fields
    body.update(model=args.model, stream=stream)
    req = urllib.request.Request(args.base_url.rstrip("/") + "/chat/completions", json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "Authorization": "Bearer x"})
    return urllib.request.urlopen(req, timeout=900)


def chat(args, messages, tools=None):
    body = {"messages": messages}
    if tools: body["tools"] = tools
    with post(args, body) as r:
        return json.load(r)["choices"][0]["message"]


def mock_result(item, shared, name, call_args, chunk_text):
    for m in item.get("mocks", []):
        if m["tool"] != name: continue
        if all(re.search(rx, str(call_args.get(k, ""))) for k, rx in m.get("match", {}).items()):
            if "returns_chunks" in m:
                return {"chunks": [{"chunk_id": c, "text": chunk_text.get(c, "")} for c in m["returns_chunks"]]}
            return m["returns"]
    return shared.get(name, {"error": "no mock defined for this call"})


def run_agent(args, item, ts, frozen, chunk_text):
    msgs = [{"role": "system", "content": frozen["system_prompt"]}]
    calls, replies = [], []
    for turn, text in enumerate(item["turns"], 1):
        msgs.append({"role": "user", "content": text})
        reply = ""
        for _ in range(8):
            m = chat(args, msgs, frozen["tools"])
            tcs = m.get("tool_calls") or []
            msgs.append({"role": "assistant", "content": strip_think(m.get("content")) or None,
                         **({"tool_calls": tcs} if tcs else {})})
            if not tcs:
                reply = strip_think(m.get("content")); break
            for tc in tcs:
                fn = tc["function"]
                try: a = json.loads(fn.get("arguments") or "{}")
                except ValueError: a = {"_raw": fn.get("arguments")}
                calls.append({"turn": turn, "tool": fn["name"], "args": a})
                res = mock_result(item, ts.get("shared_mocks", {}), fn["name"], a if isinstance(a, dict) else {}, chunk_text)
                msgs.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": res if isinstance(res, str) else json.dumps(res)})
        replies.append(reply)
    return {"calls": calls, "replies": replies, "final_reply": replies[-1] if replies else ""}


def norm(c):  # frozen chunks use "chunk_id"; the vendored prompt wants "id"
    return {**c, "id": c.get("chunk_id", c.get("id"))}


def run_pdf(args, item):
    chunks = [norm(c) for c in item["context_chunks"]]
    raw = chat(args, [{"role": "user", "content": build_answer_prompt(item["question"], chunks)}]).get("content") or ""
    return {"raw": raw, "reply": strip_think(raw), "context_ids": [c["id"] for c in chunks]}


def run_desk(args, item, system):
    body = {"messages": [{"role": "system", "content": system}, {"role": "user", "content": item["utterance"]}]}
    parser, filt, events, raw = TagStreamParser(), ThinkFilter(), [], ""
    t0 = time.perf_counter(); first = None

    def take(evs):
        nonlocal first
        for e in evs:
            events.append(e)
            if e["type"] == "sentence" and first is None: first = (time.perf_counter() - t0) * 1000

    with post(args, body, stream=True) as r:
        for line in r:
            line = line.decode().strip()
            if not line.startswith("data:") or line.endswith("[DONE]"): continue
            ch = json.loads(line[5:]).get("choices") or [{}]
            piece = (ch[0].get("delta") or {}).get("content") or ""
            raw += piece
            take(parser.feed(filt.feed(piece)))
    fin, clean, reply_raw, emotion = parser.finish()
    take(fin)
    total = (time.perf_counter() - t0) * 1000
    return {"raw": raw, "reply_raw": reply_raw, "clean": clean, "first_sentence_ms": first, "total_ms": total,
            "sentences": [e["text"] for e in events if e["type"] == "sentence"],
            "emotion": emotion,
            "actions": [f'{e["kind"]}:{e["target"]}' for e in events if e["type"] == "action"],
            "facts": re.findall(r"\[fact\s*:\s*(.*?)\s*\]", reply_raw, re.I | re.S)}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""): h.update(b)
    return h.hexdigest()


def gguf_sha256(path, cache=ROOT / "results" / ".gguf-hashes.json"):
    """sha256 of a big file, cached by path + size + mtime so only the first run pays for hashing."""
    path = Path(path).resolve(); st = path.stat(); key = f"{path}|{st.st_size}|{int(st.st_mtime)}"
    try: hashes = json.load(open(cache))
    except (OSError, ValueError): hashes = {}
    if key not in hashes:
        hashes[key] = sha256_file(path)
        cache.parent.mkdir(parents=True, exist_ok=True); cache.write_text(json.dumps(hashes, indent=1))
    return hashes[key]


def git_state():
    def git(*a): return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)
    c = git("rev-parse", "HEAD")
    commit = c.stdout.strip() if c.returncode == 0 else "uncommitted"  # no commits yet, or not a repo
    return {"commit": commit, "dirty": bool(git("status", "--porcelain").stdout.strip())}


def server_build(base_url, timeout=10):
    """Build string from GET /props (server root, not /v1); falls back to `llama-server --version`."""
    try:
        with urllib.request.urlopen(re.sub(r"/v1/?$", "", base_url.rstrip("/")) + "/props", timeout=timeout) as r:
            b = json.load(r).get("build_info")
        if b: return {"build": b, "source": "/props"}
    except Exception: pass
    try:
        o = subprocess.run(["llama-server", "--version"], capture_output=True, text=True, timeout=30)
        return {"build": (o.stdout + o.stderr).strip().splitlines()[0], "source": "--version"}
    except Exception as e: return {"build": None, "source": f"unavailable: {e!r}"}


def write_provenance(path, args, setp, started):
    """results/<setup>/<set-stem>.provenance.json: one entry per invocation (rows in the .jsonl can span several)."""
    try: prov = json.load(open(path))
    except (OSError, ValueError): prov = {"invocations": []}
    g = Path(args.gguf)
    prov["invocations"].append({
        "started": started, "ended": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "argv": sys.argv, "setup": args.setup, "candidate": args.candidate, "think": args.think,
        "repeat": args.repeat, "only": args.only, "sampling": args.sampling,
        "gguf": {"path": str(g), "size": g.stat().st_size, "sha256": gguf_sha256(g)},
        "server": server_build(args.base_url),
        "testset": {"path": str(setp), "sha256": sha256_file(setp)}, "git": git_state()})
    path.write_text(json.dumps(prov, indent=1))


def main():
    started = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    p = argparse.ArgumentParser()
    p.add_argument("--set", required=True); p.add_argument("--base-url", required=True)
    p.add_argument("--model", required=True); p.add_argument("--setup", required=True)
    p.add_argument("--candidate", required=True, choices=list(SAMPLING))
    p.add_argument("--think", required=True, choices=["on", "off"])
    p.add_argument("--repeat", type=int, default=1); p.add_argument("--include-drafts", action="store_true")
    p.add_argument("--only"); p.add_argument("--gguf", required=True, help="weights file served by llama-server (hashed for provenance)")
    args = p.parse_args()
    args.sampling = SAMPLING[args.candidate]["think" if args.think == "on" else "nothink"]
    setp = Path(args.set).resolve(); ts = json.load(open(setp))
    uc = ts["use_case"]; only = set(args.only.split(",")) if args.only else None
    frozen = chunk_text = system = None
    if uc == 1:
        frozen = json.load(open(setp.parent / ts["tools_file"]))
        pdf = setp.parent / "02-pdf-answers.json"  # read-only: chunk text for article_search mocks, if frozen
        chunk_text = {norm(c)["id"]: c["text"] for i in (json.load(open(pdf))["items"] if pdf.exists() else [])
                      for c in (i.get("context_chunks") or [])}
    if uc == 4: system = (setp.parent / ts["system_prompt_file"]).read_text().strip()

    if uc == 4:  # warm-up: load the system prompt into the server's cache so the first item's latency isn't a cold prefill
        with post(args, {"messages": [{"role": "system", "content": system}, {"role": "user", "content": "oi"}], "max_tokens": 1}) as r: r.read()
    out = ROOT / "results" / args.setup / (setp.stem + ".jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = {}
    if out.exists():
        for l in out.read_text().splitlines():
            r = json.loads(l); rows[(r["id"], r.get("run", 0))] = r
    for item in ts["items"]:
        if only and item["id"] not in only: continue
        if item.get("status") != "approved" and not args.include_drafts:
            print(f'skip {item["id"]}: status {item.get("status")} (use --include-drafts)'); continue
        if uc == 2 and not item.get("context_chunks"):
            print(f'skip {item["id"]}: context_chunks is null (not frozen yet)'); continue
        for run in range(args.repeat):
            t0 = time.time()
            try:
                res = run_agent(args, item, ts, frozen, chunk_text) if uc == 1 else run_pdf(args, item) if uc == 2 else run_desk(args, item, system)
            except Exception as e:
                res = {"error": repr(e)}
            rows[(item["id"], run)] = {"id": item["id"], "run": run, "set": str(setp), "setup": args.setup, "model": args.model,
                                       "candidate": args.candidate, "think": args.think, "sampling": args.sampling,
                                       "wall_s": round(time.time() - t0, 2), **res}
            print(f'{item["id"]} run {run}: {"ERROR " + res["error"] if "error" in res else "done"} ({time.time() - t0:.1f}s)')
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows.values()))
    prov = out.with_suffix(".provenance.json"); write_provenance(prov, args, setp, started)
    print("wrote", out, "and", prov.name)


if __name__ == "__main__":
    main()
