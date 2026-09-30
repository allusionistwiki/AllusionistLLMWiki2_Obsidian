#!/usr/bin/env python3
"""クレーム表示層: フラット配置に戻し、話別インデックス（claims/index.md）を生成する.

- フォルダ分割はしない（履歴の chXXXX/ は claims/ 直下へ戻す）
- claims/index.md に「第N話: 話タイトル → ・主張リンク」のインデックスを生成
  （リンクラベルはファイル名でなく主張文）
- 各クレームの frontmatter title は主張文の最初の句点まで（最大 64 字）に正規化
  （Quartz の Explorer/検索で実態ファイル名を晒さない）
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAIMS = ROOT / "wiki" / "claims"
NAV = ROOT / "wiki" / "nav"


def short_title(h1: str) -> str:
    t = h1.strip()
    cut = re.split(r"[。！？]", t, maxsplit=1)
    s = cut[0]
    if len(s) > 64:
        s = s[:63].rstrip("、,，") + "…"
    return s


def ep_no(ch: str) -> str:
    return str(int(ch[2:]))


def main() -> None:
    titled = 0
    flattened = 0
    claims_by_ep: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for md in sorted(CLAIMS.rglob("*.md")):
        if md.name == "index.md":
            continue
        content = md.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
        if not m:
            continue
        front, body = m.group(1), m.group(2)

        # 既存 title 行を全て除去して付け直す（旧エスケープバグ行も含む）
        front = re.sub(r"^title: .*$", "", front, flags=re.M)
        h1 = re.search(r"^# (.+)$", body, re.M)
        title = short_title(h1.group(1)) if h1 else md.stem
        title = title.replace('"', "'")
        front = re.sub(r"^(id: .*)$", lambda mm: mm.group(1) + f'\ntitle: "{title}"',
                       front, count=1, flags=re.M)
        front = re.sub(r"\n\n+", "\n", front)
        content = f"---\n{front}\n---\n{body}"
        titled += 1

        ch = re.search(r"ch(\d{4})", md.stem)
        ch = f"ch{ch.group(1)}" if ch else "ch????"
        claims_by_ep[ch].append((md.stem, title))

        # フラット配置へ（chXXXX/ サブフォルダの中身は claims/ 直下へ戻す）
        target = CLAIMS / md.name
        target.write_text(content, encoding="utf-8")
        if md.parent != CLAIMS:
            md.unlink()
            flattened += 1

    for d in [x for x in CLAIMS.iterdir() if x.is_dir()]:
        if not any(d.rglob("*")):
            d.rmdir()

    # ---- 話別インデックス（claims/index.md）----
    eps = sorted(k for k in claims_by_ep if k != "ch????")
    lines = ["---", "title: アナロジークレーム全集（話別）", "id: claims/index",
             "description: 全アナロジークレームの話別インデックス。各話の主張一覧",
             "---", "", "# アナロジークレーム全集（話別）", "",
             f"全 **{sum(len(v) for v in claims_by_ep.values())} 件**。[[nav/index|話ナビゲーション]] / [[mysteries/index|伏線台帳]] / [[references/index|外部参照]]", ""]
    for ch in eps:
        n = ep_no(ch)
        lines.append(f"## 第{n}話")
        lines.append("")
        for name, title in sorted(claims_by_ep[ch]):
            lines.append(f"- [[{name}|{title}]]")
        lines.append("")
    if claims_by_ep.get("ch????"):
        lines.append("## 話未指定")
        lines.append("")
        for name, title in claims_by_ep["ch????"]:
            lines.append(f"- [[{name}|{title}]]")
        lines.append("")
    (CLAIMS / "index.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"title 付与: {titled} 件, フラット化: {flattened} 件, index.md 生成（{len(eps)} 話）")


if __name__ == "__main__":
    main()
