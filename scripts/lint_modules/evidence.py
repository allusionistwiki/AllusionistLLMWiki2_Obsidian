"""15.3 証拠Lint: 証拠の付与、source_id、引用整合性"""
from __future__ import annotations

from pathlib import Path
from typing import List

from .utils import LintError, Severity, parse_frontmatter


class SourceRegistry:
    """source_idのレジストリ"""

    def __init__(self, sources_path: Path):
        self.sources_path = sources_path
        self.valid_ids: set = set()

    def load(self) -> None:
        if not self.sources_path.exists():
            return
        for yaml_file in self.sources_path.rglob("*.yaml"):
            self.valid_ids.add(yaml_file.stem)


def lint_evidence(file_path: Path, source_registry: SourceRegistry, raw_texts: dict) -> List[LintError]:
    errors: List[LintError] = []
    try:
        content = file_path.read_text(encoding="utf-8")
        fm, _, _ = parse_frontmatter(content)
    except Exception:
        return errors
    if not fm:
        return errors

    file_type = fm.get("type")
    epistemic = fm.get("epistemic_status", "")
    evidence = fm.get("evidence", []) or []

    # confirmed/supported 主張に証拠がない
    if file_type == "analytical_claim" and epistemic in ("confirmed", "supported"):
        if not evidence:
            errors.append(LintError(file=file_path, category="evidence", code="EVD001",
                                    severity=Severity.ERROR, message=f"epistemic_status: {epistemic} に証拠がありません"))

    for i, ev in enumerate(evidence):
        if not isinstance(ev, dict):
            continue
        source_id = ev.get("source_id")
        if not source_id:
            errors.append(LintError(file=file_path, category="evidence", code="EVD002",
                                    severity=Severity.ERROR, message=f"evidence[{i}]: source_id が欠落"))
        elif source_registry.valid_ids and source_id not in source_registry.valid_ids:
            errors.append(LintError(file=file_path, category="evidence", code="EVD003",
                                    severity=Severity.WARN, message=f"evidence[{i}]: source_id={source_id} がレジストリに存在しません"))

        locator = ev.get("locator", {})
        if not locator:
            errors.append(LintError(file=file_path, category="evidence", code="EVD004",
                                    severity=Severity.WARN, message=f"evidence[{i}]: locator が欠落"))
        else:
            chapter = locator.get("chapter")
            if not chapter:
                errors.append(LintError(file=file_path, category="evidence", code="EVD005",
                                        severity=Severity.WARN, message=f"evidence[{i}]: locator.chapter が欠落"))
            quote = ev.get("quote")
            if quote and chapter and chapter in raw_texts:
                raw = raw_texts[chapter]
                if quote not in raw and len(quote) > 10:
                    errors.append(LintError(file=file_path, category="evidence", code="EVD006",
                                            severity=Severity.WARN,
                                            message=f"evidence[{i}]: 引用が原文と一致しない可能性があります"))

    # 外部典拠間の関係には外部出典が必要
    if file_type == "external_reference":
        for i, rel in enumerate(fm.get("relations", []) or []):
            rel_evidence = rel.get("evidence", [])
            if not rel_evidence:
                errors.append(LintError(file=file_path, category="evidence", code="EVD007",
                                        severity=Severity.WARN,
                                        message=f"relations[{i}]: 外部典拠間の関係に証拠がありません"))
            else:
                for ev in rel_evidence:
                    src_id = ev.get("source_id", "")
                    if not src_id.startswith("SRC_external"):
                        errors.append(LintError(file=file_path, category="evidence", code="EVD008",
                                                severity=Severity.WARN,
                                                message=f"relations[{i}]: 外部典拠の関係には外部出典（SRC_external_*）が必要です"))

    return errors
