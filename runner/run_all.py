#!/usr/bin/env python3
"""Full run: every candidate x thinking on/off x test set, --repeat 3.

Starts one llama-server per candidate, waits for /health, runs both thinking modes, stops it.
While the server is up, samples its memory every 2 s and writes the peak to
results/<setup>/resources.json. Safe to re-run: run.py skips items that already have a result.
"""
import argparse, datetime, json, re, subprocess, sys, threading, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GGUF = Path("/Volumes/ZX20/models/gguf")
CANDIDATES = [  # cheapest first, so early results arrive early
    ("gemma4", "gemma-4-E4B-it-Q4_K_M.gguf"),
    ("qwen3.5-9b", "Qwen3.5-9B-Q4_K_M.gguf"),
    ("bonsai2", "Ternary-Bonsai-2-27B-Q2_0.gguf"),
]
SETS = ["04-voice-desk.json", "01-tool-agent.json", "02-pdf-answers.json"]
PORT = 8080
SERVER_ARGS = ["-c", "8192", "-ngl", "99", "-np", "1", "--port", str(PORT)]
UNITS = {"B": 1 / 2**20, "KB": 1 / 1024, "MB": 1, "GB": 1024}


def log(*a): print(datetime.datetime.now().strftime("%H:%M:%S"), *a, flush=True)


def footprint_mb(pid):
    """Physical footprint (includes Metal/GPU allocations on Apple Silicon), in MB."""
    o = subprocess.run(["footprint", "-p", str(pid)], capture_output=True, text=True).stdout
    m = re.search(r"Footprint:\s*([\d.]+)\s*(B|KB|MB|GB)", o)
    return float(m.group(1)) * UNITS[m.group(2)] if m else None


def rss_mb(pid):
    o = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    return int(o) / 1024 if o else None


class MemSampler(threading.Thread):
    def __init__(self, pid):
        super().__init__(daemon=True); self.pid, self.stop, self.peak = pid, threading.Event(), {"footprint_mb": 0, "rss_mb": 0}
    def run(self):
        while not self.stop.is_set():
            for k, f in (("footprint_mb", footprint_mb), ("rss_mb", rss_mb)):
                v = f(self.pid)
                if v: self.peak[k] = max(self.peak[k], v)
            self.stop.wait(2)


def healthy():
    try:
        with urllib.request.urlopen(f"http://localhost:{PORT}/health", timeout=5) as r: return r.status == 200
    except Exception: return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--only-candidates", help="comma list, e.g. gemma4,qwen3.5-9b")
    p.add_argument("--repeat", type=int, default=3)
    a = p.parse_args()
    want = set(a.only_candidates.split(",")) if a.only_candidates else None
    if healthy(): sys.exit(f"something already serves port {PORT}; stop it first")
    for cand, fname in CANDIDATES:
        if want and cand not in want: continue
        gguf = GGUF / fname
        log(f"starting llama-server for {cand}")
        srv_log = open(ROOT / "results" / f".server-{cand}.log", "a")
        srv = subprocess.Popen(["llama-server", "-m", str(gguf), *SERVER_ARGS], stdout=srv_log, stderr=subprocess.STDOUT)
        try:
            t0 = time.time()
            while not healthy():
                if srv.poll() is not None: sys.exit(f"llama-server for {cand} exited; see results/.server-{cand}.log")
                time.sleep(5)
            log(f"{cand} ready after {time.time() - t0:.0f}s")
            for think in ("off", "on"):
                setup = f"{cand}-{'think' if think == 'on' else 'nothink'}"
                mem = MemSampler(srv.pid); mem.start(); started = time.time()
                for s in SETS:
                    log(f"{setup}: {s}")
                    subprocess.run([sys.executable, str(ROOT / "runner" / "run.py"), "--set", f"testsets/{s}",
                                    "--base-url", f"http://localhost:{PORT}/v1", "--model", cand, "--candidate", cand,
                                    "--think", think, "--setup", setup, "--repeat", str(a.repeat), "--gguf", str(gguf)],
                                   cwd=ROOT, check=False)
                mem.stop.set(); mem.join()
                res = ROOT / "results" / setup / "resources.json"
                res.write_text(json.dumps({"peak": mem.peak, "server_args": SERVER_ARGS, "sample_every_s": 2,
                                           "wall_s": round(time.time() - started), "machine": "Apple M2, 16 GB"}, indent=1))
                log(f"{setup} done: peak footprint {mem.peak['footprint_mb']:.0f} MB, {time.time() - started:.0f}s")
        finally:
            srv.terminate()
            try: srv.wait(30)
            except subprocess.TimeoutExpired: srv.kill()
    log("all done")


if __name__ == "__main__":
    main()
