#!/usr/bin/env python3
"""存在しないページを指す markdown リンクを plain text 化（ unlink ）する。

fix_relative_links.py で修復不能（解決候補ゼロ）な `](target)` を検出し、
リンク記法 `[text](target)` をテキスト `text（未ページ）` に変換する。
対象: 相対リンクで、厳格解決・stem 解決のいずれでも実ファイルに到達しないもの。
--dry 付きで一覧のみ出力。

使い方: python scripts/unlink_missing.py [--dry]
"""
import posixpath
import re
import sys
from pathlib import Path

WIKI = Path(__file__).resolve().parents[1] / "wiki"
LINK = re.compile(r"\[([^\[\]]*)\]\(([^()\s]*(?:\([^()]*\)[^()\s]*)*)\)")
SEC_ALIAS = {"L1": "l1", "L2": "l2", "layers": "layers"}


def resolve(cand, files, stems):
    parts = cand.split("/")
    if parts and parts[0] in SEC_ALIAS:
        cand = "/".join([SEC_ALIAS[parts[0]]] + parts[1:])
    if cand in files or (cand + "/index.md") in files or (cand + ".md") in files:
        return True
    stem = posixpath.basename(cand.rstrip("/"))
    if stem in stems:
        return True
    return False


def main() -> int:
    dry = "--dry" in sys.argv
    files = set()
    stems = set()
    for p in WIKI.rglob("*"):
        if p.is_file():
            files.add(str(p.relative_to(WIKI)).replace("\\", "/"))
            stems.add(p.stem)
    n_links = 0
    n_files = 0
    samples = []
    for p in sorted(WIKI.rglob("*.md")):
        rp = str(p.relative_to(WIKI)).replace("\\", "/")
        d = posixpath.dirname(rp)
        text = p.read_text(encoding="utf-8", errors="replace")
        out, last = [], 0

        def sub(m):
            nonlocal n_links
            disp, href = m.group(1), m.group(2)
            if href.startswith(("http", "#", "mailto", "tel:")):
                return m.group(0)
            base = href.split("#")[0]
            if not base:
                return m.group(0)
            cand = posixpath.normpath(posixpath.join(d, base))
            if resolve(cand, files, stems):
                return m.group(0)
            n_links += 1
            if len(samples) < 20:
                samples.append((rp, disp[:30], base[:50]))
            return f"{disp}（未ページ）" if disp else "（未ページ）"

        new = LINK.sub(sub, text)
        if new != text:
            n_files += 1
            if not dry:
                p.write_text(new, encoding="utf-8")
    print(f"unlinked={n_links} files={n_files} dry={dry}")
    for s in samples:
        print("  ", s[0], "->", s[1], "|", s[2])
    return 0


if __name__ == "__main__":
    sys.exit(main())
