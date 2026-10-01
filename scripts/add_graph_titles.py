#!/usr/bin/env python3
"""グラフ表示用 title の backfill.

Quartz のグラフノード名は frontmatter title → なければファイル名。
mysteries / entities / arcs に title が無く E_char_..., MY_ch0001_... が
そのまま表示されていた。title を付与して接頭辞を消す。
- mysteries: MY_chNNNN_ を除いた名称
- entities: canonical_name
- arcs: canonical_name
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"


def add_title(path: Path, title: str) -> bool:
    s = path.read_text(encoding="utf-8")
    if re.search(r"^title: ", s[:2000], re.M):
        return False
    m = re.search(r"^---\n", s)
    if not m:
        return False
    s = s[: m.end()] + f'title: "{title}"\n' + s[m.end() :]
    path.write_text(s, encoding="utf-8")
    return True


def main() -> None:
    n = 0
    for p in (WIKI / "mysteries").glob("MY_*.md"):
        t = re.sub(r"^MY_ch\d{4}_", "", p.stem)
        if add_title(p, t):
            n += 1
    for sub in ("characters", "terminology", "organizations", "items", "motifs", "phrases"):
        for p in (WIKI / "entities" / sub).glob("E_*.md"):
            s = p.read_text(encoding="utf-8")
            m = re.search(r"^canonical_name: (.+)$", s, re.M)
            t = m.group(1).strip() if m else p.stem
            if add_title(p, t):
                n += 1
    for p in (WIKI / "arcs").glob("ARC_*.md"):
        s = p.read_text(encoding="utf-8")
        m = re.search(r"^canonical_name: (.+)$", s, re.M)
        t = m.group(1).strip() if m else p.stem
        if add_title(p, t):
            n += 1
    print(f"title backfill: {n} 件")


if __name__ == "__main__":
    main()
