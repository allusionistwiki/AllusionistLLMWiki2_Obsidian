# -*- coding: utf-8 -*-
"""RF 别名索引 cite unlink: 存在しない章ページへの cite link を plain text 化。
- 対象: wiki/l1|l2/reflections/RF_l2_aliases_index.md の [..](https://…/L1/episodes/chNNNNN)
- 存在判定: wiki/l1/episodes/chNNNNN.md が存在するか (861 章解析範囲のみ 200)。
- 冪等: 非リンク [`ch¶p`] は触らない（再走 0 件）。"""
import re
from pathlib import Path

ROOT = Path("wiki")
LINK = re.compile(r"\[(`ch\d+¶\d+`)\]\(https://allusionistwiki\.github\.io/AllusionistWiki2/(?:L1/|L2/)?episodes/(ch\d+)/?\)")
EP = ROOT / "l1" / "episodes"

existing = {p.stem for p in EP.glob("ch*.md")}
total_unlinked = 0
for layer in ("l1", "l2"):
    p = ROOT / layer / "reflections" / "RF_l2_aliases_index.md"
    if not p.exists():
        continue
    txt = p.read_text(encoding="utf-8", errors="ignore")
    n = 0
    def rep(m):
        global n
        ch = m.group(2)
        if ch in existing:
            return m.group(0)
        n += 1
        return m.group(1)  # plain code text
    new = LINK.sub(rep, txt)
    if new != txt:
        p.write_text(new, encoding="utf-8")
    total_unlinked += n
    print(layer, "unlinked:", n, "| kept 200-target links:", len(LINK.findall(txt)) - n)
print("total unlinked:", total_unlinked, "| existing episodes:", len(existing))
