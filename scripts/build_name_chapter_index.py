#!/usr/bin/env python3
"""Build deterministic name -> chapters index over ALL kakuyomu works (ground truth).

Scans every novel paragraph with Aho-Corasick over ledger names (canonical+aliases).
Writes {name: {work: {ch: para_count}}} as JSON. Used by v7 search as the
related-chapter index (the ledger's own cites are too sparse: ~1 per entity).
"""
import sys, json, io
import ahocorasick
from pathlib import Path
from collections import defaultdict

LEDGER = Path(sys.argv[1])
OUT = Path(sys.argv[2])
NOVELS = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_raw/raw/novel/kakuyomu")

d = json.load(io.open(str(LEDGER), encoding="utf-8"))
names = set()
for e in d["entities"]:
    c = e["canonical"]
    if len(c) >= 2:
        names.add(c)
    for a in e.get("aliases", []):
        n = a["name"] if isinstance(a, dict) else a
        if len(n) >= 2:
            names.add(n)
A = ahocorasick.Automaton()
for n in names:
    A.add_word(n, n)
A.make_automaton()
print("names:", len(names))

import re
def norm_ch(stem):
    m = re.match(r"ch0*(\d+)", stem)
    return int(m.group(1)) if m else None

idx = defaultdict(lambda: defaultdict(dict))  # name -> work -> {ch: count}
for wdir in sorted(NOVELS.iterdir()):
    if not wdir.is_dir():
        continue
    wname = wdir.name.split("_", 1)[-1]
    for md in sorted(wdir.glob("*.md")):
        ch = norm_ch(md.stem)
        if not ch:
            continue
        counts = defaultdict(int)
        for line in io.open(md, encoding="utf-8", errors="replace"):
            if len(line) < 2:
                continue
            for _, n in A.iter(line):
                counts[n] += 1
        for n, c in counts.items():
            idx[n][wname][ch] = c
    print("work done:", wname)
OUT.write_text(json.dumps(idx, ensure_ascii=False), encoding="utf-8")
print("written:", OUT, "names with occurrences:", len(idx))
