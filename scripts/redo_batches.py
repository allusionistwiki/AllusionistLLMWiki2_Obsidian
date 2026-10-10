#!/usr/bin/env python3
"""thin/events 欠損話の再解析を 10 話バッチで完走させる（detached 実行用）.

セッション切断で殺されないよう Start-Process で切り離して実行する。
進捗は data/redo_log.txt に追記（tail -f で監視）。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "data" / "redo_log.txt"
LIST = ROOT / "data" / "thin_redo.txt"


def main() -> None:
    chs = [int(x) for x in LIST.read_text(encoding="utf-8").split(",") if x.strip()]
    with LOG.open("a", encoding="utf-8") as log:
        log.write(f"=== redo start: {len(chs)} 話 {chs}\n", )
        for i in range(0, len(chs), 10):
            batch = chs[i:i + 10]
            r = subprocess.run(
                [sys.executable, "scripts/run_analysis_parallel.py",
                 "--only", ",".join(map(str, batch))],
                cwd=ROOT, capture_output=True, text=True)
            tail = (r.stdout + r.stderr).strip().splitlines()[-4:]
            log.write(f"batch {batch[0]}-{batch[-1]} rc={r.returncode}: "
                      + " / ".join(tail) + "\n")
            log.flush()
        log.write("REDO ALL DONE\n")


if __name__ == "__main__":
    main()
