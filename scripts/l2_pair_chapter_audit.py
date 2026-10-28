#!/usr/bin/env python3
"""L2 統合 pair の章レベル共起監査（全話使用状況の機械近似）。

適用中の alias→代表名 pair について、章単位で使用分布を照合する:
  - alias_chapters / canonical_chapters / 共起章
  - cooc_share = 共起章 / alias 章
  - appositive 数: 同一文中の同一性述語パターン（XはY / X、すなわちY /
    YことX / YであるX / 「X」（Y） 等）の件数
高使用・低共起・同一性述語ゼロの pair は過剰統合候補（降格提案）。

使い方: python scripts/l2_pair_chapter_audit.py --out <report.json>
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import ahocorasick

LEDGER = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_work/work/allusionist_v2/L2/runs/20261029T0843_c8bb/entities.json")
RAW = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_raw/raw/novel")
HIGH = {"高", "明言", "表記一致", "蓋然性高"}


def namekey(a):
    return a["name"] if isinstance(a, dict) else a


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    d = json.load(LEDGER.open(encoding="utf-8"))
    ents = d["entities"]
    applied = {}
    for e in ents:
        c = e["canonical"]
        for a in e.get("aliases", []):
            n = namekey(a)
            cf = a.get("confidence") if isinstance(a, dict) else None
            if n != c and cf in HIGH:
                applied.setdefault(n, (c, cf))

    names = set(applied) | {c for c, _ in applied.values()}
    A = ahocorasick.Automaton()
    for n in names:
        if len(n) >= 2:
            A.add_word(n, n)
    A.make_automaton()

    chap_alias = defaultdict(set)
    chap_canon = defaultdict(set)
    app_pos = Counter()  # alias -> appositive hits
    app_pat = re.compile(r"[「『]?([\u4e00-\u9fff・ヶヲ・ーA-Za-z0-9]{2,20})[」』]?\s*(?:は|、\s*すなわち|=|＝|,)\s*([\u4e00-\u9fff・ヶヲ・ーA-Za-z0-9]{2,20})")

    for md in sorted(RAW.rglob("*.md")):
        chap = md.stem.split("__")[0]
        text = md.read_text(encoding="utf-8", errors="replace")
        in_alias, in_canon = set(), set()
        for _, n in A.iter(text):
            if n in applied:
                in_alias.add(n)
            else:
                in_canon.add(n)
        for n in in_alias:
            chap_alias[n].add(chap)
        for c in in_canon:
            chap_canon[c].add(chap)
        for line in text.splitlines():
            for m in app_pat.finditer(line):
                x, y = m.group(1), m.group(2)
                if x in applied and (applied[x][0] == y or y in applied and applied[y][0] == x):
                    app_pos[x] += 1

    rows = []
    for a, (c, cf) in applied.items():
        ac, cc = chap_alias.get(a, set()), chap_canon.get(c, set())
        co = ac & cc
        share = len(co) / len(ac) if ac else 0.0
        rows.append({
            "alias": a, "canonical": c, "conf": cf,
            "alias_chapters": len(ac), "canonical_chapters": len(cc),
            "cooc_chapters": len(co), "cooc_share": round(share, 3),
            "appositive_hits": app_pos.get(a, 0),
        })
    rows.sort(key=lambda r: (r["cooc_share"], -r["alias_chapters"]))
    Path(args.out).write_text(json.dumps({
        "ledger_run": d.get("run"),
        "pairs": len(rows),
        "rows": rows,
        "low_cooc_high_use": [r for r in rows if r["alias_chapters"] >= 100 and r["cooc_share"] < 0.2 and r["appositive_hits"] == 0],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    low = [r for r in rows if r["alias_chapters"] >= 100 and r["cooc_share"] < 0.2 and r["appositive_hits"] == 0]
    print(json.dumps({"pairs": len(rows), "low_cooc_high_use": len(low)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
