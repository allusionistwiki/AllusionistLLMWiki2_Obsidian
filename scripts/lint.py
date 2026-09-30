#!/usr/bin/env python3
"""Lintツール（v5.2 設計書 第15章準拠・5カテゴリ）: 検出のみ（自動修復は fix_all.py）。

使い方:
  python scripts/lint.py                       # 全Lint実行（wiki/ 全体）
  python scripts/lint.py --category structure  # カテゴリ指定
  python scripts/lint.py --file wiki/claims/   # ファイル/ディレクトリ指定
  python scripts/lint.py --severity error      # 重要度フィルタ
  python scripts/lint.py --report work/reports/lint.md --json work/reports/lint.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import List

from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT, VAULT_ROOT, SCHEMAS_DIR, RAW_DIR, WORK_DIR
from lint_modules.utils import LintError, LintResult, Severity
from lint_modules.structure import lint_structure
from lint_modules.links import lint_links, LinkIndex
from lint_modules.evidence import lint_evidence, SourceRegistry
from lint_modules.spoiler import lint_spoiler
from lint_modules.semantic import lint_semantic, SemanticIndex

console = Console()

CATEGORIES = ["structure", "links", "evidence", "spoiler", "semantic"]

SEVERITY_STYLE = {
    Severity.ERROR: "bold red",
    Severity.WARN: "yellow",
    Severity.INFO: "blue",
}


def load_raw_texts(raw_path: Path) -> dict:
    """raw/chNNNN.txt を読み込み（引用検証用）"""
    raws = {}
    if not raw_path.exists():
        return raws
    for txt_file in raw_path.glob("ch*.txt"):
        try:
            raws[txt_file.stem] = txt_file.read_text(encoding="utf-8")
        except Exception:
            continue
    return raws


def run_lint(files: List[Path], categories: List[str], link_index: LinkIndex,
             source_registry: SourceRegistry, semantic_index: SemanticIndex,
             raw_texts: dict) -> LintResult:
    result = LintResult()
    for file_path in files:
        result.files_checked += 1
        file_errors: List[LintError] = []
        if "structure" in categories:
            file_errors.extend(lint_structure(file_path, VAULT_ROOT, SCHEMAS_DIR))
        if "links" in categories:
            file_errors.extend(lint_links(file_path, link_index))
        if "evidence" in categories:
            file_errors.extend(lint_evidence(file_path, source_registry, raw_texts))
        if "spoiler" in categories:
            file_errors.extend(lint_spoiler(file_path))
        if "semantic" in categories:
            file_errors.extend(lint_semantic(file_path, semantic_index))
        if file_errors:
            result.files_with_errors += 1
            result.errors.extend(file_errors)
    return result


def print_results(result: LintResult, severity_filter: str = None):
    errors = result.errors
    if severity_filter:
        errors = [e for e in errors if e.severity.value == severity_filter]
    if not errors:
        console.print(f"\n[bold green]✅ Lint passed ({result.files_checked} files)[/bold green]")
        return

    by_category = {}
    for e in errors:
        by_category.setdefault(e.category, []).append(e)

    for category, errs in sorted(by_category.items()):
        console.print(f"\n[bold cyan]【{category.upper()}】{len(errs)} 件[/bold cyan]")
        for e in errs[:20]:
            style = SEVERITY_STYLE[e.severity]
            console.print(f"  [{style}]{e.format()}[/{style}]")
            if e.suggestion:
                console.print(f"    [dim]→ {e.suggestion}[/dim]")
        if len(errs) > 20:
            console.print(f"  [dim]... 他 {len(errs) - 20} 件[/dim]")

    summary = result.summary()
    console.print("\n[bold]📊 サマリー[/bold]")
    table = Table()
    table.add_column("重要度", style="cyan")
    table.add_column("件数", style="white")
    for sev, count in summary["by_severity"].items():
        style = SEVERITY_STYLE.get(Severity(sev), "white")
        table.add_row(sev.upper(), f"[{style}]{count}[/{style}]")
    console.print(table)
    console.print(f"チェックファイル数: {result.files_checked}")
    console.print(f"エラーあり: {result.files_with_errors}")


def write_report(result: LintResult, report_path: Path):
    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Lintレポート {date.today().isoformat()}",
        "",
        f"- **チェックファイル数**: {result.files_checked}",
        f"- **エラーあり**: {result.files_with_errors}",
        f"- **エラー総数**: {len(result.errors)}",
        "",
        "## サマリー",
        "",
        "| 重要度 | 件数 |",
        "|:---|---:|",
    ]
    summary = result.summary()
    for sev, count in summary["by_severity"].items():
        lines.append(f"| {sev.upper()} | {count} |")
    lines += ["", "## カテゴリ別", "", "| カテゴリ | 件数 |", "|:---|---:|"]
    for cat, count in sorted(summary["by_category"].items()):
        lines.append(f"| {cat} | {count} |")
    lines.append("")

    errors_only = [e for e in result.errors if e.severity == Severity.ERROR]
    if errors_only:
        lines += ["## エラー詳細", ""]
        for e in errors_only[:100]:
            lines.append(f"### {e.code}")
            lines.append(f"- **ファイル**: `{e.file}`")
            if e.line:
                lines.append(f"- **行**: {e.line}")
            lines.append(f"- **メッセージ**: {e.message}")
            if e.suggestion:
                lines.append(f"- **推奨**: {e.suggestion}")
            lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    console.print(f"\n[green]📄 レポート出力: {report_path}[/green]")


def is_navigation_page(p: Path) -> bool:
    """build_public_index.py が生成するナビページ（index.md / nav/）は
    構造スキーマ（type/schema_version）を持たない生成物なので lint 対象外。"""
    return p.name == "index.md" or p.parent.name == "nav"


def collect_files(vault_path: Path, file_filter: str = None) -> List[Path]:
    if file_filter:
        p = Path(file_filter)
        if not p.is_absolute():
            p = ROOT / file_filter
        if p.is_file():
            return [p]
        if p.is_dir():
            return sorted(x for x in p.rglob("*.md") if not is_navigation_page(x))
        return []
    return sorted(x for x in vault_path.rglob("*.md") if not is_navigation_page(x))


def main():
    parser = argparse.ArgumentParser(description="Lintツール（v5.2 §15）")
    parser.add_argument("--category", choices=CATEGORIES, help="カテゴリ指定")
    parser.add_argument("--file", help="ファイルまたはディレクトリ指定")
    parser.add_argument("--report", help="Markdownレポート出力先")
    parser.add_argument("--json", help="JSONレポート出力先")
    parser.add_argument("--severity", choices=["error", "warn", "info"], help="表示する重要度をフィルタ")
    args = parser.parse_args()

    if not VAULT_ROOT.exists():
        console.print(f"[red]❌ vault パスが存在しません: {VAULT_ROOT}[/red]")
        sys.exit(1)

    categories = [args.category] if args.category else CATEGORIES
    files = collect_files(VAULT_ROOT, args.file)
    if not files:
        console.print("[yellow]⚠️ 対象ファイルが見つかりません[/yellow]")
        sys.exit(0)

    console.print(f"[bold]🔍 {len(files)} 件のファイルをLint中...[/bold]")
    console.print(f"[dim]カテゴリ: {', '.join(categories)}[/dim]")

    console.print("[dim]  リンクインデックスを構築中...[/dim]")
    link_index = LinkIndex(VAULT_ROOT)
    link_index.build()
    # Lint対象が vault 外（docs/samples 等）の場合、対象内リンクも解決可能に
    outside = [f for f in files if VAULT_ROOT not in f.parents]
    if outside:
        link_index.scan(outside)

    console.print("[dim]  出典レジストリを読み込み中...[/dim]")
    source_registry = SourceRegistry(ROOT / "sources" / "source-registry")
    source_registry.load()

    console.print("[dim]  意味インデックスを構築中...[/dim]")
    semantic_index = SemanticIndex(VAULT_ROOT)
    semantic_index.build()

    console.print("[dim]  原文を読み込み中...[/dim]")
    raw_texts = load_raw_texts(RAW_DIR)

    result = run_lint(files, categories, link_index, source_registry, semantic_index, raw_texts)

    print_results(result, args.severity)

    if args.report:
        rp = Path(args.report)
        write_report(result, rp if rp.is_absolute() else ROOT / rp)

    if args.json:
        jp = Path(args.json)
        if not jp.is_absolute():
            jp = ROOT / jp
        jp.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "date": date.today().isoformat(),
            "summary": result.summary(),
            "errors": [
                {"file": str(e.file), "category": e.category, "code": e.code,
                 "severity": e.severity.value, "message": e.message,
                 "line": e.line, "suggestion": e.suggestion}
                for e in result.errors
            ],
        }
        jp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        console.print(f"[green]📄 JSONレポート出力: {jp}[/green]")

    if result.has_errors():
        sys.exit(1)


if __name__ == "__main__":
    main()
