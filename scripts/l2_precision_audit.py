#!/usr/bin/env python3
"""L2 台帳 v4 精度監査（原文全話使用状況の機械監査）。

小説原文（AllusionistWiki_raw/raw/novel の章 md）を paragraph（行）単位で
Aho-Corasick 全文字列走査し、台帳の各名義について使用状況を機械集計する。

監査項目:
  A. 過剰統合候補: 高確度 alias→代表名 統合で、alias が代表名と共起しない
     paragraph（独立使用）の比率が高い pair → 要検証への降格候補。
  B. 代表名審査: 代表名が群内のが長い正式名（旧名の一部）である group
     → 全文（姓付き・正式名）の使用状況を示し primary 提案。
  C. 単独名義の merge 候補: alias を持たない単独代表名が、他代表名と
     高率で同一 paragraph に共起する場合 → 統合候補（提案のみ）。

出力: JSON レポート（stdout）:
  metrics[name] = {para, chapters, co: {canonical: n}}
  applied_pairs_top / substring_groups / cooccur_candidates（上位のみ）

使い方: python scripts/l2_precision_audit.py --out <report.json>
"""
import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import ahocorasick

LEDGER = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_work/work/allusionist_v2/L2/runs/20261029T0843_c8bb/entities.json")
RAW = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_raw/raw/novel")
HIGH = {"高", "明言", "表記一致", "蓋然性高"}


def namekey(a):
    return a["name"] if isinstance(a, dict) else a


def conf_of(a):
    return a.get("confidence") if isinstance(a, dict) else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    d = json.load(LEDGER.open(encoding="utf-8"))
    ents = d["entities"]
    canon_of = {}
    applied = {}  # alias -> (canonical, conf) for high-conf non-canonical
    aliases_by_ent = {}
    for e in ents:
        c = e["canonical"]
        canon_of.setdefault(c, c)
        for a in e.get("aliases", []):
            n = namekey(a)
            canon_of.setdefault(n, c)
        aliases_by_ent[e["id"]] = e
    for e in ents:
        c = e["canonical"]
        for a in e.get("aliases", []):
            n = namekey(a)
            if n != c and conf_of(a) in HIGH:
                applied[n] = (c, conf_of(a))

    A = ahocorasick.Automaton()
    for n in canon_of:
        if len(n) >= 2:
            A.add_word(n, n)
    A.make_automaton()
    print(f"names in automaton: {len(A)}", file=sys.stderr)

    para_hits = Counter()
    chap_hits = defaultdict(set)
    cooc = defaultdict(Counter)  # name -> Counter(co-occurring canonicals)

    n_paras = 0
    for md in sorted(RAW.rglob("*.md")):
        chap = md.stem.split("__")[0]
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for para in text.splitlines():
            para = para.strip()
            if len(para) < 2:
                continue
            n_paras += 1
            found = set()
            for _, n in A.iter(para):
                found.add(n)
            if not found:
                continue
            canonset = {canon_of[n] for n in found}
            for n in found:
                para_hits[n] += 1
                chap_hits[n].add(chap)
            for n in found:
                c = canon_of[n]
                for other in canonset:
                    if other != c:
                        cooc[n][other] += 1

    print(f"paragraphs scanned: {n_paras}", file=sys.stderr)

    # A. over-merge candidates among applied pairs
    over = []
    for a, (c, cf) in applied.items():
        pa = para_hits.get(a, 0)
        if pa < 5:
            continue
        co = cooc.get(a, {}).get(c, 0)
        indep = pa - co
        ratio = indep / pa
        if ratio >= 0.5:
            over.append({"alias": a, "canonical": c, "conf": cf, "alias_paras": pa,
                         "cooc_paras": co, "indep_ratio": round(ratio, 3)})
    over.sort(key=lambda x: -x["indep_ratio"] * x["alias_paras"])

    # B. substring-canonical groups
    groups = []
    for e in ents:
        c = e["canonical"]
        fulls = []
        for a in e.get("aliases", []):
            n = namekey(a)
            if n != c and c in n and len(n) > len(c):
                fulls.append({
                    "name": n,
                    "conf": conf_of(a),
                    "paras": para_hits.get(n, 0),
                    "chapters": len(chap_hits.get(n, ())),
                })
        if fulls:
            fulls.sort(key=lambda x: -x["paras"])
            groups.append({
                "canonical": c,
                "canonical_paras": para_hits.get(c, 0),
                "canonical_chapters": len(chap_hits.get(c, ())),
                "longer_names": fulls,
            })
    groups.sort(key=lambda g: -(max(f["paras"] for f in g["longer_names"])))

    # C. standalone canonicals with strong co-occurrence to another canonical
    standalone = []
    for e in ents:
        c = e["canonical"]
        aliased = [namekey(a) for a in e.get("aliases", []) if namekey(a) != c]
        if aliased:
            continue
        pc = para_hits.get(c, 0)
        if pc < 3:
            continue
        top = cooc.get(c, Counter()).most_common(1)
        if top and top[0][1] >= max(3, 0.5 * pc):
            standalone.append({"canonical": c, "paras": pc,
                               "cooc_with": top[0][0], "cooc_paras": top[0][1]})
    standalone.sort(key=lambda x: -x["cooc_paras"])

    report = {
        "ledger_run": d.get("run"),
        "paragraphs_scanned": n_paras,
        "applied_pairs": len(applied),
        "over_merge_candidates": over[:80],
        "over_merge_count": len(over),
        "substring_canonical_groups": groups[:80],
        "substring_canonical_count": len(groups),
        "merge_candidates_standalone": standalone[:80],
        "standalone_candidate_count": len(standalone),
        "spot": {},
    }
    for q in ["自己愛", "紫", "アズ", "アズーリア", "アズーリア・ヘレゼクシュ", "少年王"]:
        report["spot"][q] = {
            "paras": para_hits.get(q, 0),
            "chapters": len(chap_hits.get(q, ())),
            "top_cooc": cooc.get(q, Counter()).most_common(5),
            "canonical_of": canon_of.get(q),
        }
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({
        "applied_pairs": len(applied),
        "over_merge_count": len(over),
        "substring_canonical_count": len(groups),
        "standalone_candidate_count": len(standalone),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
