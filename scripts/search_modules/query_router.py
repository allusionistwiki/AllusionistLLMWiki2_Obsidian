"""クエリルーティング（質問タイプ → 適切な検索層）"""
from __future__ import annotations

import re
from enum import Enum
from typing import Optional


class QueryType(Enum):
    STRUCTURED = "structured"  # 構造化クエリ（第1層）
    EPISODE = "episode"        # エピソード検索（第2層）
    SEMANTIC = "semantic"      # 意味検索（第3層）
    HYBRID = "hybrid"          # ハイブリッド検索


class QueryRouter:
    """クエリの分類とルーティング"""

    STRUCTURED_PATTERNS = [
        r"(.+)の(視覚描写|視覚的記述|見た目|容姿)",
        r"(.+)の(セリフ|発言)",
        r"(.+)の(行動|動作)",
        r"(.+)の(関係性)",
        r"(.+)の(名称|呼称)",
        r"(.+)の(象徴|比喩)",
    ]
    EPISODE_PATTERNS = [
        r"ch(\d{4})で(何が起きた|起きたこと|全て)",
        r"(\d{4})話で(何が起きた|起きたこと)",
        r"(.+)の話",
    ]
    RELATION_PATTERNS = [
        r"(.+)と(.+)の(関係|関連)",
        r"(.+)は(.+)を(引喩|類推|参照)",
    ]

    def route(self, query: str) -> QueryType:
        for pattern in self.STRUCTURED_PATTERNS:
            if re.search(pattern, query):
                return QueryType.STRUCTURED
        for pattern in self.EPISODE_PATTERNS:
            if re.search(pattern, query):
                return QueryType.EPISODE
        for pattern in self.RELATION_PATTERNS:
            if re.search(pattern, query):
                return QueryType.SEMANTIC
        return QueryType.HYBRID

    def parse_structured_query(self, query: str) -> Optional[dict]:
        aspect_map = {
            "視覚描写": "visual", "視覚的記述": "visual", "見た目": "visual", "容姿": "visual",
            "セリフ": "speech", "発言": "speech",
            "行動": "action", "動作": "action",
            "関係性": "relationship",
            "名称": "name", "呼称": "name",
            "象徴": "symbolic", "比喩": "symbolic",
        }
        for pattern in self.STRUCTURED_PATTERNS:
            match = re.search(pattern, query)
            if match:
                return {"entity": match.group(1), "aspect": aspect_map.get(match.group(2), "visual")}
        return None

    def parse_episode_query(self, query: str) -> Optional[str]:
        match = re.search(r"ch(\d{4})", query)
        if match:
            return f"ch{match.group(1)}"
        match = re.search(r"(\d{4})話", query)
        if match:
            return f"ch{match.group(1)}"
        return None
