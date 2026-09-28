#!/usr/bin/env python3
"""イベント層（work/events/*.jsonl）から SQLite 検索インデックス（search/events.db）を構築.

使い方:
  python scripts/build_search_index.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def create_database(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            episode TEXT NOT NULL,
            entity TEXT NOT NULL,
            entity_type TEXT,
            aspect TEXT,
            observation TEXT,
            quote TEXT,
            spoiler_after TEXT,
            created TEXT
        )
        """
    )
    cur.execute("CREATE INDEX IF NOT EXISTS idx_entity ON events(entity)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_aspect ON events(aspect)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_episode ON events(episode)")
    conn.commit()
    return conn


def insert_events(conn: sqlite3.Connection, events_dir: Path) -> int:
    cur = conn.cursor()
    n = 0
    for jsonl_file in sorted(events_dir.glob("*.jsonl")):
        for line in jsonl_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            ev = json.loads(line)
            cur.execute(
                "INSERT OR REPLACE INTO events "
                "(event_id, episode, entity, entity_type, aspect, observation, quote, spoiler_after, created) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ev["event_id"], ev["episode"], ev["entity"], ev.get("entity_type"),
                 ev.get("aspect"), ev.get("observation"), ev.get("quote"),
                 ev.get("spoiler_after"), ev.get("created")),
            )
            n += 1
    conn.commit()
    return n


def main() -> int:
    db_path = ROOT / "search/events.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = create_database(db_path)
    n = insert_events(conn, ROOT / "work/events")
    print(f"OK {db_path.relative_to(ROOT)} に {n} 件のインデックスを構築")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
