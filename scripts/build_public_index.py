#!/usr/bin/env python3
"""公開サイト用の人間向けハブページを生成する（決定論的、LLM 不使用）.

生成物:
  wiki/index.md            — ポータル（概要・統計・章ナビ・節ナビ）
  wiki/chapters/index.md   — 章一覧
  wiki/chapters/chXXXX.md  — 章ハブ（その章のクレーム/伏線/参照の一覧）
  wiki/claims/index.md     — クレーム節の入口説明
  wiki/mysteries/index.md  — 伏線節の入口説明
  wiki/references/index.md — 外部参照節の入口説明

各ハブは [[wikilink]] で結ばれ、Quartz の Explorer/Graph/Backlinks が機能する。
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"

PRED_JA = {
    "analogous_to": "類似", "alludes_to": "暗喩", "parodies": "パロディ",
    "inverts": "逆転", "references": "参照", "critiques": "批評",
    "homage_to": "オマージュ", "subverts": "転倒", "echoes": "反響",
    "defines": "定義", "uses": "使用", "activates": "起動", "other": "関連",
}


def fm(title: str, desc: str, pid: str = "") -> str:
    head = f"---\ntitle: {title}\n"
    if pid:
        head += f"id: {pid}\n"
    return head + f"description: {desc}\n---\n"


def read_claims() -> list[dict]:
    out = []
    for md in sorted((WIKI / "claims").rglob("*.md")):
        if md.name == "index.md":
            continue
        content = md.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
        if not m:
            continue
        front, body = m.group(1), m.group(2)
        ch = re.search(r"ch(\d{4})", md.stem)
        pred = re.search(r"^predicate: (\S+)", front, re.M)
        title = re.search(r"^# (.+)$", body, re.M)
        out.append({
            "name": md.stem,
            "ch": f"ch{ch.group(1)}" if ch else "ch????",
            "predicate": pred.group(1) if pred else "",
            "title": title.group(1).strip() if title else md.stem,
        })
    return out


def read_mysteries() -> list[dict]:
    out = []
    for md in sorted((WIKI / "mysteries").rglob("*.md")):
        if md.name == "index.md":
            continue
        content = md.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
        if not m:
            continue
        front, body = m.group(1), m.group(2)
        intro = re.search(r"^introduced: (ch\d{4})", front, re.M)
        title = re.search(r"^# (.+)$", body, re.M)
        out.append({
            "name": md.stem,
            "ch": intro.group(1) if intro else "ch????",
            "title": title.group(1).strip() if title else md.stem,
        })
    return out


def read_refs() -> list[dict]:
    out = []
    for md in sorted((WIKI / "references").rglob("*.md")):
        if md.name == "index.md":
            continue
        content = md.read_text(encoding="utf-8")
        title = re.search(r"^# (.+)$", content, re.M)
        out.append({"name": md.stem,
                    "title": title.group(1).strip() if title else md.stem})
    return out


def main() -> None:
    claims = read_claims()
    mysteries = read_mysteries()
    refs = read_refs()

    claims_by_ch: dict[str, list[dict]] = defaultdict(list)
    for c in claims:
        claims_by_ch[c["ch"]].append(c)
    myst_by_ch: dict[str, list[dict]] = defaultdict(list)
    for m in mysteries:
        myst_by_ch[m["ch"]].append(m)
    chapters = sorted((set(claims_by_ch) | set(myst_by_ch)) - {"ch????"})
    unassigned = "ch????" in claims_by_ch or "ch????" in myst_by_ch

    # ---- 章ハブ ----
    (WIKI / "chapters").mkdir(exist_ok=True)
    for ch in chapters:
        cs = claims_by_ch.get(ch, [])
        ms = myst_by_ch.get(ch, [])
        lines = [fm(f"{ch} 章ハブ", f"{ch} のアナロジークレーム {len(cs)} 件・伏線 {len(ms)} 件の一覧", f"chapters/{ch}")]
        lines.append(f"# {ch} 章ハブ\n")
        lines.append(f"[← 章一覧](../index.md) ｜ [クレーム節](../claims/index.md) ｜ [伏線節](../mysteries/index.md)\n")
        lines.append(f"## アナロジークレーム（{len(cs)} 件）\n")
        for c in cs:
            pj = PRED_JA.get(c["predicate"], c["predicate"])
            lines.append(f"- [[{c['name']}|{c['title']}]] `[{pj}]`")
        lines.append(f"\n## 伏線（{len(ms)} 件）\n")
        for m in ms:
            lines.append(f"- [[{m['name']}|{m['title']}]]")
        lines.append("")
        (WIKI / "chapters" / f"{ch}.md").write_text("\n".join(lines), encoding="utf-8")

    # ---- 章一覧 ----
    lines = [fm("章ナビゲーション", "章ごとのアナロジークレーム・伏線の一覧", "chapters/index")]
    lines.append("# 章ナビゲーション\n")
    lines.append("| 章 | クレーム | 伏線 |")
    lines.append("|---|---:|---:|")
    for ch in chapters:
        lines.append(f"| [[chapters/{ch}]] | {len(claims_by_ch.get(ch, []))} | {len(myst_by_ch.get(ch, []))} |")
    if unassigned:
        lines.append(f"| （章未指定） | {len(claims_by_ch.get('ch????', []))} | {len(myst_by_ch.get('ch????', []))} |")
    lines.append("")
    (WIKI / "chapters" / "index.md").write_text("\n".join(lines), encoding="utf-8")

    # ---- 節インデックス ----
    (WIKI / "claims" / "index.md").write_text(fm(
        "アナロジークレーム（A_）",
        "本作の引喩・パロディ・逆転（現代文化・神話・ジャンルクリシェへの参照）を典拠付きで体系化したクレーム全集", "claims/index") +
        "# アナロジークレーム（A_）\n\n"
        "この作品は異世界転生ジャンルへの巨大なメタフィクションです。各クレームは「原文の仕掛け → 引喩先」を "
        "原文引用（ページ番号付き）と LLM 審査根拠とともに記録します。\n\n"
        f"全 **{len(claims)} 件**。章別の一覧は [[chapters/index|章ナビゲーション]] から。\n\n"
        "クレーム ID の読み方: `A_ch0001_parodies_アキラ_activates_ノーペイン_p103_安楽死の倫理` = "
        "ch0001 のイベント（ノーペイン起動, p103）が「安楽死の倫理」をパロディにしている、という主張。\n",
        encoding="utf-8")
    (WIKI / "mysteries" / "index.md").write_text(fm(
        "伏線（MY_）",
        "作中に仕掛けられた伏線・未回収要素の追跡記録", "mysteries/index") +
        "# 伏線（MY_）\n\n"
        "導入章（introduced）を起点に、回収状況を追跡する伏線台帳です。"
        "ステータスは `candidate`（候補）→ `active`（生存確認）→ `resolved`（回収）の遷移を想定しています。\n\n"
        f"全 **{len(mysteries)} 件**。章別の一覧は [[chapters/index|章ナビゲーション]] から。\n",
        encoding="utf-8")
    (WIKI / "references" / "index.md").write_text(fm(
        "外部参照（ME_）",
        "クレームが引喩する現代文化・思想・制度・作品の解説ページ", "references/index") +
        "# 外部参照（ME_）\n\n"
        "アナロジークレームの「引喩先」にあたる現代の保険商品、ガチャ課金、AR ゲーム、安楽死の倫理、"
        "テセウスの船、武侠小説……といった外部概念の解説ページです。各ページにそれを引喩として使っている"
        "クレームの一覧（backlinks）が自動で集まります。\n\n"
        f"全 **{len(refs)} 件**。\n",
        encoding="utf-8")

    # ---- ポータル ----
    n_ch = len(chapters)
    lines = [fm("幻想再帰のアリュージョニスト Wiki",
                "本作の多層アナロジー（引喩・神話参照・展開の相似/相違）を典拠付きで体系化する分析Wiki", "index")]
    lines.append("# 幻想再帰のアリュージョニスト Wiki\n")
    lines.append("「ネットミームから現代思想まで引喩が散りばめたオカルトパンク」——"
                 "本作に仕掛けられた**引喩・パロディ・逆転**を、原文引用（ページ番号付き）と審査根拠とともに"
                 "体系化する分析Wikiです。\n")
    lines.append("## 入り口\n")
    lines.append("- [[chapters/index|章ナビゲーション]] — 章ごとのクレーム・伏線一覧（ch0001〜）")
    lines.append("- [[claims/index|アナロジークレーム全集]] — 引喩の主張すべて")
    lines.append("- [[mysteries/index|伏線台帳]] — 仕掛けられた謎の追跡")
    lines.append("- [[references/index|外部参照]] — 引喩先の現代文化・思想の解説\n")
    lines.append("## 統計\n")
    lines.append(f"- 解析済み章: **{n_ch}** 章（ch0001〜ch{chapters[-1][2:]}）")
    lines.append(f"- アナロジークレーム: **{len(claims)}** 件")
    lines.append(f"- 伏線: **{len(mysteries)}** 件")
    lines.append(f"- 外部参照ページ: **{len(refs)}** 件\n")
    lines.append("## 読み方と注意\n")
    lines.append("- 各クレームページは「主張 → 原文引用 → LLM 審査根拠」の順で読めます")
    lines.append("- 本Wikiの大半の記述は **LLM による自動抽出・自動審査（llm_verified）** です。"
                 "人間レビュー済み（human_verified）への昇格が進行中で、frontmatter の `review_status` に区別が記録されています")
    lines.append("- 原文のネタバレを大量に含むため、**原作未読の方は読まないでください**")
    lines.append("- 本Wikiは非公式のファンWikiです。原作の著作権は原作者に帰属します\n")
    (WIKI / "index.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"生成: index.md, chapters/ {n_ch}+1 ページ, 節インデックス 3 ページ")


if __name__ == "__main__":
    main()
