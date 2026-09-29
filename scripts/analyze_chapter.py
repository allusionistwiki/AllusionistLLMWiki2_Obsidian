#!/usr/bin/env python3
"""章の分析層提案（A_アナロジー / MY_伏線 / theme主題候補）を LLM で大量生成し、
Work/staging/analysis_chNNNN.yaml に review_status: unreviewed で書き出す.

設計上の位置づけ:
- 抽出（extract_chapter.py）は「何が起きたか」の事実層。本スクリプトは「何を指しているか」の分析層。
- LLM 生成はすべて 提案（proposed_by: agent, epistemic_status: hypothesized, review_status: unreviewed）。
  昇格（A_/MY_ としての正規層入り）は人間レビューでのみ行う（鉄則: 人間承認ゲート）。
- quote は原文照合し quote_verified を付与（幻覚検出の機械ゲート）。

使い方:
  python scripts/analyze_chapter.py 1        # ch0001
  python scripts/analyze_chapter.py          # config の chapter_range 分
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_client import (create_client, load_config, strip_code_fence,
                        parse_json_lenient, norm_text, split_text)

ROOT = Path(__file__).resolve().parent.parent

ANALYSIS_SYSTEM_PROMPT = """
あなたは「幻想再帰のアリュージョニスト」の分析エージェントです。
この作品は異世界転生ジャンルに対する巨大なメタフィクションであり、
あなたの任務は、原文に仕掛けられた引喩・伏線・主題を、根拠付きの「提案」として大量に抽出することです。

【タスク1: アナロジー/引喩クレーム（1章あたり最低5件、多いほど良い）】
原文の仕掛け → 何が指されているか を特定する:
- 現代の製品・制度・文化（保険商品、ガチャ、スマホゲーム、AR、アプリ、SNS、客服）
- ジャンルのクリシェ（トラック転生、チート能力、転生オプション、パーティ、迷宮）
- 他作品・神話・宗教・実在歴史・思想
- 倫理的コンセプト（安楽死、道徳的外傷、技術移転規制、植民地支配、自己責任論）
出力:
{"kind":"claim","predicate":"parodies|alludes_to|analogous_to|inverts|sublates|structurally_matches|foreshadows","subject":"[[E_{対応するイベントID}]]","object":"[[ME_{引喩先スラッグ}]]","claim":"日本語一文の主張","quote":"原文からの連続引用","paragraph":"p{N}","confidence":"weak|moderate|strong|explicit"}

【タスク2: 伏線候補（MY_、この章に仕込まれた全候補）】
後の展開で回収されそうな仕込みを全て:
{"kind":"mystery","name":"伏線スラッグ","note":"内容と回収の示唆","quotes":[{"quote":"原文からの連続引用","paragraph":"p{N}"}],"expected_payoff":"どう回収されそうか"}

【タスク3: 主題候補（1章に複数、収束させず多仮説で）】
この章の主題候補を重み付きで複数提示する（相互に矛盾してよい）:
{"kind":"theme","theme":"主題の一文","weight":0.0から1.0,"quotes":[{"quote":"原文からの連続引用","paragraph":"p{N}"}],"note":"根拠"}

