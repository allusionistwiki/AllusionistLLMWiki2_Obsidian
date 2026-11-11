#!/usr/bin/env python3
"""Repair json-fail v7 records: re-format the RAW answer into strict JSON (no thinking).

Reads episodes/<id>.thinking.md files that contain a "=== RAW ===" section,
asks the model (thinking OFF, json_mode grammar) to convert the RAW analysis
text into the v7 schema, and writes episodes/<id>.json.
"""
import sys, json, io, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import llm_client
CFG = llm_client.load_config()
CLIENT = llm_client.create_client(CFG)

EP = Path(sys.argv[1])

SCHEMA = """{"mentions":[{"name":"表層名義","role":"人物|語り手|比喩|一般語","group_hint":"同一人物系列ヒント"}],
"identity":[{"a":"名義A","b":"名義B","type":"explicit|strong","quote":"逐語引用","lines":["chN pN"],"reason":"1-2文"}],
"separations":[{"a":"名義A","b":"名義B","reason":"1-2文","lines":["chN pN"]}],
"narrator":{"refers_to":"特定できた場合のみ","quote":"引用","lines":["pN"]},
"recall_used":[ch番号]}"""

REPAIR = """次の解析テキスト（JSON に収められなかった生テキスト）を、指定 schema の JSON に変換してください。
情報は追加せず、記載されたものだけを整形式へ。引用は原文記載のまま。
## schema
""" + SCHEMA + """
## 生テキスト
{raw}
出力 JSON のみ。"""


def main():
    fixed = 0
    for tf in sorted(EP.glob("*.thinking.md")):
        jf = tf.with_suffix("").with_suffix(".json") if False else Path(str(tf).replace(".thinking.md", ".json"))
        if jf.exists():
            continue
        text = io.open(tf, encoding="utf-8").read()
        if "=== RAW ===" not in text:
            continue
        raw = text.split("=== RAW ===", 1)[1].strip()
        raw = raw[:12000]
        prompt = REPAIR.replace("{raw}", raw)
        try:
            out = llm_client.call_llm(CLIENT, CFG, prompt, max_tokens=4000, temperature=0.2, json_mode=True)
        except Exception as ex:
            print(f"{tf.name}: repair-fail {ex}")
            continue
        js = re.search(r"\{.*\}", out, re.S)
        if not js:
            print(f"{tf.name}: repair-no-json")
            continue
        try:
            obj = json.loads(js.group(0))
        except Exception as ex:
            print(f"{tf.name}: repair-json-fail {ex}")
            continue
        ep_id = int(tf.name.split(".")[0])
        rec = {"episode": ep_id, "generated_at": __import__("time").strftime("%Y-%m-%dT%H:%M:%SZ"),
               "present_names": [], "search_trace": [], "recall_paras": [],
               "thinking_len_chars": 0, "thinking": text.split("=== RAW ===")[0],
               "repaired_from_raw": True, "analysis": obj}
        io.open(str(jf), "w", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
        fixed += 1
        print(f"repaired {ep_id}: identity={len(obj.get('identity', []))} sep={len(obj.get('separations', []))}")
    print("repaired:", fixed)


if __name__ == "__main__":
    main()
