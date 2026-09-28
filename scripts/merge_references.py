#!/usr/bin/env python3
"""外部参照（ME_）変換スクリプト: staging references → wiki/references/{category}/ME_*.md.

Usage:
    python scripts/merge_references.py [--episode ch0057] [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console
from rich.table import Table

console = Console()

ROOT = Path(__file__).resolve().parent.parent
VAULT_ROOT = ROOT / "wiki"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT, VAULT_ROOT, STAGING_DIR
REFERENCES_DIR = VAULT_ROOT / "references"

# subtype → (ファイル名プレフィックス, ディレクトリ)
SUBTYPE_MAP = {
    "mythology": ("myth", "mythology"),
    "religion": ("relig", "mythology"),
    "literature": ("lit", "literature"),
    "philosophy": ("phil", "philosophy"),
    "psychology": ("psych", "psychology"),
    "history": ("hist", "culture"),
    "folklore": ("folk", "culture"),
    "occult": ("occult", "culture"),
    "popular_culture": ("pop", "culture"),
    "internet_culture": ("net", "culture"),
    "author_material": ("author", "author-material"),
    "scholarly_source": ("schol", "culture"),
}

RELATION_LABELS = {
    "influenced_by": "影響を受けた", "derived_from": "派生した",
    "syncretized_with": "習合した", "reinterpreted_by": "再解釈された",
    "parodied_in": "パロディ化された",
}

AUTO_MARKER_REFERENCED_BY_START = "<!-- AUTO-GENERATED:referenced_by -->"
AUTO_MARKER_REFERENCED_BY_END = "<!-- /AUTO-GENERATED:referenced_by -->"
AUTO_MARKER_RELATIONS_START = "<!-- AUTO-GENERATED:relations -->"
AUTO_MARKER_RELATIONS_END = "<!-- /AUTO-GENERATED:relations -->"


def parse_frontmatter(content: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not m:
        return {}, content
    try:
        return yaml.safe_load(m.group(1)) or {}, m.group(2)
    except yaml.YAMLError:
        return {}, m.group(2)


def build_frontmatter(frontmatter: dict) -> str:
    yaml_str = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_str}---\n"


def extract_wikilink_name(wikilink: str) -> str:
    m = re.match(r"\[\[ME_\w+_(.+?)\]\]", wikilink)
    return m.group(1) if m else wikilink.replace("[[", "").replace("]]", "")


def find_existing_reference(reference_name: str) -> Optional[Path]:
    for category_dir in REFERENCES_DIR.iterdir() if REFERENCES_DIR.exists() else []:
        if category_dir.is_dir():
            matches = list(category_dir.glob(f"ME_*_{reference_name}.md"))
            if matches:
                return matches[0]
    return None


def build_reference_file_path(subtype: str, reference_name: str) -> Path:
    prefix, category = SUBTYPE_MAP.get(subtype, ("ext", "culture"))
    return REFERENCES_DIR / category / f"ME_{prefix}_{reference_name}.md"


def build_referenced_by_section(referenced_by: list) -> str:
    if not referenced_by:
        return ""
    lines = [AUTO_MARKER_REFERENCED_BY_START, "## 作品内での参照", ""]
    for ref in sorted(referenced_by, key=lambda x: x.get("episode", "")):
        episode = ref.get("episode", "unknown")
        claim = ref.get("claim", "")
        subject = ref.get("subject", "")
        context = ref.get("context", "")
        context_str = f" - {context}" if context else ""
        lines.append(f"- **{episode}**: {claim}")
        if subject:
            lines.append(f"  - 主語: {subject}{context_str}")
    lines.extend(["", AUTO_MARKER_REFERENCED_BY_END, ""])
    return "\n".join(lines)


def build_relations_section(relations: list) -> str:
    if not relations:
        return ""
    lines = [AUTO_MARKER_RELATIONS_START, "## 典拠間の関係", ""]
    for rel in relations:
        predicate = rel.get("predicate", "")
        label = RELATION_LABELS.get(predicate, predicate)
        lines.append(f"- **{label}** ({predicate}): {rel.get('target','')}")
    lines.extend(["", AUTO_MARKER_RELATIONS_END, ""])
    return "\n".join(lines)


def merge_referenced_by(existing: list, new: list) -> list:
    merged = list(existing)
    for new_ref in new:
        is_duplicate = any(
            ref.get("episode") == new_ref.get("episode") and ref.get("claim") == new_ref.get("claim")
            for ref in existing
        )
        if not is_duplicate:
            merged.append(new_ref)
    return merged


def merge_relations(existing: list, new: list) -> list:
    merged = list(existing)
    for new_rel in new:
        is_duplicate = any(
            rel.get("predicate") == new_rel.get("predicate") and rel.get("target") == new_rel.get("target")
            for rel in existing
        )
        if not is_duplicate:
            merged.append(new_rel)
    return merged


def build_body(frontmatter: dict) -> str:
    canonical_name = frontmatter.get("canonical_name", "")
    body = f"# {canonical_name}\n\n**領域**: {frontmatter.get('domain','')}\n\n（本文：外部典拠の説明、作品との関連など）\n\n"
    body += build_referenced_by_section(frontmatter.get("referenced_by", []))
    body += build_relations_section(frontmatter.get("relations", []))
    return body


def build_new_reference_file(ref_data: dict, episode: str) -> str:
    subtype = ref_data.get("subtype", "mythology")
    canonical_name = ref_data.get("canonical_name", "")
    prefix, _ = SUBTYPE_MAP.get(subtype, ("ext", "culture"))
    frontmatter = {
        "schema_version": "5.1",
        "id": f"ME_{prefix}_{canonical_name}",
        "type": "external_reference",
        "subtype": subtype,
        "canonical_name": canonical_name,
        "aliases": ref_data.get("aliases", []),
        "domain": ref_data.get("domain", ""),
        "document_status": "active",
        "referenced_by": ref_data.get("referenced_by", []),
        "relations": ref_data.get("relations", []),
        "created": date.today().isoformat(),
        "updated": date.today().isoformat(),
    }
    return build_frontmatter(frontmatter) + build_body(frontmatter)


def update_reference_file(file_path: Path, ref_data: dict, episode: str) -> tuple[str, bool]:
    existing_content = file_path.read_text(encoding="utf-8")
    frontmatter, _ = parse_frontmatter(existing_content)
    has_update = False

    merged_refs = merge_referenced_by(frontmatter.get("referenced_by", []), ref_data.get("referenced_by", []))
    if len(merged_refs) > len(frontmatter.get("referenced_by", [])):
        frontmatter["referenced_by"] = merged_refs
        has_update = True

    merged_rels = merge_relations(frontmatter.get("relations", []), ref_data.get("relations", []))
    if len(merged_rels) > len(frontmatter.get("relations", [])):
        frontmatter["relations"] = merged_rels
        has_update = True

    existing_aliases = frontmatter.get("aliases", [])
    for alias in ref_data.get("aliases", []):
        if alias not in existing_aliases:
            existing_aliases.append(alias)
            has_update = True
    if has_update:
        frontmatter["aliases"] = existing_aliases

    if not has_update:
        return existing_content, False

    frontmatter["updated"] = date.today().isoformat()
    return build_frontmatter(frontmatter) + build_body(frontmatter), True


def process_staging_file(staging_path: Path, dry_run: bool = False) -> dict:
    staging_data = yaml.safe_load(staging_path.read_text(encoding="utf-8"))
    episode = staging_data.get("episode", "unknown")
    references = staging_data.get("references", [])

    console.print(f"\n[bold cyan]📖 {episode}[/bold cyan] の外部参照を処理中...")
    results = {"episode": episode, "references": [], "created": 0, "updated": 0, "skipped": 0}

    for ref_data in references:
        subtype = ref_data.get("subtype", "mythology")
        canonical_name = ref_data.get("canonical_name", "")
        if not canonical_name:
            console.print("  [yellow]⚠️  canonical_name が取得できません[/yellow]")
            results["skipped"] += 1
            continue

        existing_file = find_existing_reference(canonical_name)
        if existing_file:
            content, has_update = update_reference_file(existing_file, ref_data, episode)
            if not has_update:
                console.print(f"  [dim]  - {canonical_name}: 更新なし（スキップ）[/dim]")
                results["skipped"] += 1
                continue
            action, file_path = "update", existing_file
        else:
            content = build_new_reference_file(ref_data, episode)
            action = "create"
            file_path = build_reference_file_path(subtype, canonical_name)

        if dry_run:
            console.print(f"  [magenta]  [DRY-RUN] {action}: {file_path.name}[/magenta]")
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            icon = "✨" if action == "create" else "🔄"
            console.print(f"  {icon} {action}: {file_path.name}")

        results["references"].append({"name": canonical_name, "subtype": subtype,
                                      "action": action, "file": str(file_path)})
        results["created" if action == "create" else "updated"] += 1

    return results


def main():
    parser = argparse.ArgumentParser(description="外部参照（ME_）変換スクリプト")
    parser.add_argument("--episode", help="特定のエピソードのみ処理（例: ch0057）")
    parser.add_argument("--dry-run", action="store_true", help="書き込まずに差分のみ表示")
    args = parser.parse_args()

    if not STAGING_DIR.exists():
        console.print(f"[red]❌ {STAGING_DIR} が存在しません[/red]")
        sys.exit(1)

    staging_files = sorted(STAGING_DIR.glob("staging_*.yaml"))
    if args.episode:
        staging_files = [f for f in staging_files if args.episode in f.name]
    if not staging_files:
        console.print("[yellow]⚠️  処理対象の staging ファイルが見つかりません[/yellow]")
        sys.exit(0)

    console.print(f"[bold]🔧 {len(staging_files)} 件の staging ファイルから外部参照を処理[/bold]")
    if args.dry_run:
        console.print("[magenta bold]🔍 DRY-RUN モード（書き込みなし）[/magenta bold]")

    all_results = []
    for staging_file in staging_files:
        try:
            all_results.append(process_staging_file(staging_file, dry_run=args.dry_run))
        except Exception as e:
            console.print(f"[red]❌ {staging_file.name} の処理に失敗: {e}[/red]")
            continue

    console.print("\n" + "=" * 60)
    console.print("[bold]📊 外部参照処理サマリー[/bold]")
    table = Table()
    table.add_column("エピソード", style="cyan")
    table.add_column("新規作成", style="green")
    table.add_column("更新", style="yellow")
    table.add_column("スキップ", style="dim")
    for r in all_results:
        table.add_row(r["episode"], str(r["created"]), str(r["updated"]), str(r["skipped"]))
    console.print(table)


if __name__ == "__main__":
    main()
