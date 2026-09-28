#!/usr/bin/env python3
"""Lint共通ユーティリティ"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

import yaml


class Severity(Enum):
    ERROR = "error"
    WARN = "warn"
    INFO = "info"


@dataclass
class LintError:
    """Lintエラー"""
    file: Path
    category: str
    code: str
    severity: Severity
    message: str
    line: Optional[int] = None
    suggestion: Optional[str] = None

    def format(self) -> str:
        location = f"{self.file}"
        if self.line:
            location += f":{self.line}"
        return f"[{self.severity.value.upper()}] {self.code} @ {location}: {self.message}"


@dataclass
class LintResult:
    """Lint結果"""
    errors: list = field(default_factory=list)
    files_checked: int = 0
    files_with_errors: int = 0

    def add(self, error: LintError):
        self.errors.append(error)

    def has_errors(self) -> bool:
        return any(e.severity == Severity.ERROR for e in self.errors)

    def summary(self) -> dict:
        by_severity = {"error": 0, "warn": 0, "info": 0}
        by_category = {}
        for e in self.errors:
            by_severity[e.severity.value] += 1
            by_category[e.category] = by_category.get(e.category, 0) + 1
        return {
            "total": len(self.errors),
            "by_severity": by_severity,
            "by_category": by_category,
            "files_checked": self.files_checked,
            "files_with_errors": self.files_with_errors,
        }


def parse_frontmatter(content: str) -> tuple[dict, str, Optional[int]]:
    """MarkdownからFrontmatterを分離. Returns (frontmatter_dict, body, body_start_line)."""
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content, 1
    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        frontmatter = {}
    body = match.group(2)
    frontmatter_lines = match.group(1).count("\n") + 3
    return frontmatter, body, frontmatter_lines


def parse_chapter_number(ch: str) -> Optional[int]:
    """章番号を数値に変換: ch0057 → 57"""
    match = re.match(r"^ch(\d{4})$", str(ch))
    return int(match.group(1)) if match else None


def extract_wikilink_targets(text: str) -> list[str]:
    """テキスト中の[[...]]を抽出"""
    return re.findall(r"\[\[([^\]|#]+?)(?:\|[^\]]+?)?\]\]", text)


def extract_wikilink_id(wikilink: str) -> str:
    """[[E_char_ハルベルト]] → E_char_ハルベルト"""
    return wikilink.replace("[[", "").replace("]]", "").split("|")[0]


# 有効なコア型
VALID_TYPES = {
    "arc", "episode", "entity", "external_reference",
    "analytical_claim", "mystery", "reflection",
}

VALID_ENTITY_SUBTYPES = {
    "character", "terminology", "organization",
    "item", "visual_motif", "relationship", "key_phrase",
}

VALID_REFERENCE_SUBTYPES = {
    "mythology", "religion", "literature", "philosophy",
    "psychology", "history", "folklore", "occult",
    "popular_culture", "internet_culture", "author_material", "scholarly_source",
}

VALID_CLAIM_PREDICATES = {
    "alludes_to", "analogous_to", "recurs_as", "structurally_matches",
    "misreads_as", "foreshadows", "inverts", "parodies", "sublates",
}

VALID_EPISTEMIC_STATUS = {
    "hypothesized", "supported", "confirmed",
    "disputed", "refuted", "sublated",
}

VALID_REVIEW_STATUS = {"unreviewed", "pending", "human_verified", "needs_revision"}
VALID_DOCUMENT_STATUS = {"draft", "active", "archived", "superseded"}
VALID_MYSTERY_STATUS = {
    "candidate", "open", "partially_resolved",
    "resolved", "invalidated", "unresolved_at_end",
}

# 章番号パターン
CHAPTER_PATTERN = re.compile(r"^ch\d{4}$")
SPECIAL_CHAPTERS = {"ch0000", "final", "meta"}