【鉄則】
1. 原文にない情報を出さない。quote は原文からの**連続した**引用（「...」での省略・連結禁止。1〜2文まで）
2. 出力は JSON 配列のみ。説明文・コードフェンス不要
3. 数量より根拠: 各提案には必ず quote を付ける
"""


def build_event_digest(events: list[dict]) -> str:
    lines = []
    for e in events:
        sig = ""
        if e.get("signals"):
            sig = " [" + ",".join(s.get("kind", "") for s in e["signals"]) + "]"
        lines.append(f"{e.get('event_id','')} :: {e.get('observation','')[:60]}{sig}")
    return "\n".join(lines)


def analyze_chapter(chapter_num: int, config: dict, client) -> dict | None:
    chapter = f"ch{chapter_num:04d}"
    raw_path = ROOT / config["paths"]["raw"] / f"{chapter}.txt"
    if not raw_path.exists():
        print(f"WARN {raw_path} が存在しません")
        return None
    raw_text = raw_path.read_text(encoding="utf-8")
    events_path = ROOT / config["paths"]["work"] / "events" / f"{chapter}.jsonl"
    events = []
    if events_path.exists():
        events = [json.loads(l) for l in events_path.read_text(encoding="utf-8").splitlines()]

    pipe = config.get("pipeline", {})
    chunks = split_text(raw_text, pipe.get("chunk_max_chars", 24000),
                        pipe.get("chunk_overlap_chars", 400))

    from llm_session import LlmSession
    session = LlmSession(client, config, system_prompt=ANALYSIS_SYSTEM_PROMPT)
    # 原文をチャンクごとに読み込ませる（Strata KV キャッシュ再利用、応答は最小限）
    for i, chunk in enumerate(chunks, 1):
        session.chat(f"以下は {chapter} の原文の一部（{i}/{len(chunks)}）です。"
                     f"受信のみに応答してください。\n\n{chunk}",
                     max_tokens=20, json_mode=False)

    digest = build_event_digest(events)
    ask = (f"以上が {chapter} の原文全文です。抽出済みのイベント一覧（SPO）を添付します:\n\n"
           f"{digest}\n\n"
           f"この {chapter} に対して、タスク1（アナロジー最低5件）・タスク2（伏線候補全部）"
           f"・タスク3（主題候補を複数・重み付き）を JSON 配列で出力してください。")
    content = session.chat(ask, json_mode=True)
    content = strip_code_fence(content)
    result = parse_json_lenient(content, 1)
    items = result.get("items", result) if isinstance(result, dict) else result
    if not isinstance(items, list):
        items = [items] if isinstance(items, dict) else []

    # quote 原文照合（機械ゲート）
    raw_norm = norm_text(raw_text)
    verified = 0
    for it in items:
        qs = it.get("quotes") or ([{"quote": it.get("quote", ""), "paragraph": it.get("paragraph", "")}]
                                  if it.get("quote") else [])
        it["quotes"] = qs
        for q in qs:
            ok = bool(q.get("quote")) and norm_text(q["quote"]) in raw_norm
            q["quote_verified"] = ok
            if ok:
                verified += 1
        it["proposed_by"] = {"kind": "agent", "id": "swift-1.5-iq3_xxs"}
        it["review_status"] = "unreviewed"

    out = {
        "chapter": chapter,
        "created": date.today().isoformat(),
        "status": "proposed",
        "counts": {
            "claims": sum(1 for i in items if i.get("kind") == "claim"),
            "mysteries": sum(1 for i in items if i.get("kind") == "mystery"),
            "themes": sum(1 for i in items if i.get("kind") == "theme"),
            "quotes_verified": verified,
            "quotes_total": sum(len(i.get("quotes", [])) for i in items),
        },
        "items": items,
    }
    out_path = ROOT / config["paths"]["work"] / "staging" / f"analysis_{chapter}.yaml"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(yaml.dump(out, allow_unicode=True, sort_keys=False,
                                  default_flow_style=False), encoding="utf-8")
    print(f"[{chapter}] 提案 {len(items)} 件 -> {out_path}")
    print(f"   claims={out['counts']['claims']} mysteries={out['counts']['mysteries']} "
          f"themes={out['counts']['themes']} quote照合 {verified}/{out['counts']['quotes_total']}")
    return out


def main() -> int:
    config = load_config()
    client = create_client(config)
    chapters = [int(sys.argv[1])] if len(sys.argv) > 1 else list(
        range(config["chapter_range"]["start"], config["chapter_range"]["end"] + 1))
    ok = 0
    for c in chapters:
        try:
            if analyze_chapter(c, config, client):
                ok += 1
        except Exception as e:
            print(f"[ch{c:04d}] ERROR: {e}")
    print(f"完了: {ok}/{len(chapters)} 章")
    return 0


if __name__ == "__main__":
    sys.exit(main())
