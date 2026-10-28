#!/usr/bin/env python3
"""portal（サイト最上位 index.md）をコンテンツ実数で再生成する。

vault の wiki/l1・wiki/l2・wiki/layers をスキャンし、セクション別の
ページ数・主要索引への導線・最終更新を反映したサイト入口を生成する。
出力: wiki/index.md（CI が site ルートの content/index.md として採用）。

使い方: python scripts/build_portal_index.py
"""
import re
import sys
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "wiki"
DESC_RE = re.compile(r"^(?:description|概要):[ \t]*(.+)$", re.M)


def fm_get(text: str, key: str) -> str:
    fm = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not fm:
        return ""
    m = re.search(rf"^{key}:\s*(.+)$", fm.group(1), re.M)
    return m.group(1).strip().strip("\"'") if m else ""


def desc_of(md: Path) -> str:
    try:
        t = md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    fm = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    if fm:
        m = DESC_RE.search(fm.group(1))
        if m:
            return m.group(1).strip()[:100]
    for ln in t.split("\n"):
        s = ln.strip()
        if s and not s.startswith(("#", ">", "|", "---", "!", "[")):
            return s[:100]
    return ""


def count_pages(d: Path) -> int:
    return sum(1 for p in d.rglob("*.md") if p.name != "index.md") if d.exists() else 0


def section_stats(name: str) -> dict:
    d = WIKI / name
    out = {}
    if d.exists():
        for sub in sorted(p for p in d.iterdir() if p.is_dir()):
            out[sub.name] = count_pages(sub)
    return out


def main() -> int:
    l1 = section_stats("l1")
    l2 = {k: v for k, v in section_stats("l2").items()}
    total_l1 = sum(l1.values())
    total_l2 = sum(l2.values())

    # 代表索引ページ description を抜粋（chars/episodes 索引）
    leads = {}
    for key, rel in (("chars", "l1/characters/index.md"), ("eps", "l1/episodes/index.md")):
        p = WIKI / rel
        if p.exists():
            for ln in desc_of(p).split("、"):
                s = ln.strip()
                if s[:1].isdigit():
                    leads[key] = s
                    break

    updated = datetime.date.today().isoformat()
    fm = f'---\ntitle: 幻想再帰のアリュージョニスト 解析Wiki\nsummary: "観測記録 3,582章・観測16,114件・主張65,975件の解析 wiki 群の入口"\n---\n'
    rows = []
    if total_l1:
        rows.append(
            f"| [L1 原文 Wiki](./L1/) | 章別観測の原文保持 wiki（登場人物 {l1.get('characters', 0):,}・章 {l1.get('episodes', 0):,}・主張 {l1.get('claims', 0):,} ページ） | [登場人物](./L1/characters/) · [観測章](./L1/episodes/) · [主張](./L1/claims/) · [観測地点](./L1/appearances/) |"
        )
    if total_l2:
        rows.append(
            f"| [L2 正規化 Wiki](./L2/) | L1 へ名前統合・正規化処理を適用した wiki（{total_l2:,} ページ。台帳 {l2.get('reflections', 0):,} 件の監査索引同梱） | [正規化索引 normalized.md](./L2/normalized/) · [登場人物](./L2/characters/) · [観測章](./L2/episodes/) · [主張](./L2/claims/) |"
        )
    body = f"""# 幻想再帰のアリュージョニスト 解析Wiki

長編『幻想再帰のアリュージョニスト』全文（観測記録 3,582 章・観測 16,114 件）の解析 wiki 群。全層は同一構図（層トップ＋各要素）で構成されます。

## 公開中の Wiki 層

| 層 | コンテンツ | 主要導線 |
|---|---|---|
{chr(10).join(rows)}
| [層索引（layers）](./layers/) | L0〜L7 階層モデル・生成鎖の解説 | L0 原文〜 L7 最終 の生成鎖解説 |

## 系統

- 解析パイプライン（観測→主張→台帳→層）: 各層トップの「生成鎖・来歴」
- 作業データ正: [AllusionistWiki_work](https://github.com/allusionistwiki/AllusionistWiki_work)
- 初代 Wiki（人間編集層・別系統）: [AllusionistWiki](https://allusionistwiki.github.io/AllusionistWiki/)

最終更新: {updated}
"""
    (WIKI / "index.md").write_text(fm + body, encoding="utf-8")
    print(f"portal: L1 pages={total_l1} L2 pages={total_l2} -> wiki/index.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
