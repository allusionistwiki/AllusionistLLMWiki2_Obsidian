#!/usr/bin/env python3
"""レビューキュー管理スクリプト: LLM生成本文（review_status: unreviewed）をリストアップし、
人間承認で review_status: human_verified に更新する.

使い方:
  python scripts/review_queue.py                       # レビュー対象をリストアップ
  python scripts/review_queue.py --approve             # すべて承認
  python scripts/review_queue.py --file <path>         # 特定ファイルを承認
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
from paths import VAULT_ROOT

console = Console()

LLM_MARKER_START = "<!-- LLM-GENERATED -->"


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


def collect_review_targets() -> list[dict]:
    targets = []
    for md_file in VAULT_ROOT.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            fm, body = parse_frontmatter(content)
            if LLM_MARKER_START in body and fm.get("review_status", "unreviewed") in ("unreviewed", "pending"):
                targets.append({
                    "file": str(md_file),
                    "type": fm.get("type", "unknown"),
                    "review_status": fm.get("review_status", "unreviewed"),
                    "llm_generated_at": fm.get("llm_generated_at", ""),
                })
        except Exception:
            continue
    return targets


def approve_file(file_path: Path) -> bool:
    content = file_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)
    fm["review_status"] = "human_verified"
    fm["reviewed_at"] = date.today().isoformat()
    fm["updated"] = date.today().isoformat()
    file_path.write_text(build_frontmatter(fm) + body, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="レビューキュー管理スクリプト")
    parser.add_argument("--approve", action="store_true", help="すべてのレビュー対象を承認")
    parser.add_argument("--file", help="特定のファイルを承認")
    args = parser.parse_args()

    if args.file:
        p = Path(args.file)
        if not p.exists():
            console.print(f"[red]❌ {p} が存在しません[/red]")
            sys.exit(1)
        approve_file(p)
        console.print(f"[green]✅ {p.name} を承認しました[/green]")
        return

    targets = collect_review_targets()
    if not targets:
        console.print("[green]✅ レビュー対象はありません[/green]")
        return

    if args.approve:
        n = sum(1 for t in targets if approve_file(Path(t["file"])))
        console.print(f"[green]✅ {n} 件を承認しました[/green]")
        return

    console.print(f"\n[bold]📋 レビュー対象: {len(targets)} 件[/bold]")
    table = Table()
    table.add_column("ファイル", style="cyan")
    table.add_column("タイプ", style="green")
    table.add_column("状態", style="yellow")
    table.add_column("生成日", style="magenta")
    for t in targets:
        table.add_row(Path(t["file"]).name, t["type"], t["review_status"], t["llm_generated_at"])
    console.print(table)


if __name__ == "__main__":
    main()
