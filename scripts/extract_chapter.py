#!/usr/bin/env python3
"""1章分の原文（raw/chNNNN.txt）からイベントを抽出し work/events/chNNNN.jsonl へ書き込む.

使い方:
  python scripts/extract_chapter.py            # config.yaml の chapter_range 分を処理
  python scripts/extract_chapter.py 57         # ch0057 1章だけ処理
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_client import create_client, extract_events, load_config  # noqa: E402
from validate_event import load_schema, validate_record  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def process_chapter(chapter_num: int, config: dict, client, schema: dict) -> bool:
    chapter = f"ch{chapter_num:04d}"
    raw_path = ROOT / config["paths"]["raw"] / f"{chapter}.txt"
    if not raw_path.exists():
        print(f"WARN {raw_path} が存在しません")
        return False

    print(f"\n[{chapter}] 処理中...")
    raw_text = raw_path.read_text(encoding="utf-8")
    events = extract_events(
        client, config["llm"]["model"], chapter, raw_text,
        temperature=config["llm"].get("temperature", 0.1),
    )
    print(f"   {len(events)} 件のイベントを抽出")

    valid_events, invalid = [], 0
    for event in events:
        event.setdefault("created", date.today().isoformat())
        errs = validate_record(event, schema)
        if errs:
            invalid += 1
            print(f"   NG event: {errs}")
        else:
            valid_events.append(event)

    output_path = ROOT / config["paths"]["work"] / "events" / f"{chapter}.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for event in valid_events:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    print(f"   OK {output_path.relative_to(ROOT)} に {len(valid_events)} 件書き込み")
    if invalid:
        print(f"   WARN {invalid} 件が無効（スキップ）")
    return True


def main() -> int:
    config = load_config()
    schema = load_schema("event.schema.json")

    if len(sys.argv) > 1:
        chapters = [int(sys.argv[1])]
    else:
        chapters = list(range(config["chapter_range"]["start"], config["chapter_range"]["end"] + 1))

    client = create_client(config)
    ok = sum(1 for c in chapters if process_chapter(c, config, client, schema))
    print(f"\n完了: {ok}/{len(chapters)} 章を処理")
    return 0 if ok == len(chapters) else 1


if __name__ == "__main__":
    sys.exit(main())
