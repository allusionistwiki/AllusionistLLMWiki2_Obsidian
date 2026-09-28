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


def collect_merge_candidates() -> list[dict]:
    """キャラクターの merge_candidates（status: proposed/under_review）を集める"""
    items = []
    for md_file in (VAULT_ROOT / "entities" / "characters").rglob("*.md"):
        try:
            fm, _ = parse_frontmatter(md_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        for mc in fm.get("merge_candidates", []) or []:
            if mc.get("status") in ("proposed", "under_review"):
                items.append({
                    "file": str(md_file),
                    "source": fm.get("canonical_name", md_file.stem),
                    "target": mc.get("target", ""),
                    "reason": mc.get("reason", ""),
                    "score": mc.get("similarity_score", ""),
                    "status": mc.get("status", "proposed"),
                    "proposed_by": (mc.get("proposed_by") or {}).get("kind", ""),
                })
    return items


def set_merge_status(file_path: Path, target: str, status: str) -> bool:
    """特定ファイルの merge_candidates[target] の status を更新（人間判断のみ）"""
    content = file_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)
    found = False
    for mc in fm.get("merge_candidates", []) or []:
        if mc.get("target") == target:
            mc["status"] = status
            found = True
    if not found:
        return False
    fm["updated"] = date.today().isoformat()
    file_path.write_text(build_frontmatter(fm) + body, encoding="utf-8")
    return True


def main():
    parser = argparse.ArgumentParser(description="レビューキュー管理スクリプト")
    parser.add_argument("--approve", action="store_true", help="すべてのレビュー対象を承認")
    parser.add_argument("--file", help="特定のファイルを承認")
    parser.add_argument("--merges", action="store_true", help="統合候補（merge_candidates）を一覧")
    parser.add_argument("--merge-approve", nargs=2, metavar=("FILE", "TARGET"),
                        help="統合候補を承認（merge_candidates の status を approved に）")
    parser.add_argument("--merge-reject", nargs=2, metavar=("FILE", "TARGET"),
                        help="統合候補を却下（status を rejected に）")
    args = parser.parse_args()

    if args.merge_approve:
        p, target = Path(args.merge_approve[0]), args.merge_approve[1]
        if set_merge_status(p, target, "approved"):
            console.print(f"[green]✅ {p.name} → {target} を承認しました[/green]")
            console.print("[dim]  統合本体（superseded_by への書き換え）は merge スクリプト/人間作業[/dim]")
        else:
            console.print(f"[red]❌ {p.name} に target={target} の候補がありません[/red]")
            sys.exit(1)
        return
    if args.merge_reject:
        p, target = Path(args.merge_reject[0]), args.merge_reject[1]
        if set_merge_status(p, target, "rejected"):
            console.print(f"[yellow]⏸ {p.name} → {target} を却下しました[/yellow]")
        else:
            console.print(f"[red]❌ {p.name} に target={target} の候補がありません[/red]")
            sys.exit(1)
        return

    if args.merges:
        items = collect_merge_candidates()
        if not items:
            console.print("[green]✅ 統合候補はありません[/green]")
            return
        console.print(f"\n[bold]🔗 統合候補: {len(items)} 件[/bold]")
        table = Table()
        table.add_column("ソース", style="cyan")
        table.add_column("ターゲット", style="green")
        table.add_column("根拠", style="white")
        table.add_column("類似度", style="yellow")
        table.add_column("状態", style="magenta")
        table.add_column("提案者", style="dim")
        for it in sorted(items, key=lambda x: -(x["score"] if isinstance(x["score"], (int, float)) else 0)):
            table.add_row(it["source"], it["target"], it["reason"][:40],
                          str(it["score"]), it["status"], it["proposed_by"])
        console.print(table)
        console.print("[dim]承認: --merge-approve <file> <target> ／ 却下: --merge-reject <file> <target>[/dim]")
        return

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
