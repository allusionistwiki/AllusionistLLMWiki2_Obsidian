#!/usr/bin/env python3
"""autopilot 生成物の frontmatter 修正 + ME_ 外部参照ページ生成.

1. wiki/claims, wiki/mysteries の frontmatter で YAML が date オブジェクトに
   変換した created:/date: を ISO 文字列にクォート（schema: string 要件）
2. 承認済みクレームの object [[ME_...]] に対して wiki/references/ME_*.md を生成
   （死リンク解消 + 外部参照層の骨格。subtype はキーワード启发式）
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CLAIMS = ROOT / "wiki" / "claims"
MYSTERIES = ROOT / "wiki" / "mysteries"
REFS = ROOT / "wiki" / "references"

SUBTYPE_RULES = [
    (r"家康|戦い|歴史的|徳川|植民地|条約", "history", "World History"),
    (r"なろう|クリシェ|転生ジャンル|ネット|SNS|ミーム", "internet_culture", "Internet Culture"),
    (r"神話|神々|伝承", "mythology", "Mythology"),
    (r"倫理|思想|哲学|ジレンマ", "philosophy", "Ethics & Philosophy"),
    (r"心理|認知|トラウマ", "psychology", "Psychology"),
    (r"ゲーム|ガチャ|アプリ|スマホ|保険|サポート|AR|格闘|地図|商品|業界|サービス", "popular_culture", "Contemporary Consumer Culture"),
]


def classify(me: str) -> tuple[str, str]:
    for pat, sub, dom in SUBTYPE_RULES:
        if re.search(pat, me):
            return sub, dom
    return "popular_culture", "Contemporary Culture"


def sanitize_objects() -> int:
    """クレーム frontmatter の object [[ME_...]] 内の / \\ : をワイド文字へ（ファイル名と一致させる）"""
    n = 0
    for md in CLAIMS.rglob("*.md"):
        content = md.read_text(encoding="utf-8")
        m = re.search(r'^object: "\[\[ME_(.+)\]\]"$', content, re.M)
        if not m:
            continue
        raw = m.group(1)
        safe = raw.replace("/", "／").replace("\\", "＼").replace(":", "：")
        if safe != raw:
            content = content.replace(f'object: "[[ME_{raw}]]"', f'object: "[[ME_{safe}]]"')
            md.write_text(content, encoding="utf-8")
            n += 1
    return n


def fix_dates() -> int:
    n = 0
    for md in list(CLAIMS.rglob("*.md")) + list(MYSTERIES.rglob("*.md")) + list(REFS.rglob("*.md")):
        content = md.read_text(encoding="utf-8")
        fixed = re.sub(r"^created: (\d{4}-\d{2}-\d{2})$", r'created: "\1"', content, flags=re.M)
        fixed = re.sub(r"(date: )(\d{4}-\d{2}-\d{2})", r'\1"\2"', fixed)
        # frontmatter id とファイル名の一致（／サニタイズ対応）
        stem = md.stem
        fixed = re.sub(r"^id: (\S+)$", lambda m: f"id: {stem}" if m.group(1).replace("/", "／").replace("\\", "＼").replace(":", "：") == stem else m.group(0), fixed, flags=re.M)
        if fixed != content:
            md.write_text(fixed, encoding="utf-8")
            n += 1
    return n


def fix_claim_subjects() -> int:
    """クレーム subject が events 層の実 event_id と不一致（LLM言い換え）を近傍解決."""
    import json
    events_dir = ROOT.parent / "AllusionistLLMWiki2_Work" / "events"
    ids_by_ch: dict[str, list[str]] = {}
    for jl in events_dir.glob("*.jsonl"):
        ch = jl.stem
        ids_by_ch[ch] = [json.loads(l).get("event_id", "")
                         for l in jl.read_text(encoding="utf-8").splitlines()]
    n = 0
    for md in CLAIMS.rglob("*.md"):
        content = md.read_text(encoding="utf-8")
        m = re.search(r"^subject: \"\[\[(E_ch(\d{4})_[^\]]+)\]\]\"", content, re.M)
        if not m:
            continue
        ch = f"ch{m.group(2)}"
        want = m.group(1)
        candidates = ids_by_ch.get(ch, [])
        if want in candidates:
            continue
        # 近傍一致: 同一 chapter+page の subject 部分一致
        para = re.search(r"_p(\d+)$", want)
        subj = re.sub(r"^E_ch\d{4}_", "", want)
        subj = re.sub(r"_p\d+$", "", subj)
        best = None
        for cid in candidates:
            if para and cid.endswith(f"_p{para.group(1)}") and subj.split("_")[0] in cid:
                best = cid
                break
        if best:
            content = content.replace(f"[[{want}]]", f"[[{best}]]")
            md.write_text(content, encoding="utf-8")
            n += 1
    return n


def build_me_pages() -> int:
    REFS.mkdir(parents=True, exist_ok=True)
    me_refs: dict[str, list[tuple[str, str]]] = {}
    canon: dict[str, str] = {}  # 小文字キー -> 初出の正式表記（Windows 大文字小文字無視の衝突防止）
    for md in CLAIMS.rglob("*.md"):
        content = md.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not m:
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            continue
        obj = str(fm.get("object", ""))
        mo = re.match(r"\[\[ME_(.+)\]\]", obj)
        if not mo:
            continue
        me = mo.group(1)
        key = me.lower()
        if key not in canon:
            canon[key] = me
        me = canon[key]
        title = content.split("\n# ")[1].split("\n")[0] if "\n# " in content else fm.get("id", "")
        me_refs.setdefault(me, []).append((str(fm.get("id", md.stem)), title))
    today = date.today().isoformat()
    n = 0
    for me, refs in me_refs.items():
        sub, dom = classify(me)
        safe = me.replace("/", "／").replace("\\", "＼").replace(":", "：")
        path = REFS / f"ME_{safe}.md"
        ref_lines = "\n".join(f"- [[{cid}]] — {title[:70]}" for cid, title in refs[:20])
        path.write_text(f"""---
