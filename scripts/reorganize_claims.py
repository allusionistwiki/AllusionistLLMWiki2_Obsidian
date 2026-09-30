#!/usr/bin/env python3
"""クレーム表示層の改善:
1. wiki/claims/chXXXX/ へ話別フォルダに再配置（Explorer が話単位で畳める）
2. 各クレームに短い title: を付与（Quartz の Explorer/検索は frontmatter title を表示。
   実態ファイル名 A_ch0001_parodies_..._p103_安楽死の倫理 のまま晒さない）
   title = 主張文（H1）の最初の句点まで（最大 64 字）
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAIMS = ROOT / "wiki" / "claims"


def short_title(h1: str) -> str:
    t = h1.strip()
    # 最初の句点で切る（文全体が短い場合はそのまま）
    cut = re.split(r"[。！？]", t, maxsplit=1)
    s = cut[0]
    if len(s) > 64:
        s = s[:63].rstrip("、,，") + "…"
    return s


def main() -> None:
    moved = 0
    titled = 0
    for md in sorted(CLAIMS.rglob("*.md")):
        if md.name == "index.md":
            continue
        content = md.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
        if not m:
            continue
        front, body = m.group(1), m.group(2)
        ch = re.search(r"ch(\d{4})", md.stem)
        if not ch:
            continue
        ep_dir = CLAIMS / f"ch{ch.group(1)}"
        ep_dir.mkdir(exist_ok=True)

        # title 付与（frontmatter の id の直後に入れる）
        front = re.sub(r'^title: \\".*?\\"\s*$', "", front, flags=re.M)  # 旧エスケープバグ行の除去
        if not re.search(r"^title:", front, re.M):
            h1 = re.search(r"^# (.+)$", body, re.M)
            title = short_title(h1.group(1)) if h1 else md.stem
            title = title.replace('"', "'")
            front = re.sub(r"^(id: .*)$", lambda mm: mm.group(1) + f'\ntitle: "{title}"',
                           front, count=1, flags=re.M)
            content = f"---\n{front}\n---\n{body}"
            titled += 1
        else:
            content = f"---\n{front}\n---\n{body}"

        target = ep_dir / md.name
        target.write_text(content, encoding="utf-8")
        if md.parent != ep_dir:
            md.unlink()
            moved += 1

    print(f"話別フォルダへ移動: {moved} 件, title 付与: {titled} 件")


if __name__ == "__main__":
    main()
