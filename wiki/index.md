---
title: L1 解析層（旧 LLMWiki2）
id: index
description: LLM 自動抽出・自動審査の解析フック層。アナロジー/エンティティ/外部参照の機械抽出データ
---

# L1 解析層（旧 LLMWiki2）

この層は **L1（機械抽出メイン）** の解析フックです。大半の記述は **LLM による自動抽出・自動審査（llm_verified）** で、人間レビュー済み（human_verified）への昇格が進行中。レビュー済みは本Wiki本体（人間訂正済み公開層 `/AllusionistWiki/`）に反映されています。

- 来歴: 2026-10-12 に独立サイト `AllusionistLLMWiki2` から L1 層として格下げ・統合
- 作業データ（facts / candidates 等の生データ）: [AllusionistWiki_work](https://github.com/allusionistwiki/AllusionistWiki_work)
- 階層モデル（L0〜L7）: [DESIGN_NOTES](https://github.com/allusionistwiki/AllusionistWiki_obsidian/blob/main/DESIGN_NOTES.md)

## 入り口

- [話ナビゲーション](./nav/) — 話ごとのアナロジー・伏線一覧（第1話〜）
- [登場人物一覧](./characters/) — キャラクター入口（主要キャラから各ページへ）
- [関係性マップ](./relationships/) — キャラ間の関係グラフ
- [エンティティ総覧](./entities/) — 用語・組織・アイテム・モチーフ
- [アナロジークレーム全集](./claims/) — 引喩の主張すべて
- [伏線台帳](./mysteries/) — 仕掛けられた謎の追跡
- [外部参照](./references/) — 引喩先の現代文化・思想の解説
- [「今はまだ」先延ばし索引](./deferrals/) — 原文中の先延ばしモティーフ全箇所
- [キャラ容姿描写索引](./appearances/) — 容姿・外見描写のキャラ別索引
- [アーク解析](./arcs/) — 章・アーク単位の機械抽出
- [エピソード機械データ](./episodes/) — 話単位の抽出データ
- [感想機械データ](./reflections/) — 機械抽出の感想データ

## 統計

- 解析済み: **第1話〜第272話**（272 話）
- アナロジークレーム: **1106** 件
- 伏線: **495** 件
- 外部参照ページ: **1060** 件

## 読み方と注意

- 各クレームページは「主張 → 原文引用 → LLM 審査根拠」の順で読めます
- 原文のネタバレを大量に含むため、**原作未読の方は読まないでください**
- 本Wikiは非公式のファンWikiです。原作の著作権は原作者に帰属します
