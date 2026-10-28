#!/usr/bin/env python3
"""L2 台帳 v4 を生成する（v3 台帳 + 原文全話使用状況監査 の決定論的適用）。

入力:
  - v3 台帳 entities.json（20261024T1608_fc8d）
  - paragraph 監査レポート（l2_precision_audit --out）: 名義使用状況・substring groups
  - pair 章監査レポート（l2_pair_chapter_audit --out）: 低共起 25 組

変換規則（決定論的）:
  A. primary 是正: 代表名が群内の正式名（旧代表名を内部に含む長い名）の略称で、
     正式名の原文使用が paragraph ≥1000 かつ章 ≥300 かつ高確度帯 →
     正式名を new canonical に昇格、旧代表名は alias（確度 高 / source v4-primary）。
  B. 過剰統合降格: 章共起 share < 0.2 かつ alias 章 ≥100 かつ同一性述語 0 の
     高確度 pair → 確度を「要検証」へ降格（source: v4-章共起監査、verify 注記付与）。
     実統合は行わない（恒久基準: 実統合には全話使用状況確認が必須）。

出力: work/allusionist_v2/L2/runs/<new_run_id>/
  entities.json / audit-paragraph.json / audit-pair-chapters.json /
  review-v4.md / run.json（derived_from: v3 run）+ latest.txt / runs-index 更新

使い方: python scripts/build_l2_ledger_v4.py --para <audit1.json> --pair <pair.json>
"""
import argparse
import datetime
import json
import re
import sys
import uuid
from pathlib import Path

V3 = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_work/work/allusionist_v2/L2/runs/20261024T1608_fc8d/entities.json")
L2_RUNS = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_work/work/allusionist_v2/L2")
HIGH = {"高", "明言", "表記一致", "蓋然性高"}