schema_version: "5.1"
id: ME_{safe}
type: external_reference
created: "{today}"
subtype: {sub}
canonical_name: "{me}"
domain: "{dom}"
review_status: llm_verified
---
<!-- LLM-GENERATED -->
<!-- 人間レビュー未実施: 外部参照の記述は仮。人間の追記・修正対象 -->

# {me}

本作（幻想再帰のアリュージョニスト）における外部参照（アナロジー対象）。

## 本作からの参照 ({len(refs)} 件)

{ref_lines}
""", encoding="utf-8")
        n += 1
    return n


def main() -> None:
    n1 = fix_dates()
    n3 = fix_claim_subjects()
    n4 = sanitize_objects()
    # 大文字小文字衝突（ME_turing_test vs ME_Turing_Test）を初出表記へ正規化
    canon = {}
    for md in CLAIMS.rglob("*.md"):
        m = re.search(r'^object: "\[\[ME_(.+)\]\]"$', md.read_text(encoding="utf-8"), re.M)
        if m:
            canon.setdefault(m.group(1).lower(), m.group(1))
    n5 = 0
    for md in CLAIMS.rglob("*.md"):
        content = md.read_text(encoding="utf-8")
        m = re.search(r'^object: "\[\[ME_(.+)\]\]"$', content, re.M)
        if m and canon.get(m.group(1).lower()) and m.group(1) != canon[m.group(1).lower()]:
            content = content.replace(m.group(0), f'object: "[[ME_{canon[m.group(1).lower()]}]]"')
            md.write_text(content, encoding="utf-8")
            n5 += 1
    # 平坦化後の id に合わせて ME_ ページを再生成（古いものを削除）
    for old in REFS.glob("ME_*.md"):
        old.unlink()
    n2 = build_me_pages()
    print(f"frontmatter 修正（日付クォート+id一致）: {n1} ファイル")
    print(f"subject 近傍解決: {n3} ファイル")
    print(f"object サニタイズ: {n4} / 大文字小文字正規化: {n5}")
    print(f"ME_ 参照ページ生成: {n2} 件 -> {REFS}")


if __name__ == "__main__":
    main()
