"""SQLite + FTS5 インデックスの構築（正規層6種 + 第1層イベント）.

注意: `references` は SQLite 予約語のためテーブル名は refs を使う。
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import yaml
from rich.console import Console
from rich.progress import track

console = Console()


class SearchIndexer:
    """検索インデックスの構築と管理"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        self.conn.close()

    # ========================================================
    # スキーマ作成
    # ========================================================

    def create_schema(self):
        c = self.conn.cursor()

        c.execute("""
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
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                id TEXT PRIMARY KEY,
                type TEXT,
                subtype TEXT,
                canonical_name TEXT,
                aliases TEXT,
                first_appearance TEXT,
                spoiler_after TEXT,
                file_path TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                id TEXT PRIMARY KEY,
                subject TEXT,
                predicate TEXT,
                object TEXT,
                epistemic_status TEXT,
                review_status TEXT,
                evidence_strength TEXT,
                valid_from TEXT,
                spoiler_after TEXT,
                evidence_json TEXT,
                mapping_json TEXT,
                file_path TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS mysteries (
                id TEXT PRIMARY KEY,
                mystery_status TEXT,
                introduced TEXT,
                hinted TEXT,
                resolved TEXT,
                resolution_summary TEXT,
                related_claims TEXT,
                file_path TEXT
            )
        """)
        # references は予約語 → refs
        c.execute("""
            CREATE TABLE IF NOT EXISTS refs (
                id TEXT PRIMARY KEY,
                subtype TEXT,
                canonical_name TEXT,
                domain TEXT,
                aliases TEXT,
                referenced_by_json TEXT,
                relations_json TEXT,
                file_path TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id TEXT PRIMARY KEY,
                chapter TEXT,
                arc TEXT,
                characters TEXT,
                claims TEXT,
                mysteries TEXT,
                refs TEXT,
                spoiler_after TEXT,
                file_path TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS arcs (
                id TEXT PRIMARY KEY,
                name TEXT,
                arc_number INTEGER,
                chapter_start TEXT,
                chapter_end TEXT,
                theme TEXT,
                macro_analogy TEXT,
                file_path TEXT
            )
        """)

        # FTS5 全文検索
        c.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(
                id, canonical_name, aliases,
                content='entities', content_rowid='rowid', tokenize='unicode61')
        """)
        c.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS claims_fts USING fts5(
                id, subject, predicate, object, evidence_json,
                content='claims', content_rowid='rowid', tokenize='unicode61')
        """)
        c.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS mysteries_fts USING fts5(
                id, resolution_summary,
                content='mysteries', content_rowid='rowid', tokenize='unicode61')
        """)
        c.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS refs_fts USING fts5(
                id, canonical_name, domain,
                content='refs', content_rowid='rowid', tokenize='unicode61')
        """)
        c.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS episodes_fts USING fts5(
                id, chapter, characters,
                content='episodes', content_rowid='rowid', tokenize='unicode61')
        """)

        for stmt in [
            "CREATE INDEX IF NOT EXISTS idx_events_entity ON events(entity)",
            "CREATE INDEX IF NOT EXISTS idx_events_aspect ON events(aspect)",
            "CREATE INDEX IF NOT EXISTS idx_events_episode ON events(episode)",
            "CREATE INDEX IF NOT EXISTS idx_claims_subject ON claims(subject)",
            "CREATE INDEX IF NOT EXISTS idx_claims_object ON claims(object)",
            "CREATE INDEX IF NOT EXISTS idx_claims_predicate ON claims(predicate)",
        ]:
            c.execute(stmt)
        self.conn.commit()

    # ========================================================
    # データ挿入
    # ========================================================

    def clear_all(self):
        c = self.conn.cursor()
        for table in ["events", "entities", "claims", "mysteries", "refs", "episodes", "arcs"]:
            c.execute(f"DELETE FROM {table}")
        self.conn.commit()

    def insert_event(self, e: dict):
        self.conn.execute(
            "INSERT OR REPLACE INTO events (event_id, episode, entity, entity_type, aspect,"
            " observation, quote, spoiler_after, created) VALUES (?,?,?,?,?,?,?,?,?)",
            (e.get("event_id"), e.get("episode"), e.get("entity"), e.get("entity_type"),
             e.get("aspect"), e.get("observation"), e.get("quote"),
             e.get("spoiler_after"), e.get("created")))

    def insert_entity(self, x: dict):
        self.conn.execute(
            "INSERT OR REPLACE INTO entities (id, type, subtype, canonical_name, aliases,"
            " first_appearance, spoiler_after, file_path) VALUES (?,?,?,?,?,?,?,?)",
            (x.get("id"), x.get("type"), x.get("subtype"), x.get("canonical_name"),
             json.dumps(x.get("aliases", []) or [], ensure_ascii=False),
             x.get("first_appearance"), x.get("spoiler_after"), x.get("file_path")))

    def insert_claim(self, x: dict):
        self.conn.execute(
            "INSERT OR REPLACE INTO claims (id, subject, predicate, object, epistemic_status,"
            " review_status, evidence_strength, valid_from, spoiler_after, evidence_json,"
            " mapping_json, file_path) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (x.get("id"), x.get("subject"), x.get("predicate"), x.get("object"),
             x.get("epistemic_status"), x.get("review_status"), x.get("evidence_strength"),
             x.get("valid_from"), x.get("spoiler_after"),
             json.dumps(x.get("evidence", []) or [], ensure_ascii=False),
             json.dumps(x.get("mapping", []) or [], ensure_ascii=False), x.get("file_path")))

    def insert_mystery(self, x: dict):
        self.conn.execute(
            "INSERT OR REPLACE INTO mysteries (id, mystery_status, introduced, hinted,"
            " resolved, resolution_summary, related_claims, file_path) VALUES (?,?,?,?,?,?,?,?)",
            (x.get("id"), x.get("mystery_status"), x.get("introduced"),
             json.dumps(x.get("hinted", []) or [], ensure_ascii=False), x.get("resolved"),
             x.get("resolution_summary"),
             json.dumps(x.get("related_claims", []) or [], ensure_ascii=False), x.get("file_path")))

    def insert_reference(self, x: dict):
        self.conn.execute(
            "INSERT OR REPLACE INTO refs (id, subtype, canonical_name, domain, aliases,"
            " referenced_by_json, relations_json, file_path) VALUES (?,?,?,?,?,?,?,?)",
            (x.get("id"), x.get("subtype"), x.get("canonical_name"), x.get("domain"),
             json.dumps(x.get("aliases", []) or [], ensure_ascii=False),
             json.dumps(x.get("referenced_by", []) or [], ensure_ascii=False),
             json.dumps(x.get("relations", []) or [], ensure_ascii=False), x.get("file_path")))

    def insert_episode(self, x: dict):
        self.conn.execute(
            "INSERT OR REPLACE INTO episodes (id, chapter, arc, characters, claims,"
            " mysteries, refs, spoiler_after, file_path) VALUES (?,?,?,?,?,?,?,?,?)",
            (x.get("id"), x.get("chapter"), x.get("arc"),
             json.dumps(x.get("characters", []) or [], ensure_ascii=False),
             json.dumps(x.get("claims", []) or [], ensure_ascii=False),
             json.dumps(x.get("mysteries", []) or [], ensure_ascii=False),
             json.dumps(x.get("references", []) or [], ensure_ascii=False),
             x.get("spoiler_after"), x.get("file_path")))

    def insert_arc(self, x: dict):
        self.conn.execute(
            "INSERT OR REPLACE INTO arcs (id, name, arc_number, chapter_start, chapter_end,"
            " theme, macro_analogy, file_path) VALUES (?,?,?,?,?,?,?,?)",
            (x.get("id"), x.get("name"), x.get("arc_number"), x.get("chapter_start"),
             x.get("chapter_end"), x.get("theme"), x.get("macro_analogy"), x.get("file_path")))

    def rebuild_fts(self):
        c = self.conn.cursor()
        # external-content FTS5 の正規リビルド（直接 DELETE は disk image を壊す）
        for fts_table in ["entities_fts", "claims_fts", "mysteries_fts", "refs_fts", "episodes_fts"]:
            c.execute(f"INSERT INTO {fts_table}({fts_table}) VALUES('rebuild')")
        self.conn.commit()

    # ========================================================
    # Vault からの読み込み
    # ========================================================

    def index_vault(self, vault_path: Path, events_path: Path = None):
        self.clear_all()

        if events_path and events_path.exists():
            event_files = list(events_path.glob("*.jsonl"))
            console.print(f"[cyan]イベントをインデックス化中... ({len(event_files)} ファイル)[/cyan]")
            for event_file in track(event_files, description="events"):
                try:
                    for line in event_file.read_text(encoding="utf-8").splitlines():
                        if line.strip():
                            self.insert_event(json.loads(line))
                except Exception as e:
                    console.print(f"[yellow]⚠️ {event_file.name}: {e}[/yellow]")

        md_files = list(vault_path.rglob("*.md"))
        console.print(f"[cyan]Vaultをインデックス化中... ({len(md_files)} ファイル)[/cyan]")
        for md_file in track(md_files, description="vault"):
            try:
                fm, _ = self._parse_frontmatter(md_file.read_text(encoding="utf-8"))
                if not fm or "type" not in fm:
                    continue
                file_type = fm["type"]
                fm["file_path"] = str(md_file.relative_to(vault_path))
                if file_type == "entity":
                    self.insert_entity(fm)
                elif file_type == "analytical_claim":
                    self.insert_claim(fm)
                elif file_type == "mystery":
                    timeline = fm.get("timeline", {})
                    fm["introduced"] = timeline.get("introduced")
                    fm["hinted"] = timeline.get("hinted", [])
                    fm["resolved"] = timeline.get("resolved")
                    self.insert_mystery(fm)
                elif file_type == "external_reference":
                    self.insert_reference(fm)
                elif file_type == "episode":
                    self.insert_episode(fm)
                elif file_type == "arc":
                    chapter_range = fm.get("chapter_range", {})
                    fm["chapter_start"] = chapter_range.get("start")
                    fm["chapter_end"] = chapter_range.get("end")
                    self.insert_arc(fm)
            except Exception as e:
                console.print(f"[yellow]⚠️ {md_file.name}: {e}[/yellow]")

        console.print("[cyan]FTSインデックスを構築中...[/cyan]")
        self.rebuild_fts()
        self.conn.commit()

        c = self.conn.cursor()
        console.print("\n[bold green]✅ インデックス構築完了[/bold green]")
        for table in ["events", "entities", "claims", "mysteries", "refs", "episodes", "arcs"]:
            c.execute(f"SELECT COUNT(*) FROM {table}")
            console.print(f"  {table}: {c.fetchone()[0]} 件")

    @staticmethod
    def _parse_frontmatter(content: str) -> tuple[dict, str]:
        match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
        if not match:
            return {}, content
        try:
            fm = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            fm = {}
        return fm, match.group(2)
