"""S6 段: L2 台帳 → 下層Wiki L2（index.md + 相関索引ページ）を vault wiki/l2/ へ生成。

Usage: python scripts/build_l2_pages.py <work_run_id>
Reads : work repo runs/<id>/{entities.json, clusters*.jsonl(裁定), rejected-candidates.jsonl}
Writes: vault wiki/l2/index.md（統計・見方・データ所在）
        vault wiki/l2/correlations.md（統合済み名相関グループ一覧・kind・確度）
        vault wiki/l2/aliases-index.md（名義→正規ID 転換表・上位）
"""
import json
import sys
import collections
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
WIKI = Path(__file__).resolve().parents[1] / "wiki"
WORK_RUNS = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_work") / "work" / "allusionist_v2" / "L2" / "runs"

KIND_LABEL = {"character": "キャラクター", "terminology": "用語", "item": "アイテム",
              "organization": "組織", "location": "場所", "motif": "モティーフ",
              "phrase": "フレーズ", "event": "事件", "creature": "生物",
              "relationship": "関係", "?": "未分類"}


def main():
    if len(sys.argv) < 2:
        print("usage: build_l2_pages.py <work_run_id>")
        sys.exit(2)
    run_id = sys.argv[1]
    rd = WORK_RUNS / run_id
    data = json.loads((rd / "entities.json").read_text(encoding="utf-8"))
    ents = data["entities"]

    kinds = collections.Counter(e["kind"] for e in ents)
    merged = [e for e in ents if len(e.get("aliases", [])) > 1]
    merged.sort(key=lambda e: -len(e["aliases"]))
    with_alias = sum(len(e["aliases"]) - 1 for e in merged)
    conf = collections.Counter(e.get("merge_evidence", "?") for e in merged)
    kind_conf = collections.Counter(e.get("kind_confidence", "?") for e in ents)

    out = WIKI / "l2"
    out.mkdir(exist_ok=True)
    REFL = WIKI / "reflections"
    REFL.mkdir(exist_ok=True)
    today = __import__("datetime").date.today().isoformat()


    v3n={"aspect_of":0,"generic":0,"needs":0}
    for e in ents:
        if e.get("parent"): v3n["aspect_of"]+=1
        if e.get("entity_status")=="generic": v3n["generic"]+=1
        if e.get("entity_status")=="needs": v3n["needs"]+=1
    parents=[e for e in ents if e.get("children")]
    nchild=sum(len(c["id"]) and 1 for e in parents for c in e["children"])
    # ---- index.md ----------------------------------------------------------
    idx = ["---", 'schema_version: "5.1"', "id: l2/index",
           "title: L2 名前統合台帳（下層Wiki）",
           "description: L1 名義を統合した正規化エンティティ台帳。名相関グループと統合/kind 裁定の確定結果。",
           "type: index", "date: %s" % today, "---", ""]
    idx += [
        "# L2 — 名前統合・正規化層（下層Wiki）",
        "",
        "L1（機械抽出）の名義ゆらぎを統合した**正規化エンティティ台帳**です。生成 run と設計:",
        "- 設計・実行計画: [work L2 README](https://github.com/allusionistwiki/AllusionistWiki_work/blob/main/work/allusionist_v2/L2/README.md)",
        "- 生成 run: `%s`（来歴: L1 run 和集合 → L0 ¶N）" % run_id,
        "- 台帳データ（機械読取）: [entities.json](https://github.com/allusionistwiki/AllusionistWiki_work/tree/main/work/allusionist_v2/L2/runs/%s)" % run_id,
        "",
        "## 統計",
        "",
        "| 項目 | 値 |",
        "|---|---|",
        "| 台帳エンティティ数 | %d |" % len(ents),
        "| 統合名義数（aliases 追加） | %d |" % with_alias,
        "| 複数名義を持つ実体 | %d |" % len(merged),
        "| 統合確度内訳 | %s |" % " / ".join("%s %d" % (k, c) for k, c in conf.most_common()),
        "| kind 内訳 | %s |" % " / ".join("%s %d" % (KIND_LABEL.get(k, k), c) for k, c in kinds.most_common()),
        "| 実体判定 v3（付随/一般名詞/保留） | %d / %d / %d |" % (v3n["aspect_of"], v3n["generic"], v3n["needs"]),
        "| 親子構造 | 親 %d 実体・子 %d 件 |" % (len(parents), nchild),
        "",
        "## 見方",
        "",
        "- **安定 ID**: 公開済み `E_*` ID は不変の canonical。統合は aliases 移動のみ（ID 再発行なし）。",
        "- **確度ラベル**: 各統合は 明言 / 蓋然性高 / 要検証 を持つ（要検証は再裁定対象）。",
        "- **来歴**: 台帳の `l1_refs`（run:facts/ch#fact_id）から L1 fact → L0（chNNNNN + ¶N）へ辿れる。",
        "- 関連語（X選・都市X 等）は統合せず関係として `relations.jsonl` に保持。",
        "",
        "## ページ",
        "",
        "- [名相関索引](../reflections/RF_l2_correlations.md) — 統合済みグループ一覧（代表名 ← 統合名義・kind・確度）",
        "- [名義変換表](../reflections/RF_l2_aliases_index.md) — L1 素名義 → 正規 ID の照会表（上位）",
        "",
    ]
    (out / "index.md").write_text("\n".join(idx), encoding="utf-8")

    # ---- correlations.md ---------------------------------------------------
    body = ["---", 'schema_version: "5.1"', "id: RF_l2_correlations",
            "title: 名相関索引（統合済みグループ）",
            "description: 名前の相関と統合の裁定結果。代表名に統合された全名義・kind・確度を大型グループから掲載。",
            "type: reflection", 'created: "%s"' % today, "tags: []", "---", "",
            "# 名相関索引",
            "",
            "統合名義数の多いグループから掲載（生成: build_l2_pages.py / run `%s`）。全件は台帳データ参照。" % run_id,
            "確度: 明言=原文明言の同一性 / 蓋然性高=表記・文脈からの高確度統合 / 要検証=再裁定対象。",
            ""]
    n_page = min(len(merged), 1200)
    for e in merged[:n_page]:
        k = KIND_LABEL.get(e["kind"], e["kind"])
        al = ", ".join(
            ("`%s`〔%s・%s〕" % (a["name"], a.get("confidence", "?"), a.get("source", "?")))
            if isinstance(a, dict) else "`%s`" % a
            for a in e["aliases"] if (a["name"] if isinstance(a, dict) else a) != e["canonical"])
        line = "- **%s**（`%s`／%s／確度: %s）← %s" % \
               (e["canonical"], e["id"], k, e.get("merge_evidence", "?"), al)
        kids = e.get("children") or []
        if kids:
            line += "\n  - 付随属性（子）: %s" % ", ".join(
                "**%s**" % (c.get("name") or c.get("id")) for c in kids[:20])
        parent = e.get("parent")
        if parent:
            line += "\n  - 親実体: `%s`（%s／確度: %s）" % \
                    (parent.get("id"), parent.get("relation", "aspect"),
                     parent.get("confidence", "?"))
        body.append(line)
    body += ["", "（掲載 %d / 統合済み %d 件・全件は台帳データ）" % (n_page, len(merged)), ""]
    (REFL / "RF_l2_correlations.md").write_text("\n".join(body), encoding="utf-8")

    # ---- aliases-index.md --------------------------------------------------
    def aname(a):
        return a["name"] if isinstance(a, dict) else a
    rows = []
    for e in merged:
        for a in e["aliases"]:
            nm = aname(a)
            if nm != e["canonical"]:
                rows.append((nm, e, a if isinstance(a, dict) else {}))
    rows.sort(key=lambda t: (-len(t[1]["aliases"]), t[0]))
    body = ["---", 'schema_version: "5.1"', "id: RF_l2_aliases_index",
            "title: 名義変換表（L1 素名義 → 正規 ID）",
            "description: L1 facts に現れた名義がどの正規実体へ統合されたかの照会表。確度・根拠・検証点付き。",
            "type: reflection", 'created: "%s"' % today, "tags: []", "---", "",
            "# 名義変換表",
            "",
            "確度: 明言=原文同一性の直接観測 / 蓋然性高=全話証拠裁定（v2） / 表記一致=正規化同一 / 要検証=根拠未確認（検証点参照）。",
            "検証点は統合前に確認すべき事項。引用は根拠となった章の段落。",
            "",
            "| 名義 | 正規 ID | 代表名 | kind | 確度 | 根拠 | 検証点 |",
            "|---|---|---|---|---|---|---|",
            ""]
    def esc(s):
        return str(s).replace("|", "｜").replace("\n", " ")[:140]
    for nm, e, a in rows[:5000]:
        cites = a.get("cites") or []
        cite_md = " ".join("[`%s¶%s`](https://allusionistwiki.github.io/AllusionistWiki/episodes/%s/)"
                           % (c[0], c[1], c[0]) for c in cites[:2])
        basis = "%s：%s" % (a.get("source", "?"), esc(a.get("reason", "")))
        verify = "；".join(esc(v) for v in (a.get("verify") or [])) or "—"
        body.append("| %s | `%s` | %s | %s | %s | %s %s | %s |" %
                    (esc(nm), e["id"], esc(e["canonical"]),
                     KIND_LABEL.get(e["kind"], e["kind"]),
                     a.get("confidence", "?"), esc(basis), cite_md, esc(verify)))
    body += ["", "（掲載 %d / %d 行）" % (min(len(rows), 5000), len(rows)), ""]
    (REFL / "RF_l2_aliases_index.md").write_text("\n".join(body), encoding="utf-8")

    print("[done] pages=3 entities=%d merged=%d alias_rows=%d" % (len(ents), len(merged), len(rows)))
    print("=== BUILD L2 PAGES DONE ===")


if __name__ == "__main__":
    main()
