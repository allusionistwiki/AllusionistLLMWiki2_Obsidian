#!/usr/bin/env python3
"""L1 エンティティページの重複登録修復（決定論）。

Usage: python scripts/fix_entity_pages_dedup.py [layer_dir ...]  # 既定: wiki/l1
対象: 指定レイヤーの entities/**/*.md（生成後に wiki/l2 へ後処理として実行してよい）
 1) 観測 bullet 行（- **chNNNN**: quote）の完全一致重複を初出のみへ削除。
    同一発話・同一描写の多件登録（ペリュトン 10 件等）の是正。
 2) 「L2 台帳対応」節の下位エンティティ列挙を名義単位で重複排除（順序保持）。
冪等: 再実行で差分ゼロ。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LAYERS = [ROOT / "wiki" / a for a in (sys.argv[1:] or ["l1"])]
OBS_RE = re.compile(r"- \*\*(?:ch\d{4}|unknown)\*\*: ")
CHILD_RE = re.compile(r"(この実体が所有する下位エンティティ: )(.*?)(。)")


def main():
    n_obs = n_child = n_pages = 0
    for wiki in LAYERS:
        pages = sorted((wiki / "entities").rglob("*.md"))
        for p in pages:
            t = p.read_text(encoding="utf-8")
            orig = t
            # 1) 観測 bullet 完全一致重複の削除
            seen = set()
            out = []
            for line in t.splitlines():
                s = line.strip()
                if OBS_RE.match(s):
                    if s in seen:
                        continue
                    seen.add(s)
                out.append(line)
            t = "\n".join(out) + ("\n" if orig.endswith("\n") else "")
            removed = len(orig.splitlines()) - len(t.splitlines())
            if removed:
                n_obs += removed
            # 2) 下位エンティティ列挙の重複排除
            def _dedup(m):
                head, items, tail = m.group(1), m.group(2), m.group(3)
                parts = re.split(r"、", items)
                uniq = list(dict.fromkeys(x.strip() for x in parts if x.strip()))
                if len(uniq) < len(parts):
                    return head + "、".join(uniq) + tail
                return m.group(0)
            t2 = CHILD_RE.sub(_dedup, t)
            if t2 != t:
                n_child += 1
            t = t2
            if t != orig:
                p.write_text(t, encoding="utf-8")
                n_pages += 1
    print(f"pages_changed={n_pages} obs_dup_lines_removed={n_obs} children_dedup_pages={n_child}")
    print("=== FIX ENTITY PAGES DEDUP DONE ===")


if __name__ == "__main__":
    main()
