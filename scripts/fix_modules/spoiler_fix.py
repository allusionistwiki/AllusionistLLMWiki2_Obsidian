"""ネタバレ修復（L2）: meta レベルの audience に analyst 追加"""
from __future__ import annotations

import re
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


def collect_spoiler_fixes(file_path: Path) -> List[FixItem]:
    fixes: List[FixItem] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return fixes

    fm, body = _parse_frontmatter(content)
    if not fm:
        return fixes

    disclosure = fm.get("disclosure", {})
    if disclosure:
        level = disclosure.get("level")
        audience = disclosure.get("audience", [])
        if level == "meta" and audience and "analyst" not in audience:
            def fix_meta_audience(original: str) -> str:
                fm2, body2 = _parse_frontmatter(original)
                disc = fm2.get("disclosure", {})
                aud = disc.get("audience", [])
                if "analyst" not in aud:
                    aud.append("analyst")
                    disc["audience"] = aud
                    fm2["disclosure"] = disc
                return _rebuild_frontmatter(fm2, body2)

            fixes.append(FixItem(
                file=file_path, category="spoiler", code="SPR003_FIX",
                safety_level=SafetyLevel.L2, description="metaレベルのaudienceにanalystを追加",
                suggestion="audience: [..., analyst] に修正", apply_fn=fix_meta_audience))

    return fixes
