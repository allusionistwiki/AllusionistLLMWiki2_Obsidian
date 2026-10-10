#!/usr/bin/env python3
"""analysis は揃っているのに autopilot 審査の空応答で全件 reject された章の再審査.

data/autopilot_redo.txt の話番号に対し autopilot_review.process だけ再実行し、
その後 merge_all → 表示層 → lint → commit_all を一度だけ行う。
進捗は data/autopilot_redo_log.txt に追記（detached 実行用）。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

LOG = ROOT / "data" / "autopilot_redo_log.txt"
LIST = ROOT / "data" / "autopilot_redo.txt"


def main() -> None:
    from llm_client import create_client, load_config
    from autopilot_review import process

    chs = [int(x) for x in LIST.read_text(encoding="utf-8").split(",") if x.strip()]
    cfg = load_config()
    client = create_client(cfg)
    with LOG.open("a", encoding="utf-8") as log:
        log.write(f"=== autopilot redo start: {len(chs)} 話 {chs}\n")
        log.flush()
        for c in chs:
            try:
                process(c, cfg, client)
                log.write(f"ch{c:04d} done\n")
            except Exception as e:
                log.write(f"ch{c:04d} ERR: {e}\n")
            log.flush()
        for cmd in (
            ["scripts/merge_all.py"],
            ["scripts/shorten_titles.py"],
            ["scripts/build_entities.py"],
            ["scripts/build_relationship_map.py"],
            ["scripts/build_public_index.py"],
            ["scripts/lint.py", "--severity", "error"],
        ):
            r = subprocess.run([sys.executable] + cmd, cwd=ROOT,
                               capture_output=True, text=True)
            tail = (r.stdout + r.stderr).strip().splitlines()[-2:]
            log.write(f"{' '.join(cmd)} rc={r.returncode}: " + " / ".join(tail) + "\n")
            log.flush()
        r = subprocess.run(
            [sys.executable, "scripts/commit_all.py", "-m",
             "autopilot 審査バグ修正（json_object 厳格モードの空応答で全件reject→lenient主経路へ）"
             "に伴う 21 話再審査・昇格（ch0041,0118,0143,0147,0172,0187,0197,0200,0202,0214,"
             "0220,0225,0226,0229,0234,0246,0254,0258,0263,0268,0272）+ 表示層再生成"],
            cwd=ROOT, capture_output=True, text=True)
        tail = (r.stdout + r.stderr).strip().splitlines()[-2:]
        log.write(f"commit rc={r.returncode}: " + " / ".join(tail) + "\n")
        log.write("AUTOPILOT REDO DONE\n")
        log.flush()


if __name__ == "__main__":
    main()
