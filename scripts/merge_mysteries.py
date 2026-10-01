#!/usr/bin/env python3
"""ミステリー（MY_）変換スクリプト: staging mysteries → wiki/mysteries/MY_*.md.

Usage:
    python scripts/merge_mysteries.py [--episode ch0057] [--dry-run]
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
MYSTERIES_DIR = VAULT_ROOT / "mysteries"

STATUS_LABELS = {
    "candidate": "候補", "open": "未解決", "partially_resolved": "部分的に解決",
    "resolved": "解決済み", "invalidated": "無効化", "unresolved_at_end": "未解決のまま完結",
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
    m = re.match(r"\[\[(?:MY|E|A)_(.+?)\]\]", wikilink)
    return m.group(1) if m else wikilink.replace("[[", "").replace("]]", "")


def find_existing_mystery(mystery_slug: str) -> Optional[Path]:
    p = MYSTERIES_DIR / f"MY_{mystery_slug}.md"
    return p if p.exists() else None


def build_timeline_section(timeline: dict) -> str:
    lines = ["## タイムライン", ""]
    if timeline.get("introduced"):
        lines.append(f"- **提示**: {timeline['introduced']}")
    for chapter in sorted(timeline.get("hinted", [])):
        lines.append(f"- **ヒント**: {chapter}")
    if timeline.get("resolved"):
        lines.append(f"- **解決**: {timeline['resolved']}")
    if timeline.get("invalidated"):
        lines.append(f"- **無効化**: {timeline['invalidated']}")
    lines.append("")
    return "\n".join(lines)


def build_body(frontmatter: dict) -> str:
    slug = extract_wikilink_name(frontmatter.get("id", ""))
    status = frontmatter.get("mystery_status", "open")
    label = STATUS_LABELS.get(status, status)
    body = f"# {slug}\n\n**状態**: {status} ({label})\n\n（本文：謎の説明、考察、関連情報など）\n\n"
    body += build_timeline_section(frontmatter.get("timeline", {}))
    if frontmatter.get("resolution_summary"):
        body += f"\n## 解決の要約\n\n{frontmatter['resolution_summary']}\n"
    return body


def clean_timeline(timeline: dict) -> dict:
    """空文字の resolved/invalidated を除去（スキーマ pattern 準拠）."""
    return {k: v for k, v in timeline.items() if v not in ("", [], None)}


def build_new_mystery_file(mystery_data: dict, episode: str) -> str:
    slug = extract_wikilink_name(mystery_data.get("canonical_target", ""))
    status = mystery_data.get("status", "candidate")
    timeline = clean_timeline({
        "introduced": mystery_data.get("introduced", episode),
        "hinted": [],
    })
    frontmatter = {
        "schema_version": "5.1",
        "id": f"MY_{slug}",
        "type": "mystery",
        "title": re.sub(r"^ch\d{4}_", "", slug),
        "mystery_status": status,
        "timeline": timeline,
        "related_facts": mystery_data.get("related_facts", []),
        "related_claims": mystery_data.get("related_claims", []),
        "disclosure": {
            "minimum_progress": episode,
            "audience": ["reader", "rereader", "analyst"],
            "level": "surface",
        },
        "created": date.today().isoformat(),
        "updated": date.today().isoformat(),
    }
    return build_frontmatter(frontmatter) + build_body(frontmatter)


def update_mystery_file(file_path: Path, mystery_data: dict, episode: str) -> tuple[str, bool]:
    existing_content = file_path.read_text(encoding="utf-8")
    frontmatter, _ = parse_frontmatter(existing_content)
    has_update = False

    timeline = frontmatter.get("timeline", {})
    if timeline.get("resolved"):
        return existing_content, False

    hinted = timeline.get("hinted", [])
    if episode not in hinted and episode != timeline.get("introduced"):
        hinted.append(episode)
        timeline["hinted"] = sorted(hinted)
        has_update = True

    current_status = frontmatter.get("mystery_status", "candidate")
    new_status = mystery_data.get("status", current_status)
    if current_status == "candidate" and hinted:
        new_status = "open"
    if new_status != current_status:
        frontmatter["mystery_status"] = new_status
        has_update = True

    if mystery_data.get("resolved"):
        timeline["resolved"] = mystery_data["resolved"]
        frontmatter["mystery_status"] = "resolved"
        frontmatter["resolution_summary"] = mystery_data.get("resolution_summary", "")
        has_update = True

    if not has_update:
        return existing_content, False

    frontmatter["timeline"] = clean_timeline(timeline)
    frontmatter["updated"] = date.today().isoformat()
    return build_frontmatter(frontmatter) + build_body(frontmatter), True


def process_staging_file(staging_path: Path, dry_run: bool = False) -> dict:
    staging_data = yaml.safe_load(staging_path.read_text(encoding="utf-8"))
    episode = staging_data.get("episode", "unknown")
    mysteries = staging_data.get("mysteries", [])

    console.print(f"\n[bold cyan]📖 {episode}[/bold cyan] のミステリーを処理中...")
    results = {"episode": episode, "mysteries": [], "created": 0, "updated": 0, "skipped": 0}

    for mystery_data in mysteries:
        slug = extract_wikilink_name(mystery_data.get("canonical_target", ""))
        if not slug:
            console.print("  [yellow]⚠️  ミステリー名が取得できません[/yellow]")
            results["skipped"] += 1
            continue

        existing_file = find_existing_mystery(slug)
        if existing_file:
            content, has_update = update_mystery_file(existing_file, mystery_data, episode)
            if not has_update:
                console.print(f"  [dim]  - {slug}: 更新なし（スキップ）[/dim]")
                results["skipped"] += 1
                continue
            action, file_path = "update", existing_file
        else:
            content = build_new_mystery_file(mystery_data, episode)
            action = "create"
            file_path = MYSTERIES_DIR / f"MY_{slug}.md"

        if dry_run:
            console.print(f"  [magenta]  [DRY-RUN] {action}: {file_path.name}[/magenta]")
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            icon = "✨" if action == "create" else "🔄"
            console.print(f"  {icon} {action}: {file_path.name}")

        results["mysteries"].append({"slug": slug, "action": action, "file": str(file_path)})
        results["created" if action == "create" else "updated"] += 1

    return results


def main():
    parser = argparse.ArgumentParser(description="ミステリー（MY_）変換スクリプト")
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

    console.print(f"[bold]🔧 {len(staging_files)} 件の staging ファイルからミステリーを処理[/bold]")
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
    console.print("[bold]📊 ミステリー処理サマリー[/bold]")
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
