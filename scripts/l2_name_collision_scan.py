#!/usr/bin/env python3
"""Same-name distinct-person detection (カーイン型).

Scans the main novel paragraphs for names occurring multiple times per paragraph
and parallel same-name mentions within a sentence. Emits collision candidate
report (per name: paragraphs with 2+ mentions, chapters) for human/LLM review.
"""
import ahocorasick, json, re, sys, io
from pathlib import Path
from collections import defaultdict

LEDGER = Path(sys.argv[1])
OUT = Path(sys.argv[2])
KAKUYOMU = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_raw/raw/novel/kakuyomu/16816927859268545348_幻想再帰のアリュージョニスト")

d = json.load(io.open(str(LEDGER), encoding="utf-8"))
names = set()
for e in d["entities"]:
    c = e["canonical"]
    if len(c) >= 3:  # 2文字一般語を避け、固有名寄りから
        names.add(c)
    for a in e.get("aliases", []):
        n = a["name"] if isinstance(a, dict) else a
        if len(n) >= 3:
            names.add(n)
A = ahocorasick.Automaton()
for n in names:
    A.add_word(n, n)
A.make_automaton()

para_hits = defaultdict(list)   # name -> [(ch, pno, count)]
para2 = defaultdict(int)
for md in sorted(KAKUYOMU.glob("*.md")):
    ch = int(md.name.split("__")[0].replace("ch", ""))
    for pno, line in enumerate(md.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if len(line) < 8:
            continue
        cnt = defaultdict(int)
        for _, n in A.iter(line):
            cnt[n] += 1
        for n, c in cnt.items():
            if c >= 2:
                para2[n] += 1
                if len(para_hits[n]) < 5:
                    para_hits[n].append((ch, pno, c, line[:80]))

report = []
for n, k in sorted(para2.items(), key=lambda x: -x[1]):
    report.append({"name": n, "paras_multi_mention": k, "samples": para_hits[n]})
OUT.write_text(json.dumps({"names_scanned": len(names), "collision_candidates": len(report),
                           "top": report[:80]}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("names scanned:", len(names))
print("names with >=1 multi-mention paragraph:", len(report))
for r in report[:25]:
    print(" ", r["name"], r["paras_multi_mention"], "|", r["samples"][0][3][:60])
