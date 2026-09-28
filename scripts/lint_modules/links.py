"""15.2 リンクLint: 死リンク、旧ID、循環参照"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set

from .utils import LintError, Severity, parse_frontmatter, extract_wikilink_targets


class LinkIndex:
    """全ファイルのID・aliasをインデックス化"""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.ids: Set[str] = set()
        self.id_to_file: Dict[str, Path] = {}
        self.alias_to_id: Dict[str, str] = {}
        self.legacy_ids: Dict[str, str] = {}
        self.superseded_by: Dict[str, str] = {}

    def build(self) -> None:
        self.scan(self.vault_path.rglob("*.md"))

    def scan(self, files) -> None:
        """指定ファイル群をインデックスに追加（Lint対象が vault 外のとき相互リンク解決用）"""
        for md_file in files:
            try:
                content = md_file.read_text(encoding="utf-8")
                fm, _, _ = parse_frontmatter(content)
                if not fm or "id" not in fm:
                    continue
                file_id = str(fm["id"])
                self.ids.add(file_id)
                self.id_to_file[file_id] = md_file
                for alias in fm.get("aliases", []) or []:
                    self.alias_to_id[str(alias)] = file_id
                if "legacy_id" in fm:
                    self.legacy_ids[str(fm["legacy_id"])] = file_id
                if fm.get("document_status") == "superseded" and "superseded_by" in fm:
                    target = str(fm["superseded_by"]).replace("[[", "").replace("]]", "")
                    self.superseded_by[file_id] = target
            except Exception:
                continue

    def resolve(self, link: str) -> tuple[bool, str]:
        if link in self.ids:
            return True, "ok"
        if link in self.alias_to_id:
            return True, f"alias→{self.alias_to_id[link]}"
        if link in self.legacy_ids:
            return False, f"legacy_id→{self.legacy_ids[link]} に置き換えてください"
        if link in self.superseded_by:
            return False, f"superseded → {self.superseded_by[link]} に移行済み"
        return False, "存在しないリンク"


def lint_links(file_path: Path, index: LinkIndex) -> List[LintError]:
    errors: List[LintError] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return errors

    fm, body, body_start_line = parse_frontmatter(content)
    if not fm:
        return errors

    frontmatter_links = _extract_links_from_dict(fm)
    body_links = []
    for i, line in enumerate(body.split("\n"), start=body_start_line):
        for link in extract_wikilink_targets(line):
            body_links.append((link, i))

    all_links = [(link, None) for link in frontmatter_links] + body_links

    for link, line_no in all_links:
        resolved, reason = index.resolve(link)
        if not resolved:
            if "legacy_id" in reason:
                errors.append(LintError(file=file_path, category="links", code="LNK001",
                                        severity=Severity.WARN, message=f"旧IDリンク: [[{link}]] ({reason})", line=line_no))
            elif "superseded" in reason:
                errors.append(LintError(file=file_path, category="links", code="LNK002",
                                        severity=Severity.WARN, message=f"supersededリンク: [[{link}]] ({reason})", line=line_no))
            else:
                errors.append(LintError(file=file_path, category="links", code="LNK003",
                                        severity=Severity.ERROR, message=f"死リンク: [[{link}]]", line=line_no))

    # 循環 superseded_by 検出
    if fm.get("id") in index.superseded_by:
        visited = set()
        current = str(fm["id"])
        while current in index.superseded_by:
            if current in visited:
                errors.append(LintError(file=file_path, category="links", code="LNK004",
                                        severity=Severity.ERROR, message=f"循環superseded_by: {fm['id']}"))
                break
            visited.add(current)
            current = index.superseded_by[current]

    return errors


def _extract_links_from_dict(d: dict) -> List[str]:
    links = []

    def traverse(obj):
        if isinstance(obj, str):
            links.extend(re.findall(r"\[\[([^\]|#]+?)(?:\|[^\]]+?)?\]\]", obj))
        elif isinstance(obj, dict):
            for v in obj.values():
                traverse(v)
        elif isinstance(obj, list):
            for item in obj:
                traverse(item)

    traverse(d)
    return links
