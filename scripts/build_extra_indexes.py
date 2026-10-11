#!/usr/bin/env python3
"""追加索引生成: 「今はまだ」先延ばし索引 + キャラ容姿描写索引.

一次データ: Work/deferral_facts/chNNNN.jsonl（専用再解析 extract_deferral_appearance.py の出力）。
- deferral: quote + refers_to（先延ばしされている具体的対象）+ who + paragraph
- appearance: quote + character + features + note + paragraph
deferral_facts に deferral が無い章は raw 機械スキャンにフォールバック。
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
RAW = ROOT / "raw"
WORK = ROOT.parent / "AllusionistLLMWiki2_Work"
FACTS = WORK / "deferral_facts"      # kind=deferral（専用解析A extract_deferrals.py）
APPEAR_FACTS = WORK / "appearance_facts"  # kind=appearance（専用解析B extract_appearances.py）

sys.path.insert(0, str(ROOT / "scripts"))
from build_public_index import (  # noqa: E402
    episode_heading,
    fm,
    kanji_num,
    load_episode_meta,
)

DEFER_PAT = re.compile(
    r"今はまだ|今のところまだ|現時点ではまだ|まだ存在しな|まだない|まだ無い")
PAGE_MARK = re.compile(r"【p(\d+)】")


def clean_sentence(text: str, start: int, end: int) -> str:
    """マッチを含む一文を抽出（行番号・ページマーカーを除去し 200 字で切る）."""
    ls = max(text.rfind("。", 0, start), text.rfind("\n", 0, start))
    le = text.find("。", end)
    le = le + 1 if le >= 0 else min(end + 120, len(text))
    sent = text[ls + 1:le]
    sent = re.sub(r"【p\d+】", "", sent)
    sent = " ".join(s.strip() for s in sent.splitlines()
                    if s.strip() and not s.strip().isdigit())
    return sent[:200]


def nearest_page(text: str, pos: int) -> str:
    pages = [int(m.group(1)) for m in PAGE_MARK.finditer(text[:pos])]
    return f"p{pages[-1]}" if pages else ""


def load_facts() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for d in (FACTS, APPEAR_FACTS):
        for jl in sorted(d.glob("ch*.jsonl")):
            for line in jl.read_text(encoding="utf-8").splitlines():
                try:
                    out[jl.stem].append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def collect_deferrals(facts: dict) -> dict[str, list[dict]]:
    """章ごとの deferral 記録。専用解析の無い章は raw 機械スキャンで補う（対象未解析）."""
    by_ep: dict[str, list[dict]] = {}
    for p in sorted(RAW.glob("ch*.txt")):
        recs = [r for r in facts.get(p.stem, []) if r["kind"] == "deferral"]
        if recs:
            by_ep[p.stem] = recs
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        recs = []
        for m in DEFER_PAT.finditer(text):
            sent = clean_sentence(text, m.start(), m.end())
            if sent:
                recs.append({"kind": "deferral", "episode": p.stem,
                             "paragraph": nearest_page(text, m.start()),
                             "quote": sent, "refers_to": "", "who": ""})
        if recs:
            by_ep[p.stem] = recs
    return by_ep


def build_deferrals(meta: dict, facts: dict) -> int:
    out_dir = WIKI / "deferrals"
    out_dir.mkdir(exist_ok=True)
    by_ep = collect_deferrals(facts)
    total = sum(len(v) for v in by_ep.values())
    lines = [fm("「今はまだ」先延ばし索引",
               "原文中の「今はまだ」系表現と、それが先延ばししている具体的対象の索引",
               "deferrals/index")]
    lines.append("# 「今はまだ」先延ばし索引\n")
    lines.append(
        f"全 **{total} 箇所**（{len(by_ep)} 話）。本作の反復モティーフである「今はまだ」——"
        "決断・開示・到達を意図的に先延ばし続ける留保の表現です。各項目は原文引用と、"
        "専用解析が特定した**先延ばしされている具体的対象**（何がまだなのか）を載せています。"
        "ch0158 の「『今はまだ』という留保が物語をどこまでも遅延させていく」という自己言及が"
        "このモティーフの核心を示しています。\n")
    cur_chapter = None
    for ch in sorted(by_ep):
        recs = by_ep[ch]
        e = meta.get(ch, {})
        cno = e.get("chapter")
        if cno != cur_chapter:
            cur_chapter = cno
            ct = e.get("chapter_title", "")
            lines.append(f"\n## 第{kanji_num(int(cno))}章　{ct}\n" if cno and ct
                         else "\n## 章未指定\n")
        lines.append(episode_heading(ch, meta) + "\n")
        for r in recs:
            if not (r.get("refers_to") or "").strip():
                continue  # LLM が「先延ばしの示唆なし」と判定した箇所は索引から除外
            who = f" ｜ 発言: {r['who']}" if r.get("who") else ""
            pg = r.get("paragraph", "")
            cite = f"（{pg}）" if pg else ""
            target = r.get("refers_to") or "（対象未解析）"
            lines.append(f"- {target}{who}{cite}")
            if r.get("quote"):
                lines.append(f"  > {r['quote'][:160]}")
        lines.append("")
    (out_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"deferrals: {total} 箇所 / {len(by_ep)} 話")
    return total


def build_appearances(meta: dict, facts: dict) -> int:
    out_dir = WIKI / "appearances"
    out_dir.mkdir(exist_ok=True)
    char_pages = {p.stem for p in (WIKI / "entities" / "characters").glob("E_char_*.md")}
    by_char: dict[str, dict] = {}
    for ch, recs in facts.items():
        for r in recs:
            if r["kind"] != "appearance":
                continue
            name = (r.get("character") or "").strip()
            if not name:
                continue
            d = by_char.setdefault(name, {"items": [], "count": 0, "eps": set()})
            d["count"] += 1
            d["eps"].add(ch)
            if len(d["items"]) < 15:
                d["items"].append(r)
    ordered = sorted(by_char.items(), key=lambda kv: -kv[1]["count"])
    total_desc = sum(d["count"] for d in by_char.values())
    lines = [fm("キャラ容姿描写索引",
               "キャラクターの容姿・外見描写を原文典拠付きでキャラ別に列挙した索引",
               "appearances/index")]
    lines.append("# キャラ容姿描写索引\n")
    lines.append(
        f"全 **{len(ordered)} キャラ・{total_desc} 記述**。専用解析が原文から抽出した"
        "容姿・外見描写（髪・瞳・体格・服装・義肢・声など）を、観測数の多い順に列挙しています。"
        "性格・行動描写は含みません。各項目は原文引用と出現話の典拠付きです。"
        "個別キャラの来歴はキャラページへ。\n")
    for name, d in ordered:
        first = min(d["eps"])
        head = f"## [[{name}|{name}]]" if f"E_char_{name}" in char_pages else f"## {name}"
        lines.append(f"\n{head}\n")
        epn = first[2:].lstrip("0") or "0"
        lines.append(f"初出: [[nav/{first}|{epn}話]] ｜ 容姿記述 {d['count']} 件\n")
        for r in d["items"]:
            feats = "・".join((r.get("features") or [])[:6])
            pg = r.get("paragraph", "")
            cite = f"（{pg}）" if pg else ""
            ep = r["episode"]
            lines.append(f"- {r.get('note', '')} ｜ {feats} ｜ 典拠: "
                         f"[[nav/{ep}|{ep[2:].lstrip('0') or '0'}話]]{cite}")
            if r.get("quote"):
                lines.append(f"  > {r['quote'][:140]}")
        lines.append("")
    (out_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"appearances: {len(ordered)} キャラ / {total_desc} 記述")
    return len(ordered)


def main() -> int:
    meta = load_episode_meta()
    # episodes.json の chapter_title をメタに注入（chapter_heading 用）
    ep_data = json.loads((ROOT / "data" / "episodes.json").read_text(encoding="utf-8"))
    chapters = {int(c["no"]): c["title"] for c in ep_data.get("chapters", [])}
    for ch, e in meta.items():
        cno = e.get("chapter")
        if cno is not None and cno in chapters:
            e["chapter_title"] = chapters[cno]
    facts = load_facts()
    build_deferrals(meta, facts)
    build_appearances(meta, facts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
