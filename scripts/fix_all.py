#!/usr/bin/env python3
"""自動修復スクリプト（統括ランナー）: Lint検出と修復適用を分離（v5.2 §15.6）.

安全レベル: L1=安全（意味不変）/ L2=注意（構造変更・可逆）/ L3=危険（人間確認必須・未実装）
安全機構: バックアップ（work/_backup/）、差分表示、変更ログ（work/changesets/）、デフォルト dry-run.

使い方:
  python scripts/fix_all.py                          # dry-run（デフォルト）
  python scripts/fix_all.py --apply                  # L1のみ適用
  python scripts/fix_all.py --level L2 --apply -y    # L2まで確認なし適用
  python scripts/fix_all.py --category structure
  python scripts/fix_all.py --file wiki/claims/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.console import Console

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT, VAULT_ROOT
from fix_modules.utils import FixItem, SafetyLevel, BackupManager, ChangeLog, apply_fix
from fix_modules.structure_fix import collect_structure_fixes
from fix_modules.links_fix import collect_link_fixes, LinkFixIndex
from fix_modules.spoiler_fix import collect_spoiler_fixes

console = Console()


def collect_files(vault_path: Path, file_filter: str = None) -> list[Path]:
    if file_filter:
        p = Path(file_filter)
        if not p.is_absolute():
            p = ROOT / p
        if p.is_file():
            return [p]
        if p.is_dir():
            return sorted(p.rglob("*.md"))
        return []
    return sorted(vault_path.rglob("*.md"))


def collect_all_fixes(files: list[Path], categories: list[str], link_index: LinkFixIndex) -> list[FixItem]:
    all_fixes: list[FixItem] = []
    for file_path in files:
        if "structure" in categories:
            all_fixes.extend(collect_structure_fixes(file_path))
        if "links" in categories:
            all_fixes.extend(collect_link_fixes(file_path, link_index))
        if "spoiler" in categories:
            all_fixes.extend(collect_spoiler_fixes(file_path))
    return all_fixes


def filter_fixes(fixes: list[FixItem], max_level: SafetyLevel, category_filter: str = None) -> list[FixItem]:
    filtered = []
    for fix in fixes:
        if fix.safety_level.value > max_level.value:
            continue
        if category_filter and fix.category != category_filter:
            continue
        filtered.append(fix)
    return filtered


def print_fix_plan(fixes: list[FixItem]):
    if not fixes:
        console.print("[yellow]⚠️ 修復候補はありません[/yellow]")
        return
    by_level = {SafetyLevel.L1: [], SafetyLevel.L2: [], SafetyLevel.L3: []}
    for fix in fixes:
        by_level[fix.safety_level].append(fix)
    level_names = {
        SafetyLevel.L1: "🟢 L1: 安全（意味を変更しない）",
        SafetyLevel.L2: "🟡 L2: 注意（構造を変更するが可逆）",
        SafetyLevel.L3: "🔴 L3: 危険（意味を変更する可能性）",
    }
    for level in [SafetyLevel.L1, SafetyLevel.L2, SafetyLevel.L3]:
        level_fixes = by_level[level]
        if not level_fixes:
            continue
        console.print(f"\n[bold]{level_names[level]}[/bold] ({len(level_fixes)} 件)")
        by_category: dict = {}
        for fix in level_fixes:
            by_category.setdefault(fix.category, []).append(fix)
        for category, cat_fixes in sorted(by_category.items()):
            console.print(f"  [cyan]【{category}】{len(cat_fixes)} 件[/cyan]")
            for fix in cat_fixes[:10]:
                console.print(f"    - {fix.code} @ {fix.file.name}")
                console.print(f"      [dim]{fix.suggestion}[/dim]")
            if len(cat_fixes) > 10:
                console.print(f"    [dim]... 他 {len(cat_fixes) - 10} 件[/dim]")


def main():
    parser = argparse.ArgumentParser(description="自動修復スクリプト")
    parser.add_argument("--apply", action="store_true", help="実際に適用（デフォルトはdry-run）")
    parser.add_argument("--level", choices=["L1", "L2", "L3"], default="L1",
                        help="適用する最大安全レベル（デフォルト: L1）")
    parser.add_argument("--category", choices=["structure", "links", "spoiler"], help="カテゴリ指定")
    parser.add_argument("--file", help="ファイルまたはディレクトリ指定")
    parser.add_argument("--no-diff", action="store_true", help="差分表示を省略")
    parser.add_argument("--yes", "-y", action="store_true", help="確認なしで適用")
    args = parser.parse_args()

    if not VAULT_ROOT.exists():
        console.print(f"[red]❌ vault パスが存在しません: {VAULT_ROOT}[/red]")
        sys.exit(1)

    categories = [args.category] if args.category else ["structure", "links", "spoiler"]
    max_level = SafetyLevel(int(args.level.replace("L", "")))

    files = collect_files(VAULT_ROOT, args.file)
    if not files:
        console.print("[yellow]⚠️ 対象ファイルが見つかりません[/yellow]")
        sys.exit(0)

    console.print(f"[bold]🔧 {len(files)} 件のファイルから修復候補を収集中...[/bold]")
    console.print(f"[dim]カテゴリ: {', '.join(categories)}[/dim]")
    console.print(f"[dim]最大安全レベル: {args.level}[/dim]")

    link_index = LinkFixIndex(VAULT_ROOT)
    link_index.build()

    all_fixes = collect_all_fixes(files, categories, link_index)
    filtered_fixes = filter_fixes(all_fixes, max_level, args.category)

    print_fix_plan(filtered_fixes)
    if not filtered_fixes:
        sys.exit(0)

    if not args.apply:
        console.print("\n[yellow]💡 これは dry-run です。適用するには --apply を使用してください[/yellow]")
        console.print(f"[dim]   例: python scripts/fix_all.py --apply --level {args.level}[/dim]")
        sys.exit(0)

    if not args.yes:
        console.print(f"\n[bold yellow]⚠️ {len(filtered_fixes)} 件の修復を適用します。よろしいですか？[/bold yellow]")
        try:
            response = input("続行する場合は 'yes' と入力: ").strip().lower()
        except EOFError:
            console.print("[red]標準入力がなくキャンセルしました（--yes で確認スキップ可）[/red]")
            sys.exit(0)
        if response != "yes":
            console.print("[red]キャンセルしました[/red]")
            sys.exit(0)

    backup_manager = BackupManager()
    change_log = ChangeLog()

    console.print("\n[bold]🔧 修復を適用中...[/bold]")
    applied_count = sum(
        1 for fix in filtered_fixes
        if apply_fix(fix, backup_manager, change_log, dry_run=False, show_diff_flag=not args.no_diff)
    )
    skipped_count = len(filtered_fixes) - applied_count

    console.print("\n[bold]📊 サマリー[/bold]")
    console.print(f"  適用: {applied_count} 件")
    console.print(f"  スキップ: {skipped_count} 件")
    console.print(f"  [dim]{backup_manager.summary()}[/dim]")
    log_path = change_log.save()
    if log_path:
        console.print(f"  [green]変更ログ: {log_path}[/green]")


if __name__ == "__main__":
    main()
