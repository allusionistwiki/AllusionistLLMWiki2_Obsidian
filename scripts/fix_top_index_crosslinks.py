# -*- coding: utf-8 -*-
"""深さ1索引 (layer top) の ../../<section>/ 越境リンクを ../../../<section>/ へ（flat 出力形に一致）。
- /L1/index.html から ../../nav/ = root bare (404)、../../../nav/ = /L1/nav/ (200)。
- 冪等: ../../../ 形は再対象化しない（ネガティブ先読み）。
- 対象: wiki/l1/index.md, wiki/l2/index.md のみ（depth 1 索引）。"""
import re
from pathlib import Path

SECS = r"(?:nav|characters|relationships|entities|claims|mysteries|episodes|arcs|references|deferrals|appearances|reflections|normalized|cycleb)"
pat = re.compile(r"\]\((?!\.\./)(" + SECS + r"/index\.md)\)")
for layer in ("l1", "l2"):
    p = Path(f"wiki/{layer}/index.md")
    txt = p.read_text(encoding="utf-8", errors="ignore")
    new, n = pat.subn(r"](../../../\g<1>", txt)
    if n:
        p.write_text(new, encoding="utf-8")
    chk = p.read_text(encoding="utf-8", errors="ignore")
    print(layer, "rewritten:", n, "| remaining:", len(pat.findall(chk)))
