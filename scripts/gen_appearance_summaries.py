#!/usr/bin/env python3
"""キャラ容姿の5行要約を LLM で生成し data/appearance_summaries.json に保存（resume 対応）.

1 呼び出しで複数キャラをまとめて要約する。入力は容姿記述の note+features（性格・行動は除外）。
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT.parent / "AllusionistLLMWiki2_Work"
FACTS = WORK / "deferral_facts"
CACHE = ROOT / "data" / "appearance_summaries.json"
CFG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))["llm"]

sys.path.insert(0, str(ROOT / "scripts"))
from llm_client import (create_client, load_config, call_llm,  # noqa: E402
                        strip_code_fence, parse_json_lenient)  # noqa: E402

BATCH = 8
CFG_ALL = load_config()
CLIENT = create_client(CFG_ALL)
CFG = CFG_ALL["llm"]


def load_chars() -> dict[str, list[dict]]:
    by_char: dict[str, list[dict]] = defaultdict(list)
    for jl in sorted(FACTS.glob("ch*.jsonl")):
        for line in jl.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r["kind"] != "appearance":
                continue
            name = (r.get("character") or "").strip()
            if name:
                by_char[name].append(r)
    return by_char


def summarize(names: list[str], by_char: dict) -> dict[str, str]:
    parts = []
    for n in names:
        items = by_char[n][:20]
        lines = []
        for r in items:
            feats = "・".join((r.get("features") or [])[:6])
            lines.append(f"- {r.get('note', '')}{' ｜ ' + feats if feats else ''}")
        parts.append(f"### {n}\n" + "\n".join(lines))
    prompt = (
        "以下は小説の各キャラクターの容姿描写の抜粋です。キャラごとに5行以内の"
        "容姿要約を日本語で生成してください（髪・瞳・肌・体格・服装・義肢・声など外見のみ。"
        "性格・行動は書かない。記述に矛盾があれば『話により〜』と併記）。"
        "出力は JSON: {\"要約\": {キャラ名: 要約文字列}} のみ。\n\n" + "\n\n".join(parts)
    )
    out = {}
    for _ in range(3):
        try:
            txt = call_llm(CLIENT, CFG_ALL, prompt, json_mode=False,
                           temperature=CFG.get("temperature", 1.0),
                           max_tokens=CFG.get("max_tokens", 64000))
        except Exception:
            continue
        obj = parse_json_lenient(strip_code_fence(txt), 1)
        if isinstance(obj, dict) and isinstance(obj.get("要約"), dict):
            for n in names:
                s = obj["要約"].get(n)
                if isinstance(s, str) and s.strip():
                    out[n] = s.strip().replace("\n", " ／ ")
            break
    return out


def main() -> int:
    by_char = load_chars()
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    todo = [n for n in by_char if n not in cache]
    print(f"対象 {len(by_char)} / 未生成 {len(todo)}")
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i + BATCH]
        got = summarize(batch, by_char)
        cache.update(got)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"batch {i//BATCH+1}: {len(got)}/{len(batch)}（累計 {len(cache)}）")
    print(f"APPEARANCE SUMMARIES DONE: {len(cache)}/{len(by_char)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
