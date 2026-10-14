---
schema_version: "5.1"
id: layers/index
title: 下層Wiki索引
description: L0〜L7 階層モデル（DESIGN_NOTES 準拠）に基づく下層Wiki（L1〜L6）の索引。入口は L7（表示＝最新層）
date: 2026-10-14
---

# 下層Wiki索引

本 Wiki の**表示（最新）層（サイト直下）は L7（人間訂正済み公開層）**です。パイプラインの各層（L1〜L6）の産出物は**下層Wiki として並列公開**します（公開範囲方針: L1〜L7 すべて公開。L0 原文のみ非公開）。各下層Wiki は来歴（run ID・facts・審査根拠）を辿る起点です。

## 一覧（L0〜L7 階層モデル準拠）

| 層 | 下層Wiki | 内容（DESIGN_NOTES / work README 準拠） | 状態 |
|---|---|---|---|
| L1 | **[L1Wiki](https://allusionistwiki.github.io/AllusionistWiki2/l1/)** | 機械抽出メイン（facts / candidates / 審査データ）。claims / mysteries / references / deferrals / appearances / entities / arcs / episodes | **稼働中** |
| L2 | L2Wiki | 名前統合・prefix 修正 — **正規化済みエンティティ台帳**（安定 ID・aliases・kind・first_seen L0 アンカー・`l1_refs` 来歴、統合根拠の確度ラベル必須） | 準備中 |
| L3 | L3Wiki | 整合性検証 — **検証済みクレーム集**（クレームの矛盾・重複検証） | 準備中 |
| L4 | L4Wiki | LLM 単話内容整理（1話ごとの機械整理） | 準備中 |
| L5 | L5Wiki | 各話統合内容整理（複数話にまたがる機械整理） | 準備中 |
| L6 | L6Wiki | 内容統合（全体統合） | 準備中 |
| L7 | 表示（最新）層（サイト直下） | 人間訂正・整理済み公開層 | **稼働中** |
| L0 | （非公開） | raw 原文 — `AllusionistWiki_raw`（private repo）。参照は manifest ID + chNNNNN + ¶N | private |

## 生成構造

```
表示（最新）層 = L7（サイト直下・入口）
└─ 下層Wiki（L1〜L6 を並列公開）
   ├─ L1Wiki  /l1/  ← 稼働中
   ├─ L2Wiki  /l2/  ← 準備中
   ├─ L3Wiki  /l3/  ← 準備中
   ├─ L4Wiki  /l4/  ← 準備中
   ├─ L5Wiki  /l5/  ← 準備中
   └─ L6Wiki  /l6/  ← 準備中
```

- 層は 2 つの梯子: **L1→L2→L3 は処理段階**（抽出→正規化→検証）、**L4→L5→L6 は粒度**（単話→複数話→全体）。層は処理名でなく**産出物名**で持つ（L2=正規化済みエンティティ台帳、L3=検証済みクレーム集）
- 来歴チェーン: L7 クレーム → L3 run → L2 run → L1 run（`run.json.derived_from`）→ L0（manifest ID + chNNNNN + ¶N）。連鎖を切らない
- 追加手順: `work/<層>/runs/` の産出物 → 生成器 → vault 内下層ツリー（`wiki/<層>/`）→ CI が Wiki2 配下へ配置 → 本索引に追記

## 関連

- 表示（最新）層: [サイトトップ](https://allusionistwiki.github.io/AllusionistWiki2/)
- 作業データ（facts/candidates 等の生データ）: [AllusionistWiki_work](https://github.com/allusionistwiki/AllusionistWiki_work)
- 階層モデル（L0〜L7）の仕様書: [DESIGN_NOTES](https://github.com/allusionistwiki/AllusionistWiki_obsidian/blob/main/DESIGN_NOTES.md)・[work README](https://github.com/allusionistwiki/AllusionistWiki_work/blob/main/README.md)
