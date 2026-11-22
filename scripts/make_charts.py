"""Build the README charts from results/summary/summary.json.

    python3 scripts/make_charts.py              # write chart_data.json and the SVGs (needs matplotlib)
    python3 scripts/make_charts.py --check      # stdlib only: fail if chart_data.json is stale (used by CI)

chart_data.json holds every plotted point, so CI can verify the charts against
summary.json without matplotlib and without diffing SVG bytes.

Encoding: colour = candidate, filled marker/bar = thinking off, hollow/hatched = thinking on.
Colours are the Okabe-Ito colour-blind-safe set. Each chart is written twice (light and dark)
and embedded in the README with <picture>.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUMMARY = ROOT / "results" / "summary" / "summary.json"
OUT = ROOT / "results" / "summary" / "charts"
DATA = OUT / "chart_data.json"

SETUPS = ["gemma4-nothink", "gemma4-think", "qwen3.5-9b-nothink", "qwen3.5-9b-think", "bonsai2-nothink", "bonsai2-think"]
CANDIDATE_COLOR = {"gemma4": "#0072B2", "qwen3.5-9b": "#D55E00", "bonsai2": "#009E73"}
CASES = [("01-tool-agent", "#1 Tool-calling agent"), ("02-pdf-answers", "#2 Answering from PDFs"), ("04-voice-desk", "#4 PT-BR voice assistant")]
THEMES = {
    "light": {"fg": "#24292f", "muted": "#656d76", "grid": "#d0d7de", "bg": "#ffffff"},
    "dark": {"fg": "#e6edf3", "muted": "#8b949e", "grid": "#30363d", "bg": "#0d1117"},
}


def candidate(setup):
    return setup.rsplit("-", 1)[0]


def think(setup):
    return setup.endswith("-think")


def build_data(summary):
    """Every plotted point, straight from summary.json (no rounding beyond what the summary has)."""
    by_case = {uc["id"]: {s["setup"]: s for s in uc["setups"]} for uc in summary["use_cases"]}
    rows = {"pass_rate": [], "speed": [], "memory": []}
    for cid, _ in CASES:
        for name in SETUPS:
            s = by_case[cid][name]
            base = {"use_case": cid, "setup": name, "pct": s["pass_pct"], "lo": s["ci_low_pct"], "hi": s["ci_high_pct"],
                    "content_only": cid == "04-voice-desk" and think(name)}
            rows["pass_rate"].append(base)
            rows["speed"].append({**base, "x": s["med_tok_s"]})
            rows["memory"].append({**base, "x": s["peak_footprint_gb"],
                                   "partial": "understates" in (s.get("footprint_note") or "")})
    return {"source": "results/summary/summary.json", "charts": rows}


def check():
    want = build_data(json.loads(SUMMARY.read_text()))
    have = json.loads(DATA.read_text()) if DATA.exists() else None
    if have != want:
        sys.exit(f"{DATA.relative_to(ROOT)} is stale: run `python3 scripts/make_charts.py` and commit the result")
    print("chart_data.json matches summary.json")


def style(theme):
    import matplotlib as mpl
    t = THEMES[theme]
    mpl.rcParams.update({
        "svg.hashsalt": "will-it-fit", "svg.fonttype": "path", "font.family": "DejaVu Sans", "font.size": 10,
        "figure.facecolor": t["bg"], "axes.facecolor": t["bg"], "savefig.facecolor": t["bg"],
        "text.color": t["fg"], "axes.labelcolor": t["fg"], "axes.edgecolor": t["grid"],
        "xtick.color": t["muted"], "ytick.color": t["muted"], "grid.color": t["grid"],
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "axes.axisbelow": True,
        "legend.frameon": False,
    })
    return t


def legend_handles(t):
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", color=c, markersize=8, label=n) for n, c in CANDIDATE_COLOR.items()]
    h.append(Line2D([], [], marker="o", ls="", markerfacecolor=t["bg"], markeredgecolor=t["fg"], markersize=8, label="thinking on (hollow)"))
    h.append(Line2D([], [], marker="o", ls="", color=t["fg"], markersize=8, label="thinking off (filled)"))
    return h


def draw_bars(data, theme):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    t = style(theme)
    fig, ax = plt.subplots(figsize=(9, 4.6))
    w = 0.13
    for ci, (cid, _) in enumerate(CASES):
        for si, name in enumerate(SETUPS):
            p = next(r for r in data["pass_rate"] if r["use_case"] == cid and r["setup"] == name)
            x = ci + (si - 2.5) * w
            col = CANDIDATE_COLOR[candidate(name)]
            ax.bar(x, p["pct"], w * 0.9, color=t["bg"] if think(name) else col, edgecolor=col, linewidth=1.6,
                   hatch="////" if think(name) else None, zorder=2)
            ax.errorbar(x, p["pct"], yerr=[[p["pct"] - p["lo"]], [p["hi"] - p["pct"]]], color=t["fg"], capsize=2.5, lw=1, zorder=3)
            ax.text(x, p["hi"] + 1.5, f'{p["pct"]}' + ("*" if p["content_only"] else ""), ha="center", va="bottom", fontsize=7.5, color=t["fg"])
    ax.set_xticks(range(len(CASES)), [n for _, n in CASES])
    ax.set_ylim(0, 112)
    ax.set_yticks(range(0, 101, 20))
    ax.set_ylabel("Pass rate (%), 95% CI")
    ax.grid(axis="x", visible=False)
    handles = [Patch(facecolor=c, edgecolor=c, label=n) for n, c in CANDIDATE_COLOR.items()]
    handles += [Patch(facecolor=t["bg"], edgecolor=t["fg"], hatch="////", label="thinking on (hatched)"),
                Patch(facecolor=t["fg"], edgecolor=t["fg"], label="thinking off (solid)")]
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=5, fontsize=8.5)
    fig.text(0.01, 0.005, "* #4 thinking-on setups are scored on content only (the 1 s first-sentence rule cannot apply).", fontsize=7.5, color=t["muted"])
    ax.set_title("Pass rate by setup and use case", loc="left", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    return fig


def draw_pareto(rows, theme, xlabel, title, log_x=False, note=None):
    import matplotlib.pyplot as plt
    t = style(theme)
    fig, axes = plt.subplots(1, 3, figsize=(11, 4.4), sharey=True)
    for ax, (cid, cname) in zip(axes, CASES):
        pts = [r for r in rows if r["use_case"] == cid]
        for r in pts:
            col = CANDIDATE_COLOR[candidate(r["setup"])]
            hollow = think(r["setup"])
            ax.errorbar(r["x"], r["pct"], yerr=[[r["pct"] - r["lo"]], [r["hi"] - r["pct"]]], fmt="none", ecolor=col, elinewidth=1.2, capsize=2, alpha=0.8, zorder=2)
            ax.scatter(r["x"], r["pct"], s=70, marker="o", facecolor=t["bg"] if hollow else col, edgecolor=col, linewidth=1.8, zorder=3)
            mark = ("†" if r.get("partial") else "") + ("*" if r["content_only"] else "")
            if mark:  # colour + marker already identify the setup; only flag the caveats
                ax.annotate(mark, (r["x"], r["pct"]), textcoords="offset points", xytext=(8, 4), fontsize=11, color=t["fg"])
        ax.set_title(cname, fontsize=10, loc="left")
        ax.set_xlabel(xlabel)
        if log_x: ax.set_xscale("log")
        ax.set_ylim(-4, 104)
        ax.margins(x=0.12)
    axes[0].set_ylabel("Pass rate (%), 95% CI")
    fig.suptitle(title, x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.legend(handles=legend_handles(t), loc="lower center", ncol=5, fontsize=8.5, bbox_to_anchor=(0.5, 0.0))
    foot = "* #4 thinking-on: content only, outside the <1 s race."
    if note: foot += "  " + note
    fig.text(0.01, 0.095, foot, fontsize=7.5, color=t["muted"])
    fig.tight_layout(rect=(0, 0.13, 1, 0.94))
    return fig


def main():
    summary = json.loads(SUMMARY.read_text())
    data = build_data(summary)
    OUT.mkdir(parents=True, exist_ok=True)
    DATA.write_text(json.dumps(data, indent=1) + "\n")
    import matplotlib
    matplotlib.use("svg")
    import matplotlib.pyplot as plt
    c = data["charts"]
    for theme in THEMES:
        figs = {
            "pass-rate": draw_bars(c, theme),
            "pareto-speed": draw_pareto(c["speed"], theme, "Median tokens/s (higher is faster)", "Pass rate against speed"),
            "pareto-memory": draw_pareto(c["memory"], theme, "Peak memory footprint (GB, lower is lighter)", "Pass rate against memory",
                                         note="† footprint recorded for resumed passes only, so it understates real use."),
        }
        for name, fig in figs.items():
            fig.savefig(OUT / f"{name}-{theme}.svg", format="svg", metadata={"Date": None})
            plt.close(fig)
    print(f"wrote {len(THEMES) * 3} SVGs and chart_data.json to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    check() if "--check" in sys.argv else main()
