#!/usr/bin/env python3
"""Rescue pending_retry episodes: convert their saved thinking prose into the compact schema JSON."""
import sys, json, io, re
from pathlib import Path
EP_ARG = sys.argv[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.argv = [sys.argv[0],
            "C:/Users/d5dx/Downloads/Code/AllusionistWiki_work/work/allusionist_v2/L2/runs/20261029T0843_c8bb/entities.json",
            "C:/Users/d5dx/AppData/Local/hermes/profiles/awiki2/cache/scratch/dummy_v7"]
import os
os.environ.setdefault("V7_NAMEIDX", "C:/Users/d5dx/AppData/Local/hermes/profiles/awiki2/cache/scratch/name-chapter-index.json")
import llm_client
import l2_name_resolution_v7 as V7

EP = Path(EP_ARG)
CFG = llm_client.load_config()
CLIENT = llm_client.create_client(CFG)

PROMPT = """あなたは解析結果の整形係です。下の「解析思考テキスト」から、決定済みの判定だけを抽出して compact schema の JSON に整形してください。新規の推論・追加判断はしない。記載された判定のみを、記載された名前・引用・ch番号で転記する。

## compact schema（フィールド6個・items は文字列のみ）
{"fields":[
 "M|表層名義|role(人物|語り手|比喩|一般語)",
 "I|a|b|type(explicit|strong)|逐語引用|使用ch|思考1文",
 "S|a|b|分離理由1文|使用ch",
 "N|語り手が指す人物|逐語引用|使用p行",
 "R|使用した関連ch番号"
]}

## 解析思考テキスト
{thinking}

出力 JSON のみ。"""


def main():
    fixed = 0
    for p in sorted(EP.glob("*.json")):
        rec = json.load(io.open(p, encoding="utf-8"))
        if not rec.get("pending_retry"):
            continue
        ep_id = rec["episode"]
        tf = Path(str(p).replace(".json", ".thinking.md"))
        print(f"{ep_id}: found={tf.exists()}", flush=True)
        if not tf.exists():
            print(f"{ep_id}: no thinking.md, skip")
            continue
        thinking = io.open(tf, encoding="utf-8").read()[:12000]
        prompt = PROMPT.replace("{thinking}", thinking)
        try:
            out = llm_client.call_llm(CLIENT, CFG, prompt, max_tokens=4000, temperature=0.2, json_mode=False)
        except Exception as ex:
            print(f"{ep_id}: convert-fail {ex}")
            continue
        js = re.search(r"\{.*\}", out, re.S)
        if not js:
            print(f"{ep_id}: convert-no-json")
            continue
        try:
            obj = json.loads(js.group(0))
        except Exception:
            try:
                obj = llm_client.parse_json_lenient(js.group(0), 0)
                if isinstance(obj, list):
                    obj = obj[0] if obj and isinstance(obj[0], dict) else {}
            except Exception as ex:
                print(f"{ep_id}: convert-json-fail {ex}")
                continue
        analysis = V7.parse_fields(obj)
        if analysis is None:
            print(f"{ep_id}: convert-empty")
            continue
        full = {"episode": ep_id, "generated_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ"),
                "present_names": rec.get("present_names", []), "search_trace": rec.get("search_trace", []),
                "recall_paras": rec.get("recall_paras", []), "thinking_len_chars": len(thinking),
                "thinking": thinking, "rescued_from_thinking": True, "analysis": analysis}
        io.open(p, "w", encoding="utf-8").write(json.dumps(full, ensure_ascii=False, indent=1) + "\n")
        fixed += 1
        print(f"rescued {ep_id}: I={len(analysis['identity'])} S={len(analysis['separations'])} M={len(analysis['mentions'])}")
    print("rescued:", fixed)


if __name__ == "__main__":
    main()
