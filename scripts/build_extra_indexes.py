#!/usr/bin/env python3
"""追加索引生成: 「今はまだ」先延ばし索引 + キャラ容姿描写索引.

- wiki/deferrals/index.md : 原文本文中の「今はまだ」系表現（先延ばしモティーフ）を
  章→話→引用文の順で列挙（他インデックスと同フォーマット）。
- wiki/appearances/index.md : Work/facts の character 記述から容姿・外見描写を
  抽出し、キャラ別に列挙。キャラページがあればリンク。

raw/ と Work/facts は gitignore 対象（非公開）だが、生成物は wiki 側に入る。
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

sys.path.insert(0, str(ROOT / "scripts"))
from build_public_index import (  # noqa: E402
    episode_heading,
    fm,
    kanji_num,
    load_episode_meta,
)

DEFER_PAT = re.compile(
    r"今はまだ|今のところまだ|現時点ではまだ|まだ存在しな|まだない|まだ無い"
)
PAGE_MARK = re.compile(r"【p(\d+)】")

APPEAR_PAT = re.compile(
    r"髪|瞳|目|顔|肌|肌色|身長|体格|体系|姿|風体|外見|容貌|風貌|服|衣装|服装|鎧|兜|盾|"
    r"傷|痣|義手|義腕|義足|義体|翼|角\b|尾\b|爪|小柄|大柄|細身|痩身|巨躯|肥|白髪|黒髪|"
    r"銀髪|金髪|赤毛|茶髪|青い|紅い|蒼い|白い肌|黒い肌|日焼け|眼鏡|巨乳|美少女|美青年|"
    r"美男|美女|醜|老い|若々|幼い|子供のような|声.*?(高い|低い|掠|低)"
)


def clean_sentence(text: str, start: int, end: int) -> str:
    """マッチを含む一文を抽出（行番号・ページマーカーを除去し 200 字で切る）."""
    ls = max(text.rfind("。", 0, start), text.rfind("\n", 0, start))
    le = text.find("。", end)
    le = le + 1 if le >= 0 else min(end + 120, len(text))
    sent = text[ls + 1:le]
    sent = re.sub(r"【p\d+】", "", sent)
    sent = re.sub(r"^\s*\d+\s*$", "", sent, flags=re.M)
    sent = " ".join(s.strip() for s in sent.splitlines() if s.strip())
    return sent[:200]


def nearest_page(text: str, pos: int) -> str:
    pages = [int(m.group(1)) for m in PAGE_MARK.finditer(text[:pos])]
    return f"p{pages[-1]}" if pages else ""


def build_deferrals(meta: dict) -> int:
    out_dir = WIKI / "deferrals"
    out_dir.mkdir(exist_ok=True)
    by_ep: dict[str, list[str]] = defaultdict(list)
    total = 0
    for p in sorted(RAW.glob("ch*.txt")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in DEFER_PAT.finditer(text):
            sent = clean_sentence(text, m.start(), m.end())
            if not sent:
                continue
            pg = nearest_page(text, m.start())
            suffix = f"（{pg}）" if pg else ""
            by_ep[p.stem].append(f"{sent}{suffix}")
            total += 1
    lines = [fm("「今はまだ」先延ばし索引",
               "原文本文中の「今はまだ」系表現（決断の先延ばし・留保のモティーフ）を話別に列挙した索引",
               "deferrals/index")]
    lines.append("# 「今はまだ」先延ばし索引\n")
    lines.append(
        f"全 **{total} 箇所**（{len(by_ep)} 話）。本作の反復モティーフである「今はまだ」——"
        "決断・開示・到達を意図的に先延ばし続ける留保の表現を、原文から章・話別に抽出した索引です。"
        "ch0158 の「『今はまだ』という留保が物語をどこまでも遅延させていく」という自己言及が"
        "このモティーフの核心を示しています。\n")
    cur_chapter = None
    for ch in sorted(by_ep):
        e = meta.get(ch, {})
        cno = e.get("chapter")
        if cno != cur_chapter:
            cur_chapter = cno
            ct = e.get("chapter_title", "")
            lines.append(f"\n## 第{kanji_num(int(cno))}章　{ct}\n" if cno and ct
                         else f"\n## 章未指定\n")
        lines.append(episode_heading(ch, meta) + "\n")
        for s in by_ep[ch]:
            lines.append(f"- {s}")
        lines.append("")
    (out_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"deferrals: {total} 箇所 / {len(by_ep)} 話")
    return total


def build_appearances(meta: dict) -> int:
    out_dir = WIKI / "appearances"
    out_dir.mkdir(exist_ok=True)
    char_pages = {p.stem for p in (WIKI / "entities" / "characters").glob("E_char_*.md")}
    by_char: dict[str, dict] = {}
    for jl in sorted(WORK.glob("facts/ch*.jsonl")):
        for line in jl.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("entity_type") != "character":
                continue
            name = (r.get("subject") or "").strip()
            if not name:
                continue
            desc = " ".join(filter(None, [r.get("is_a"), r.get("observation")]))
            if not APPEAR_PAT.search(desc):
                continue
            d = by_char.setdefault(name, {"eps": [], "items": [], "count": 0})
            d["count"] += 1
            ep = r.get("episode", jl.stem)
            if ep not in d["eps"]:
                d["eps"].append(ep)
            key = desc[:80]
            if len(d["items"]) < 12 and key not in {i[0] for i in d["items"]}:
                q = (r.get("quote") or "")[:120]
                d["items"].append((key, q, ep, r.get("paragraph", "")))
    ordered = sorted(by_char.items(), key=lambda kv: -kv[1]["count"])
    lines = [fm("キャラ容姿描写索引",
               "キャラクターの容姿・外見描写を原文典拠付きでキャラ別に列挙した索引",
               "appearances/index")]
    lines.append("# キャラ容姿描写索引\n")
    lines.append(
        f"全 **{len(ordered)} キャラ**。Work/facts 層から容姿・外見に関する記述"
        "（髪・瞳・体格・服装・義肢・声など）を抽出し、観測数の多い順に列挙しています。"
        "各項目は初出話の典拠付きです。個別キャラの来歴はキャラページへ。\n")
    for name, d in ordered:
        first = min(d["eps"]) if d["eps"] else "ch????"
        head = f"## [[{name}|{name}]]" if f"E_char_{name}" in char_pages else f"## {name}"
        lines.append(f"\n{head}\n")
        lines.append(f"初出: [[nav/{first}|{first[2:].lstrip('0') or '0'}話]] ｜ 容姿記述 {d['count']} 件\n")
        for key, q, ep, para in d["items"]:
            epn = ep[2:].lstrip("0") or "0"
            cite = f"（{para}）" if para else ""
            lines.append(f"- {key} ｜ 典拠: [[nav/{ep}|{epn}話]]{cite}")
            if q:
                lines.append(f"  > {q}")
        lines.append("")
    (out_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"appearances: {len(ordered)} キャラ")
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
    build_deferrals(meta)
    build_appearances(meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
