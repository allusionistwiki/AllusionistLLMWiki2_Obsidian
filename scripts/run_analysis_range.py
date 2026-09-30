#!/usr/bin/env python3
"""ch0033〜ch0272 の解析をチャンク実行し、チャンクごとにコミットする.

pipeline.py は 1 話ずつ events→facts→analysis→autopilot を回す（LLM 直列）。
10 話ごとに区切って commit_all（vault+work 相互参照コミット）し、
progress ファイルに到達話数を記録するので、中断しても続きから再開できる。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROGRESS = ROOT / "data" / "analysis_progress.txt"
START, END = 33, 272
CHUNK = 10


def main() -> None:
    done = 0
    if PROGRESS.exists():
        done = int(PROGRESS.read_text(encoding="utf-8").strip() or 0)
    start = max(START, done + 1)
    print(f"再開: ch{start:04d}（完了 {done} 話）", flush=True)
    for lo in range(start, END + 1, CHUNK):
        hi = min(lo + CHUNK - 1, END)
        args = [str(n) for n in range(lo, hi + 1)]
        r = subprocess.run([sys.executable, "scripts/pipeline.py", *args],
                           cwd=ROOT, check=False)
        PROGRESS.write_text(str(hi), encoding="utf-8")
        print(f"[chunk ch{lo:04d}-ch{hi:04d}] pipeline rc={r.returncode}", flush=True)
        subprocess.run([sys.executable, "scripts/commit_all.py", "-m",
                        f"ch{lo:04d}-ch{hi:04d} 解析（events/facts/analysis/autopilot）"],
                       cwd=ROOT, check=False)
        print(f"[chunk ch{lo:04d}-ch{hi:04d}] committed", flush=True)
    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
