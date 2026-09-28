"""15.1 構造Lint: YAML構文、必須フィールド、ID整合性、配置、JSON Schema検証"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List

import yaml

from .utils import (
    LintError, Severity, parse_frontmatter,
    VALID_TYPES, VALID_ENTITY_SUBTYPES, VALID_REFERENCE_SUBTYPES,
    CHAPTER_PATTERN, SPECIAL_CHAPTERS,
)

# 配置チェック（IDプレフィックス → 期待ディレクトリ）
ID_PREFIX_DIR = {
    "ARC_": "wiki/arcs",
    "O_": "wiki/episodes",
    "E_char_": "wiki/entities/characters",
    "E_term_": "wiki/entities/terminology",
    "E_org_": "wiki/entities/organizations",
    "E_item_": "wiki/entities/items",
    "E_motif_": "wiki/entities/motifs",
    "E_relation_": "wiki/entities/relationships",
    "E_phrase_": "wiki/entities/phrases",
    "ME_myth_": "wiki/references/mythology",
    "ME_lit_": "wiki/references/literature",
    "ME_phil_": "wiki/references/philosophy",
    "ME_psych_": "wiki/references/psychology",
    "ME_pop_": "wiki/references/culture",
    "ME_net_": "wiki/references/culture",
    "ME_author_": "wiki/references/author-material",
    "A_": "wiki/claims",
    "MY_": "wiki/mysteries",
    "RF_": "wiki/reflections",
}

SCHEMA_MAP = {
    "entity": "entity.schema.json",
    "external_reference": "reference.schema.json",
    "analytical_claim": "claim.schema.json",
    "mystery": "mystery.schema.json",
    "episode": "episode.schema.json",
    "arc": "arc.schema.json",
    "reflection": "reflection.schema.json",
    "source": "source.schema.json",
}


def lint_structure(file_path: Path, vault_root: Path, schemas_dir: Path) -> List[LintError]:
    """構造Lint"""
    errors: List[LintError] = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(LintError(file=file_path, category="structure", code="STR001",
                                severity=Severity.ERROR, message=f"ファイル読み込み失敗: {e}"))
        return errors

    if not content.startswith("---"):
        errors.append(LintError(file=file_path, category="structure", code="STR002",
                                severity=Severity.ERROR, message="Frontmatterがありません（ファイル先頭が --- で始まっていません）"))
        return errors

    try:
        frontmatter, body, body_line = parse_frontmatter(content)
    except yaml.YAMLError as e:
        errors.append(LintError(file=file_path, category="structure", code="STR003",
                                severity=Severity.ERROR, message=f"YAML構文エラー: {e}"))
        return errors

    if not frontmatter:
        errors.append(LintError(file=file_path, category="structure", code="STR004",
                                severity=Severity.ERROR, message="Frontmatterが空です"))
        return errors

    # schema_version
    if "schema_version" not in frontmatter:
        errors.append(LintError(file=file_path, category="structure", code="STR005",
                                severity=Severity.ERROR, message="schema_version が欠落しています",
                                suggestion='schema_version: "5.1" を追加'))
    elif str(frontmatter["schema_version"]) != "5.1":
        errors.append(LintError(file=file_path, category="structure", code="STR006",
                                severity=Severity.WARN, message=f"未知の schema_version: {frontmatter['schema_version']}",
                                suggestion='schema_version: "5.1" に更新'))

    # id フィールド + ファイル名一致
    if "id" not in frontmatter:
        errors.append(LintError(file=file_path, category="structure", code="STR007",
                                severity=Severity.ERROR, message="id フィールドが欠落しています"))
    else:
        if str(frontmatter["id"]) != file_path.stem:
            errors.append(LintError(file=file_path, category="structure", code="STR008",
                                    severity=Severity.ERROR,
                                    message=f"IDとファイル名が不一致: id={frontmatter['id']}, file={file_path.stem}",
                                    suggestion=f"ファイル名を {frontmatter['id']}.md に変更"))
        # 配置チェック（docs/samples は対象外）
        root = vault_root.parent
        try:
            rel = file_path.parent.relative_to(root).as_posix()
        except ValueError:
            rel = ""
        expected = next((d for pfx, d in ID_PREFIX_DIR.items() if str(frontmatter["id"]).startswith(pfx)), None)
        if expected and rel and not rel.startswith("docs/samples"):
            if rel != expected:
                errors.append(LintError(file=file_path, category="structure", code="STR019",
                                        severity=Severity.ERROR,
                                        message=f"配置ディレクトリの不一致: {rel} (期待: {expected})",
                                        suggestion=f"{expected}/ へ移動"))

    # type フィールド
    if "type" not in frontmatter:
        errors.append(LintError(file=file_path, category="structure", code="STR009",
                                severity=Severity.ERROR, message="type フィールドが欠落しています"))
    elif frontmatter["type"] not in VALID_TYPES:
        errors.append(LintError(file=file_path, category="structure", code="STR010",
                                severity=Severity.ERROR, message=f"未知の type: {frontmatter['type']}",
                                suggestion=f"有効値: {', '.join(sorted(VALID_TYPES))}"))
    else:
        _lint_subtype(file_path, frontmatter, errors)

    # 章番号パターン
    for field_name in ["first_appearance", "spoiler_after", "valid_from"]:
        value = frontmatter.get(field_name)
        if value and isinstance(value, str):
            if value not in SPECIAL_CHAPTERS and not CHAPTER_PATTERN.match(value):
                errors.append(LintError(file=file_path, category="structure", code="STR011",
                                        severity=Severity.WARN, message=f"不正な章番号パターン: {field_name}={value}"))

    # JSON Schema 検証（v5.1 スキーマ準拠）
    errors.extend(_lint_json_schema(file_path, frontmatter, schemas_dir))

    return errors


def _lint_subtype(file_path: Path, fm: dict, errors: list):
    t = fm["type"]
    if t == "entity":
        if "subtype" not in fm:
            errors.append(LintError(file=file_path, category="structure", code="STR012",
                                    severity=Severity.ERROR, message="type: entity に subtype が欠落"))
        elif fm["subtype"] not in VALID_ENTITY_SUBTYPES:
            errors.append(LintError(file=file_path, category="structure", code="STR013",
                                    severity=Severity.ERROR, message=f"未知の entity subtype: {fm['subtype']}",
                                    suggestion=f"有効値: {', '.join(sorted(VALID_ENTITY_SUBTYPES))}"))
    elif t == "external_reference":
        if "subtype" not in fm:
            errors.append(LintError(file=file_path, category="structure", code="STR014",
                                    severity=Severity.ERROR, message="type: external_reference に subtype が欠落"))
        elif fm["subtype"] not in VALID_REFERENCE_SUBTYPES:
            errors.append(LintError(file=file_path, category="structure", code="STR015",
                                    severity=Severity.ERROR, message=f"未知の reference subtype: {fm['subtype']}",
                                    suggestion=f"有効値: {', '.join(sorted(VALID_REFERENCE_SUBTYPES))}"))


def _lint_json_schema(file_path: Path, fm: dict, schemas_dir: Path) -> List[LintError]:
    """v5.1 JSON Schema による Frontmatter 検証（STR020）"""
    errors: List[LintError] = []
    node_type = fm.get("type")
    if node_type not in SCHEMA_MAP:
        return errors
    schema_path = schemas_dir / SCHEMA_MAP[node_type]
    if not schema_path.exists():
        return errors
    try:
        import jsonschema

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        resolver = jsonschema.RefResolver(base_uri=schemas_dir.as_uri() + "/", referrer=schema)
        validator = jsonschema.Draft7Validator(schema, resolver=resolver)
        for err in validator.iter_errors(fm):
            loc = ".".join(map(str, err.path))
            errors.append(LintError(file=file_path, category="structure", code="STR020",
                                    severity=Severity.ERROR, message=f"Schema[{loc}]: {err.message}"))
    except ImportError:
        pass
    return errors
