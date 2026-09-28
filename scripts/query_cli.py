#!/usr/bin/env python3
"""検索クエリ CLI（第1層 SQLite）.

使い方:
  python scripts/query_cli.py                                   # インタラクティブ
  python scripts/query_cli.py --entity ハルベルト --aspect visual
  python scripts/query_cli.py --episode ch0057
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "search/events.db"


def run_query(conn: sqlite3.Connection, entity=None, aspect=None, episode=None):
    q = "SELECT episode, entity, aspect, observation, quote FROM events WHERE 1=1"
    params = []
    if entity:
        q += " AND entity = ?"
        params.append(entity)
    if aspect:
        q += " AND aspect = ?"
        params.append(aspect)
    if episode:
        q += " AND episode = ?"
        params.append(episode)
    q += " ORDER BY episode, event_id"
    return conn.execute(q, params).fetchall()


def show(rows) -> None:
    if not rows:
        print("該当するイベントが見つかりませんでした")
        return
    print(f"検索結果（{len(rows)}件）")
    for ep, ent, asp, obs, quote in rows:
        print(f"  [{ep}] {ent} ({asp}): {obs[:60]}")


def main() -> int:
    if not DB.exists():
        print("search/events.db が存在しません。先に build_search_index.py を実行してください。")
        return 1
    ap = argparse.ArgumentParser()
    ap.add_argument("--entity")
    ap.add_argument("--aspect")
    ap.add_argument("--episode")
    args = ap.parse_args()

    conn = sqlite3.connect(DB)
    if args.entity or args.aspect or args.episode:
        show(run_query(conn, args.entity, args.aspect, args.episode))
        conn.close()
        return 0

    # インタラクティブ
    while True:
        entity = input("エンティティ名（空白でスキップ, quit で終了）: ").strip()
        if entity == "quit":
            break
        aspect = input("アスペクト visual|name|speech|action|relationship|symbolic（空白でスキップ）: ").strip() or None
        episode = input("エピソード ch0001（空白でスキップ）: ").strip() or None
        show(run_query(conn, entity or None, aspect, episode))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
