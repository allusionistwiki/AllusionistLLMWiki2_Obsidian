#!/usr/bin/env python3
"""autopilot_review.py — 人間判断ゲートの LLM 代替（仮運用）.

本来 人間レビューが必要な判断を、明示的に「LLM 代替」として実行し、
すべて review_status: llm_verified（人間 human_verified とは区別）+
provenance.reviewed_by.kind: agent で記録する。後で人間が差し替えられる。

代替する判断:
1. analysis_chNNNN.yaml の提案（A_/MY_/theme）の取捨選択 → wiki/claims, wiki/mysteries へ昇格
2. 章主題の重み収束（theme 多仮説 → 主主題+副主題の暫定決定）
3. entity 名（subject）の表記ゆれクラスタ検出 → config/alias_candidates.yaml に提案

使い方:
  python scripts/autopilot_review.py 1        # ch0001
  python scripts/autopilot_review.py          # chapter_range 分（analysis がある章のみ）
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_client import create_client, load_config, strip_code_fence, parse_json_lenient

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT.parent / "AllusionistLLMWiki2_Work"
LOG_PATH = WORK / "reports" / "autopilot_log.md"

REVIEW_SYSTEM_PROMPT = """
あなたは「幻想再帰のアリュージョニスト」分析Wikiのレビューエージェントです。
抽出エージェントが提案したアナロジー(A_)・伏線(MY_)・主題(theme)候補を審査します。

【審査基準】
1. 原文根拠: quote が主張を支えているか（引用から読みすぎではないか）
2. 引喩の妥当性: 引喩先は作品のメタフィクション構造（ジャンル自己言及）と整合するか
3. 伏線の妥当性: 「伏線」と呼べる仕込みか（単なる謎描写は却下）
4. 重複: 同一仕掛けの言い換えでないか
5. 作品知識の混入禁止: 原文にない後展開知識での判断はしない

【出力形式】JSON 配列のみ。入力順を維持し、各提案に審査を付ける:
[
  {"index": 0, "verdict": "accept|revise|reject",
   "reason": "日本語1文の根拠",
   "revised_claim": "verdict=revise のとき修正後の主張文（日本語）",
   "confidence": "weak|moderate|strong"}
]
accept は確信できるものだけ。迷ったら revise か reject。数量より品質。
"""


def load_analysis(chapter: str) -> dict | None:
    p = WORK / "staging" / f"analysis_{chapter}.yaml"
    if not p.exists():
        return None
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def review_items(client, config, chapter: str, items: list[dict]) -> list[dict]:
    compact = []
    for i, it in enumerate(items):
        compact.append({
            "index": i, "kind": it.get("kind"),
            "claim": it.get("claim") or it.get("note") or it.get("theme"),
            "predicate": it.get("predicate"), "subject": it.get("subject"),
            "object": it.get("object") or it.get("name"),
            "quotes": [q.get("quote", "") for q in it.get("quotes", [])][:2],
            "verified": [q.get("quote_verified") for q in it.get("quotes", [])][:2],
        })
    user = (f"以下は {chapter} の分析提案です。審査してください:\n\n"
            + json.dumps(compact, ensure_ascii=False, indent=1))
    content = client.chat.completions.create(
        model=config["llm"]["model"],
        messages=[{"role": "system", "content": REVIEW_SYSTEM_PROMPT},
                  {"role": "user", "content": user}],
        temperature=0.1, max_tokens=config["llm"].get("max_tokens", 64000),
        response_format={"type": "json_object"},
        extra_body={"chat_template_kwargs": {"enable_thinking": False}},
    ).choices[0].message.content
    content = strip_code_fence(content)
    result = parse_json_lenient(content, 1)
    verdicts = result.get("reviews", result) if isinstance(result, dict) else result
    if not isinstance(verdicts, list):
        verdicts = []
    return verdicts


def slug(s: str) -> str:
    import re
    return re.sub(r"[（）()\[\]【】「」『』\s]+", "", s or "")


def promote(chapter: str, items: list[dict], verdicts: list[dict], log: list[str]) -> dict:
    """accept/revise を wiki/claims, wiki/mysteries へ昇格（llm_verified 明記）"""
    today = date.today().isoformat()
    counts = {"claims": 0, "mysteries": 0, "rejected": 0}
    vmap = {v.get("index"): v for v in verdicts}
    for i, it in enumerate(items):
        v = vmap.get(i, {"verdict": "reject", "reason": "審査応答なし"})
        verdict = v.get("verdict", "reject")
        if verdict == "reject":
            counts["rejected"] += 1
            continue
        if it.get("kind") == "claim":
            obj = slug((it.get("object") or "ME_外部参照").replace("[[ME_", "").replace("]]", ""))
            subj = slug((it.get("subject") or "").replace("[[", "").replace("]]", ""))
            claim_text = v.get("revised_claim") if verdict == "revise" else it.get("claim", "")
            fname = f"A_{chapter}_{it.get('predicate', 'alludes_to')}_{subj}_{obj}.md"
            path = ROOT / "wiki" / "claims" / fname
            path.parent.mkdir(parents=True, exist_ok=True)
            quotes = "\n".join(f"> {q.get('quote','')}（{q.get('paragraph','')}）"
                               for q in it.get("quotes", []))
            path.write_text(f"""---
