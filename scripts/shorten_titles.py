#!/usr/bin/env python3
"""表示層の日本語化・要約化（LLM 一括生成、決定論的キャッシュ付き）.

1. ME_（外部参照）: canonical_name が英語のページに日本語表示名 title: を付与
   （例: abandonment → 「見捨てられた者の放置（養育放棄）」）
2. A_（クレーム）: frontmatter title を 25 字程度の短いラベルに置換
   （一覧・Explorer 用。全文主張文は個別ページの H1 に残す）

生成物は data/display_titles.json にキャッシュし、再実行時はスキップ。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from llm_client import create_client, load_config, call_llm  # noqa: E402

WIKI = ROOT / "wiki"
CACHE = ROOT / "data" / "display_titles.json"

PRED_JA = {
    "analogous_to": "類似", "alludes_to": "暗喩", "parodies": "パロディ",
    "inverts": "逆転", "references": "参照", "critiques": "批評",
    "homage_to": "オマージュ", "subverts": "転倒", "echoes": "反響",
    "foreshadows": "伏線", "structurally_matches": "構造対応",
    "recurs_as": "再帰", "misreads_as": "誤読", "sublates": "止揚",
    "defines": "定義", "uses": "使用", "activates": "起動", "other": "関連",
}


def split_front(content: str) -> tuple[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    return (m.group(1), m.group(2)) if m else ("", content)


def load_cache() -> dict:
    if CACHE.exists():
        return json.loads(CACHE.read_text(encoding="utf-8"))
    return {"claims": {}, "me": {}}


def save_cache(cache: dict) -> None:
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


def llm_json(client, config, prompt: str) -> dict:
    raw = call_llm(client, config, prompt, json_mode=True, max_tokens=3000)
    raw = re.sub(r"^```json\s*|\s*```$", "", raw.strip())
    return json.loads(raw)


def batched(xs: list, n: int):
    for i in range(0, len(xs), n):
        yield xs[i:i + n]


def main() -> None:
    config = load_config()
    client = create_client(config)
    cache = load_cache()

    # ---- 1. ME_ 日本語表示名 ----
    me_items = []
    for md in sorted((WIKI / "references").rglob("*.md")):
        if md.name == "index.md":
            continue
        front, body = split_front(md.read_text(encoding="utf-8"))
        name = md.stem
        h1 = re.search(r"^# (.+)$", body, re.M)
        h1t = h1.group(1).strip() if h1 else name
        sample = re.search(r"— (.+)$", body, re.M)
        if name in cache["me"]:
            continue
        me_items.append({"id": name, "name": h1t,
                         "context": (sample.group(1)[:120] if sample else "")})

    for batch in batched(me_items, 15):
        payload = json.dumps(batch, ensure_ascii=False)
        prompt = (
            "以下は小説『幻想再帰のアリュージョニスト』の分析Wikiにある外部参照概念の一覧です。\n"
            "各概念の**日本語表示名**を作ってください。規則:\n"
            "- 定着した日本語表記があるものはそれを使う（例: fiat_currency → 紙幣・法定通貨、"
            "frankenstein → フランケンシュタイン、3d_printing → 3Dプリント）\n"
            "- 英語のみの用語は日本語訳＋必要ならカタカナ併記（例: abandonment → 養育放棄・見捨てられ）\n"
            "- 12字以内めざす。説明的な語は避ける\n"
            "- 文脈は「その概念が本作でどう引喩されているか」の抜粋\n"
            "出力は JSON: {\"<id>\": \"<日本語表示名>\"} のみ。\n\n" + payload)
        try:
            out = llm_json(client, config, prompt)
            for k, v in out.items():
                v = str(v).strip().strip('"""')
                if k and v:
                    cache["me"][k] = v[:40]
            save_cache(cache)
            print(f"ME 日本語名: +{len(out)}（累計 {len(cache['me'])}）", flush=True)
        except Exception as e:
            print(f"ME バッチ失敗: {e}", flush=True)

    # ---- 2. A_ 短いラベル ----
    claim_items = []
    for md in sorted((WIKI / "claims").rglob("*.md")):
        if md.name == "index.md":
            continue
        front, body = split_front(md.read_text(encoding="utf-8"))
        name = md.stem
        if name in cache["claims"]:
            continue
        pred = re.search(r"^predicate: (\S+)", front, re.M)
        obj = re.search(r"^object: \"?\[\[ME_([^\]]+)\]\]", front, re.M)
        h1 = re.search(r"^# (.+)$", body, re.M)
        claim_items.append({
            "id": name,
            "pred": PRED_JA.get(pred.group(1), "関連") if pred else "関連",
            "me": cache["me"].get("ME_" + obj.group(1), obj.group(1)) if obj else "",
            "claim": (h1.group(1).strip() if h1 else name)[:150],
        })

    for batch in batched(claim_items, 15):
        payload = json.dumps(batch, ensure_ascii=False)
        prompt = (
            "以下は小説分析Wikiのアナロジークレーム（本作の仕掛け→引喩先）の一覧です。\n"
            "各クレームの**一覧表示用タイトル**を作ってください。規則:\n"
            "- 「引喩先＋仕掛けの核心」を 18 字以内で名詞的に（例: 「無課金ガチャへの転生」「家康の脱糞で死の恐怖を正当化」）\n"
            "- 説明文を要約した名詞句。体言止め。動詞で始めない\n"
            "- me は日本語化済みの引喩先名、pred は関係の種類\n"
            "出力は JSON: {\"<id>\": \"<タイトル>\"} のみ。\n\n" + payload)
        try:
            out = llm_json(client, config, prompt)
            for k, v in out.items():
                v = str(v).strip().strip('"""')
                if k and v:
                    cache["claims"][k] = v[:30]
            save_cache(cache)
            print(f"クレーム短題: +{len(out)}（累計 {len(cache['claims'])}）", flush=True)
        except Exception as e:
            print(f"クレーム バッチ失敗: {e}", flush=True)

    # ---- 3. frontmatter への書き込み ----
    n_me = n_cl = 0
    for md in sorted((WIKI / "references").rglob("*.md")):
        if md.name == "index.md":
            continue
        t = cache["me"].get(md.stem)
        if not t:
            continue
        content = md.read_text(encoding="utf-8")
        front, body = split_front(content)
        front = re.sub(r"^title: .*$", "", front, flags=re.M)
        front = re.sub(r"^(id: .*)$", lambda mm: mm.group(1) + f"\ntitle: {t}",
                       front, count=1, flags=re.M)
        md.write_text(f"---\n{front}\n---\n{body}", encoding="utf-8")
        n_me += 1
    for md in sorted((WIKI / "claims").rglob("*.md")):
        if md.name == "index.md":
            continue
        t = cache["claims"].get(md.stem)
        if not t:
            continue
        content = md.read_text(encoding="utf-8")
        front, body = split_front(content)
        front = re.sub(r"^title: .*$", "", front, flags=re.M)
        front = re.sub(r"^(id: .*)$", lambda mm: mm.group(1) + f"\ntitle: {t}",
                       front, count=1, flags=re.M)
        md.write_text(f"---\n{front}\n---\n{body}", encoding="utf-8")
        n_cl += 1

    print(f"frontmatter 書込: ME {n_me} 件, クレーム {n_cl} 件")


if __name__ == "__main__":
    main()
