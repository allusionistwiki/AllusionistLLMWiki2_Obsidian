# -*- coding: utf-8 -*-
"""Quartz FolderNotes 用：サブフォルダの index.md を生成する。

対象:
  wiki/entities/characters/index.md
  wiki/entities/items/index.md
  wiki/entities/terminology/index.md
  wiki/episodes/index.md
各 index は層内相対 markdown リスト（ファイル名を晒さず frontmatter title を使う）。
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"

def read_title(p: Path) -> str:
    txt = p.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"^title:\s*'?(.*?)'?\s*$", txt[:2000], re.M)
    if m:
        return m.group(1).strip()
    return p.stem

def build(folder: Path, header: str, sort_key=None):
    pages = sorted([p for p in folder.glob("*.md") if p.name != "index.md"], key=sort_key)
    lines = [f"# {header}", "", f"全 **{len(pages)} 件**。", ""]
    for p in pages:
        title = read_title(p)
        lines.append(f"- [{title}](./{p.name})")
    lines.append("")
    (folder / "index.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"{folder.relative_to(ROOT)}/index.md: {len(pages)} 件")

def chapter_key(p: Path) -> str:
    m = re.search(r"ch(\d+)", p.name)
    return m.group(1) if m else p.name

build(WIKI / "entities/characters", "キャラクター索引")
build(WIKI / "entities/items", "アイテム索引")
build(WIKI / "entities/terminology", "用語索引")
build(WIKI / "episodes", "話別サマリー索引", sort_key=chapter_key)