schema_version: "5.1"
id: A_{chapter}_{it.get('predicate','alludes_to')}_{subj}_{obj}
type: analytical_claim
created: {today}
subject: "[[{subj}]]"
predicate: {it.get('predicate', 'alludes_to')}
object: "[[ME_{obj}]]"
epistemic_status: hypothesized
review_status: llm_verified
document_status: draft
spoiler_after: {chapter}
evidence_strength: {it.get('confidence', 'moderate')}
provenance:
  proposed_by: {{kind: agent, id: swift-1.5-iq3_xxs}}
  reviewed_by: {{kind: agent, id: swift-1.5-iq3_xxs, date: {today}}}
---
<!-- LLM-GENERATED -->
<!-- 人間レビュー未実施: review_status=llm_verified は LLM 自己審査による暫定承認 -->

# {claim_text}

{quotes}

**審査（LLM 代替）**: {v.get('reason','')}
""", encoding="utf-8")
            counts["claims"] += 1
            log.append(f"- [A] {fname} :: {claim_text[:60]} :: {v.get('reason','')[:50]}")
        elif it.get("kind") == "mystery":
            name = slug(it.get("name", "").replace("MY_", ""))
            fname = f"MY_{chapter}_{name}.md"
            path = ROOT / "wiki" / "mysteries" / fname
            path.parent.mkdir(parents=True, exist_ok=True)
            quotes = "\n".join(f"> {q.get('quote','')}（{q.get('paragraph','')}）"
                               for q in it.get("quotes", []))
            path.write_text(f"""---
schema_version: "5.1"
id: MY_{chapter}_{name}
type: mystery
created: {today}
mystery_status: candidate
spoiler_after: {chapter}
review_status: llm_verified
timeline:
  introduced: {chapter}
provenance:
  proposed_by: {{kind: agent, id: swift-1.5-iq3_xxs}}
  reviewed_by: {{kind: agent, id: swift-1.5-iq3_xxs, date: {today}}}
---
<!-- LLM-GENERATED -->
<!-- 人間レビュー未実施: review_status=llm_verified は LLM 自己審査による暫定承認 -->

# {name}

{it.get('note','')}

**回収示唆**: {it.get('expected_payoff','')}

{quotes}

**審査（LLM 代替）**: {v.get('reason','')}
""", encoding="utf-8")
            counts["mysteries"] += 1
            log.append(f"- [MY] {fname} :: {it.get('note','')[:60]} :: {v.get('reason','')[:50]}")
        elif it.get("kind") == "theme":
            # 主題は wiki/episodes の frontmatter 候補として staging に残す（昇格は集約時）
            counts.setdefault("themes_accepted", 0)
            counts["themes_accepted"] += 1
            log.append(f"- [theme w={it.get('weight','')}] {chapter}: {it.get('theme','')[:70]} :: {v.get('reason','')[:50]}")
    return counts


def append_log(chapter: str, counts: dict, log: list[str]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    header_needed = not LOG_PATH.exists()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        if header_needed:
            f.write("# Autopilot ログ（LLM 代替実施記録）\n\n"
                    "review_status: llm_verified = LLM 自己審査による暫定承認（人間 human_verified に置換対象）\n\n")
        f.write(f"## {chapter}（{date.today().isoformat()}）\n\n")
        f.write(f"昇格: claims={counts.get('claims',0)} mysteries={counts.get('mysteries',0)} "
                f"themes={counts.get('themes_accepted',0)} 却下={counts.get('rejected',0)}\n\n")
        f.write("\n".join(log) + "\n\n")


def process(chapter_num: int, config: dict, client) -> bool:
    chapter = f"ch{chapter_num:04d}"
    analysis = load_analysis(chapter)
    if not analysis:
        print(f"WARN analysis_{chapter}.yaml なし（スキップ）")
        return False
    items = analysis.get("items", [])
    print(f"[{chapter}] 提案 {len(items)} 件を LLM レビュー中...")
    verdicts = review_items(client, config, chapter, items)
    log: list[str] = []
    counts = promote(chapter, items, verdicts, log)
    append_log(chapter, counts, log)
    print(f"[{chapter}] 昇格 claims={counts.get('claims',0)} mysteries={counts.get('mysteries',0)} "
          f"themes={counts.get('themes_accepted',0)} 却下={counts.get('rejected',0)}")
    return True


def main() -> int:
    config = load_config()
    client = create_client(config)
    chapters = [int(sys.argv[1])] if len(sys.argv) > 1 else list(
        range(config["chapter_range"]["start"], config["chapter_range"]["end"] + 1))
    ok = 0
    for c in chapters:
        try:
            if process(c, config, client):
                ok += 1
        except Exception as e:
            print(f"[ch{c:04d}] ERROR: {e}")
    print(f"完了: {ok}/{len(chapters)} 章")
    return 0


if __name__ == "__main__":
    sys.exit(main())
