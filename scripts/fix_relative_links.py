#!/usr/bin/env python3
"""markdown 相対リンクを厳格解決で検証し、壊れているものを正しい相対パスへ書き換える。

- `](target)` 形式の相対リンクのみ対象（http/#/mailto 等はスキップ、wikilink は対象外）。
- 厳格解決: 起点ディレクトリからの相対パスとして解決し、ファイル実在を確認
  （`x/` 形は x/index.md、拡張子なしは x.md として確認）。
- 壊れている場合、basename（stem）が vault 内で一意ならその実ファイルへの
  正しい相対パス（.md 形）へ書き換える。複数候補は同一最上位セクション優先、
  それでも曖昧なら書き換えず報告する。
- .md 実在リンク（アンカー付き含む）は無変換。

使い方: python scripts/fix_relative_links.py [--dry]
"""
import posixpath
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"
LINK = re.compile(r"\]\(([^()\s]*(?:\([^()]*\)[^()\s]*)*)\)")  # 括弧入りファイル名に対応
# サイト公開構造のセクション接頭辞は vault の層ディレクトリに対応する
SEC_ALIAS = {"L1": "l1", "L2": "l2", "layers": "layers"}


def resolve_file(cand: str, files: set) -> str | None:
    """解決 candidates を受け取り、存在するファイル相対パスを返す。"""
    for cand in (cand,):
        parts = cand.split("/")
        if parts and parts[0] in SEC_ALIAS:
            mapped = "/".join([SEC_ALIAS[parts[0]]] + parts[1:])
            if (mapped + "/index.md") in files:
                return mapped + "/index.md"
            if mapped in files:
                return mapped
    if (cand + "/index.md") in files:
        return cand + "/index.md"
    if cand in files:
        return cand
    return None


def main() -> int:
    dry = "--dry" in sys.argv
    files = set()
    by_stem = defaultdict(list)
    for p in WIKI.rglob("*.md"):
        rp = str(p.relative_to(WIKI)).replace("\\", "/")
        files.add(rp)
        by_stem[p.stem].append(rp)

    changed_files = 0
    changes = Counter()
    ambiguous = Counter()
    for p in sorted(WIKI.rglob("*.md")):
        rp = str(p.relative_to(WIKI)).replace("\\", "/")
        d = posixpath.dirname(rp)
        text = p.read_text(encoding="utf-8", errors="replace")
        out = []
        last = 0
        modified = False
        for m in LINK.finditer(text):
            href = m.group(1)
            if href.startswith(("http", "#", "mailto", "tel:", "irc:", "wiki:")):
                continue
            base, _, anchor = href.partition("#")
            if not base:
                continue
            # 厳格解決（公開セクション接頭辞 L1/L2 は vault の l1/l2 に対応）
            cand = posixpath.normpath(posixpath.join(d, base))
            ok = resolve_file(cand, files)
            if not ok and not base.endswith((".md", "/")):
                ok = resolve_file(cand + ".md", files)
            if ok:
                continue
            stem = posixpath.basename(base.rstrip("/"))
            cands = by_stem.get(stem, [])
            section = rp.split("/")[0]
            pref = [c for c in cands if c.split("/")[0] == section]
            use = pref if len(pref) == 1 else (cands if len(cands) == 1 else [])
            if len(use) == 1:
                new_rel = posixpath.relpath(use[0], d)
                new_href = new_rel + (("#" + anchor) if anchor else "")
                out.append(text[last:m.start() + 2] + new_href + ")")
                last = m.end() + 1
                modified = True
                changes[(rp.split("/")[0], base[:40], "fixed")] += 1
            else:
                changes[(rp.split("/")[0], base[:40], "ambiguous" if cands else "missing")] += 1
                if len(ambiguous) < 15 and (rp, href) not in ambiguous:
                    ambiguous[(rp, href)] = len(cands)
        if modified:
            changed_files += 1
            if last < len(text):
                out.append(text[last:])
            if not dry:
                p.write_text("".join(out), encoding="utf-8")
    print(f"changed_files={changed_files} dry={dry}")
    for (sec, base, kind), c in sorted(changes.items(), key=lambda x: -x[1])[:25]:
        print(f"{c:6d}  {kind}  sec={sec}  eg={base}")
    print("AMBIG/MISSING examples:")
    for (rp, href), n in list(ambiguous.items())[:15]:
        print("   ", rp, "->", href[:60], f"(candidates={n})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
