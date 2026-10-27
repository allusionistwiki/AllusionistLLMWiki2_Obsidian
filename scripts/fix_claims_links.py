#!/usr/bin/env python3
"""claims の dead link 修正（L1 側再生成）。

v5.3 design: claims の subject は SPO グラフノード（event_id）参照であり、
graph ノードは frontmatter の graph: フィールド側に属する（イベント層の生成物）。
ページツリーに events ページは存在しないため、subject の wikilink は
LNK003 死リンクになる。→ frontmatter subject はプレーンテキスト（`code`）へ
変換し、表示は維持して死リンクを解消する（parent 参照と同じ方針）。
"""
import re
import sys
from pathlib import Path

VAULT = Path(r"C:/Users/d5dx/Downloads/Code/AllusionistLLMWiki2")
CLAIMS = VAULT / "wiki" / "claims"


def main():
    n = 0
    for p in CLAIMS.glob("*.md"):
        t = p.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
        if not m:
            continue
        fm = m.group(1)
        fm2 = fm
        # subject / object 値の wikilink → プレーン `id`
        def sub_kv(mm):
            key, val = mm.group(1), mm.group(2)
            inner = re.findall(r"\[\[([^\]|#]+?)(?:\|[^\]]+?)?\]\]", val)
            if not inner:
                return mm.group(0)
            code = " ".join(f"`{i}`" for i in inner)
            return f"{key}: {code}"
        fm2 = re.sub(r"^(subject|object):\s*(.+)$", sub_kv, fm2, flags=re.M)
        if fm2 != fm:
            p.write_text("---\n" + fm2 + t[m.end():], encoding="utf-8")
            n += 1
    print(f"claims fixed: {n}")
    print("=== FIX CLAIMS LINKS DONE ===")


if __name__ == "__main__":
    main()
