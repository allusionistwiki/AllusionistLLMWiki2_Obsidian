"""15.5 意味Lint: 重複主張、伏線整合性、未参照ME_など"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set, Tuple

from .utils import LintError, Severity, parse_frontmatter


class SemanticIndex:
    """意味Lint用のインデックス"""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.claim_triples: Dict[Tuple[str, str, str], List[Path]] = {}
        self.mysteries: Dict[str, Tuple[str, str, Path]] = {}
        self.reference_counts: Dict[str, int] = {}
        self.referenced_me: Set[str] = set()
        self.rf_resulted_in: Dict[str, List[str]] = {}
        self.all_a_ids: Set[str] = set()
        self.all_my_ids: Set[str] = set()

    def build(self) -> None:
        for md_file in self.vault_path.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                fm, _, _ = parse_frontmatter(content)
                if not fm or "id" not in fm:
                    continue
                file_type = fm.get("type")
                file_id = str(fm["id"])

                if file_type == "analytical_claim":
                    self.all_a_ids.add(file_id)
                    subject = fm.get("subject", "")
                    predicate = fm.get("predicate", "")
                    obj = fm.get("object", "")
                    key = (subject, predicate, obj)
                    self.claim_triples.setdefault(key, []).append(md_file)
                    for wikilink in [subject, obj]:
                        if str(wikilink).startswith("[[ME_"):
                            self.referenced_me.add(str(wikilink).replace("[[", "").replace("]]", ""))
                elif file_type == "mystery":
                    self.all_my_ids.add(file_id)
                    status = fm.get("mystery_status", "")
                    resolved = fm.get("timeline", {}).get("resolved", "")
                    self.mysteries[file_id] = (status, resolved, md_file)
                elif file_type == "external_reference":
                    self.reference_counts[file_id] = 0
                elif file_type == "reflection":
                    resulted_in = fm.get("resulted_in", [])
                    if resulted_in:
                        self.rf_resulted_in[file_id] = [
                            str(r).replace("[[", "").replace("]]", "") for r in resulted_in
                        ]
            except Exception:
                continue


def lint_semantic(file_path: Path, index: SemanticIndex) -> List[LintError]:
    errors: List[LintError] = []
    try:
        content = file_path.read_text(encoding="utf-8")
        fm, _, _ = parse_frontmatter(content)
    except Exception:
        return errors
    if not fm or "id" not in fm:
        return errors

    file_type = fm.get("type")
    file_id = str(fm["id"])

    # A_: 同一 subject-predicate-object の重複
    if file_type == "analytical_claim":
        key = (fm.get("subject", ""), fm.get("predicate", ""), fm.get("object", ""))
        duplicates = index.claim_triples.get(key, [])
        if len(duplicates) > 1:
            other_files = [f for f in duplicates if f != file_path]
            if other_files:
                errors.append(LintError(file=file_path, category="semantic", code="SEM001",
                                        severity=Severity.WARN,
                                        message=f"同一subject-predicate-objectの重複A_が{len(duplicates)}件あります: "
                                                f"{', '.join(f.name for f in other_files)}"))
        for cc in fm.get("conflicting_claims", []) or []:
            if cc.get("resolution_status") not in ("disputed", "sublated", "refuted"):
                errors.append(LintError(file=file_path, category="semantic", code="SEM002",
                                        severity=Severity.WARN,
                                        message=f"conflicting_claims: 競合{cc.get('claim_id')}にresolution_statusが設定されていません"))

    # MY_: resolved 状態と timeline の整合
    if file_type == "mystery":
        status = fm.get("mystery_status", "")
        resolved = fm.get("timeline", {}).get("resolved")
        if status == "resolved" and not resolved:
            errors.append(LintError(file=file_path, category="semantic", code="SEM003",
                                    severity=Severity.ERROR,
                                    message="mystery_status: resolved だが timeline.resolved が未設定"))
        if status == "resolved" and resolved:
            episode_dir = index.vault_path / "episodes"
            if episode_dir.exists():
                found = any(f.name.startswith(f"O_{resolved}_") for f in episode_dir.glob("*.md"))
                if not found:
                    errors.append(LintError(file=file_path, category="semantic", code="SEM004",
                                            severity=Severity.WARN,
                                            message=f"resolved章 {resolved} のエピソードファイルが存在しません"))

    # RF_: resulted_in の A_ 実在性
    if file_type == "reflection":
        for link in fm.get("resulted_in", []) or []:
            a_id = str(link).replace("[[", "").replace("]]", "")
            if a_id not in index.all_a_ids:
                errors.append(LintError(file=file_path, category="semantic", code="SEM005",
                                        severity=Severity.WARN, message=f"resulted_in: [[{a_id}]] が存在しません"))

    # ME_: 孤立外部参照
    if file_type == "external_reference":
        if file_id not in index.referenced_me:
            errors.append(LintError(file=file_path, category="semantic", code="SEM006",
                                    severity=Severity.INFO,
                                    message="どのA_からも参照されていません（孤立した外部参照）"))

    return errors
