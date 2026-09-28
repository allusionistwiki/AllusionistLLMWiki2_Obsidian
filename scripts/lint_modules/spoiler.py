"""15.4 ネタバレLint: 開示条件の整合性"""
from __future__ import annotations

from pathlib import Path
from typing import List

from .utils import LintError, Severity, parse_frontmatter, parse_chapter_number


def _chapter_value(ch: str) -> int:
    if ch == "ch0000":
        return 0
    if ch == "final":
        return 99999
    if ch == "meta":
        return 999999
    n = parse_chapter_number(ch)
    return n if n is not None else -1


def _level_value(level: str) -> int:
    levels = {"surface": 0, "hint": 1, "revelation": 2, "meta": 3}
    return levels.get(level, -1)


def lint_spoiler(file_path: Path) -> List[LintError]:
    errors: List[LintError] = []
    try:
        content = file_path.read_text(encoding="utf-8")
        fm, _, _ = parse_frontmatter(content)
    except Exception:
        return errors
    if not fm:
        return errors

    file_type = fm.get("type")

    # reveal_stages の整合性（高レベル情報が早期開示されていないか）
    reveal_stages = fm.get("reveal_stages", [])
    if reveal_stages and isinstance(reveal_stages, list):
        prev_available, prev_level = -1, -1
        for i, stage in enumerate(reveal_stages):
            if not isinstance(stage, dict):
                continue
            available = stage.get("available_after")
            level = stage.get("stage")
            if not available or not level:
                continue
            av_value, lv_value = _chapter_value(available), _level_value(level)
            if av_value < prev_available and lv_value > prev_level:
                errors.append(LintError(file=file_path, category="spoiler", code="SPR001",
                                        severity=Severity.ERROR,
                                        message=f"reveal_stages[{i}]: より高いレベルの情報が、より早く開示されています"))
            prev_available, prev_level = av_value, lv_value

    # disclosure の整合性
    disclosure = fm.get("disclosure", {})
    if disclosure:
        minimum_progress = disclosure.get("minimum_progress")
        level = disclosure.get("level")
        if minimum_progress and level:
            if level == "revelation" and minimum_progress == "ch0000":
                errors.append(LintError(file=file_path, category="spoiler", code="SPR002",
                                        severity=Severity.ERROR,
                                        message="disclosure: revelationレベルをch0000で開示は矛盾"))
        if level == "meta":
            audience = disclosure.get("audience", [])
            if audience and "analyst" not in audience:
                errors.append(LintError(file=file_path, category="spoiler", code="SPR003",
                                        severity=Severity.ERROR,
                                        message="disclosure: metaレベルはanalyst限定にすべき"))

    # MY_: resolved が introduced より前ではないか
    if file_type == "mystery":
        timeline = fm.get("timeline", {})
        introduced = timeline.get("introduced")
        resolved = timeline.get("resolved")
        if introduced and resolved:
            if _chapter_value(resolved) < _chapter_value(introduced):
                errors.append(LintError(file=file_path, category="spoiler", code="SPR004",
                                        severity=Severity.ERROR,
                                        message=f"timeline: resolved({resolved})がintroduced({introduced})より前"))

    # evidence の章が spoiler_after より前ではないか（開示条件の下限）
    spoiler_after = fm.get("spoiler_after")
    if spoiler_after and fm.get("evidence"):
        min_val = _chapter_value(spoiler_after)
        for i, ev in enumerate(fm["evidence"]):
            if isinstance(ev, dict):
                ch = ev.get("locator", {}).get("chapter")
                if ch and _chapter_value(ch) > min_val:
                    errors.append(LintError(file=file_path, category="spoiler", code="SPR005",
                                            severity=Severity.WARN,
                                            message=f"evidence[{i}]: 証拠の章 {ch} が spoiler_after({spoiler_after}) より後（spoiler_after の更新を検討）"))

    return errors
