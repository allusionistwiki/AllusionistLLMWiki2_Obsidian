#!/usr/bin/env python3
"""作品内存在（物品・アプリ・技能・制度・組織・場所・用語）のプロファイル抽出: X is Y 型.

イベント抽出（extract_chapter.py）は「出来事」中心で、サイバーカラテ道場のような
作品内製品/技能/制度の「それは何か」が構造化されない。本スクリプトはそれを専用に拾う:

  サイバーカラテ道場 is_a 格闘アプリ / has_property 動作アシスト / enables 一般人の達人化
  ノーペイン is_a 介錯支援アプリ / functions_as 痛覚・罪悪感の遮断
  転生保険 is_a 保険商品 / defines 一発勝負の転生

出力: Work/facts/chNNNN.jsonl（events とは別フォルダ。集約時に entity ページの骨格になる）

使い方:
  python scripts/extract_facts.py 1        # ch0001
  python scripts/extract_facts.py          # config の chapter_range 分
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_client import (create_client, load_config, strip_code_fence,
                        parse_json_lenient, norm_text, split_text, slug)

ROOT = Path(__file__).resolve().parent.parent

FACT_TYPES = ["is_a", "has_property", "functions_as", "appears_as", "is_made_of",
              "is_located", "requires", "enables", "defines", "binds",
              "named_for", "origin"]

FACTS_SYSTEM_PROMPT = """
あなたは「幻想再帰のアリュージョニスト」の作品内存在プロファイル抽出エージェントです。

【任務】
原文に登場する「作品内の物品・アプリ・ソフトウェア・技能・格闘術・制度・商品・組織・場所・用語・固有名詞」を**全て**列挙し、各存在について「X is Y」型の事実を抽出する。
人物の出来事（誰々が何をした）は対象外。**存在そのものの正体・性質・機能**を書く。

【fact_type（X is Y 型）】
- is_a: X は Y である（カテゴリ定義。例: サイバーカラテ道場 is_a 格闘アプリ）
- has_property: X は 性質Y を持つ（例: 金鎖 has_property 環が減ると死）
- functions_as: X は Y として機能する（例: ノーペイン functions_as 痛覚遮断）
- appears_as: X は Y の姿で現れる
- is_made_of: X は Y でできている
- is_located: X は Y に所在する
- requires: X は Y を必要とする（代価・条件。例: 魔法 requires 名前）
- enables: X は Y を可能にする
- defines: X は Y を定義する（制度がルールを規定）
- binds: X は Y を束縛する（呪い・契約）
- named_for: X の名は Y に由来する/対応する（命名の意匠）
- origin: X の出自/製造者は Y

【出力形式】JSON 配列のみ:
[
  {
    "episode": "ch{NNNN}",
    "subject": "存在スラッグ（記号なし短い名前。例: サイバーカラテ道場）",
    "fact_type": "上記12種から1つ",
    "is_a": "Y側（is_a のときカテゴリ、他は性質・機能の簡潔な語）",
    "entity_type": "item|terminology|organization|character|motif|relationship|phrase",
    "observation": "日本語で1文の記述",
    "quote": "原文からの連続引用（省略連結禁止）",
    "paragraph": "p{N}"
  }
]

【鉄則】
1. 原文にない情報を出さない。quote は原文からの**連続した**引用
2. 作品内創作物語を優先: アプリ名・技能名・商品名・制度名・魔法道具・地名は**漏らさず**
3. 1章あたり 20〜60 件。存在1つにつき複数 fact（is_a + functions_as + has_property ...）を書いてよい
4. event_id/fact_id は作らなくてよい（システムが採番する）
"""


def canonical_fact_id(f: dict, counter: dict) -> dict:
    episode = f.get("episode", "")
    subject = slug(f.get("subject", "unknown"))
    ftype = f.get("fact_type", "is_a")
    if ftype not in FACTS_SYSTEM_PROMPT and ftype not in FACT_TYPES:
        ftype = "is_a"
    obj = slug(f.get("is_a") or f.get("object", "")) or "x"
    para = re.sub(r"[^0-9]", "", str(f.get("paragraph", "0")))
    base = f"F_{episode}_{subject}_{ftype}_{obj}"
    key = f"{base}_p{para}"
    n = counter.get(key, 0)
    counter[key] = n + 1
    f["fact_id"] = key if n == 0 else f"{base}_{n + 1}_p{para}"
    f["paragraph"] = f"p{para}"
    f.setdefault("object", obj)
    return f


def process_facts(chapter_num: int, config: dict, client) -> bool:
    chapter = f"ch{chapter_num:04d}"
    raw_path = ROOT / config["paths"]["raw"] / f"{chapter}.txt"
    if not raw_path.exists():
        print(f"WARN {raw_path} が存在しません")
        return False
    raw_text = raw_path.read_text(encoding="utf-8")

    pipe = config.get("pipeline", {})
    chunks = split_text(raw_text, pipe.get("chunk_max_chars", 24000),
                        pipe.get("chunk_overlap_chars", 400))

    from llm_session import LlmSession
    session = LlmSession(client, config, system_prompt=FACTS_SYSTEM_PROMPT)
    facts, seen = [], set()
    for i, chunk in enumerate(chunks, 1):
        if len(chunks) == 1:
            user = f"以下の原文（{chapter}）から作品内存在の fact を抽出してください：\n\n{chunk}"
        else:
            user = (f"以下は {chapter} の原文の一部（{i}/{len(chunks)}）です。"
                    f"この部分から作品内存在の fact を抽出してください：\n\n{chunk}")
        content = session.chat(user, json_mode=True)
        content = strip_code_fence(content)
        result = parse_json_lenient(content, i)
        part = result.get("facts", result) if isinstance(result, dict) else result
        if not isinstance(part, list):
            part = [part] if isinstance(part, dict) else []
        for f in part:
            key = (slug(f.get("subject", "")), f.get("fact_type"),
                   slug(f.get("is_a", "")), norm_text(f.get("quote", "")))
            if key in seen:
                continue
            seen.add(key)
            facts.append(f)

    facts.sort(key=lambda f: (slug(f.get("subject", "")), f.get("fact_type", "")))
    raw_norm = norm_text(raw_text)
    counter: dict = {}
    out_path = ROOT / config["paths"]["work"] / "facts" / f"{chapter}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_ok = 0
    with open(out_path, "w", encoding="utf-8") as fh:
        for f in facts:
            f = canonical_fact_id(f, counter)
            f["quote_verified"] = bool(f.get("quote")) and norm_text(f["quote"]) in raw_norm
            f["created"] = date.today().isoformat()
            fh.write(json.dumps(f, ensure_ascii=False) + "\n")
            n_ok += 1
    verified = sum(1 for f in facts if f.get("quote_verified"))
    print(f"[{chapter}] fact {n_ok} 件 -> {out_path}（quote照合 {verified}/{n_ok}）")
    return True


def main() -> int:
    config = load_config()
    client = create_client(config)
    chapters = [int(sys.argv[1])] if len(sys.argv) > 1 else list(
        range(config["chapter_range"]["start"], config["chapter_range"]["end"] + 1))
    ok = 0
    for c in chapters:
        try:
            if process_facts(c, config, client):
                ok += 1
        except Exception as e:
            print(f"[ch{c:04d}] ERROR: {e}")
    print(f"完了: {ok}/{len(chapters)} 章")
    return 0


if __name__ == "__main__":
    sys.exit(main())
