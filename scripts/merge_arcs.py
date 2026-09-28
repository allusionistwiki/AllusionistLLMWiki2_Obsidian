#!/usr/bin/env python3
"""アーク（ARC_）変換スクリプト: arc_definitions.yaml → wiki/arcs/ARC_*.md + エピソード arc フィールド更新.

使い方:
  python scripts/merge_arcs.py                # 全アークを処理
  python scripts/merge_arcs.py --arc ARC_01   # 特定のアークのみ
  python scripts/merge_arcs.py --dry-run      # 書き込まずに差分表示
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import VAULT_ROOT, SCHEMAS_DIR

console = Console()

ARCS_DIR = VAULT_ROOT / "arcs"
EPISODES_DIR = VAULT_ROOT / "episodes"
MYSTERIES_DIR = VAULT_ROOT / "mysteries"
ARC_DEFINITIONS_FILE = SCHEMAS_DIR / "arc_definitions.yaml"

AUTO_EP_START, AUTO_EP_END = "<!-- AUTO-GENERATED:episodes -->", "<!-- /AUTO-GENERATED:episodes -->"
AUTO_MY_START, AUTO_MY_END = "<!-- AUTO-GENERATED:mysteries -->", "<!-- /AUTO-GENERATED:mysteries -->"


def parse_frontmatter(content: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not m:
        return {}, content
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2)


def build_frontmatter(fm: dict) -> str:
    return "---\n" + yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False) + "---\n"


def extract_wikilink_name(link: str) -> str:
    m = re.match(r"\[\[(?:MY|ARC)_(.+?)\]\]", link)
    return m.group(1) if m else link.replace("[[", "").replace("]]", "")


def load_arc_definitions() -> list[dict]:
    if not ARC_DEFINITIONS_FILE.exists():
        console.print(f"[red]❌ {ARC_DEFINITIONS_FILE} が存在しません[/red]")
        sys.exit(1)
    with open(ARC_DEFINITIONS_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f).get("arcs", [])


def find_episodes_in_range(start: str, end: str) -> list[str]:
    episodes = []
    if not EPISODES_DIR.exists():
        return episodes
    for ep in sorted(EPISODES_DIR.glob("O_ch*.md")):
        m = re.match(r"O_(ch\d{4})_", ep.name)
        if m and start <= m.group(1) <= end:
            episodes.append(f"[[{ep.stem}]]")
    return episodes


def find_episode_file(chapter: str) -> Path | None:
    matches = sorted(EPISODES_DIR.glob(f"O_{chapter}_*.md"))
    return matches[0] if matches else None


def update_episode_arc_field(episode_file: Path, arc_wikilink: str, dry_run: bool = False) -> bool:
    content = episode_file.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)
    if fm.get("arc") == arc_wikilink:
        return False
    fm["arc"] = arc_wikilink
    fm["updated"] = date.today().isoformat()
    if dry_run:
        console.print(f"    [dim][DRY-RUN] {episode_file.name} に arc フィールド設定[/dim]")
        return True
    episode_file.write_text(build_frontmatter(fm) + body, encoding="utf-8")
    return True


def collect_open_mysteries(arc_chapters: list[str], dry_run: bool = False) -> list[str]:
    open_mysteries = set()
    for chapter in arc_chapters:
        ep_file = find_episode_file(chapter)
        if not ep_file:
            continue
        fm, _ = parse_frontmatter(ep_file.read_text(encoding="utf-8"))
        for link in fm.get("mysteries", []):
            name = extract_wikilink_name(link)
            my_file = MYSTERIES_DIR / f"MY_{name}.md"
            if not my_file.exists():
                if not dry_run:
                    console.print(f"    [dim][WARN] ミステリーファイルなし: {name}[/dim]")
                continue
            my_fm, _ = parse_frontmatter(my_file.read_text(encoding="utf-8"))
            if my_fm.get("mystery_status", "candidate") not in ("resolved", "invalidated", "unresolved_at_end"):
                open_mysteries.add(link)
    return sorted(open_mysteries)


def build_section(start: str, title: str, items: list[str], empty: str, end: str) -> str:
    lines = [start, f"## {title}", ""]
    lines += [f"- {i}" for i in items] if items else [empty]
    lines += ["", end, ""]
    return "\n".join(lines)


def build_new_arc_file(arc_def: dict, episodes: list[str], open_mysteries: list[str]) -> str:
    arc_id, name = arc_def["id"], arc_def["name"]
    slug = arc_def.get("slug", name)
    theme = arc_def.get("theme", "")
    macro = arc_def.get("macro_analogy", "")
    desc = arc_def.get("description", "").strip()
    arc_number = 0
    if "_" in arc_id:
        try:
            arc_number = int(arc_id.split("_")[1])
        except ValueError:
            pass
    fm = {
        "schema_version": "5.1",
        "id": f"{arc_id}_{slug}",
        "type": "arc",
        "canonical_name": name,
        "arc_number": arc_number,
        "chapter_range": arc_def.get("chapters", {}),
        "theme": theme,
        "document_status": "active",
        "created": date.today().isoformat(),
        "updated": date.today().isoformat(),
    }
    if macro:
        fm["macro_analogy"] = macro
    body = f"# {name}\n\n"
    if theme:
        body += f"**テーマ**: {theme}\n\n"
    body += (desc + "\n\n") if desc else "（本文：アークの概要を記述）\n"
    body += build_section(AUTO_EP_START, "このアークのエピソード", episodes, "（エピソードなし）", AUTO_EP_END)
    body += build_section(AUTO_MY_START, "未回収の伏線", open_mysteries, "（なし）", AUTO_MY_END)
    return build_frontmatter(fm) + body


def update_arc_file(path: Path, arc_def: dict, episodes: list[str], open_mysteries: list[str]) -> tuple[str, bool]:
    content = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)
    has_update = False
    for key in ("theme", "macro_analogy"):
        v = arc_def.get(key, "")
        if v and fm.get(key) != v:
            fm[key] = v
            has_update = True
    cr = arc_def.get("chapters", {})
    if cr and fm.get("chapter_range") != cr:
        fm["chapter_range"] = cr
        has_update = True
    for start, end, section in (
        (AUTO_EP_START, AUTO_EP_END, build_section(AUTO_EP_START, "このアークのエピソード", episodes, "（エピソードなし）", AUTO_EP_END)),
        (AUTO_MY_START, AUTO_MY_END, build_section(AUTO_MY_START, "未回収の伏線", open_mysteries, "（なし）", AUTO_MY_END)),
    ):
        if start in body:
            pattern = re.escape(start) + r".*?" + re.escape(end)
            new_body = re.sub(pattern, section.rstrip(), body, flags=re.DOTALL)
            if new_body != body:
                body = new_body
                has_update = True
        else:
            body = body.rstrip() + "\n\n" + section
            has_update = True
    if not has_update:
        return content, False
    fm["updated"] = date.today().isoformat()
    return build_frontmatter(fm) + body, True


def process_arc_definition(arc_def: dict, dry_run: bool = False) -> dict:
    arc_id, name = arc_def["id"], arc_def["name"]
    slug = arc_def.get("slug", name)
    chapters = arc_def.get("chapters", {})
    start, end = chapters.get("start", ""), chapters.get("end", "")
    console.print(f"\n[bold cyan]📖 {arc_id}_{name}[/bold cyan] を処理中...")

    results = {"arc_id": arc_id, "name": name, "action": None, "episodes_updated": 0, "open_mysteries": 0}

    episodes = find_episodes_in_range(start, end)
    console.print(f"  [dim]範囲 {start}〜{end} のエピソード: {len(episodes)} 件[/dim]")

    arc_wikilink = f"[[{arc_id}_{slug}]]"
    updated = sum(
        1
        for ep_link in episodes
        if (ep_file := EPISODES_DIR / f"{extract_wikilink_name(ep_link)}.md").exists()
        and update_episode_arc_field(ep_file, arc_wikilink, dry_run)
    )
    console.print(f"  [dim]arc フィールド更新: {updated} 件[/dim]")

    arc_chapters = [m.group(1) for ep in episodes if (m := re.match(r"O_(ch\d{4})_", extract_wikilink_name(ep)))]
    open_mysteries = collect_open_mysteries(arc_chapters, dry_run)
    console.print(f"  [dim]未回収の伏線: {len(open_mysteries)} 件[/dim]")

    file_path = ARCS_DIR / f"{arc_id}_{slug}.md"
    if file_path.exists():
        content, has_update = update_arc_file(file_path, arc_def, episodes, open_mysteries)
        if not has_update:
            console.print("  [dim]更新なし（スキップ）[/dim]")
            results["action"] = "skipped"
            return results
        action = "update"
    else:
        content = build_new_arc_file(arc_def, episodes, open_mysteries)
        action = "create"

    if dry_run:
        console.print(f"  [magenta][DRY-RUN] {action}: {file_path.name}[/magenta]")
    else:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        console.print(f"  {'✨' if action == 'create' else '🔄'} {action}: {file_path.name}")

    results.update(action=action, episodes_updated=updated, open_mysteries=len(open_mysteries))
    return results


def main():
    parser = argparse.ArgumentParser(description="アーク（ARC_）変換スクリプト")
    parser.add_argument("--arc", help="特定のアークのみ処理（例: ARC_01）")
    parser.add_argument("--episode", help="特定エピソード（chNNNN）を含むアークのみ処理")
    parser.add_argument("--dry-run", action="store_true", help="書き込まずに差分のみ表示")
    args = parser.parse_args()

    arc_definitions = load_arc_definitions()
    if not arc_definitions:
        console.print("[yellow]⚠️ アーク定義が見つかりません[/yellow]")
        sys.exit(0)
    if args.arc:
        arc_definitions = [a for a in arc_definitions if a.get("id") == args.arc]
        if not arc_definitions:
            console.print(f"[yellow]⚠️ {args.arc} の定義が見つかりません[/yellow]")
            sys.exit(0)
    if args.episode:
        ep = args.episode if args.episode.startswith("ch") else f"ch{int(args.episode):04d}"
        arc_definitions = [
            a for a in arc_definitions
            if a.get("chapters", {}).get("start", "") <= ep <= a.get("chapters", {}).get("end", "")
        ]
        if not arc_definitions:
            console.print(f"[yellow]⚠️ {ep} を含むアークが見つかりません[/yellow]")
            sys.exit(0)

    console.print(f"[bold]🔧 {len(arc_definitions)} 件のアーク定義を処理[/bold]")
    if args.dry_run:
        console.print("[magenta bold]🔍 DRY-RUN モード（書き込みなし）[/magenta bold]")

    results = []
    for arc_def in arc_definitions:
        try:
            results.append(process_arc_definition(arc_def, dry_run=args.dry_run))
        except Exception as e:
            console.print(f"[red]❌ {arc_def.get('id', 'unknown')} 処理失敗: {e}[/red]")

    table = Table(title="アーク処理サマリー")
    table.add_column("アーク", style="cyan")
    table.add_column("アクション", style="green")
    table.add_column("エピソード更新", style="yellow")
    table.add_column("未回収伏線", style="magenta")
    for r in results:
        table.add_row(r["name"], r["action"] or "skipped", str(r["episodes_updated"]), str(r["open_mysteries"]))
    console.print(table)


if __name__ == "__main__":
    main()
