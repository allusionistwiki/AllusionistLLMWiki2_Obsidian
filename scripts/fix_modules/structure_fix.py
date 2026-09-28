"""構造修復（L1〜L2）: schema_version / created・updated / document_status / canonical_name 追加"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import List

import yaml

from .utils import FixItem, SafetyLevel


def _parse_frontmatter(content: str):
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content
    try:
        fm = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, match.group(2)


def _rebuild_frontmatter(fm: dict, body: str) -> str:
    yaml_str = yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_str}---\n{body}"


def collect_structure_fixes(file_path: Path) -> List[FixItem]:
    fixes: List[FixItem] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return fixes

    fm, body = _parse_frontmatter(content)
    if not fm:
        return fixes

    # L1: schema_version 追加
    if "schema_version" not in fm:
        def add_schema_version(original: str) -> str:
            fm2, body2 = _parse_frontmatter(original)
            return _rebuild_frontmatter({"schema_version": "5.1", **fm2}, body2)

        fixes.append(FixItem(
            file=file_path, category="structure", code="STR005",
            safety_level=SafetyLevel.L1, description="schema_version が欠落",
            suggestion='schema_version: "5.1" を追加', apply_fn=add_schema_version))

    # L1: created/updated 追加
    if "created" not in fm or "updated" not in fm:
        today = date.today().isoformat()

        def add_timestamps(original: str) -> str:
            fm2, body2 = _parse_frontmatter(original)
            fm2.setdefault("created", today)
            fm2.setdefault("updated", today)
            return _rebuild_frontmatter(fm2, body2)

        fixes.append(FixItem(
            file=file_path, category="structure", code="STR016",
            safety_level=SafetyLevel.L1, description="created/updated が欠落",
            suggestion=f"created/updated: {today} を追加", apply_fn=add_timestamps))

    # L2: entity の canonical_name（ファイル名から推定）
    if fm.get("type") == "entity" and "canonical_name" not in fm:
        name_match = re.match(r"E_\w+_(.+)$", file_path.stem)
        if name_match:
            guessed_name = name_match.group(1)

            def add_canonical_name(original: str) -> str:
                fm2, body2 = _parse_frontmatter(original)
                fm2["canonical_name"] = guessed_name
                return _rebuild_frontmatter(fm2, body2)

            fixes.append(FixItem(
                file=file_path, category="structure", code="STR017",
                safety_level=SafetyLevel.L2, description="canonical_name が欠落（ファイル名から推定）",
                suggestion=f"canonical_name: {guessed_name} を追加", apply_fn=add_canonical_name))

    # L1: analytical_claim の document_status
    if fm.get("type") == "analytical_claim" and "document_status" not in fm:
        def add_document_status(original: str) -> str:
            fm2, body2 = _parse_frontmatter(original)
            fm2["document_status"] = "active"
            return _rebuild_frontmatter(fm2, body2)

        fixes.append(FixItem(
            file=file_path, category="structure", code="STR018",
            safety_level=SafetyLevel.L1, description="document_status が欠落",
            suggestion="document_status: active を追加", apply_fn=add_document_status))

    return fixes
