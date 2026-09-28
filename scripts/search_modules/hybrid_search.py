"""ハイブリッド検索（構造化 + FTS5全文 + ベクトル、RRF統合）"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import List

from rich.console import Console

from .indexer import SearchIndexer
from .vector_store import VectorStore

console = Console()


class HybridSearcher:
    """ハイブリッド検索"""

    def __init__(self, db_path: Path, vector_db_path: Path, config: dict = None):
        self.indexer = SearchIndexer(db_path)
        search_cfg = (config or {}).get("search", {})
        self.vector_store = VectorStore(
            vector_db_path,
            embedding_provider=search_cfg.get("embedding_provider", "ollama"),
            embedding_model=search_cfg.get("embedding_model", "nomic-embed-text-v1.5"),
            config=config,
        )

    def close(self):
        self.indexer.close()
        self.vector_store.close()

    # ========================================================
    # 構造化クエリ（第1層）
    # ========================================================

    def search_events(self, entity: str = None, aspect: str = None,
                      episode: str = None, limit: int = 50) -> List[dict]:
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        if entity:
            query += " AND entity = ?"
            params.append(entity)
        if aspect:
            query += " AND aspect = ?"
            params.append(aspect)
        if episode:
            query += " AND episode = ?"
            params.append(episode)
        query += " ORDER BY episode, event_id LIMIT ?"
        params.append(limit)
        return [dict(row) for row in self.indexer.conn.execute(query, params).fetchall()]

    def search_claims_by_entity(self, entity: str, limit: int = 20) -> List[dict]:
        rows = self.indexer.conn.execute(
            "SELECT * FROM claims WHERE subject LIKE ? OR object LIKE ? ORDER BY valid_from LIMIT ?",
            (f"%{entity}%", f"%{entity}%", limit)).fetchall()
        return [dict(row) for row in rows]

    # ========================================================
    # 全文検索（FTS5）
    # ========================================================

    def fulltext_search(self, query: str, limit: int = 20) -> List[dict]:
        results = []
        fts_query = self._escape_fts_query(query)
        c = self.indexer.conn.cursor()

        specs = [
            ("entities_fts", "entities",
             "SELECT id, type, canonical_name AS name, file_path, canonical_name, aliases FROM entities",
             "canonical_name", "aliases"),
            ("claims_fts", "claims",
             "SELECT id, 'analytical_claim' AS type, subject||' '||predicate||' '||object AS name, file_path, subject, predicate, object FROM claims",
             "subject", "predicate", "object"),
            ("refs_fts", "refs",
             "SELECT id, 'external_reference' AS type, canonical_name AS name, file_path, canonical_name, domain FROM refs",
             "canonical_name", "domain"),
        ]
        for fts_table, base_table, base_select, *like_cols in specs:
            try:
                c.execute(f"""
                    SELECT t.id, t.type, t.name, t.file_path, bm25({fts_table}) AS rank
                    FROM {fts_table} JOIN ({base_select}) t ON {fts_table}.rowid = t.rowid
                    WHERE {fts_table} MATCH ? ORDER BY rank LIMIT ?
                """, (fts_query, limit))
                for row in c.fetchall():
                    results.append({"id": row["id"], "type": row["type"], "name": row["name"],
                                    "file_path": row["file_path"], "score": -row["rank"],
                                    "source": f"fts_{base_table}"})
            except sqlite3.OperationalError:
                pass
            # 日本語は unicode61 で分かち書きされないため、FTS が空なら LIKE にフォールバック
            if not any(r["source"] == f"fts_{base_table}" for r in results):
                where = " OR ".join(f"{col} LIKE ?" for col in like_cols)
                params = [f"%{query}%" for _ in like_cols]
                try:
                    c.execute(f"SELECT t.* FROM ({base_select}) t WHERE {where} LIMIT ?",
                              params + [limit])
                    for row in c.fetchall():
                        results.append({"id": row["id"], "type": row["type"], "name": row["name"],
                                        "file_path": row["file_path"], "score": 0.5,
                                        "source": f"like_{base_table}"})
                except sqlite3.OperationalError:
                    pass

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    @staticmethod
    def _escape_fts_query(query: str) -> str:
        # FTS5 の特殊文字をエスケープ（クォートで囲む方が安全）
        q = query.strip()
        escaped = q.replace('"', '""')
        return f'"{escaped}"'

    # ========================================================
    # ベクトル検索（第3層）
    # ========================================================

    def semantic_search(self, query: str, limit: int = 10, doc_type: str = None) -> List[dict]:
        return self.vector_store.search(query, limit=limit, doc_type=doc_type)

    # ========================================================
    # ハイブリッド検索（RRF）
    # ========================================================

    def hybrid_search(self, query: str, limit: int = 10) -> List[dict]:
        fts_results = self.fulltext_search(query, limit=limit * 2)
        try:
            semantic_results = self.semantic_search(query, limit=limit * 2)
        except Exception as e:
            console.print(f"[dim]ベクトル検索スキップ（埋め込みプロバイダ未起動？）: {e}[/dim]")
            semantic_results = []

        rrf_scores = {}
        k = 60

        for rank, result in enumerate(fts_results):
            doc_id = result["id"]
            entry = rrf_scores.setdefault(doc_id, {
                "id": doc_id, "name": result.get("name", ""),
                "type": result.get("type", ""), "file_path": result.get("file_path", ""),
                "score": 0.0, "sources": [],
            })
            entry["score"] += 1.0 / (k + rank + 1)
            entry["sources"].append("fts")

        for rank, result in enumerate(semantic_results):
            doc_id = result["id"]
            entry = rrf_scores.setdefault(doc_id, {
                "id": doc_id, "name": result.get("text_content", "")[:50],
                "type": result.get("doc_type", ""),
                "file_path": result.get("metadata", {}).get("file_path", ""),
                "score": 0.0, "sources": [],
            })
            entry["score"] += 1.0 / (k + rank + 1)
            entry["sources"].append("semantic")

        return sorted(rrf_scores.values(), key=lambda x: x["score"], reverse=True)[:limit]
