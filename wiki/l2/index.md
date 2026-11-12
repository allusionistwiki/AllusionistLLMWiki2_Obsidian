---
schema_version: "5.1"
id: l2/index
title: L2 名前統合台帳（下層Wiki）
description: L1 名義を統合した正規化エンティティ台帳。名相関グループと統合/kind 裁定の確定結果。
type: index
date: 2026-11-13
---

# L2 — 名前統合・正規化層（下層Wiki）

L1（機械抽出）の名義ゆらぎを統合した**正規化エンティティ台帳**です。生成 run と設計:
- 設計・実行計画: [work L2 README](https://github.com/allusionistwiki/AllusionistWiki_work/blob/main/work/allusionist_v2/L2/README.md)
- 生成 run: `20261113T1230_v10`（来歴: L1 run 和集合 → L0 ¶N）
- 台帳データ（機械読取）: [entities.json](https://github.com/allusionistwiki/AllusionistWiki_work/tree/main/work/allusionist_v2/L2/runs/20261113T1230_v10)

## 統計

| 項目 | 値 |
|---|---|
| 台帳エンティティ数 | 17337 |
| 統合名義数（aliases 追加） | 499 |
| 複数名義を持つ実体 | 363 |
| 統合確度内訳 | 明言 195 / 蓋然性高 151 / 要検証 17 |
| kind 内訳 | 用語 6755 / キャラクター 4277 / アイテム 3768 / 組織 920 / 場所 660 / モティーフ 328 / 生物 260 / 関係 130 / 事件 124 / フレーズ 115 |
| 実体判定 v3（付随/一般名詞/保留） | 462 / 958 / 37 |
| 親子構造 | 親 190 実体・子 1616 件 |

## 見方

- **安定 ID**: 公開済み `E_*` ID は不変の canonical。統合は aliases 移動のみ（ID 再発行なし）。
- **確度ラベル**: 各統合は 明言 / 蓋然性高 / 要検証 を持つ（要検証は再裁定対象）。
- **来歴**: 台帳の `l1_refs`（run:facts/ch#fact_id）から L1 fact → L0（chNNNNN + ¶N）へ辿れる。
- 関連語（X選・都市X 等）は統合せず関係として `relations.jsonl` に保持。

## ページ

- [名相関索引](../reflections/RF_l2_correlations.md) — 統合済みグループ一覧（代表名 ← 統合名義・kind・確度）
- [名義変換表](../reflections/RF_l2_aliases_index.md) — L1 素名義 → 正規 ID の照会表（上位）
