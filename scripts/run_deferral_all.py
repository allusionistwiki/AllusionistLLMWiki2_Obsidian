#!/usr/bin/env python3
"""全 272 話の deferral/appearance 専用再解析（resume 対応・ログ付き）."""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(r"C:/Users/d5dx/Downloads/Code/AllusionistLLMWiki2")
OUT = ROOT.parent / "AllusionistLLMWiki2_Work" / "deferral_facts"
LOG = ROOT / "data" / "deferral_redo_log.txt"

chapters = sorted(p.stem for p in (ROOT / "raw").glob("ch*.txt"))
todo = [c for c in chapters if not (OUT / f"{c}.jsonl").exists()]
with LOG.open("a", encoding="utf-8") as fh:
    fh.write(f"=== run start {datetime.now():%F %T} todo={len(todo)} ===\n")
for i, ch in enumerate(todo, 1):
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "extract_deferral_appearance.py"), ch],
                       capture_output=True, text=True, cwd=str(ROOT), timeout=1800)
    tail = (r.stdout.strip().splitlines() or [""])[-1]
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"{i}/{len(todo)} [{ch}] {tail} rc={r.returncode}\n")
    if r.returncode != 0:
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"  stderr: {r.stderr[-300:]}\n")
with LOG.open("a", encoding="utf-8") as fh:
    fh.write(f"=== DEFERRAL REDO DONE {datetime.now():%F %T} ===\n")
