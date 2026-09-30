#!/usr/bin/env python3
"""共通パス解決: config.yaml の paths.repos を解決して各ディレクトリを提供.

vault リポジトリ（AllusionistLLMWiki2）の scripts/ から呼び出す前提。
work は兄弟リポジトリ（AllusionistLLMWiki2_Work）に分離されている（v5.2 最終構成）。
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve(path_str: str) -> Path:
    p = Path(path_str)
    if not p.is_absolute():
        p = ROOT / p
    return p.resolve()


cfg = load_config()
_paths = cfg.get("paths", {})

RAW_DIR = resolve(_paths.get("raw", "raw"))
VAULT_ROOT = resolve(_paths.get("vault", "wiki"))
SCHEMAS_DIR = resolve(_paths.get("schemas", "schemas"))
# work は分離リポジトリ（config: paths.work → ../AllusionistLLMWiki2_Work）
WORK_DIR = resolve(_paths.get("work", "work"))
EVENTS_DIR = WORK_DIR / "events"
FACTS_DIR = WORK_DIR / "facts"
STAGING_DIR = WORK_DIR / "staging"
REPORTS_DIR = WORK_DIR / "reports"
CHANGESETS_DIR = WORK_DIR / "changesets"
MERGED_DIR = WORK_DIR / "_merged"
SEARCH_DIR = WORK_DIR / "search"
