"""S7 補助: L2 正規化 wiki の入口 index を生成（生成規則・統計・監査集計）。"""
import json
import re
import sys
import datetime
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "wiki" / "l2" / "normalized"
LEDGER = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_work")

HIGH = {"高", "明言", "表記一致", "蓋然性高"}


def main():
    run_id = sys.argv[1]
    doc = json.load(open(LEDGER / f"work/allusionist_v2/L2/runs/{run_id}/entities.json", encoding="utf-8"))
    entities = doc["entities"]

    alias_map, low_map = {}, {}
    for e in entities:
        canon, eid = e["canonical"], e["id"]
        for a in e.get("aliases", []):
            if isinstance(a, str):
                n, c = a, ""
            else:
                n, c = a.get("name"), a.get("confidence", "")
            if not n or n == canon:
                continue
            if c in HIGH:
                alias_map.setdefault(n, (canon, c, eid))
            else:
                if n not in alias_map:
                    low_map.setdefault(n, (canon, c))

    pages = sorted(p for p in OUT.rglob("*.md"))
    page_count = len(pages)
    audit_pages = 0
    banner_pages = 0
    total_repl = 0
    conf_counter = Counter()
    pair_counter = Counter()
    title_to_stem = {}
    for p in pages:
        text = p.read_text(encoding="utf-8")
        fm_m = re.match(r"^---\n(.*?\n)---\n", text, re.S)
        if fm_m:
            t_m = re.search(r"^title:\s*(.+)$", fm_m.group(1), re.M)
            if t_m:
                t = t_m.group(1).strip().strip("'\"")
                title_to_stem.setdefault(t, p.stem)
        m = re.search(r"## 名前正規化監査[^\n]*\n\n\| 元名義.*?\n\|---.*?\n((?:\|.*\n)*)", text)
        if m:
            audit_pages += 1
            for row in re.findall(r"^\| (.+?) \| (.+?) \| (.+?) \| (\d+) \|$", m.group(1), re.M):
                a, c, conf, n = row
                total_repl += int(n)
                conf_counter[conf] += int(n)
                pair_counter[(a, c, conf)] += int(n)
        if "名前統合（L2 run" in text:
            banner_pages += 1

    today = datetime.date.today().isoformat()
    fm = f'---\ntitle: "L2 正規化Wiki 索引"\nid: "L2_NORMALIZED_INDEX"\nkind: "index"\ncreated: "{today}"\nupdated: "{today}"\nl2_run: "{run_id}"\n---\n'
    body = f"""# L2 正規化Wiki（L1 への名前統合・正規化処理の適用結果）

[L2 台帳（生成規則の中心）](https://allusionistwiki.github.io/AllusionistWiki2/l2/) · [别名統合一覧](https://allusionistwiki.github.io/AllusionistWiki2/l2/reflections/RF_l2_aliases_index/) · [L1 原文 Wiki](https://allusionistwiki.github.io/AllusionistWiki2/l1/)

- 生成 run: `{run_id}`（L2 台帳 run 由来。台帳は本 wiki の**生成規則の一要素**であり、公開対象はこの正規化 wiki 構造）
- 対象: L1 全ページ {page_count} のミラー（同一相対パス）
- 置換を適用したページ: {audit_pages}（総置換 {total_repl} 件）/ 別名統合バナー: {banner_pages}
- 確度帯（適用済みの別名→代表名マッピング {len(alias_map)} 件）: {', '.join(f'{k} {v}' for k, v in conf_counter.most_common())}
- **適用しない帯域**: 要検証・needs 系の別名 {len(low_map)} 件は本文を元のままにし、ページ内「注記（置換しない）」にのみ表示
- 監査: 各ページ末尾の「名前正規化監査」表に 元名義→代表名・確度・件数 を列挙（来歴: L2 台帳 → 変換規則 → 本ページ）
- 代表名別 → 統合された别名の一覧（上位）:

| 代表名 | 統合别名数 | 代表例 |
|---|---|---|
"""
    canon_groups = {}
    for a, (c, conf, eid) in alias_map.items():
        canon_groups.setdefault(c, []).append((a, conf))
    for c, lst in sorted(canon_groups.items(), key=lambda kv: -len(kv[1]))[:50]:
        ex = "、".join(a for a, _ in lst[:3])
        stem = title_to_stem.get(c)
        cell = f"[[{stem}|{c}]]" if stem else f"**{c}**"
        body += f"| {cell} | {len(lst)} | {ex} |\n"
    (OUT / "index.md").write_text(fm + body, encoding="utf-8")
    print(json.dumps({
        "pages": page_count,
        "audit_pages": audit_pages,
        "banner_pages": banner_pages,
        "total_replacements": total_repl,
        "applied_alias_pairs": len(alias_map),
        "annotate_only_pairs": len(low_map),
        "canon_groups": len(canon_groups),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
