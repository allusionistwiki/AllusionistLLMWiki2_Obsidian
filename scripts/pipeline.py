#!/usr/bin/env python3
"""1章の全工程を自動実行するパイプライン（LLM auto-review 標準運用）.

  events抽出 → facts抽出 → analysis提案 → autopilot(LLM審査・昇格) → 出力整形 → lint

人間関与は scripts/human_ops.py（reject/修正指示/追記）のみ。
全生成物は review_status: llm_verified（人間 human_verified への置換対象として区別）。

使い方:
  python scripts/pipeline.py 33          # ch0033 1章
  python scripts/pipeline.py 33 40       # ch0033-0040
  python scripts/pipeline.py             # config の chapter_range 分
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_client import create_client, load_config
from validate_event import load_schema
from extract_chapter import process_chapter
from extract_facts import process_facts
from analyze_chapter import analyze_chapter
from autopilot_review import process as autopilot_process

ROOT = Path(__file__).resolve().parent.parent


def run_fixers() -> None:
    for script in ("fix_autopilot_output.py", "fix_autopilot_output2.py"):
        subprocess.run([sys.executable, f"scripts/{script}"], cwd=ROOT, check=False)


def main() -> int:
    args = [int(a) for a in sys.argv[1:]]
    config = load_config()
    if not args:
        args = list(range(config["chapter_range"]["start"],
                          config["chapter_range"]["end"] + 1))
    schema = load_schema("event.schema.json")
    client = create_client(config)
    results = []
    for c in args:
        stages = []
        for name, fn in (
            ("events", lambda: process_chapter(c, config, client, schema)),
            ("facts", lambda: process_facts(c, config, client)),
            ("analysis", lambda: analyze_chapter(c, config, client)),
            ("autopilot", lambda: autopilot_process(c, config, client)),
        ):
            try:
                ok = fn()
                stages.append(f"{name}={'ok' if ok else 'skip'}")
            except Exception as e:
                stages.append(f"{name}=ERR({e})")
        print(f"[ch{c:04d}] " + " ".join(stages), flush=True)
        results.append((c, stages))
    run_fixers()
    print("=== 出力整形（fixers）完了。lint 確認: python scripts/lint.py --severity error ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
