"""Merge the extra stats from results/<setup>/grades.json into results/summary/summary.json.

Only adds keys (fail_types, wall_s_total, answerable, unanswerable); never renames or
removes one, so the website that reads summary.json keeps working. Needs the local raw
results (they are git-ignored), so run it on the machine that ran the eval:

    for d in results/*-*think; do python3 runner/grade.py $d; done
    python3 scripts/add_summary_extras.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUMMARY = ROOT / "results" / "summary" / "summary.json"
NEW_KEYS = ("fail_types", "wall_s_total", "answerable", "unanswerable")


def main():
    summary = json.loads(SUMMARY.read_text())
    for uc in summary["use_cases"]:
        for s in uc["setups"]:
            gf = ROOT / "results" / s["setup"] / "grades.json"
            if not gf.exists():
                print(f'skip {s["setup"]} {uc["id"]}: no grades.json')
                continue
            g = json.loads(gf.read_text()).get(uc["id"])
            if not g:
                continue
            for k in NEW_KEYS:
                if k in g:
                    s[k] = g[k]
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
