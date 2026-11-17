# -*- coding: utf-8 -*-
"""死 page cite の plain 化（冪等）。
section 索引・nav 等が絶対 URL で cite するエンティティ/クレーム/ミステリー/参照
ページのうち、vault 側に実ファイルが無いものを plain code text へ。
- 対象: wiki/l1/**/*.md, wiki/l2/**/*.md 内の
  [text](https://allusionistwiki.github.io/AllusionistWiki2/<Lx>/<slug>) 形リンク
- 実在判定: wiki/<lx>/<slug>.md の存在（URL デコード後）
- 置換: リンク -> `slug`（コードテキスト）。来歴情報（text）は保持するため
  text が slug と異なる場合は text をそのままプレーンテキスト化。
"""
import re
from pathlib import Path
from urllib.parse import unquote

SITE = r"https://allusionistwiki.github.io/AllusionistWiki2/"
LINK = re.compile(r"\[([^\]]*)\]\(" + SITE + r"(L1|L2)/([^)\s]+)\)")

root = Path(".")
total = 0
for layer_dir in ("wiki/l1", "wiki/l2"):
    for p in Path(layer_dir).rglob("*.md"):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        def repl(m):
            text, lx, slug = m.group(1), m.group(2), m.group(3)
            slug = unquote(slug).rstrip("/")
            base = Path("wiki") / lx.lower()
            target = base / (slug + ".md")
            if target.exists() or (base / slug / "index.md").exists():
                return m.group(0)
            plain = text if text and text != slug else slug
            return plain + "（未公開）"
        new, n = LINK.subn(repl, txt)
        if n:
            # 実在リンクはそのままなので n は置換数ではない -> 差分有無で判定
            if new != txt:
                p.write_text(new, encoding="utf-8")
                total += 1
print("files changed:", total)
# 冪等性: 残存死リンク数
dead = 0
for layer_dir in ("wiki/l1", "wiki/l2"):
    for p in Path(layer_dir).rglob("*.md"):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        for m in LINK.finditer(txt):
            slug = unquote(m.group(3)).rstrip("/")
            base = Path("wiki") / m.group(2).lower()
            if not ((base / (slug + ".md")).exists() or (base / slug / "index.md").exists()):
                dead += 1
print("remaining dead site-url cites:", dead)
