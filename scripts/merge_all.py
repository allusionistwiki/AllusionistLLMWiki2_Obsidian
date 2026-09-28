#!/usr/bin/env python3
"""すべての変換を統括するランナー（staging → 正規層）.

Usage:
    python scripts/merge_all.py [--episode ch0057] [--dry-run]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from rich.console import Console

console = Console()

ROOT = Path(__file__).resolve().parent.parent

SCRIPTS = [
    ("エンティティ", "scripts/merge_to_canonical.py"),
    ("クレーム", "scripts/merge_claims.py"),
    ("ミステリー", "scripts/merge_mysteries.py"),
    ("外部参照", "scripts/merge_references.py"),
    ("エピソード", "scripts/merge_episodes.py"),
]


def main():
    parser = argparse.ArgumentParser(description="すべての変換を統括実行")
    parser.add_argument("--episode", help="特定のエピソードのみ処理")
    parser.add_argument("--dry-run", action="store_true", help="書き込まずに差分のみ表示")
    args = parser.parse_args()

    for name, script in SCRIPTS:
        console.print(f"\n[bold cyan]{'=' * 60}[/bold cyan]")
        console.print(f"[bold cyan]📦 {name}の変換を開始[/bold cyan]")
        console.print(f"[bold cyan]{'=' * 60}[/bold cyan]")

        cmd = [sys.executable, str(ROOT / script)]
        if args.episode:
            cmd.extend(["--episode", args.episode])
        if args.dry_run:
            cmd.append("--dry-run")

        result = subprocess.run(cmd)
        if result.returncode != 0:
            console.print(f"[red]❌ {name}の変換に失敗しました[/red]")
            sys.exit(1)

    console.print("\n[bold green]✅ すべての変換が完了しました[/bold green]")


if __name__ == "__main__":
    main()
