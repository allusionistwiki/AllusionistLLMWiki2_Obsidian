#!/usr/bin/env python3
"""専用再解析A: 「今はまだ」先延ばし索引データのみ（容姿とは分離）。

出力: Work/deferral_facts/chNNNN.jsonl（kind=deferral のみ）
  {"kind":"deferral","episode":"chNNNN","paragraph":"pNNN","quote":"原文一文",
   "refers_to":"何が先延ばしされているか（具体対象）","who":"発言者/主体","quote_verified":bool}

対象: raw/ を機械スキャン（DEFER_PAT）してヒットした章のみ。
LLM には原文全文＋ヒット箇所を渡して「言及対象」を特定させる。
再実行は deferral データのみを上書きするので容姿データ（appearance_facts/）に影響なし。
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
from paths import WORK_DIR
OUT_DIR = WORK_DIR / "deferral_facts"

# 「今はまだ」系に限定（いずれ/そのうち/準備ができたら 等の日常表現は対象外）。
# 目的は伏線・将来の暗示の検出: 「今は〜でない（が、そのうち〜になる）」という含み。
DEFER_PAT = re.compile(
    r"今は[、,・\s]*まだ|今のところまだ|現時点ではまだ|まだ存在しな|まだない|まだ無い"
    r"|今は(やめ|控|自重|我慢|堪)"
    r"|わからないままだ|知らないままだ|知らぬままだ"
    r"|見えないままだ|届かぬままだ|及ばぬままだ")
PAGE_MARK = re.compile(r"【p(\d+)】")

SYSTEM = (
    "あなたは日本の長編小説の分析者です。タスクAのみ JSON で出力します。\n"
    "タスクA【今はまだ・伏線暗示】: 目的は『伏線・将来の暗示』の検出である。"
    "原文中の「今はまだ」「今は、まだ」「今は〜やめておく」「〜ないままだ」等の箇所から、"
    "『何が先延ばし・留保・未達とされており、物語の将来で実現・開示・到達することが示唆されているか』"
    "を特定する。抽象的な「先延ばし」ではなく、文脈から具体的な対象"
    "（例:「アキラへの攻撃の開始」「真実の開示」「第五階層への到達」）を記述する。発言者がいれば記す。\n"
    "refers_to は単体で読んで何の話か分かる完全な記述にすること。必須要件: "
    "(1) 代名詞（彼/彼女/それ/あの）を使わず、キャラ名・物名を原文の固有名詞で明記する。"
    "(2) 誰が・何を・どうする（実現・開示・到達・解禁等）のが先延ばしなのかが一文で分かる形にする。"
    "(3) 20〜60字程度で、その章を読んでいない人にも状況が伝わる補足（肩書き・関係・経緯の一言）を含める。"
    "悪い例:「攻撃の開始」「真実の開示」→ 何の話か分からない。"
    "良い例:「アズーリアが黒い魔導書でエスフェイルを撃破する呪文の準備（管理者権限の委譲と術者階梯の向上）」"
    "「アキラの左腕（喪失した義腕）がいつ取り戻されるか」。\n"
    "重要: 単なる日常表現・雑談・比喩で、プロットの将来に関する示唆を含まない箇所は "
    "refers_to を空文字にすること（索引に載せない）。例: 単なる時刻の遅さ、日常の用事、"
    "能力の欠如の描写だけで将来の含みがないものは対象外。\n"
    "出力は JSON オブジェクト:\n"
    '{"deferrals":[{"index":0,"paragraph":"p123",'
    '"quote":"原文からの正確な一〜二文（改変禁止）",'
    '"refers_to":"先延ばしされている具体的対象（伏線・将来の暗示）","who":"発言者（不明なら空）"}]}\n'
    "quote は必ず原文に存在する文字列をそのまま使うこと。存在しない引用は禁止。"
)


def scan_hits(text: str) -> list[tuple[int, str]]:
    out = []
    for m in DEFER_PAT.finditer(text):
        ls = max(text.rfind("。", 0, m.start()), text.rfind("\n", 0, m.start()))
        le = text.find("。", m.start())
        le = le + 1 if le >= 0 else min(m.end() + 120, len(text))
        sent = text[ls + 1:le]
        sent = re.sub(r"【p\d+】", "", sent)
        sent = " ".join(s.strip() for s in sent.splitlines() if s.strip() and not s.strip().isdigit())
        if sent:
            pages = [int(x.group(1)) for x in PAGE_MARK.finditer(text[:m.start()])]
            out.append((pages[-1] if pages else 0, sent[:220]))
    return out


def norm(s: str) -> str:
    return re.sub(r"[\s\u3000]+", "", s)


def process_chapter(ch: str, config: dict, client) -> dict:
    text = (RAW / f"{ch}.txt").read_text(encoding="utf-8", errors="ignore")
    defers = scan_hits(text)
    if not defers:
        # ヒットなし章: 旧パターン時代の残留 deferral 記録も空にする
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / f"{ch}.jsonl").write_text("", encoding="utf-8")
        return {"chapter": ch, "deferrals": 0, "skipped": True}
    raw_norm = norm(text)
    records: list[dict] = []
    ctx = "\n".join(f"[{i}] (p{p}) {s}" for i, (p, s) in enumerate(defers))
    ask = (f"以下は {ch} の原文全文です。\n\n{text}\n\n"
           f"上記原文中の「今はまだ」系・「〜ないままだ」系のヒット箇所を以下に列挙します（番号付き）:\n{ctx}\n\n"
           "タスクAのみ出力してください: 各番号の箇所について、原文の文脈を読んで "
           "refers_to（伏線・将来の暗示として先延ばしされている具体的対象）と who を特定し、"
           "quote には該当原文をそのまま。"
           "refers_to は代名詞を使わずキャラ名・物名を明記し、単体で読んで何の話か分かる完全な一文にすること。"
           "文脈上、日常表現・比喩・単なる状態描写で将来の示唆が無い箇所は refers_to を空文字にすること。"
           'JSON: {"deferrals":[{"index":0,"paragraph":"pNNN","quote":"...","refers_to":"...","who":"..."}]}')
    for attempt in range(3):
        try:
            content = strip_code_fence(call_llm(client, config, ask,
                                                system_prompt=SYSTEM, json_mode=True))
            data = parse_json_lenient(content, 1)
        except Exception as e:
            print(f"  retry {attempt+1} 失敗: {e}")
            continue
        items = data.get("deferrals", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        good = [i for i in items if norm(i.get("quote", "")) in raw_norm]
        # 品質ゲート: refers_to が短すぎる（単体で何の話か分からない）ものは不採用としてリトライ
        if len(good) >= 1 and all(len((i.get("refers_to") or "").strip()) >= 12
                                  for i in good if (i.get("refers_to") or "").strip()):
            for r in good:
                i = r.get("index")
                pg = r.get("paragraph") or (f"p{defers[i][0]}" if isinstance(i, int) and i < len(defers) else "")
                records.append({"kind": "deferral", "episode": ch, "paragraph": pg,
                                "quote": r.get("quote", ""), "refers_to": r.get("refers_to", ""),
                                "who": r.get("who", ""),
                                "quote_verified": norm(r.get("quote", "")) in raw_norm})
            break
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{ch}.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + ("\n" if records else ""),
        encoding="utf-8")
    return {"chapter": ch, "deferrals": len(records)}


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
        tot += r.get("deferrals", 0)
        print(f"[{ch}] deferrals={r.get('deferrals', 0)}")
    print(f"TOTAL deferrals={tot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
