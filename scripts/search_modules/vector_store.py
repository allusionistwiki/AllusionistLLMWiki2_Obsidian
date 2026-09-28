"""ベクトル検索（埋め込み）: ollama / openai_compatible（MiaAI-Lab）プロバイダ対応"""
from __future__ import annotations

import json
import sqlite3
import struct
from pathlib import Path
from typing import List

from rich.console import Console

console = Console()


class VectorStore:
    """ベクトルストア（SQLite embeddings テーブル + cosine 類似度）"""

    def __init__(self, db_path: Path, embedding_provider: str = "ollama",
                 embedding_model: str = "nomic-embed-text-v1.5", config: dict = None):
        self.db_path = db_path
        self.embedding_provider = embedding_provider
        self.embedding_model = embedding_model
        self.config = config or {}
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_schema()

    def _create_schema(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT PRIMARY KEY,
                doc_type TEXT,
                text_content TEXT,
                vector BLOB,
                metadata TEXT
            )
        """)
        self.conn.commit()

    def close(self):
        self.conn.close()

    # ========================================================
    # 埋め込み生成
    # ========================================================

    def embed(self, text: str) -> List[float]:
        if self.embedding_provider == "ollama":
            return self._embed_ollama(text)
        elif self.embedding_provider == "openai_compatible":
            return self._embed_openai_compatible(text)
        raise ValueError(f"Unknown embedding provider: {self.embedding_provider}")

    def _embed_ollama(self, text: str) -> List[float]:
        import requests
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={"model": self.embedding_model, "prompt": text},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["embedding"]

    def _embed_openai_compatible(self, text: str) -> List[float]:
        from openai import OpenAI
        llm = self.config.get("llm", {})
        client = OpenAI(base_url=llm.get("base_url"), api_key=llm.get("api_key", "local"))
        response = client.embeddings.create(model=self.embedding_model, input=text)
        return response.data[0].embedding

    # ========================================================
    # 保存・検索
    # ========================================================

    def add(self, doc_id: str, doc_type: str, text: str, metadata: dict = None):
        vector = self.embed(text)
        self.conn.execute(
            "INSERT OR REPLACE INTO embeddings (id, doc_type, text_content, vector, metadata)"
            " VALUES (?,?,?,?,?)",
            (doc_id, doc_type, text, self._vector_to_blob(vector),
             json.dumps(metadata or {}, ensure_ascii=False)))
        self.conn.commit()

    def search(self, query: str, limit: int = 10, doc_type: str = None) -> List[dict]:
        query_vector = self.embed(query)
        if doc_type:
            rows = self.conn.execute(
                "SELECT id, doc_type, text_content, vector, metadata FROM embeddings WHERE doc_type = ?",
                (doc_type,)).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT id, doc_type, text_content, vector, metadata FROM embeddings").fetchall()
        results = []
        for row in rows:
            results.append({
                "id": row["id"],
                "doc_type": row["doc_type"],
                "text_content": row["text_content"],
                "similarity": self._cosine_similarity(query_vector, self._blob_to_vector(row["vector"])),
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            })
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    def clear(self):
        self.conn.execute("DELETE FROM embeddings")
        self.conn.commit()

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]

    # ========================================================
    # ユーティリティ
    # ========================================================

    @staticmethod
    def _vector_to_blob(vector: List[float]) -> bytes:
        return struct.pack(f"{len(vector)}f", *vector)

    @staticmethod
    def _blob_to_vector(blob: bytes) -> List[float]:
        n = len(blob) // 4
        return list(struct.unpack(f"{n}f", blob))

    @staticmethod
    def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)
