#!/usr/bin/env python3
"""3KB 未満の薄い events/facts/staging を reject（削除）し、対象話を再解析する.

  python scripts/redo_thin_chapters.py --list      # 対象話の表示
  python scripts/redo_thin_chapters.py --clean     # 薄い成果物を削除
  python scripts/redo_thin_chapters.py --redo      # 削除後、章並列で再解析
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT.parent / "AllusionistLLMWiki2_Work"
THRESHOLD = 3000
DIRS = ("events", "facts", "staging")
REDO_LIST = ROOT / "data" / "thin_redo.txt"


def thin_chapters() -> list[int]:
    bad: set[int] = set()
    for d in DIRS:
        p = WORK / d
        if not p.exists():
            continue
        for f in p.iterdir():
            if not f.is_file():
                continue
            m = re.search(r"ch(\d{4})", f.name)
            if m and f.stat().st_size < THRESHOLD:
                c = int(m.group(1))
                if c >= 84:  # 検証済み ch0083 以前は対象外
                    bad.add(c)
    return sorted(bad)


def clean(chs: list[int]) -> int:
    n = 0
    for c in chs:
        for d in DIRS:
            p = WORK / d
            for f in (p.glob(f"ch{c:04d}.jsonl"),
                      p.glob(f"staging_ch{c:04d}.yaml"),
                      p.glob(f"analysis_ch{c:04d}.yaml")):
                for x in f:
                    if x.stat().st_size < THRESHOLD:
                        x.unlink()
                        n += 1
    return n


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--list"
    chs = thin_chapters()
    if mode == "--list":
        print(f"薄い成果物を持つ話 {len(chs)} 件: {chs}")
        return
    if mode == "--clean":
        n = clean(chs)
        if chs:
            REDO_LIST.write_text(",".join(str(c) for c in chs), encoding="utf-8")
        print(f"削除: {n} ファイル（{len(chs)} 話分）→ data/thin_redo.txt に記録")
        return
    if mode == "--redo":
        if REDO_LIST.exists():
            chs = [int(x) for x in REDO_LIST.read_text(encoding="utf-8").split(",") if x.strip()]
        removed = clean(chs)
        print(f"削除: {removed} ファイル → 再解析 {len(chs)} 話", flush=True)
        if not chs:
            print("再解析対象なし", flush=True)
            return
        r = subprocess.run([sys.executable, "scripts/run_analysis_parallel.py",
                            "--only", ",".join(str(c) for c in chs)],
                           cwd=ROOT)
        if r.returncode == 0:
            REDO_LIST.unlink(missing_ok=True)
        sys.exit(r.returncode)


if __name__ == "__main__":
    main()
