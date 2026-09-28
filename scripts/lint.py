#!/usr/bin/env python3
"""AllusionistLLMWiki2 v5.1 Lint: Frontmatter スキーマ検証 + 構造/リンク/証拠/ネタバレチェック.

検出のみを行う（自動修復は行わない）。設計書 §15 準拠。

使い方:
  python scripts/lint.py            # wiki/ 配下を検査
  python scripts/lint.py docs/samples  # 対象ディレクトリを指定
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent
SCHEMAS = VAULT / "schemas"

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

FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
WIKILINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]")


def parse_frontmatter(path: Path) -> tuple[dict | None, list[str]]:
    text = path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        return None, ["Frontmatter not found"]
    try:
        import yaml

        data = yaml.safe_load(m.group(1))
    except Exception as e:  # yaml.YAMLError
        return None, [f"YAML parse error: {e}"]
    if not isinstance(data, dict):
        return None, ["Frontmatter is not a mapping"]
    return data, []


def validate_schema(data: dict) -> list[str]:
    import jsonschema

    errors: list[str] = []
    sv = data.get("schema_version")
    if sv != "5.1":
        errors.append(f"Unsupported schema_version: {sv}")
    node_type = data.get("type")
    if node_type not in SCHEMA_MAP:
        return errors + [f"Unknown type: {node_type}"]
    schema_path = SCHEMAS / SCHEMA_MAP[node_type]
    if not schema_path.exists():
        return errors + [f"Schema not found: {schema_path.name}"]
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    resolver = jsonschema.RefResolver(
        base_uri=SCHEMAS.as_uri() + "/", referrer=schema
    )
    validator = jsonschema.Draft7Validator(schema, resolver=resolver)
    for err in validator.iter_errors(data):
        loc = ".".join(map(str, err.path))
        errors.append(f"Schema[{loc}]: {err.message}")
    return errors


def check_id_filename(data: dict, path: Path) -> list[str]:
    id_ = data.get("id", "")
    stem = path.stem
    if id_ and id_ != stem:
        return [f"ID/filename mismatch: id={id_} file={stem}"]
    expected = None
    for prefix, d in ID_PREFIX_DIR.items():
        if id_.startswith(prefix):
            expected = d
            break
    if expected:
        rel = path.parent.relative_to(VAULT).as_posix()
        if rel.startswith("docs/samples"):
            return []  # サンプルは配置チェック対象外
        if rel != expected:
            return [f"Wrong directory: {rel} (expected {expected})"]
    return []


def collect_ids(paths: list[Path]) -> dict[str, Path]:
    ids: dict[str, Path] = {}
    for p in paths:
        data, _ = parse_frontmatter(p)
        if data and data.get("id"):
            ids[str(data["id"])] = p
    return ids


def check_links(data: dict, ids: dict[str, Path]) -> list[str]:
    errors = []
    for target in WIKILINK_RE.findall(json.dumps(data, ensure_ascii=False)):
        t = target.strip()
        if re.match(r"^(ARC|O|E|ME|A|MY|RF)_", t) and t not in ids:
            errors.append(f"Dead link: [[{t}]]")
    return errors


def check_evidence(data: dict) -> list[str]:
    errors = []
    t = data.get("type")
    if t == "analytical_claim":
        if data.get("epistemic_status") in ("confirmed", "supported") and not data.get("evidence"):
            errors.append("confirmed/supported claim without evidence")
        for ev in data.get("evidence", []) or []:
            sid = str(ev.get("source_id", ""))
            if not re.match(r"^SRC_(ch\d{4}|external_\d{3})$", sid):
                errors.append(f"Bad source_id: {sid}")
    if t == "external_reference":
        for rel in data.get("relations", []) or []:
            if not rel.get("evidence"):
                errors.append(f"ME relation '{rel.get('predicate')}' without external evidence")
    return errors


def check_spoiler(data: dict) -> list[str]:
    errors = []
    ch_re = re.compile(r"^ch(\d{4})")

    def chnum(v):
        m = ch_re.match(str(v))
        return int(m.group(1)) if m else None

    sa = data.get("spoiler_after")
    disc = data.get("disclosure") or {}
    mp = disc.get("minimum_progress")
    if sa and mp:
        a, b = chnum(sa), chnum(mp)
        if a is not None and b is not None and b < a:
            errors.append(f"disclosure.minimum_progress {mp} earlier than spoiler_after {sa}")
    if data.get("type") == "mystery":
        tl = data.get("timeline") or {}
        intro = chnum(tl.get("introduced"))
        for h in tl.get("hinted", []) or []:
            hn = chnum(h)
            if intro is not None and hn is not None and hn < intro:
                errors.append(f"hinted {h} earlier than introduced")
        if data.get("mystery_status") == "resolved" and not tl.get("resolved"):
            errors.append("mystery_status=resolved without timeline.resolved")
    return errors


def lint_file(path: Path, ids: dict[str, Path]) -> list[str]:
    data, errors = parse_frontmatter(path)
    if data is None:
        return errors
    errors += validate_schema(data)
    errors += check_id_filename(data, path)
    errors += check_links(data, ids)
    errors += check_evidence(data)
    errors += check_spoiler(data)
    return errors


def main() -> int:
    targets = sys.argv[1:] or ["wiki"]
    files: list[Path] = []
    for t in targets:
        p = (VAULT / t) if not Path(t).is_absolute() else Path(t)
        if p.is_dir():
            files += sorted(p.rglob("*.md"))
        elif p.suffix == ".md":
            files.append(p)
    ids = collect_ids(sorted((VAULT / "wiki").rglob("*.md")) + sorted((VAULT / "docs/samples").rglob("*.md")))
    dup: dict[str, int] = {}
    for p in sorted((VAULT / "wiki").rglob("*.md")):
        data, _ = parse_frontmatter(p)
        if data and data.get("id"):
            dup[str(data["id"])] = dup.get(str(data["id"]), 0) + 1
    bad = 0
    for p in files:
        errors = lint_file(p, ids)
        for i, c in dup.items():
            if c > 1:
                errors.append(f"Duplicate ID: {i} ({c} files)")
                dup = {}
        if errors:
            bad += 1
            print(f"NG {p.relative_to(VAULT)}")
            for e in errors:
                print(f"   - {e}")
        else:
            print(f"OK {p.relative_to(VAULT)}")
    print(f"\n{len(files)} files, {bad} with errors")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
