#!/usr/bin/env python3
"""公開サイト用の人間向けハブページを生成する（決定論的、LLM 不使用）.

用語: 掲載単位は「話」（ep = なろうのエピソード番号、内部 ID は chXXXX）。
「章」は arc 層の別概念なので本スクリプトでは使わない。

生成物:
  wiki/index.md            — ポータル（概要・統計・話ナビ・節ナビ）
  wiki/nav/index.md        — 話一覧（アナロジー/伏線/外部参照の列）
  wiki/nav/chXXXX.md       — 話ハブ（その話のクレーム/伏線/外部参照の一覧）
  wiki/claims/index.md     — クレーム節の入口説明
  wiki/mysteries/index.md  — 伏線節の入口説明
  wiki/references/index.md — 外部参照節の入口説明
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
NAV = WIKI / "nav"

PRED_JA = {
    "analogous_to": "類似", "alludes_to": "暗喩", "parodies": "パロディ",
    "inverts": "逆転", "references": "参照", "critiques": "批評",
    "homage_to": "オマージュ", "subverts": "転倒", "echoes": "反響",
    "foreshadows": "伏線", "structurally_matches": "構造対応",
    "recurs_as": "再帰", "misreads_as": "誤読", "sublates": "止揚",
    "defines": "定義", "uses": "使用", "activates": "起動", "other": "関連",
}


def ep_no(ch: str) -> str:
    """ch0007 -> 7（なろうのエピソード番号）"""
    return str(int(ch[2:]))


def fm(title: str, desc: str, pid: str = "") -> str:
    head = f"---\ntitle: {title}\n"
    if pid:
        head += f"id: {pid}\n"
    return head + f"description: {desc}\n---\n"


def split_front(content: str) -> tuple[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    return (m.group(1), m.group(2)) if m else ("", content)


def read_claims() -> list[dict]:
    out = []
    for md in sorted((WIKI / "claims").rglob("*.md")):
        if md.name == "index.md":
            continue
        front, body = split_front(md.read_text(encoding="utf-8"))
        ch = re.search(r"ch(\d{4})", md.stem)
        pred = re.search(r"^predicate: (\S+)", front, re.M)
        obj = re.search(r"^object: \"?\[\[ME_([^\]]+)\]\]", front, re.M)
        title = re.search(r"^# (.+)$", body, re.M)
        out.append({
            "name": md.stem,
            "ch": f"ch{ch.group(1)}" if ch else "ch????",
            "predicate": pred.group(1) if pred else "",
            "me": obj.group(1) if obj else "",
            "title": title.group(1).strip() if title else md.stem,
        })
    return out


def read_mysteries() -> list[dict]:
    out = []
    for md in sorted((WIKI / "mysteries").rglob("*.md")):
        if md.name == "index.md":
            continue
        front, body = split_front(md.read_text(encoding="utf-8"))
        # timeline: 配下（インデントあり）とトップレベル両対応
        intro = re.search(r"^\s*introduced:\s*(ch\d{4})", front, re.M)
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
        title = re.search(r"^# (.+)$", md.read_text(encoding="utf-8"), re.M)
        out.append({"name": md.stem,
                    "title": title.group(1).strip() if title else md.stem})
    return out


def main() -> None:
    claims = read_claims()
    mysteries = read_mysteries()
    refs = read_refs()

    claims_by_ep: dict[str, list[dict]] = defaultdict(list)
    for c in claims:
        claims_by_ep[c["ch"]].append(c)
    myst_by_ep: dict[str, list[dict]] = defaultdict(list)
    for m in mysteries:
        myst_by_ep[m["ch"]].append(m)
    eps = sorted((set(claims_by_ep) | set(myst_by_ep)) - {"ch????"})
    unassigned = "ch????" in claims_by_ep or "ch????" in myst_by_ep

    # 用語改定前の生成物（chapters/）を掃除
    old = WIKI / "chapters"
    if old.exists():
        for f in old.glob("*.md"):
            f.unlink()
        old.rmdir()

    NAV.mkdir(exist_ok=True)
    for f in NAV.glob("*.md"):
        f.unlink()

    # ---- 話ハブ ----
    for ch in eps:
        cs = claims_by_ep.get(ch, [])
        ms = myst_by_ep.get(ch, [])
        mes = sorted({c["me"] for c in cs if c["me"]})
        n = ep_no(ch)
        lines = [fm(f"第{n}話（{ch}）",
                    f"第{n}話のアナロジー {len(cs)} 件・伏線 {len(ms)} 件・外部参照 {len(mes)} 件",
                    f"nav/{ch}")]
        lines.append(f"# 第{n}話（{ch}）\n")
        lines.append(f"[← 話一覧](../nav/index.md) ｜ [クレーム節](../claims/index.md) ｜ [伏線節](../mysteries/index.md)\n")
        lines.append(f"## アナロジークレーム（{len(cs)} 件）\n")
        for c in cs:
            pj = PRED_JA.get(c["predicate"], c["predicate"])
            lines.append(f"- [[{c['name']}|{c['title']}]] `[{pj}]`")
        lines.append(f"\n## 伏線（{len(ms)} 件）\n")
        for m in ms:
            lines.append(f"- [[{m['name']}|{m['title']}]]")
        if mes:
            lines.append(f"\n## 引喩先・外部参照（{len(mes)} 件）\n")
            for me in mes:
                lines.append(f"- [[ME_{me}]]")
        lines.append("")
        (NAV / f"{ch}.md").write_text("\n".join(lines), encoding="utf-8")

    # ---- 話一覧 ----
    lines = [fm("話ナビゲーション", "話ごとのアナロジー・伏線・外部参照の一覧", "nav/index")]
    lines.append("# 話ナビゲーション\n")
    lines.append("掲載単位は「話」（なろうのエピソード番号）。`chXXXX` は内部 ID です。\n")
    lines.append("| 話 | アナロジー（A_） | 伏線（MY_） | 外部参照（ME_） |")
    lines.append("|---|---:|---:|---:|")
    for ch in eps:
        cs = claims_by_ep.get(ch, [])
        mes = sorted({c["me"] for c in cs if c["me"]})
        lines.append(f"| [[nav/{ch}|第{ep_no(ch)}話]] | {len(cs)} | {len(myst_by_ep.get(ch, []))} | {len(mes)} |")
    if unassigned:
        lines.append(f"| （話未指定） | {len(claims_by_ep.get('ch????', []))} | {len(myst_by_ep.get('ch????', []))} | 0 |")
    lines.append("")
    (NAV / "index.md").write_text("\n".join(lines), encoding="utf-8")

    # ---- 節インデックス ----
    # claims/index.md: 話別インデックス（第N話 → 主張リンク、ラベルは主張文）
    idx = ["---", "title: アナロジークレーム全集（話別）", "id: claims/index",
           "description: 全アナロジークレームの話別インデックス。各話の主張一覧", "---", "",
           "# アナロジークレーム全集（話別）", "",
           f"全 **{len(claims)} 件**。[[nav/index|話ナビゲーション]] / [[mysteries/index|伏線台帳]] / [[references/index|外部参照]]", "",
           "ID の読み方: `A_ch0001_parodies_..._p103_安楽死の倫理` = 第1話のイベント（ノーペイン起動, p103）が「安楽死の倫理」をパロディにしている、という主張。", ""]
    for ch in eps:
        idx.append(f"## 第{ep_no(ch)}話")
        idx.append("")
        for c in claims_by_ep.get(ch, []):
            idx.append(f"- [[{c['name']}|{c['title']}]]")
        idx.append("")
    if claims_by_ep.get("ch????"):
        idx.append("## 話未指定")
        idx.append("")
        for c in claims_by_ep["ch????"]:
            idx.append(f"- [[{c['name']}|{c['title']}]]")
        idx.append("")
    (WIKI / "claims" / "index.md").write_text("\n".join(idx), encoding="utf-8")
    (WIKI / "mysteries" / "index.md").write_text(fm(
        "伏線（MY_）",
        "作中に仕掛けられた伏線・未回収要素の追跡記録", "mysteries/index") +
        "# 伏線（MY_）\n\n"
        "導入話（introduced）を起点に、回収状況を追跡する伏線台帳です。"
        "ステータスは `candidate`（候補）→ `active`（生存確認）→ `resolved`（回収）の遷移を想定しています。\n\n"
        f"全 **{len(mysteries)} 件**。話別の一覧は [[nav/index|話ナビゲーション]] から。\n",
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
    n_ep = len(eps)
    lines = [fm("幻想再帰のアリュージョニスト Wiki",
                "本作の多層アナロジー（引喩・神話参照・展開の相似/相違）を典拠付きで体系化する分析Wiki", "index")]
    lines.append("# 幻想再帰のアリュージョニスト Wiki\n")
    lines.append("「ネットミームから現代思想まで引喩が散りばめたオカルトパンク」——"
                 "本作に仕掛けられた**引喩・パロディ・逆転**を、原文引用（ページ番号付き）と審査根拠とともに"
                 "体系化する分析Wikiです。\n")
    lines.append("## 入り口\n")
    lines.append("- [[nav/index|話ナビゲーション]] — 話ごとのアナロジー・伏線一覧（第1話〜）")
    lines.append("- [[claims/index|アナロジークレーム全集]] — 引喩の主張すべて")
    lines.append("- [[mysteries/index|伏線台帳]] — 仕掛けられた謎の追跡")
    lines.append("- [[references/index|外部参照]] — 引喩先の現代文化・思想の解説\n")
    lines.append("## 統計\n")
    lines.append(f"- 解析済み: **第1話〜第{ep_no(eps[-1])}話**（{n_ep} 話）")
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

    n_myst_assigned = sum(len(v) for k, v in myst_by_ep.items() if k != "ch????")
    n_claims_assigned = sum(len(v) for k, v in claims_by_ep.items() if k != "ch????")
    print(f"生成: index.md, nav/ {n_ep}+1 ページ, 節インデックス 3 ページ")
    print(f"話割当: claims {n_claims_assigned}/{len(claims)}, mysteries {n_myst_assigned}/{len(mysteries)}")


if __name__ == "__main__":
    main()
