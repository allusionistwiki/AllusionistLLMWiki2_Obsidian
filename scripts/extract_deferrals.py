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
OUT_DIR = ROOT.parent / "AllusionistLLMWiki2_Work" / "deferral_facts"

# 「今はまだ」本体＋カンマ/改行またぎ＋同型の先延ばし示唆（いずれ/そのうち/時期が来たら/
# 準備ができたら/追って/未定/今ではない/〜がまだだった/〜ないままだ 等）
DEFER_PAT = re.compile(
    r"今は[、,・\s]*まだ|今のところまだ|現時点ではまだ|まだ存在しな|まだない|まだ無い"
    r"|今(では|じゃ)ない|今は(やめ|控|自重|我慢|堪)"
    r"|まだ先|時期が来|そのうち|いずれ"
    r"|準備ができ(たら|い|次第)|決まり次第|追って"
    r"|後(で|日)に?(教|伝え|回|連|報告|知ら)"
    r"|未定|決めていない|決められていない"
    r"|まだだった|まだまだ|わからないままだ|知らないままだ|知らぬままだ"
    r"|見えないままだ|届かぬままだ|及ばぬままだ")
PAGE_MARK = re.compile(r"【p(\d+)】")

SYSTEM = (
    "あなたは日本の長編小説の分析者です。タスクAのみ JSON で出力します。\n"
    "タスクA【今はまだ】: 原文中の「今はまだ」「今は、まだ」および同型の先延ばし示唆"
    "（「いずれ」「そのうち」「時期が来たら」「準備ができたら」「追って」「未定」「今ではない」"
    "「今はやめておく」「〜がまだだった」「〜ないままだ」等）の箇所ごとに、"
    "『何が先延ばし・留保・未達とされているのか』を特定する。抽象的な「先延ばし」ではなく、"
    "文脈から具体的な対象（例:「アキラへの攻撃の開始」「真実の開示」「第五階層への到達」）を記述する。"
    "発言者がいれば記す。\n"
    "出力は JSON オブジェクト:\n"
    '{"deferrals":[{"index":0,"paragraph":"p123",'
    '"quote":"原文からの正確な一〜二文（改変禁止）",'
    '"refers_to":"先延ばしされている具体的対象","who":"発言者（不明なら空）"}]}\n'
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
        # ヒットなし章: 既存 deferral 記録も空にする（パターン拡張で対象外になったわけではない）
        return {"chapter": ch, "deferrals": 0, "skipped": True}
    raw_norm = norm(text)
    records: list[dict] = []
    ctx = "\n".join(f"[{i}] (p{p}) {s}" for i, (p, s) in enumerate(defers))
    ask = (f"以下は {ch} の原文全文です。\n\n{text}\n\n"
           f"上記原文中の「今はまだ」系表現・先延ばし示唆（いずれ/そのうち/時期が来たら/"
           f"準備ができたら/追って/未定/今ではない/〜がまだだった 等を含む）のヒット箇所を"
           f"以下に列挙します（番号付き）:\n{ctx}\n\n"
           "タスクAのみ出力してください: 各番号の箇所について、原文の文脈を読んで "
           "refers_to（先延ばしされている具体的対象）と who を特定し、quote には該当原文をそのまま。"
           "文脈上、単なる比喩や無関係な「まだ」で先延ばしの示唆が無い箇所は refers_to を空文字にすること。"
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
        if len(good) >= 1:
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
