#!/usr/bin/env python3
"""イベント層からエンティティ（E_*）ページを生成する（LLM 解説付き、キャッシュ式）.

- ../AllusionistLLMWiki2_Work/events/ch*.jsonl の subject/object をエンティティ種別別に集約
- 各エンティティに: canonical_name / aliases / first_appearance / 代表引用 / 関連クレーム
- 解説文は LLM がイベント観測から生成（data/entity_notes.json にキャッシュ、差分のみ生成）
- 出力: wiki/entities/<種別>/E_<prefix>_<名>.md + wiki/entities/index.md + wiki/characters/index.md
- 公開ハブ: エンティティ入口（wiki/entities/index.md）と キャラ入口（wiki/characters/index.md）は別建て、
  どちらもトップページ（wiki/index.md）からリンク

再実行安全: 本文の「自動生成セクション」のみ更新、人間が追記した本文は保持。
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

WORK = ROOT.parent / "AllusionistLLMWiki2_Work"
EVENTS = WORK / "events"
WIKI = ROOT / "wiki"
CACHE = ROOT / "data" / "entity_notes.json"

TYPE_DIR = {
    "character": ("characters", "char"),
    "terminology": ("terminology", "term"),
    "organization": ("organizations", "org"),
    "item": ("items", "item"),
    "key_phrase": ("phrases", "phrase"),
    "visual_motif": ("motifs", "motif"),
    # relationship は subject がキャラの観測種別（エンティティそのものではない）→ 対象外
}
TYPE_JA = {
    "character": "キャラクター", "terminology": "用語", "organization": "組織",
    "item": "アイテム", "key_phrase": "言葉", "visual_motif": "モチーフ",
}
MIN_EVENTS = 2  # 単発言及はエンティティ化しない
JUNK_NAMES = {"null", "none", "undefined", "n/a", "不明", "？", "?"}
# 抽象主語（「アキラへの期待」「アキラの左腕」等）も意図的に抽出する:
# 個別記事は確認用のフックであり、本命はそれらをフックにした上位統合記事。


def split_front(content: str) -> tuple[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    return (m.group(1), m.group(2)) if m else ("", content)


def sanitize(name: str) -> str:
    n = name.strip().strip("『』「」\"'（）() ")
    n = re.sub(r"[/\\:*?<>|.\s]+", "_", n)
    return n[:40]


def collect() -> dict[tuple[str, str], dict]:
    """(type, name) -> 集約データ"""
    agg: dict[tuple[str, str], dict] = defaultdict(lambda: {
        "events": [], "quotes": [], "aliases": set(), "first": "ch9999",
        "claims": set(),
    })
    claims_by_event: dict[str, list[str]] = defaultdict(list)
    for md in (WIKI / "claims").rglob("*.md"):
        if md.name == "index.md":
            continue
        front, _ = split_front(md.read_text(encoding="utf-8"))
        ev = re.search(r"^\s*(?:event|subject): \"?\[\[(E_ch\d{4}[^]]+)\]\]", front, re.M)
        if ev:
            claims_by_event[ev.group(1)].append(md.stem)

    for p in sorted(EVENTS.glob("ch*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            e = json.loads(line)
            t = e.get("entity_type", "")
            t = {"phrase": "key_phrase", "motif": "visual_motif"}.get(t, t)
            if t not in TYPE_DIR:
                continue
            ep = e.get("episode", "")
            for role, name in (("subject", e.get("subject", "")),
                               ("object", e.get("object", ""))):
                name = name.strip()
                if not name or len(name) < 2 or name.lower() in JUNK_NAMES:
                    continue
                d = agg[(t, name)]
                d["events"].append(e)
                if e.get("quote"):
                    d["quotes"].append((ep, e["quote"]))
                if ep and ep < d["first"]:
                    d["first"] = ep
                for c in claims_by_event.get(e.get("event_id", ""), []):
                    d["claims"].add(c)
                # 別名がけ（subject 側のみ: object は対象名そのもの）
                if role == "subject":
                    d["aliases"].add(name)
    return agg


def load_cache() -> dict:
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict) -> None:
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


def gen_notes(pending: list[dict]) -> dict:
    """LLM でエンティティ解説を生成（15件/バッチ）"""
    from llm_client import call_llm, create_client, load_config
    config = load_config()
    client = create_client(config)
    out: dict[str, str] = {}
    for i in range(0, len(pending), 15):
        batch = pending[i:i + 15]
        payload = json.dumps(batch, ensure_ascii=False)
        prompt = (
            "小説『幻想再帰のアリュージョニスト』の登場人物・用語に関する観測記録です。\n"
            "各エンティティの**解説文（2〜3文）**を日本語で書いてください。規則:\n"
            "- 観測記録にない事実（考察の飛躍）を書かない。曖昧な点は「〜とされる」程度に留める\n"
            "- 1件目: 何者か/何であるか。2〜3件目: 作中での役割・特徴\n"
            "- spoiler に配慮し、初出以降の決定的な正体暴露は書かない（観測に明記されたものだけ）\n"
            "出力は JSON: {\"<key>\": \"<解説文>\"} のみ。\n\n" + payload)
        try:
            raw = call_llm(client, config, prompt, json_mode=True, max_tokens=3000)
            raw = re.sub(r"^```json\s*|\s*```$", "", raw.strip())
            out.update({k: str(v).strip() for k, v in json.loads(raw).items() if v})
            print(f"解説生成: +{len(out)}（累計 {len(out)}）", flush=True)
        except Exception as ex:
            print(f"バッチ失敗: {ex}", flush=True)
    return out


AUTO_START = "<!-- AUTO:BEGIN -->"
AUTO_END = "<!-- AUTO:END -->"


def render_body(d: dict, note: str, page_id: str, name: str,
               claims: list[str], claim_titles: dict[str, str]) -> str:
    parts = [f"# {name}", ""]
    if note:
        parts += [note, ""]
    parts.append(AUTO_START)
    aliases = sorted(a for a in d["aliases"] if a != name)[:8]
    if aliases:
        parts += [f"**別名**: {'、'.join(aliases)}", ""]
    evs = d["events"]
    eps = sorted({e.get("episode", "") for e in evs if e.get("episode")})
    parts.append(f"**初出**: {d['first']} ｜ **観測イベント**: {len(evs)} 件"
                 f"（{len(eps)} 話に出現）")
    parts.append("")
    quotes = d["quotes"][:5]
    if quotes:
        parts.append("## 代表引用")
        parts.append("")
        for ep, q in quotes:
            q1 = q.strip().replace("\n", " ")[:120]
            parts.append(f"> {q1}（{ep}）")
        parts.append("")
    if claims:
        parts.append("## 関連クレーム")
        parts.append("")
        for c in sorted(claims)[:12]:
            parts.append(f"- [[{c}|{claim_titles.get(c, c)}]]")
        parts.append("")
    parts.append(AUTO_END)
    return "\n".join(parts)


def main() -> None:
    agg = collect()

    # 種別別に件数フィルタ → ページ化対象
    targets: dict[tuple[str, str], dict] = {}
    for (t, name), d in agg.items():
        if len(d["events"]) < MIN_EVENTS:
            continue
        s = sanitize(name)
        if not s:
            continue
        targets[(t, s)] = d

    # 解説キャッシュ
    cache = load_cache()
    claim_titles = {}
    for md in (WIKI / "claims").rglob("*.md"):
        if md.name == "index.md":
            continue
        front, _ = split_front(md.read_text(encoding="utf-8"))
        ft = re.search(r'^title: "?([^"\n]+)"?$', front, re.M)
        claim_titles[md.stem] = ft.group(1).strip() if ft else md.stem

    pending = []
    for (t, s), d in targets.items():
        key = f"{t}:{s}"
        if key in cache:
            continue
        evs = [{"ep": e.get("episode"), "obs": e.get("observation", "")[:100]}
               for e in d["events"][:8]]
        pending.append({"key": key, "type": TYPE_JA[t], "name": s,
                        "first": d["first"], "events": evs})
    if pending:
        new = gen_notes(pending)
        cache.update(new)
        save_cache(cache)

    # ---- ページ生成 ----
    n_pages = 0
    per_type: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for (t, s), d in sorted(targets.items()):
        sub, prefix = TYPE_DIR[t]
        page_id = f"E_{prefix}_{s}"
        note = cache.get(f"{t}:{s}", "")
        claims = sorted(d["claims"])
        body = render_body(d, note, page_id, s, claims, claim_titles)
        fm = (f"---\nschema_version: \"5.1\"\nid: {page_id}\ntype: entity\n"
              f"subtype: {t}\ncanonical_name: {s}\n"
              f"first_appearance: {d['first']}\nspoiler_after: {d['first']}\n"
              f"document_status: active\nreview_status: llm_verified\n"
              f"created: \"2026-09-30\"\n---\n")
        out_dir = WIKI / "entities" / sub
        out_dir.mkdir(parents=True, exist_ok=True)
        md_path = out_dir / f"{page_id}.md"
        # 人間追記の保持: AUTO セクションを差し替え
        if md_path.exists():
            old = md_path.read_text(encoding="utf-8")
            of, ob = split_front(old)
            m = re.search(re.escape(AUTO_START) + r".*?" + re.escape(AUTO_END),
                          ob, re.DOTALL)
            if m:
                # 新 body の AUTO 部分を旧の AUTO 位置へ差し替え（人間追記は保持）
                new_auto = re.search(re.escape(AUTO_START) + r".*?" + re.escape(AUTO_END),
                                     body, re.DOTALL)
                if new_auto:
                    ob = ob[:m.start()] + new_auto.group(0) + ob[m.end():]
                md_path.write_text(f"---\n{of}\n---\n{ob}", encoding="utf-8")
                n_pages += 1
                per_type[t].append((s, d))
                continue
        md_path.write_text(fm + "\n" + body + "\n", encoding="utf-8")
        n_pages += 1
        per_type[t].append((s, d))

    # ---- エンティティ入口（全種別ハブ）----
    lines = ["---", "title: エンティティ（登場人物・用語・組織）",
             "id: entities/index",
             "description: 作中エンティティの総覧。キャラクター入口は [[characters/index|こちら]]",
             "---", "", "# エンティティ", "",
             "イベント観測から自動集約した作中エンティティの総覧です。"
             "各ページに初出・観測数・代表引用・関連クレームが集まります。", "",
             f"キャラクター入口: [[characters/index|登場人物一覧]]（トップページからも直接）", ""]
    for t in TYPE_DIR:
        items = per_type.get(t, [])
        if not items:
            continue
        lines.append(f"## {TYPE_JA[t]}（{len(items)} 件）")
        lines.append("")
        for s, d in sorted(items, key=lambda x: -len(x[1]["events"])):
            prefix = TYPE_DIR[t][1]
            lines.append(f"- [[E_{prefix}_{s}|{s}]]（{len(d['events'])} 件・初出 {d['first']}）")
        lines.append("")
    (WIKI / "entities" / "index.md").write_text("\n".join(lines), encoding="utf-8")

    # ---- キャラ入口（別建てハブ）----
    chars = per_type.get("character", [])
    lines = ["---", "title: 登場人物一覧", "id: characters/index",
             "description: キャラクター入口。主要キャラから各エンティティページへ",
             "---", "", "# 登場人物", "",
             f"観測イベント数順（{len(chars)} 件）。用語・組織などは [[entities/index|エンティティ総覧]] から。", ""]
    for s, d in sorted(chars, key=lambda x: -len(x[1]["events"])):
        lines.append(f"- [[E_char_{s}|{s}]] — 観測 {len(d['events'])} 件・初出 {d['first']}")
    lines.append("")
    (WIKI / "characters").mkdir(exist_ok=True)
    (WIKI / "characters" / "index.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"エンティティページ: {n_pages} 件（解説キャッシュ {len(cache)}）")
    for t in TYPE_DIR:
        print(f"  {TYPE_JA[t]}: {len(per_type.get(t, []))}")


if __name__ == "__main__":
    main()
