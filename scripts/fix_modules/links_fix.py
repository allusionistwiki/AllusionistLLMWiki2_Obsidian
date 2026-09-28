"""リンク修復（L2）: legacy_id / superseded リンクの正規IDへの置換"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List

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


class LinkFixIndex:
    """リンク修復用のインデックス（legacy_id / superseded_by → 置換先）"""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.legacy_to_canonical: Dict[str, str] = {}
        self.superseded_to_target: Dict[str, str] = {}

    def build(self):
        for md_file in self.vault_path.rglob("*.md"):
            try:
                fm, _ = _parse_frontmatter(md_file.read_text(encoding="utf-8"))
                if not fm or "id" not in fm:
                    continue
                if "legacy_id" in fm:
                    self.legacy_to_canonical[str(fm["legacy_id"])] = str(fm["id"])
                if fm.get("document_status") == "superseded" and "superseded_by" in fm:
                    target = str(fm["superseded_by"]).replace("[[", "").replace("]]", "")
                    self.superseded_to_target[str(fm["id"])] = target
            except Exception:
                continue

    def resolve_replacement(self, link: str) -> tuple[bool, str]:
        if link in self.legacy_to_canonical:
            return True, self.legacy_to_canonical[link]
        if link in self.superseded_to_target:
            return True, self.superseded_to_target[link]
        return False, link


def collect_link_fixes(file_path: Path, index: LinkFixIndex) -> List[FixItem]:
    fixes: List[FixItem] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return fixes

    wikilinks = set(re.findall(r"\[\[([^\]|#]+?)(?:\|[^\]]+?)?\]\]", content))
    replacements: Dict[str, str] = {}
    for link in wikilinks:
        needs_replace, new_target = index.resolve_replacement(link)
        if needs_replace and new_target != link:
            replacements[link] = new_target
    if not replacements:
        return fixes

    def create_replace_fn(repls: Dict[str, str]):
        def replace_links(original: str) -> str:
            modified = original
            for old, new in repls.items():
                modified = modified.replace(f"[[{old}]]", f"[[{new}]]")
                modified = re.sub(
                    rf"\[\[{re.escape(old)}\|([^\]]+)\]\]",
                    rf"[[{new}|\1]]",
                    modified,
                )
            return modified
        return replace_links

    desc = "; ".join(f"[[{old}]] → [[{new}]]" for old, new in replacements.items())
    fixes.append(FixItem(
        file=file_path, category="links", code="LNK_FIX",
        safety_level=SafetyLevel.L2, description=f"リンク置換（{len(replacements)}件）",
        suggestion=desc, apply_fn=create_replace_fn(replacements)))
    return fixes
