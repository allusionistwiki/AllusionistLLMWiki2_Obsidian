#!/usr/bin/env python3
"""キャラ別容姿ページ生成: wiki/appearances/AP_<キャラ名>.md + 索引の作り直し.

- 各キャラの AP_ ページ: 要約（LLM・cache data/appearance_summaries.json）＋ 容姿記述全文（AUTO）
- 索引 appearances/index.md: キャラ名リンク（AP_ ページへ）＋ 5 行程度要約
- E_char_ ページが存在するキャラは相互リンク
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki" / "l1"
from paths import WORK_DIR as WORK
FACTS = WORK / "appearance_facts"  # 専用解析B の出力
CACHE = ROOT / "data" / "appearance_summaries.json"

sys.path.insert(0, str(ROOT / "scripts"))
from build_public_index import fm, load_episode_meta, episode_heading, kanji_num  # noqa: E402


def safe_id(name: str) -> str:
    # キャラ名に / \ : 等を含む場合、ID/ファイル名では安全な文字へ置換（Frozen/Torch と同種問題）。リンク表示は原名を維持
    return (name.replace("/", "_").replace("\\", "_").replace(":", "：")
            .replace("*", "＊").replace("?", "？").replace('"', "”")
            .replace("<", "＜").replace(">", "＞").replace("|", "｜")
            .replace(" ", "_").replace("\n", "_"))


def load_facts() -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for jl in sorted(FACTS.glob("ch*.jsonl")):
        for line in jl.read_text(encoding="utf-8").splitlines():
            try:
                out[jl.stem].append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def collect_chars(facts: dict) -> dict[str, dict]:
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
            d["items"].append(r)
    return by_char


def summaries() -> dict[str, str]:
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def build_pages(by_char: dict, meta: dict) -> int:
    # 個別ページは entities/characters 配下（ID pattern は ARC|O|E|ME|A|MY|RF|SRC のみ許可なので E_char_ 接頭辞）
    out_dir = WIKI / "entities" / "characters"
    out_dir.mkdir(exist_ok=True)
    char_pages = {p.stem for p in out_dir.glob("E_char_*.md")}
    sums = summaries()
    today = date.today().isoformat()
    n = 0
    ordered = sorted(by_char.items(), key=lambda kv: -kv[1]["count"])
    for name, d in ordered:
        sid = safe_id(name)
        pid = f"E_char_{sid}_容姿"
        first = min(d["eps"])
        # entity として lint を通す（schema: subtype/canonical_name 必須）
        head = [f"---\ntitle: {name}（容姿）\nschema_version: '5.1'\nid: {pid}\n"
                f"type: entity\nsubtype: character\ncanonical_name: {name}\n"
                f"first_appearance: {first}\nspoiler_after: {first}\n"
                f"document_status: active\nreview_status: llm_verified\n"
                f"created: '{today}'\nupdated: '{today}'\n"
                f"description: キャラ容姿描写ページ\n---\n"]
        head.append(f"# {name}｜容姿\n")
        s = sums.get(name, "")
        head.append("## 要約\n")
        head.append(s if s else "（要約生成中）")
        head.append("")
        if f"E_char_{sid}" in char_pages:
            head.append(f"キャラ本ページ: [[E_char_{sid}|{name}]]\n")
        head.append("<!-- AUTO:BEGIN -->")
        first = min(d["eps"])
        epn = first[2:].lstrip("0") or "0"
        head.append(f"\n初出: [{epn}話](../../nav/{first}.md) ｜ 容姿記述 {d['count']} 件\n")
        for r in d["items"]:
            feats = "・".join((r.get("features") or [])[:6])
            pg = r.get("paragraph", "")
            cite = f"（{pg}）" if pg else ""
            ep = r["episode"]
            e = meta.get(ep, {})
            head.append(f"- {r.get('note', '')}{' ｜ ' + feats if feats else ''} ｜ 典拠: "
                        f"[{ep[2:].lstrip('0') or '0'}話](../../nav/{ep}.md){cite}")
            if r.get("quote"):
                head.append(f"  > {r['quote'][:200]}")
        head.append("<!-- AUTO:END -->")
        (out_dir / f"{pid}.md").write_text("\n".join(head) + "\n", encoding="utf-8")
        n += 1
    print(f"AP_ ページ生成: {n}")
    return n


def build_index(by_char: dict, meta: dict) -> None:
    out_dir = WIKI / "appearances"
    out_dir.mkdir(exist_ok=True)
    # 旧 AP_ 生成物（旧方式）を掃除
    for p in out_dir.glob("AP_*.md"):
        p.unlink()
    char_pages = {p.stem for p in (WIKI / "entities" / "characters").glob("E_char_*.md")}
    sums = summaries()
    ordered = sorted(by_char.items(), key=lambda kv: -kv[1]["count"])
    total_desc = sum(d["count"] for d in by_char.values())
    lines = [fm("キャラ容姿描写索引",
               "キャラ別の容姿描写ページへの索引（要約付き）",
               "appearances/index")]
    lines.append("# キャラ容姿描写索引\n")
    lines.append(
        f"全 **{len(ordered)} キャラ・{total_desc} 記述**。キャラ名は全体ページ（存在する場合）、"
        "**容姿** は容姿の個別ページ（要約＋原文典拠付きの全記述）へのリンクです。"
        "要約は LLM 生成（llm_verified）。性格・行動描写は含みません。\n")
    for name, d in ordered:
        sid = safe_id(name)
        pid = f"E_char_{sid}_容姿"
        s = sums.get(name, "")
        first = min(d["eps"])
        epn = first[2:].lstrip("0") or "0"
        if f"E_char_{sid}" in char_pages:
            head = f"## [[E_char_{sid}|{name}]] ｜ [[{pid}|容姿]]"
        else:
            head = f"## {name} ｜ [[{pid}|容姿]]"
        lines.append(head)
        lines.append(f"初出: [{epn}話](../nav/{first}.md) ｜ 容姿記述 {d['count']} 件\n")
        if s:
            lines.append(s)
            lines.append("")
    (out_dir / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("索引再生成: appearances/index.md")


def main() -> int:
    meta = load_episode_meta()
    ep_data = json.loads((ROOT / "data" / "episodes.json").read_text(encoding="utf-8"))
    chapters = {int(c["no"]): c["title"] for c in ep_data.get("chapters", [])}
    for ch, e in meta.items():
        cno = e.get("chapter")
        if cno is not None and cno in chapters:
            e["chapter_title"] = chapters[cno]
    facts = load_facts()
    by_char = collect_chars(facts)
    build_pages(by_char, meta)
    build_index(by_char, meta)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
