#!/usr/bin/env python3
"""L2 名前解消 v5: 1 章ずつ実読して名前一同一性の証拠レコードを作る。

章全文（行番号付き）+ その章に出現する名前の台帳抜粋だけを LLM に与え、
mentions / identity（explicit・strong）/ separations を章ごとに抽出する。
決定は集計器（l2_resolution_aggregate.py）が行い、このスクリプトは
証拠レコードのみを追加専用で保存する。

使い方:
  python scripts/l2_name_resolution.py --out <staging dir> --max 12
  python scripts/l2_name_resolution.py --out <staging dir> --chapters ch5001,ch5002
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import ahocorasick

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm_client import call_llm, create_client, load_config, parse_json_lenient, strip_code_fence

LEDGER = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_work/work/allusionist_v2/L2/runs/20261029T0843_c8bb/entities.json")
MAIN = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_raw/raw/novel/kakuyomu/16816927859268545348_幻想再帰のアリュージョニスト")
PROMPT_TMPL = """あなたは長編『幻想再帰のアリュージョニスト』の 1 話を通読し、この章に出現する登場人物名義の「同一性証拠」だけを集める解析者です。推測で統合せず、本文に現れた証拠のみを抽出してください。

# この章に出現する名義の台帳抜粋（参考: 既存の統合状態。正しいとは限らない）
{context}

# 出力 JSON（この形式のみ返す）
{{"mentions":[{{"name":"...","paras":[行番号],"role":"この章での役割 1 行"}}],
"identity":[{{"a":"名義A","b":"名義B","kind":"explicit|strong","quotes":["¶行番号: 原文引用"]}}],
"separations":[{{"a":"名義A","b":"名義B","quotes":["¶行番号: 原文引用"]}}]}}

規則:
- identity/explicit: 本文に同一性述語があるものだけ（名乗り・自己紹介・呼称・「AはBである」・通称宣言・「AことB」）。引用 ¶ 番号付きで原文を添える。
- identity/strong: 同一場面・連続する場面で同一の行為主体として描かれる（一人二役の記述）。引用付き。
- separations: 同一場面〜連続場面で両名義が独立した行為主体（別々の行動・別々の受話・並列言及）として扱う証拠。
- 台帳に無い名前が出現したら mentions だけに追加（identity は出さない）。
- 台帳の既存統合が本文と矛盾する場合は separations に記録する。
# 章本文（行番号付き）
{episode}
"""


def namekey(a):
    return a["name"] if isinstance(a, dict) else a


def load_ledger():
    d = json.load(LEDGER.open(encoding="utf-8"))
    by_canon = {}
    name_to_canon = {}
    for e in d["entities"]:
        by_canon[e["canonical"]] = e
        for a in e.get("aliases", []):
            name_to_canon.setdefault(namekey(a), e["canonical"])
        name_to_canon.setdefault(e["canonical"], e["canonical"])
    return d, by_canon, name_to_canon


def chapters():
    out = []
    for md in MAIN.glob("ch*.md"):
        m = re.match(r"^(ch\d+)", md.stem)
        if m:
            out.append((m.group(1), md))
    out.sort()
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--max", type=int, default=12)
    ap.add_argument("--chapters", default=None)
    args = ap.parse_args()

    out_dir = Path(args.out)
    eps_dir = out_dir / "episodes"
    eps_dir.mkdir(parents=True, exist_ok=True)

    d, by_canon, name_to_canon = load_ledger()
    A = ahocorasick.Automaton()
    for n in name_to_canon:
        if len(n) >= 2:
            A.add_word(n, n)
    A.make_automaton()

    config = load_config()
    client = create_client(config)

    wanted = None
    if args.chapters:
        wanted = set(args.chapters.split(","))

    done = 0
    for ch, md in chapters():
        if wanted and ch not in wanted:
            continue
        outp = eps_dir / f"{ch}.json"
        if outp.exists():
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        present = sorted({n for _, n in A.iter(text)}, key=len, reverse=True)
        rec = {"chapter": ch, "source": str(md), "present": present,
               "mentions": [], "identity": [], "separations": []}
        if not present:
            outp.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
            continue
        # 台帳抜粋: present 名義が属する实体グループのみ
        ctx_lines = []
        seen_ids = set()
        for n in present[:60]:
            c = name_to_canon.get(n)
            e = by_canon.get(c)
            if not e or e["id"] in seen_ids:
                continue
            seen_ids.add(e["id"])
            als = [namekey(a) for a in e.get("aliases", [])][:25]
            ctx_lines.append(f"- {e['canonical']} (kind={e['kind']}) alias: {', '.join(als)}")
        numbered = "\n".join(f"¶{i+1}: {ln}" for i, ln in enumerate(text.splitlines()) if ln.strip())
        prompt = PROMPT_TMPL.format(context="\n".join(ctx_lines) or "(台帳該当なし)", episode=numbered)
        try:
            raw = call_llm(client, config, prompt)
            data = parse_json_lenient(strip_code_fence(raw), 0)
            if isinstance(data, list):
                data = data[0] if data and isinstance(data[0], dict) else {}
            rec.update({k: data.get(k, []) for k in ("mentions", "identity", "separations")})
            rec["model"] = config.get("model")
        except Exception as exc:  # noqa: BLE001
            rec["error"] = str(exc)[:300]
        outp.write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
        done += 1
        print(f"{ch}: present={len(present)} identity={len(rec['identity'])} sep={len(rec['separations'])}", flush=True)
        if done >= args.max:
            break
    print(f"done episodes={done} -> {eps_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
