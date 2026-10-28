"""S7 段: L2Wiki 入口ページ（トップ）を生成する。

構成方針（2026-10-28）:
- 公開対象の主眼は「L1 wiki へ名前統合・正規化処理を適用した wiki 構造（正規化 wiki）」。
  正規化エンティティ台帳は本 wiki の生成規則の一要素であり、トップは台帳中心にしない。
- トップ = 正規化 wiki への入口（統計・監査・利用規約）＋ 生成規則（台帳・别名索引・
  相関索引）への入口節 ＋ 他層への導線。
- 表示は frontmatter の aliases（代表名）で解決できる代表名リンクを使う。
- 台帳の統計値・代表名グループは台帳 JSON から機械的に生成する。
"""
import json
import re
import sys
import datetime
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "wiki" / "l2" / "index.md"
LEDGER = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_work")
NORM = ROOT / "wiki" / "l2"

HIGH = {"高", "明言", "表記一致", "蓋然性高"}
SITE = "https://allusionistwiki.github.io/AllusionistWiki2"


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

    kind_counter = Counter(e.get("kind") or "未分類" for e in entities)
    canon_groups = {}
    for a, (c, conf, eid) in alias_map.items():
        canon_groups.setdefault(c, []).append((a, conf))

    # 代表名 -> ページ stem（frontmatter title 一致）
    title_to_stem = {}
    for p in NORM.rglob("*.md"):
        if p == NORM / "index.md":
            continue  # 入口自身の title に自己対応させない
        text = p.read_text(encoding="utf-8", errors="replace")
        fm_m = re.match(r"^---\n(.*?\n)---\n", text, re.S)
        if fm_m:
            t_m = re.search(r"^title:\s*(.+)$", fm_m.group(1), re.M)
            if t_m:
                t = t_m.group(1).strip().strip("'\"")
                title_to_stem.setdefault(t, p.stem)

    norm_count = len(list(NORM.rglob("*.md")))
    today = datetime.date.today().isoformat()

    fm = (f'---\ntitle: "L2Wiki"\nid: "L2_WIKI_TOP"\nkind: "index"\n'
          f'created: "2026-10-28"\nupdated: "{today}"\nl2_run: "{run_id}"\n---\n')
    body = f"""# L2Wiki — 名前統合・正規化 Wiki

L1 wiki の全ページに**名前統合・正規化処理を適用した解析層 wiki** です。同じ名前の人（别名・隠れ名・呼び方の変遷）を代表名に統合した本文と、その判断根拠（来歴・監査）を辿れる構造になっています。

- 正規化 wiki に入る: [正規化Wiki 索引]({SITE}/L2/)
- 台帳 run: `{run_id}`（生成規則の中心）

## 正規化 wiki（メイン構造）

L1 全 {norm_count} ページのミラー（同一相対パス）。高確度帯の别名→代表名のみ本文を置換し、各ページ末尾に置換監査表（元名義→代表名・確度・件数）を付けています。要検証・needs 系は置換せず注記に留め、過剰統合を避けています。

- 正規化 wiki 索引: [{SITE}/L2/]({SITE}/L2/)
- 登場人物（正規化後）: [{SITE}/L2/characters/]({SITE}/L2/characters/)
- 容姿描写（正規化後）: [{SITE}/L2/appearances/]({SITE}/L2/appearances/)

## 生成規則（台帳・索引）— 本 wiki の一要素

台帳そのものは閲覧対象ではなく、上の正規化 wiki を作るための規則の集合です。

- 正規化エンティティ台帳 総計 {len(entities)} 实体（{', '.join(f'{k} {v}' for k, v in kind_counter.most_common())}）
- 别名統合マッピング: 高確度帯 {len(alias_map)} 件（置換に適用）/ 要検証・needs {len(low_map)} 件（注記のみ）
- 别名統合一覧: [别名統合一覧（RF_l2_aliases_index）]({SITE}/L2/reflections/RF_l2_aliases_index/)
- 変換の相関・根拠: [RF_l2_correlations]({SITE}/L2/reflections/RF_l2_correlations/)
- 台帳の設計・手順: [L2 README（work repo）](https://github.com/allusionistwiki/AllusionistWiki_work/blob/main/work/allusionist_v2/L2/README.md)

## 代表名別 統合例（上位）

| 代表名 | 統合别名数 | 代表例 |
|---|---|---|
"""
    for c, lst in sorted(canon_groups.items(), key=lambda kv: -len(kv[1]))[:20]:
        stem = title_to_stem.get(c)
        cell = f"[[{stem}|{c}]]" if stem else f"**{c}**"
        ex = "、".join(a for a, _ in lst[:3])
        body += f"| {cell} | {len(lst)} | {ex} |\n"

    body += f"""
## 他層への導線

- 観測元（L1 原文 Wiki・表示層）: [{SITE}/]({SITE}/) / [L1 下位層]({SITE}/L1/)
- 层索引（L2Wiki 系統の一覧）: [{SITE}/layers/]({SITE}/layers/)
- 作業データ（facts/candidates 生データ）: [AllusionistWiki_work](https://github.com/allusionistwiki/AllusionistWiki_work)

## 来歴

L7 観測 → L3 審査 → L2 名前統合（本台帳）→ **正規化 wiki 生成（本層）** → L1 原文（対照）。台帳 run の来歴・run.json は work repo の `work/allusionist_v2/L2/runs/{run_id}/` に格納。
"""
    OUT.write_text(fm + body, encoding="utf-8")
    print(json.dumps({
        "written": str(OUT),
        "entities": len(entities),
        "applied_pairs": len(alias_map),
        "annotate_pairs": len(low_map),
        "norm_pages": norm_count,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
