#!/usr/bin/env python3
"""エピソード（O_）変換スクリプト: staging 全体 → wiki/episodes/O_chNNNN_summary.md（ハブファイル）.

Usage:
    python scripts/merge_episodes.py [--episode ch0057] [--dry-run]
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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT, VAULT_ROOT, STAGING_DIR
EPISODES_DIR = VAULT_ROOT / "episodes"

AUTO_MARKER_LINKS_START = "<!-- AUTO-GENERATED:links -->"
AUTO_MARKER_LINKS_END = "<!-- /AUTO-GENERATED:links -->"

ENTITY_TYPE_LABEL = {
    "characters": "登場人物", "terminology": "用語", "organizations": "組織",
    "items": "物品", "motifs": "モチーフ", "relationships": "関係性", "phrases": "キーフレーズ",
}

KEY_MAP = {
    "character": "characters", "terminology": "terminology", "organization": "organizations",
    "item": "items", "motif": "motifs", "relationship": "relationships", "phrase": "phrases",
}


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
    m = re.match(r"\[\[(?:E|A|MY|ME|ARC)_(.+?)\]\]", wikilink)
    return m.group(1) if m else wikilink.replace("[[", "").replace("]]", "")


def find_existing_episode(episode: str) -> Path | None:
    matches = sorted(EPISODES_DIR.glob(f"O_{episode}_*.md"))
    return matches[0] if matches else None


def collect_links_from_staging(staging_data: dict) -> dict:
    links = {k: [] for k in ["characters", "terminology", "organizations", "items",
                             "motifs", "relationships", "phrases", "claims", "mysteries", "references"]}
    episode = staging_data.get("episode", "")

    for entity in staging_data.get("entities", []):
        target = entity.get("canonical_target", "")
        key = KEY_MAP.get(entity.get("entity_type", ""))
        if target and key and target not in links[key]:
            links[key].append(target)

    for claim in staging_data.get("claims", []):
        target = claim.get("canonical_target")
        if not target:
            target = (f"[[A_{claim.get('predicate','')}_{extract_wikilink_name(claim.get('subject',''))}"
                      f"_{extract_wikilink_name(claim.get('object',''))}_{episode}]]")
        if target not in links["claims"]:
            links["claims"].append(target)

    for mystery in staging_data.get("mysteries", []):
        target = mystery.get("canonical_target", "")
        if target and target not in links["mysteries"]:
            links["mysteries"].append(target)

    for ref in staging_data.get("references", []):
        target = ref.get("canonical_target", "")
        if not target:
            target = f"[[ME_{ref.get('subtype','mythology')}_{ref.get('canonical_name','')}]]"
        if target and target not in links["references"]:
            links["references"].append(target)

    return links


def build_links_section(links: dict) -> str:
    lines = [AUTO_MARKER_LINKS_START, "## このエピソードの要素", ""]
    has_content = False
    for key in ["characters", "terminology", "organizations", "items", "motifs", "relationships", "phrases"]:
        items = links.get(key, [])
        if items:
            has_content = True
            lines.append(f"### {ENTITY_TYPE_LABEL.get(key, key)}")
            lines.append("")
            lines.extend(f"- {item}" for item in items)
            lines.append("")
    for key, label in [("claims", "分析主張"), ("mysteries", "伏線"), ("references", "参照された典拠")]:
        if links[key]:
            has_content = True
            lines.append(f"### {label}")
            lines.append("")
            lines.extend(f"- {item}" for item in links[key])
            lines.append("")
    if not has_content:
        lines += ["（要素なし）", ""]
    lines.append(AUTO_MARKER_LINKS_END)
    lines.append("")
    return "\n".join(lines)


def build_new_episode_body(episode: str, links: dict) -> str:
    body = f"# {episode}\n\n## 概要\n\n（ここにエピソードの要約を記述。人間が書くか、LLMで生成）\n\n"
    body += "## 主要な出来事\n\n- （出来事1）\n- （出来事2）\n\n"
    body += build_links_section(links)
    body += "\n## メモ\n\n（このエピソードに関する自由なメモ）\n"
    return body


def build_new_episode_file(episode: str, links: dict) -> str:
    frontmatter = {
        "schema_version": "5.1",
        "id": f"O_{episode}_summary",
        "type": "episode",
        "title": "summary",
        "chapter": episode,
        "spoiler_after": episode,
        "document_status": "active",
        "created": date.today().isoformat(),
        "updated": date.today().isoformat(),
    }
    for key in ["characters", "terminology", "organizations", "items", "motifs", "relationships", "phrases",
                "claims", "mysteries", "references"]:
        if links[key]:
            frontmatter[key] = links[key]
    return build_frontmatter(frontmatter) + build_new_episode_body(episode, links)


def update_episode_links(body: str, links: dict) -> str:
    new_section = build_links_section(links)
    if AUTO_MARKER_LINKS_START in body:
        pattern = re.escape(AUTO_MARKER_LINKS_START) + r".*?" + re.escape(AUTO_MARKER_LINKS_END)
        body = re.sub(pattern, new_section.rstrip(), body, flags=re.DOTALL)
    else:
        body = body.rstrip() + "\n\n" + new_section
    return body


def update_episode_file(file_path: Path, links: dict) -> tuple[str, bool]:
    existing_content = file_path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(existing_content)
    has_update = False
    for key in ["characters", "terminology", "organizations", "items", "motifs", "relationships",
                "phrases", "claims", "mysteries", "references"]:
        added = set(links.get(key, [])) - set(frontmatter.get(key, []))
        if added:
            frontmatter[key] = sorted(set(frontmatter.get(key, [])) | set(links.get(key, [])))
            has_update = True
    if not has_update:
        return existing_content, False
    frontmatter["updated"] = date.today().isoformat()
    return build_frontmatter(frontmatter) + update_episode_links(body, links), True


def process_staging_file(staging_path: Path, dry_run: bool = False) -> dict:
    staging_data = yaml.safe_load(staging_path.read_text(encoding="utf-8"))
    episode = staging_data.get("episode", "unknown")
    console.print(f"\n[bold cyan]📖 {episode}[/bold cyan] のエピソードを処理中...")

    links = collect_links_from_staging(staging_data)
    existing_file = find_existing_episode(episode)

    if existing_file:
        content, has_update = update_episode_file(existing_file, links)
        if not has_update:
            console.print("  [dim]  - 更新なし（スキップ）[/dim]")
            return {"episode": episode, "action": "skipped", "file": str(existing_file)}
        action, file_path = "update", existing_file
    else:
        content = build_new_episode_file(episode, links)
        action = "create"
        file_path = EPISODES_DIR / f"O_{episode}_summary.md"

    counts = {k: len(links[k]) for k in ["characters", "claims", "mysteries", "references"]}
    if dry_run:
        console.print(f"  [magenta]  [DRY-RUN] {action}: {file_path.name}[/magenta]")
    else:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        icon = "✨" if action == "create" else "🔄"
        console.print(f"  {icon} {action}: {file_path.name}")
    console.print(f"  [dim]  {counts}[/dim]")
    return {"episode": episode, "action": action, "file": str(file_path)}


def main():
    parser = argparse.ArgumentParser(description="エピソード（O_）変換スクリプト")
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

    console.print(f"[bold]🔧 {len(staging_files)} 件の staging ファイルからエピソードを処理[/bold]")
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
    console.print("[bold]📊 エピソード処理サマリー[/bold]")
    table = Table()
    table.add_column("エピソード", style="cyan")
    table.add_column("アクション", style="green")
    table.add_column("ファイル")
    for r in all_results:
        table.add_row(r["episode"], r["action"] or "skipped", r["file"] or "-")
    console.print(table)


if __name__ == "__main__":
    main()
