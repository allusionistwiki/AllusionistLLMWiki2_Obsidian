#!/usr/bin/env python3
"""専用再解析: 「今はまだ」対象抽出 + キャラ容姿描写抽出（章単位・原文直接添付）.

出力: Work/deferral_facts/chNNNN.jsonl
  {"kind":"deferral","episode":"chNNNN","paragraph":"pNNN","quote":"原文一文",
   "refers_to":"何が先延ばしされているか（具体対象）","who":"発言者/主体","note":"要約"}
  {"kind":"appearance","episode":"chNNNN","paragraph":"pNNN","quote":"原文一節",
   "character":"キャラ名","features":["髪","瞳",...],"note":"容姿の要約"}

対象章: raw/ 全文を機械スキャンしてヒットした章のみ（漏れなし）。
LLM には原文ヒット箇所＋文脈を渡して「言及対象」を特定させる。
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

# 拡張: カンマ/改行またぎ「今は、まだ」＋同型の先延ばし示唆（いずれ/そのうち/時期が来たら/準備ができたら/追って/未定 等）
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
APPEAR_HINT = re.compile(
    r"髪|瞳|目|顔|肌|身長|体格|姿|風体|外見|容貌|風貌|服|衣装|鎧|兜|傷|義手|義腕|義足|義体|"
    r"翼|角|尾|爪|小柄|大柄|細身|巨躯|白髪|黒髪|銀髪|金髪|赤毛|眼鏡|美貌|異相|声")

SYSTEM = (
    "あなたは日本の長編小説の分析者です。二つの専用タスクを JSON で出力します。\n"
    "タスクA【今はまだ】: 原文中の「今はまだ」「今は、まだ」および同型の先延ばし示唆"
    "（「いずれ」「そのうち」「時期が来たら」「準備ができたら」「追って」「未定」「今ではない」"
    "「今はやめておく」等）の箇所ごとに、"
    "『何が先延ばし・留保・未達とされているのか』を特定する。抽象的な「先延ばし」ではなく、"
    "文脈から具体的な対象（例:「アキラへの攻撃の開始」「真実の開示」「第五階層への到達」）を記述する。"
    "発言者がいれば記す。\n"
    "タスクB【容姿】: 原文中に現れるキャラクターの容姿・外見描写（髪・瞳・肌・体格・服装・義肢・"
    "声・顔立ち等）を、キャラ名ごとに抽出する。性格・行動・能力は容姿ではないので含めない。\n"
    "出力は JSON オブジェクト:\n"
    '{"deferrals":[{"paragraph":"p123","quote":"原文からの正確な一〜二文（改変禁止）",'
    '"refers_to":"先延ばしされている具体的対象","who":"発言者（不明なら空）"}],\n'
    '"appearances":[{"paragraph":"p456","quote":"原文からの正確な一〜二文（改変禁止）",'
    '"character":"キャラ名","features":["髪","肌"],"note":"容姿の簡潔な要約"}]}\n'
    "quote は必ず原文に存在する文字列をそのまま使うこと。存在しない引用は禁止。"
)


def scan_hits(text: str) -> tuple[list[tuple[int, str]], list[tuple[int, str]]]:
    """(page, sentence) のリストを返す（deferral / appearance ヒット）."""
    defers, appears = [], []
    for m in DEFER_PAT.finditer(text):
        ls = max(text.rfind("。", 0, m.start()), text.rfind("\n", 0, m.start()))
        le = text.find("。", m.start())
        le = le + 1 if le >= 0 else min(m.end() + 120, len(text))
        sent = text[ls + 1:le]
        sent = re.sub(r"【p\d+】", "", sent)
        sent = " ".join(s.strip() for s in sent.splitlines() if s.strip() and not s.strip().isdigit())
        if sent:
            pages = [int(x.group(1)) for x in PAGE_MARK.finditer(text[:m.start()])]
            defers.append((pages[-1] if pages else 0, sent[:220]))
    # 容姿は章全体を LLM に読ませる（機械抽出は漏れるため、ヒット章判定にのみ使う）
    for m in APPEAR_HINT.finditer(text):
        ls = max(text.rfind("。", 0, m.start()), text.rfind("\n", 0, m.start()))
        le = text.find("。", m.end())
        le = le + 1 if le >= 0 else min(m.end() + 160, len(text))
        sent = text[ls + 1:le]
        sent = re.sub(r"【p\d+】", "", sent)
        sent = " ".join(s.strip() for s in sent.splitlines() if s.strip() and not s.strip().isdigit())
        if sent:
            pages = [int(x.group(1)) for x in PAGE_MARK.finditer(text[:m.start()])]
            appears.append((pages[-1] if pages else 0, sent[:220]))
    return defers, appears


def norm(s: str) -> str:
    return re.sub(r"[\s\u3000]+", "", s)


def process_chapter(ch: str, config: dict, client, deferral_only: bool = False) -> dict:
    text = (RAW / f"{ch}.txt").read_text(encoding="utf-8", errors="ignore")
    defers, appears = scan_hits(text)
    if not defers and not appears:
        return {"chapter": ch, "deferrals": 0, "appearances": 0, "skipped": True}
    raw_norm = norm(text)
    records: list[dict] = []
    kept_appearances: list[dict] = []
    if deferral_only:
        # 既存 jsonl の appearance 記録は保持し、deferral のみ再生成して差し替える
        jp = OUT_DIR / f"{ch}.jsonl"
        if jp.exists():
            for line in jp.read_text(encoding="utf-8").splitlines():
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("kind") == "appearance":
                    kept_appearances.append(r)
        records.extend(kept_appearances)

    # タスクA: 「今はまだ」箇所（ヒット箇所＋前後文脈を渡す）
    if defers:
        ctx = "\n".join(f"[{i}] (p{p}) {s}" for i, (p, s) in enumerate(defers))
        ask = (f"以下は {ch} の原文全文です。\n\n{text}\n\n"
               f"上記原文中の「今はまだ」系表現・先延ばし示唆（いずれ/そのうち/時期が来たら/"
               f"準備ができたら/追って/未定/今ではない 等を含む）のヒット箇所を以下に列挙します（番号付き）:\n{ctx}\n\n"
               "タスクAのみ出力してください: 各番号の箇所について、原文の文脈を読んで "
               "refers_to（先延ばしされている具体的対象）と who を特定し、quote には該当原文をそのまま。"
               "文脈上、単なる比喩や無関係な「まだ」で先延ばしの示唆が無い箇所は refers_to を空文字にすること。"
               'JSON: {"deferrals":[{"index":0,"paragraph":"pNNN","quote":"...","refers_to":"...","who":"..."}]}')
        recs = _ask(ask, config, client, raw_norm)
        for r in recs:
            i = r.get("index")
            pg = r.get("paragraph") or (f"p{defers[i][0]}" if isinstance(i, int) and i < len(defers) else "")
            records.append({"kind": "deferral", "episode": ch, "paragraph": pg,
                            "quote": r.get("quote", ""), "refers_to": r.get("refers_to", ""),
                            "who": r.get("who", ""),
                            "quote_verified": norm(r.get("quote", "")) in raw_norm})

    # タスクB: 容姿描写（原文全文から抽出）
    if appears:
        ask = (f"以下は {ch} の原文全文です。\n\n{text}\n\n"
               "タスクBのみ出力してください: この章に現れるキャラクターの容姿・外見描写を "
               "キャラ名ごとに全て抽出（髪・瞳・肌・体格・服装・義肢・声・顔立ち等）。"
               "性格・行動は含めない。quote は原文そのまま。")
        recs = _ask(ask, config, client, raw_norm)
        for r in recs:
            records.append({"kind": "appearance", "episode": ch,
                            "paragraph": r.get("paragraph", ""), "quote": r.get("quote", ""),
                            "character": r.get("character", ""),
                            "features": r.get("features", []), "note": r.get("note", ""),
                            "quote_verified": norm(r.get("quote", "")) in raw_norm})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{ch}.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + ("\n" if records else ""),
        encoding="utf-8")
    nd = sum(1 for r in records if r["kind"] == "deferral")
    na = sum(1 for r in records if r["kind"] == "appearance")
    return {"chapter": ch, "deferrals": nd, "appearances": na}


def _ask(ask: str, config: dict, client, raw_norm: str) -> list[dict]:
    from llm_client import load_config  # noqa: F401  (client 側で解決済み想定の注記)
    for attempt in range(3):
        try:
            content = strip_code_fence(call_llm(client, config, ask,
                                                system_prompt=SYSTEM, json_mode=True))
            data = parse_json_lenient(content, 1)
        except Exception as e:
            print(f"  retry {attempt+1} 失敗: {e}")
            continue
        if isinstance(data, dict):
            items = data.get("deferrals", []) + data.get("appearances", [])
        elif isinstance(data, list):
            items = data
        else:
            items = []
        good = [i for i in items if norm(i.get("quote", "")) in raw_norm]
        if len(good) >= 1:
            return good
    return []


def main() -> int:
    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    from openai import OpenAI
    llm = config["llm"]
    client = OpenAI(base_url=llm["base_url"], api_key=llm.get("api_key", "local"))
    chapters = sorted(p.stem for p in RAW.glob("ch*.txt"))
    args = sys.argv[1:]
    deferral_only = "--deferral-only" in args
    todo = [a for a in args if not a.startswith("--")] or chapters
    tot_d = tot_a = 0
    for ch in todo:
        r = process_chapter(ch, config, client, deferral_only=deferral_only)
        tot_d += r.get("deferrals", 0)
        tot_a += r.get("appearances", 0)
        print(f"[{ch}] deferrals={r.get('deferrals', 0)} appearances={r.get('appearances', 0)}")
    print(f"TOTAL deferrals={tot_d} appearances={tot_a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
