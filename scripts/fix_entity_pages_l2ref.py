"""L1 エンティティページ post-processing 修復（決定論・LLM 不使用）。

Usage: python scripts/fix_entity_pages_l2ref.py <work_run_id>
Input : work/allusionist_v2/L2/runs/<id>/entities.json（L2 台帳）
        wiki/entities/**/*.md
Effects:
 1) 象徴・比喩セクションの重複 bullets を初出のみへ削除。
 2) frontmatter first_appearance / spoiler_after を AUTO:ブロックの **初出**（事実上の観測最小）へ同期。
 3) L2 台帳に存在する名義は「L2 台帳対応」節を注入（冪等: マーカーで置換）。
"""
import json
import re
import sys
from pathlib import Path

WIKI = Path(__file__).resolve().parent.parent / "wiki"
sys.path.insert(0, r"C:/Users/d5dx/Downloads/Code/AllusionistWiki_work/scripts")
from l2_common import norm_key  # noqa: E402

RUN = sys.argv[1]
LEDGER = Path(
    r"C:/Users/d5dx/Downloads/Code/AllusionistWiki_work/work/allusionist_v2/L2/runs") / RUN / "entities.json"


def main():
    ents = json.loads(LEDGER.read_text(encoding="utf-8"))["entities"]
    byid = {e["id"]: e for e in ents}
    l2 = {}
    for e in ents:
        l2[norm_key(e["canonical"])] = e
        for a in e.get("aliases", []):
            l2.setdefault(norm_key(a), e)

    n_dedup = n_fs = n_ref = 0
    for p in sorted((WIKI / "entities").rglob("*.md")):
        t = p.read_text(encoding="utf-8")
        orig = t

        # 1) 象徴・比喩の重複 bullets 削除
        m = re.search(r"(## 象徴・比喩\n)(.*?)(?=\n<!-- /AUTO-GENERATED:symbolic -->)", t, re.S)
        if m:
            seen = set()
            kept = []
            for line in m.group(2).splitlines():
                key = line.strip()
                if key.startswith("- ") and key in seen:
                    continue
                if key.startswith("- "):
                    seen.add(key)
                kept.append(line)
            new = "\n".join(kept)
            if new != m.group(2):
                t = t[:m.start(2)] + new + t[m.end(2):]
                n_dedup += 1

        # 2) first_appearance 同期（AUTO:ブロックの初出が frontmatter より古い場合）
        body = re.search(r"\*\*初出\*\*:\s*(ch\d+)", t)
        fmfa = re.search(r"^first_appearance:\s*(ch\d+)", t, re.M)
        if body and fmfa and body.group(1) < fmfa.group(1):
            t = t[:fmfa.start(1)] + body.group(1) + t[fmfa.end(1):]
            fs = re.search(r"^spoiler_after:\s*(ch\d+)", t, re.M)
            if fs and fs.group(1) > body.group(1):
                t = t[:fs.start(1)] + body.group(1) + t[fs.end(1):]
            n_fs += 1

        # 3) L2 台帳対応 節
        cn = re.search(r"^canonical_name:\s*\"?([^\"\n]+)\"?", t, re.M)
        name = cn.group(1).strip() if cn else None
        hit = l2.get(norm_key(name)) if name else None
        block_pat = re.compile(r"<!-- AUTO-GENERATED:l2ref -->.*?<!-- /AUTO-GENERATED:l2ref -->", re.S)
        if hit:
            e = hit
            status = e.get("entity_status", "active")
            parent = e.get("parent")
            children = e.get("children", [])
            lines = []
            if parent:
                p = byid.get(parent["id"])
                if p:
                    lines.append('この名義は **%s** に付随する属性・側面（relation: %s）として統合されています。親実体: [[%s|%s]]。'
                                 % (p["canonical"], parent.get("relation", "aspect"), p["id"], p["canonical"]))
            if status == "generic":
                lines.append('この名義は一般名詞・場面名称と判定され、**実体台帳の統合対象外**です（記録として ID のみ保持）。')
            if status == "needs":
                lines.append('この名義は実体判定**要検証**（台帳 v3 で保留）です。')
            if children:
                ch = "、".join("**%s**" % (byid[c["id"]]["canonical"])
                              for c in children if c["id"] in byid)
                lines.append('この実体が所有する下位エンティティ: %s。' % ch)
            lines.append('この名義は L2 名前統合台帳の正規エンティティ **%s**（ID `%s` / kind: %s / 統合根拠: %s）に対応します。'
                         '表記ゆれ・別名の名義変換は [名義変換表](/AllusionistWiki2/reflections/RF_l2_aliases_index)、'
                         '統合グループ一覧は [名相関索引](/AllusionistWiki2/reflections/RF_l2_correlations) を参照。'
                         % (e["canonical"], e["id"], e["kind"], e.get("merge_evidence", "-")))
            sec = ('<!-- AUTO-GENERATED:l2ref -->\n## L2 台帳対応\n\n'
                   + "\n\n".join(lines) +
                   '\n<!-- /AUTO-GENERATED:l2ref -->')
            if block_pat.search(t):
                t = block_pat.sub(sec, t)
            else:
                t = t.rstrip() + "\n\n" + sec + "\n"
            n_ref += 1
        elif block_pat.search(t):
            t = block_pat.sub("", t)

        if t != orig:
            p.write_text(t, encoding="utf-8")
    print("dedup_pages=%d first_appearance_synced=%d l2ref_sections=%d" % (n_dedup, n_fs, n_ref))
    print("=== FIX ENTITY PAGES L2REF DONE ===")


if __name__ == "__main__":
    main()
