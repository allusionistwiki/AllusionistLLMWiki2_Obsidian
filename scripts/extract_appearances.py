#!/usr/bin/env python3
"""専用再解析B: キャラ容姿描写データのみ（先延ばし索引とは分離）。

出力: Work/appearance_facts/chNNNN.jsonl（kind=appearance のみ）
  {"kind":"appearance","episode":"chNNNN","paragraph":"pNNN","quote":"原文一節",
   "character":"キャラ名","features":["髪","瞳",...],"note":"容姿の要約","quote_verified":bool}

対象: raw/ を機械スキャン（APPEAR_HINT）してヒットした章のみ。
LLM には原文全文を渡して容姿描写をキャラ名ごとに全抽出させる（性格・行動は除外）。
再実行は appearance データのみを上書きするので deferral データ（deferral_facts/）に影響なし。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from llm_client import call_llm, parse_json_lenient, strip_code_fence  # noqa: E402

RAW = ROOT / "raw"
OUT_DIR = ROOT.parent / "AllusionistLLMWiki2_Work" / "appearance_facts"

APPEAR_HINT = re.compile(
    r"髪|瞳|目|顔|肌|身長|体格|姿|風体|外見|容貌|風貌|服|衣装|鎧|兜|傷|義手|義腕|義足|義体|"
    r"翼|角|尾|爪|小柄|大柄|細身|巨躯|白髪|黒髪|銀髪|金髪|赤毛|眼鏡|美貌|異相|声")

SYSTEM = (
    "あなたは日本の長編小説の分析者です。タスクBのみ JSON で出力します。\n"
    "タスクB【容姿】: 原文中に現れるキャラクターの容姿・外見描写（髪・瞳・肌・体格・服装・義肢・"
    "声・顔立ち等）を、キャラ名ごとに抽出する。性格・行動・能力は容姿ではないので含めない。\n"
    "出力は JSON オブジェクト:\n"
    '"appearances":[{"paragraph":"p456","quote":"原文からの正確な一〜二文（改変禁止）",'
    '"character":"キャラ名","features":["髪","肌"],"note":"容姿の簡潔な要約"}]}\n'
    "quote は必ず原文に存在する文字列をそのまま使うこと。存在しない引用は禁止。"
)


def norm(s: str) -> str:
    return re.sub(r"[\s\u3000]+", "", s)


def process_chapter(ch: str, config: dict, client) -> dict:
    text = (RAW / f"{ch}.txt").read_text(encoding="utf-8", errors="ignore")
    if not APPEAR_HINT.search(text):
        return {"chapter": ch, "appearances": 0, "skipped": True}
    raw_norm = norm(text)
    records: list[dict] = []
    ask = (f"以下は {ch} の原文全文です。\n\n{text}\n\n"
           "タスクBのみ出力してください: この章に現れるキャラクターの容姿・外見描写を "
           "キャラ名ごとに全て抽出（髪・瞳・肌・体格・服装・義肢・声・顔立ち等）。"
           "性格・行動は含めない。quote は原文そのまま。")
    for attempt in range(3):
        try:
            content = strip_code_fence(call_llm(client, config, ask,
                                                system_prompt=SYSTEM, json_mode=True))
            data = parse_json_lenient(content, 1)
        except Exception as e:
            print(f"  retry {attempt+1} 失敗: {e}")
            continue
        items = data.get("appearances", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        good = [i for i in items if norm(i.get("quote", "")) in raw_norm]
        if len(good) >= 1:
            for r in good:
                records.append({"kind": "appearance", "episode": ch,
                                "paragraph": r.get("paragraph", ""), "quote": r.get("quote", ""),
                                "character": r.get("character", ""),
                                "features": r.get("features", []), "note": r.get("note", ""),
                                "quote_verified": norm(r.get("quote", "")) in raw_norm})
            break
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{ch}.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + ("\n" if records else ""),
        encoding="utf-8")
    return {"chapter": ch, "appearances": len(records)}


def main() -> int:
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    from openai import OpenAI
    llm = config["llm"]
    client = OpenAI(base_url=llm["base_url"], api_key=llm.get("api_key", "local"))
    chapters = sorted(p.stem for p in RAW.glob("ch*.txt"))
    todo = [a for a in sys.argv[1:] if not a.startswith("--")] or chapters
    tot = 0
    for ch in todo:
        r = process_chapter(ch, config, client)
        tot += r.get("appearances", 0)
        print(f"[{ch}] appearances={r.get('appearances', 0)}")
    print(f"TOTAL appearances={tot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
