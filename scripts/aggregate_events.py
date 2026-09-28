#!/usr/bin/env python3
"""第1層イベント層（work/events/*.jsonl）から第2層中間集約層（work/staging/staging_chNNNN.yaml）を生成.

使い方:
  python scripts/aggregate_events.py          # 全イベントファイルを集約
  python scripts/aggregate_events.py ch0057   # 1章分だけ集約
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT, WORK_DIR


def rel(p) -> str:
    try:
        return str(Path(p).relative_to(ROOT))
    except ValueError:
        return str(p)

# entity_type → 正規層プレフィックス（命名規則 docs/naming-convention.md 準拠）
TYPE_PREFIX = {
    "character": "char",
    "terminology": "term",
    "organization": "org",
    "item": "item",
    "motif": "motif",
    "relationship": "relation",
    "phrase": "phrase",
}


def aggregate_chapter(chapter: str, events_dir: Path, staging_dir: Path) -> bool:
    events_file = events_dir / f"{chapter}.jsonl"
    if not events_file.exists():
        return False

    events = [json.loads(line) for line in events_file.read_text(encoding="utf-8").splitlines() if line.strip()]

    entities = defaultdict(lambda: {"entity_type": None, "aspects": defaultdict(list)})
    for event in events:
        e = entities[event["entity"]]
        e["entity_type"] = event.get("entity_type", "character")
        e["aspects"][event["aspect"]].append({
            "event_ref": event["event_id"],
            "quote": event.get("quote", ""),
            "locator": event.get("locator", {}),
            "spoiler_after": event.get("spoiler_after", chapter),
        })

    staging_data = {
        "episode": chapter,
        "created": date.today().isoformat(),
        "status": "pending_merge",
        "entities": [],
    }
    for entity_name, entity_data in entities.items():
        prefix = TYPE_PREFIX.get(entity_data["entity_type"], "term")
        staging_data["entities"].append({
            "canonical_target": f"[[E_{prefix}_{entity_name}]]",
            "entity_type": entity_data["entity_type"],
            "aspects": {a: {"observations": obs} for a, obs in entity_data["aspects"].items()},
            "first_appearance_candidate": True,
        })

    output_path = staging_dir / f"staging_{chapter}.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        yaml.dump(staging_data, allow_unicode=True, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    print(f"OK {rel(output_path)} に集約（{len(staging_data['entities'])} エンティティ）")
    return True


def main() -> int:
    events_dir = WORK_DIR / "events"
    staging_dir = WORK_DIR / "staging"
    if len(sys.argv) > 1:
        chapters = [sys.argv[1]]
    else:
        chapters = [f.stem for f in sorted(events_dir.glob("*.jsonl"))]
    if not chapters:
        print("work/events/ に .jsonl がありません")
        return 0
    n = sum(1 for c in chapters if aggregate_chapter(c, events_dir, staging_dir))
    print(f"\n{n}/{len(chapters)} 章を集約")
    return 0


if __name__ == "__main__":
    sys.exit(main())
