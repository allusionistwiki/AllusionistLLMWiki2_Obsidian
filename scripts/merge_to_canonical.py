#!/usr/bin/env python3
"""正規層（Markdown）変換スクリプト: 第2層 staging YAML → 第3層 エンティティ Markdown.

Usage:
    python scripts/merge_to_canonical.py                    # 全エピソードを処理
    python scripts/merge_to_canonical.py --episode ch0057   # 特定のエピソードのみ
    python scripts/merge_to_canonical.py --dry-run          # 書き込まずに差分表示
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

console = Console()

ROOT = Path(__file__).resolve().parent.parent
VAULT_ROOT = ROOT / "wiki"
STAGING_DIR = ROOT / "work/staging"
REPORTS_DIR = ROOT / "work/reports"

# entity_type → 正規層プレフィックス（docs/naming-convention.md 準拠）
TYPE_PREFIX = {
    "character": "char",
    "terminology": "term",
    "organization": "org",
    "item": "item",
    "motif": "motif",
    "relationship": "relation",
    "phrase": "phrase",
}

# entity_type → entity.schema.json の subtype（スキーマ準拠）
TYPE_SUBTYPE = {
    "character": "character",
    "terminology": "terminology",
    "organization": "organization",
    "item": "item",
    "motif": "visual_motif",
    "relationship": "relationship",
    "phrase": "key_phrase",
}

# entity_type → ディレクトリのマッピング
ENTITY_TYPE_DIRS = {
    "character": "entities/characters",
    "terminology": "entities/terminology",
    "organization": "entities/organizations",
    "item": "entities/items",
    "motif": "entities/motifs",
    "relationship": "entities/relationships",
    "phrase": "entities/phrases",
}

# アスペクト → セクションタイトルのマッピング
ASPECT_SECTIONS = {
    "visual": "視覚的記述",
    "name": "名称・呼称",
    "speech": "セリフ・発言",
    "action": "行動・動作",
    "relationship": "関係性",
    "symbolic": "象徴・比喩",
}

AUTO_MARKER_PREFIX = "<!-- AUTO-GENERATED:"
AUTO_MARKER_SUFFIX = " -->"


def parse_frontmatter(content: str) -> tuple[dict, str]:
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not match:
        return {}, content
    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        frontmatter = {}
    return frontmatter, match.group(2)


def build_frontmatter(frontmatter: dict) -> str:
    yaml_str = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_str}---\n"


def build_section_markers(aspect: str) -> tuple[str, str]:
    return f"{AUTO_MARKER_PREFIX}{aspect}{AUTO_MARKER_SUFFIX}", f"<!-- /AUTO-GENERATED:{aspect} -->"


def build_aspect_section(aspect: str, observations: list) -> str:
    if not observations:
        return ""
    section_title = ASPECT_SECTIONS.get(aspect, aspect)
    start_marker, end_marker = build_section_markers(aspect)
    lines = [start_marker, f"## {section_title}", ""]
    sorted_obs = sorted(observations, key=lambda x: x.get("locator", {}).get("chapter", ""))
    for obs in sorted_obs:
        chapter = obs.get("locator", {}).get("chapter", "unknown")
        quote = obs.get("quote", "")
        lines.append(f"- **{chapter}**: {quote}")
    lines.extend(["", end_marker, ""])
    return "\n".join(lines)


def extract_observations_from_section(body: str, aspect: str) -> list:
    start_marker, end_marker = build_section_markers(aspect)
    match = re.search(re.escape(start_marker) + r"(.*?)" + re.escape(end_marker), body, re.DOTALL)
    if not match:
        return []
    observations = []
    for line in match.group(1).split("\n"):
        m = re.match(r"- \*\*(ch\d{4}|unknown)\*\*: (.*)", line.strip())
        if m:
            observations.append({"locator": {"chapter": m.group(1)}, "quote": m.group(2)})
    return observations


def merge_observations(existing: list, new: list) -> list:
    merged = list(existing)
    for new_obs in new:
        new_chapter = new_obs.get("locator", {}).get("chapter", "")
        new_quote = new_obs.get("quote", "")
        is_duplicate = any(
            obs.get("locator", {}).get("chapter") == new_chapter and obs.get("quote") == new_quote
            for obs in existing
        )
        if not is_duplicate:
            merged.append(new_obs)
    return merged


def update_auto_sections(body: str, aspects: dict) -> str:
    for aspect, aspect_data in aspects.items():
        new_observations = aspect_data.get("observations", [])
        if not new_observations:
            continue
        start_marker, end_marker = build_section_markers(aspect)
        if start_marker in body:
            existing_obs = extract_observations_from_section(body, aspect)
            merged_obs = merge_observations(existing_obs, new_observations)
            new_section = build_aspect_section(aspect, merged_obs)
            pattern = re.escape(start_marker) + r".*?" + re.escape(end_marker)
            body = re.sub(pattern, new_section.rstrip(), body, flags=re.DOTALL)
        else:
            new_section = build_aspect_section(aspect, new_observations)
            if new_section:
                body = body.rstrip() + "\n\n" + new_section
    return body


def get_entity_file_path(entity_type: str, entity_name: str) -> Path:
    prefix = TYPE_PREFIX.get(entity_type, "term")
    subdir = ENTITY_TYPE_DIRS.get(entity_type, "entities/terminology")
    return VAULT_ROOT / subdir / f"E_{prefix}_{entity_name}.md"


def build_new_entity_file(entity_name: str, entity_type: str, episode: str, aspects: dict) -> str:
    prefix = TYPE_PREFIX.get(entity_type, "term")
    frontmatter = {
        "schema_version": "5.1",
        "id": f"E_{prefix}_{entity_name}",
        "type": "entity",
        "subtype": TYPE_SUBTYPE.get(entity_type, entity_type),
        "canonical_name": entity_name,
        "aliases": [],
        "first_appearance": episode,
        "spoiler_after": episode,
        "document_status": "active",
        "created": date.today().isoformat(),
        "updated": date.today().isoformat(),
    }
    body = f"# {entity_name}\n\n（本文：人間が記述する部分。自動生成では変更されません。）\n"
    for aspect, aspect_data in aspects.items():
        observations = aspect_data.get("observations", [])
        if observations:
            section = build_aspect_section(aspect, observations)
            if section:
                body += "\n" + section
    return build_frontmatter(frontmatter) + body


def merge_entity_file(file_path: Path, entity_name: str, entity_type: str, episode: str, aspects: dict) -> tuple[str, str]:
    if not file_path.exists():
        return "create", build_new_entity_file(entity_name, entity_type, episode, aspects)

    frontmatter, body = parse_frontmatter(file_path.read_text(encoding="utf-8"))
    frontmatter["updated"] = date.today().isoformat()
    current_first = frontmatter.get("first_appearance", "ch9999")
    if episode < current_first:
        frontmatter["first_appearance"] = episode
        frontmatter["spoiler_after"] = episode
    body = update_auto_sections(body, aspects)
    return "update", build_frontmatter(frontmatter) + body


def process_staging_file(staging_path: Path, dry_run: bool = False) -> dict:
    staging_data = yaml.safe_load(staging_path.read_text(encoding="utf-8"))
    episode = staging_data.get("episode", "unknown")
    entities = staging_data.get("entities", [])

    console.print(f"\n[bold cyan]📖 {episode}[/bold cyan] を処理中...")
    results = {"episode": episode, "entities": [], "created": 0, "updated": 0, "skipped": 0}

    for entity_data in entities:
        target = entity_data.get("canonical_target", "")
        m = re.match(r"\[\[E_(\w+)_(.+?)\]\]", target)
        if not m:
            console.print(f"  [yellow]⚠️  不正な canonical_target: {target}[/yellow]")
            results["skipped"] += 1
            continue
        entity_type = entity_data.get("entity_type", m.group(1))
        entity_name_clean = m.group(2)
        aspects = entity_data.get("aspects", {})

        has_observations = any(obs_list.get("observations") for obs_list in aspects.values())
        if not has_observations:
            console.print(f"  [dim]  - {entity_name_clean}: 観察なし（スキップ）[/dim]")
            results["skipped"] += 1
            continue

        file_path = get_entity_file_path(entity_type, entity_name_clean)
        action, content = merge_entity_file(file_path, entity_name_clean, entity_type, episode, aspects)

        if dry_run:
            console.print(f"  [magenta]  [DRY-RUN] {action}: {file_path.relative_to(ROOT)}[/magenta]")
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            icon = "✨" if action == "create" else "🔄"
            console.print(f"  {icon} {action}: {file_path.relative_to(ROOT)}")

        results["entities"].append({"name": entity_name_clean, "action": action, "file": str(file_path)})
        results["created" if action == "create" else "updated"] += 1

    return results


def generate_report(all_results: list, dry_run: bool = False) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"merge_report_{date.today().isoformat()}.md"
    lines = [
        f"# マージレポート {date.today().isoformat()}",
        "",
        f"- **モード**: {'DRY-RUN' if dry_run else '本実行'}",
        f"- **処理エピソード数**: {len(all_results)}",
        f"- **新規作成**: {sum(r['created'] for r in all_results)}",
        f"- **更新**: {sum(r['updated'] for r in all_results)}",
        f"- **スキップ**: {sum(r['skipped'] for r in all_results)}",
        "",
    ]
    for result in all_results:
        lines += [f"## {result['episode']}", "", f"- 新規作成: {result['created']}",
                  f"- 更新: {result['updated']}", f"- スキップ: {result['skipped']}", ""]
        if result["entities"]:
            lines += ["| エンティティ | アクション | ファイル |", "|:---|:---|:---|"]
            for entity in result["entities"]:
                lines.append(f"| {entity['name']} | {entity['action']} | `{entity['file']}` |")
            lines.append("")
    if not dry_run:
        report_path.write_text("\n".join(lines), encoding="utf-8")
        console.print(f"\n[green]📄 レポートを生成: {report_path.relative_to(ROOT)}[/green]")
    return report_path


def main():
    parser = argparse.ArgumentParser(description="正規層（Markdown）変換スクリプト")
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

    console.print(f"[bold]🔧 {len(staging_files)} 件の staging ファイルを処理[/bold]")
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
    console.print("[bold]📊 サマリー[/bold]")
    table = Table()
    table.add_column("エピソード", style="cyan")
    table.add_column("新規作成", style="green")
    table.add_column("更新", style="yellow")
    table.add_column("スキップ", style="dim")
    for r in all_results:
        table.add_row(r["episode"], str(r["created"]), str(r["updated"]), str(r["skipped"]))
    console.print(table)
    generate_report(all_results, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
