---
schema_version: "5.1"
id: layers-index
title: 下層Wiki索引
type: index
description: 解析層（L1・L2・L3…）から生成される下層Wikiの索引。表示（最新）層の下に並列で増やす
date: 2026-10-14
---

# 下層Wiki索引

下層Wikiは `AllusionistWiki_work` の各解析層（L1, L2, L3…）の産出物から生成され、表示（最新）層の下に**並列**で配置されます。各下層Wikiは来歴（run ID・facts・審査根拠）を辿る起点です。

## 一覧

- **[L1Wiki](https://allusionistwiki.github.io/AllusionistWiki2/l1/)** — L1 層（機械抽出メイン）。claims / mysteries / references / deferrals / appearances / entities / arcs / episodes。大半が llm_verified、human_verified 昇格中
- **L2Wiki（準備中）** — L2 層（エンティティ台帳）。entities.json＋確度ラベルを起点にしたキャラ・対象の台帳Wiki
- **L3Wiki（準備中）** — L3 層（上位統合）。mysteries・arcs・関係性をフックにした統合記事のWiki

## 生成構造

```
表示（最新）層（サイト直下）
└─ 下層Wiki（並列）
   ├─ L1Wiki  /l1/  ← 稼働中
   ├─ L2Wiki  /l2/  ← 準備中
   └─ L3Wiki  /l3/  ← 準備中
```

- 各下層Wikiは対応する work 層の run 産出物から生成し、来歴チェーン（L7→L3→L2→L1→L0 ¶N）を切る
- 追加手順: work 層の産出物 → 生成器 → vault 内下層ツリー → CI が Wiki2 配下へ配置

## 関連

- 表示（最新）層: [サイトトップ](https://allusionistwiki.github.io/AllusionistWiki2/)
- 作業データ（facts/candidates 等の生データ）: [AllusionistWiki_work](https://github.com/allusionistwiki/AllusionistWiki_work)
- 階層モデル（L0〜L7）: [DESIGN_NOTES](https://github.com/allusionistwiki/AllusionistWiki_obsidian/blob/main/DESIGN_NOTES.md)