def namekey(a):
    return a["name"] if isinstance(a, dict) else a


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--para", required=True)
    ap.add_argument("--pair", required=True)
    args = ap.parse_args()

    d = json.load(V3.open(encoding="utf-8"))
    ents = d["entities"]
    para = json.load(open(args.para, encoding="utf-8"))
    pair = json.load(open(args.pair, encoding="utf-8"))

    para_stats = {s: v for s, v in para.get("spot", {}).items()}
    # name -> paragraph/chapter stats from substring groups + spot
    stat = {}
    for g in para.get("substring_canonical_groups", []):
        stat[g["canonical"]] = {"paras": g.get("canonical_paras", 0), "chapters": g.get("canonical_chapters", 0)}
        for f in g.get("longer_names", []):
            stat[f["name"]] = {"paras": f.get("paras", 0), "chapters": f.get("chapters", 0)}
    for s, v in para_stats.items():
        stat.setdefault(s, {"paras": v.get("paras", 0), "chapters": v.get("chapters", 0)})

    by_id = {e["id"]: e for e in ents}
    by_canon = {e["canonical"]: e for e in ents}

    changes = []

    # A. primary promotions
    for g in para.get("substring_canonical_groups", []):
        c = g["canonical"]
        e = by_canon.get(c)
        if not e:
            continue
        cands = [f for f in g["longer_names"]
                 if f.get("paras", 0) >= 1000 and f.get("chapters", 0) >= 300
                 and (f.get("conf") in HIGH)]
        if not cands:
            continue
        best = max(cands, key=lambda f: f["paras"])
        new_canon = best["name"]
        if new_canon == e["canonical"]:
            continue
        if new_canon in by_canon and by_canon[new_canon] is not e:
            changes.append({"type": "primary_skip", "from": c, "to": new_canon, "why": "target has own entity"})
            continue
        old = e["canonical"]
        e["canonical"] = new_canon
        e["aliases"].append({"name": old, "confidence": "高", "source": "v4-primary",
                             "reason": f"v4 全話使用監査: 正式名「{new_canon}」が原文 {best['paras']} 文中・{best['chapters']} 章で使用、代表名を正式名へ是正",
                             "cites": [], "verify": []})
        changes.append({"type": "primary_promoted", "from": old, "to": new_canon,
                        "paras": best["paras"], "chapters": best["chapters"]})

    # B. demotions
    demoted = 0
    for r in pair.get("low_cooc_high_use", []):
        a, c = r["alias"], r["canonical"]
        e = by_canon.get(c)
        if not e:
            continue
        for al in e.get("aliases", []):
            if isinstance(al, dict) and al["name"] == a and al.get("confidence") in HIGH:
                al["confidence"] = "要検証"
                al["source"] = "v4-章共起監査"
                al["verify"] = (al.get("verify") or []) + [
                    f"v4 章共起監査: alias {r['alias_chapters']}章/代表名との共起 {r['cooc_chapters']}章"
                    f"(share {r['cooc_share']})・同一性述語 0 件 → 別实体の可能性、全話人手確認まで統合適用しない"
                ]
                demoted += 1
                changes.append({"type": "demoted", "alias": a, "canonical": c,
                                "alias_chapters": r["alias_chapters"], "cooc_share": r["cooc_share"]})

    ts = datetime.datetime.now().strftime("%Y%m%dT%H%M")
    run_id = f"{ts}_{uuid.uuid4().hex[:4]}"
    out = L2_RUNS / "runs" / run_id
    out.mkdir(parents=True, exist_ok=True)
    out_json = dict(d)
    out_json["run"] = run_id
    out_json["schema"] = "l2-entities/3"
    (out / "entities.json").write_text(json.dumps(out_json, ensure_ascii=False), encoding="utf-8")
    Path(args.para).copy(out / "audit-paragraph.json")
    Path(args.pair).copy(out / "audit-pair-chapters.json")

    rev = [f"# L2 台帳 v4 審査レポート（run {run_id}・derived_from {d.get('run')}）", ""]
    rev.append("## 根拠")
    rev.append(f"- 原文全話 paragraph 走査（paragraphs_scanned={para.get('paragraphs_scanned')}）")
    rev.append(f"- pair 章共起・同一性述語監査（pairs={pair.get('pairs')}）")
    rev.append("")
    for typ, title in (("primary_promoted", "primary 是正（代表名→正式名）"),
                       ("demoted", "過剰統合降格（高確度→要検証）")):
        rows = [c for c in changes if c["type"] == typ]
        rev.append(f"## {title}: {len(rows)} 件")
        for c in rows:
            if typ == "primary_promoted":
                rev.append(f"- {c['from']} → **{c['to']}**（原文 {c['paras']} 文中・{c['chapters']} 章）")
            else:
                rev.append(f"- {c['alias']} → {c['canonical']}: 章共起 share {c['cooc_share']} / alias {c['alias_chapters']} 章 → 要検証へ降格")
        rev.append("")
    (out / "review-v4.md").write_text("\n".join(rev), encoding="utf-8")

    runmeta = {
        "run_id": run_id,
        "layer": "L2",
        "created": datetime.datetime.now().isoformat(),
        "derived_from": [d.get("run")],
        "inputs": {
            "v3_ledger": str(V3),
            "audit_paragraph": args.para,
            "audit_pair_chapters": args.pair,
            "corpus": "AllusionistWiki_raw/raw/novel",
        },
        "changes": {
            "primary_promotions": sum(1 for c in changes if c["type"] == "primary_promoted"),
            "demotions": demoted,
            "skipped": sum(1 for c in changes if c["type"] == "primary_skip"),
        },
    }
    (out / "run.json").write_text(json.dumps(runmeta, ensure_ascii=False, indent=1), encoding="utf-8")
    (L2_RUNS / "latest.txt").write_text(run_id, encoding="utf-8")
    # runs-index 更新: 旧 run を superseded、本 run を active に
    idx_path = L2_RUNS.parent / "index" / "runs-index.json"
    idx = json.load(idx_path.open(encoding="utf-8"))
    for rid, meta in idx.get("L2", {}).items():
        if meta.get("status") == "active":
            meta["status"] = "superseded"
            meta["superseded_by"] = run_id
    idx["L2"][run_id] = {
        "path": f"work/allusionist_v2/L2/runs/{run_id}",
        "status": "active",
        "kind": "name-integration-v4",
        "derived_from": [d.get("run")],
        "stats": runmeta["changes"],
    }
    idx_path.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"run_id": run_id,
                      "primary_promotions": runmeta["changes"]["primary_promotions"],
                      "demotions": demoted}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
