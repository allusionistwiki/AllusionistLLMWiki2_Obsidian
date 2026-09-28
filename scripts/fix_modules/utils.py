#!/usr/bin/env python3
"""自動修復共通ユーティリティ: 安全レベル、バックアップ、差分表示、変更ログ"""
from __future__ import annotations

import difflib
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import ROOT, WORK_DIR

console = Console()

BACKUP_DIR = WORK_DIR / "_backup"
CHANGESETS_DIR = WORK_DIR / "changesets"


class SafetyLevel(Enum):
    L1 = 1  # 安全: 意味を変更しない
    L2 = 2  # 注意: 構造を変更するが可逆
    L3 = 3  # 危険: 意味を変更する可能性


@dataclass
class FixItem:
    """修復候補"""
    file: Path
    category: str
    code: str
    safety_level: SafetyLevel
    description: str
    suggestion: str
    apply_fn: Optional[Callable[[str], str]] = None

    def format(self) -> str:
        return f"[L{self.safety_level.value}] {self.code} @ {self.file.name}: {self.description}"


class BackupManager:
    """バックアップ管理（work/_backup/{timestamp}/）"""

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_root = BACKUP_DIR / self.timestamp
        self.backed_up: List[Path] = []

    def backup_file(self, file_path: Path) -> Path:
        try:
            rel_path = file_path.relative_to(ROOT)
        except ValueError:
            rel_path = Path(file_path.name)
        backup_path = self.backup_root / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        self.backed_up.append(file_path)
        return backup_path

    def summary(self) -> str:
        return f"{len(self.backed_up)} ファイルを {self.backup_root} にバックアップ"


class ChangeLog:
    """変更ログ記録（work/changesets/fix_{timestamp}.yaml）"""

    def __init__(self):
        self.entries: List[dict] = []

    def record(self, fix_item: FixItem, applied: bool = True):
        self.entries.append({
            "timestamp": datetime.now().isoformat(),
            "file": str(fix_item.file),
            "category": fix_item.category,
            "code": fix_item.code,
            "safety_level": f"L{fix_item.safety_level.value}",
            "description": fix_item.description,
            "suggestion": fix_item.suggestion,
            "applied": applied,
        })

    def save(self) -> Optional[Path]:
        if not self.entries:
            return None
        CHANGESETS_DIR.mkdir(parents=True, exist_ok=True)
        log_path = CHANGESETS_DIR / f"fix_{datetime.now():%Y%m%d_%H%M}.yaml"
        data = {
            "type": "fix_changelog",
            "created": datetime.now().isoformat(),
            "total_applied": sum(1 for e in self.entries if e["applied"]),
            "total_skipped": sum(1 for e in self.entries if not e["applied"]),
            "entries": self.entries,
        }
        with open(log_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return log_path


def show_diff(file_path: Path, original: str, modified: str):
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile=f"{file_path.name} (original)",
        tofile=f"{file_path.name} (modified)",
        n=3,
    )
    diff_text = "".join(diff)
    if not diff_text:
        console.print("[dim]（変更なし）[/dim]")
        return
    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
    console.print(Panel(syntax, title=str(file_path), border_style="cyan"))


def apply_fix(fix_item: FixItem, backup_manager: BackupManager, change_log: ChangeLog,
              dry_run: bool = False, show_diff_flag: bool = True) -> bool:
    """修復を適用（バックアップ→差分→書き込み→ログ）"""
    if fix_item.apply_fn is None:
        return False
    try:
        original = fix_item.file.read_text(encoding="utf-8")
        modified = fix_item.apply_fn(original)
    except Exception as e:
        console.print(f"[red]❌ {fix_item.file.name}: 適用関数の実行に失敗: {e}[/red]")
        change_log.record(fix_item, applied=False)
        return False
    if original == modified:
        return False
    if show_diff_flag:
        show_diff(fix_item.file, original, modified)
    if dry_run:
        console.print("[magenta]  [DRY-RUN] 上記の変更を適用予定[/magenta]")
        change_log.record(fix_item, applied=False)
        return False
    backup_manager.backup_file(fix_item.file)
    fix_item.file.write_text(modified, encoding="utf-8")
    change_log.record(fix_item, applied=True)
    console.print(f"[green]✅ 適用: {fix_item.file.name}[/green]")
    return True
