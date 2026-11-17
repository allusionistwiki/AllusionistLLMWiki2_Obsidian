---
title: "L2Wiki"
id: "L2_WIKI_TOP"
kind: "index"
created: "2026-10-28"
updated: "2026-11-16"
l2_run: "20261116T1700_v144"
---
# L2Wiki — 名前統合・正規化 Wiki

L1 wiki の全ページに**名前統合・正規化処理を適用した解析層 wiki** です。同じ名前の人（别名・隠れ名・呼び方の変遷）を代表名に統合した本文と、その判断根拠（来歴・監査）を辿れる構造になっています。

- 正規化 wiki に入る: [正規化Wiki 索引](https://allusionistwiki.github.io/AllusionistWiki2/L2/)
- 台帳 run: `20261116T1700_v144`（生成規則の中心）

## 正規化 wiki（メイン構造）

L1 全 16573 ページのミラー（同一相対パス）。高確度帯の别名→代表名のみ本文を置換し、各ページ末尾に置換監査表（元名義→代表名・確度・件数）を付けています。要検証・needs 系は置換せず注記に留め、過剰統合を避けています。

## 入り口

L1 と同一のセクション構造です（内容は名前統合・正規化処理適用済み）。

- **層索引（L1/L2 の並び）** → [層索引](https://allusionistwiki.github.io/AllusionistWiki2/layers/)
- ★ [ポータル（全 Wiki 統合索引）](https://allusionistwiki.github.io/) — 本組織の全 Wiki 横断の入口
- [正規化索引](normalized.md) — 名前統合の監査・統計・代表名表（本層の主眼）
- [話ナビゲーション](../../../nav/index.md) — 話ごとのアナロジー・伏線一覧（正規化後）
- [登場人物一覧](../../../characters/index.md) — キャラクター入口（主要キャラから各ページへ）
- [関係性マップ](../../../relationships/index.md) — キャラ間の関係グラフ
- [エンティティ総覧](../../../entities/index.md) — 用語・組織・アイテム・モチーフ
- [アナロジークレーム全集](../../../claims/index.md) — 引喩の主張すべて
- [伏線台帳](../../../mysteries/index.md) — 仕掛けられた謎の追跡
- [観測章索引](../../../episodes/index.md) — 章別観測索引（正規化後）
- [章アーク](../../../arcs/index.md) — 章アーク構造
- [外部参照](../../../references/index.md) — 引喩先の現代文化・思想の解説
- [「今はまだ」先延ばし索引](../../../deferrals/index.md) — 原文中の先延ばしモティーフ全箇所
- [キャラ容姿描写索引](../../../appearances/index.md) — 容姿・外見描写のキャラ別索引
- [cycleb 観測再生成層](../../../cycleb/index.md) — 観測再生成チェーンのページ群（589 話・台帳接続）
- 台帳 run: `20261116T1700_v144`（生成規則の中心）

## 統計

- 正規化ミラー: **16573** ページ（L1 と同一相対パス）
- 别名→代表名 本文置換: 高確度帯 **421** 対（全置換件数は [正規化索引](normalized.md) 掲載）
- 台帳: **17469** 实体（高確度置換 421 / 注釈専用 103）

## 読み方と注意

- 各ページ末尾の**置換監査表**（元名義→代表名・確度・件数）で統合の根拠が辿れます。要検証・needs 系は置換せず注記のみ（過剰統合回避）
- 本Wikiの大半の記述は **LLM による自動抽出・自動審査（llm_verified）** です。frontmatter の `review_status` に区別が記録されています
- 原文のネタバレを大量に含むため、**原作未読の方は読まないでください**
- 本Wikiは非公式のファンWikiです。原作の著作権は原作者に帰属します

## 生成規則（台帳・索引）— 本 wiki の一要素

台帳そのものは閲覧対象ではなく、上の正規化 wiki を作るための規則の集合です。

- 正規化エンティティ台帳 総計 17469 实体（terminology 6786, character 4322, item 3793, organization 928, location 675, motif 328, creature 268, relationship 130, event 124, phrase 115）
- 别名統合マッピング: 高確度帯 421 件（置換に適用）/ 要検証・needs 103 件（注記のみ）
- 别名統合一覧: [别名統合一覧（RF_l2_aliases_index）](https://allusionistwiki.github.io/AllusionistWiki2/L2/reflections/RF_l2_aliases_index.html)
- 変換の相関・根拠: [RF_l2_correlations](https://allusionistwiki.github.io/AllusionistWiki2/L2/reflections/RF_l2_correlations.html)
- 台帳の設計・手順: [L2 README（work repo）](https://github.com/allusionistwiki/AllusionistWiki_work/blob/main/work/allusionist_v2/L2/README.md)

## 代表名別 統合例（上位）

| 代表名 | 統合别名数 | 代表例 |
|---|---|---|
| [[./entities/characters/E_char_シナモリアキラ|シナモリアキラ]] | 5 | アキラ殿、品森晶/Akira Shinamori、語り手 |
| [[./entities/characters/E_char_ハルベルト|ハルベルト]] | 4 | 歌姫Spear、歌姫Ｓｐｅａｒ、ハル |
| [[./entities/characters/ME_Organ_Rode|オルガンローデ]] | 3 | 呪文竜、覇竜王滅呪、銀竜草滅呪 |
| [[./entities/characters/E_char_エレクトラ|エレクトラ]] | 3 | ユディーア、キニス、キニスちゃん |
| [[./entities/characters/E_char_ペリュトン|ペリュトン]] | 3 | 青い鳥、ラハブ、枝角有翼の青鹿 |
| [[./entities/characters/E_char_キロン|キロン]] | 3 | 聖騎士、転生者殺し、聖騎士キロン |
| [[./entities/characters/E_char_クナータ|クナータ]] | 3 | 聖女クナータ、聖女、聖女様 |
| [[./entities/characters/E_char_太陰|太陰]] | 3 | イルディアンサ、第四衛星、第四衛星イルディアンサ |
| [[./entities/characters/E_char_エル・ア・フィリス|エル・ア・フィリス]] | 3 | 言理の妖精、エルアフィリスさん、言理の妖精フィリス |
| [[./entities/characters/E_char_再生者|再生者]] | 3 | オルクス、オルクス＝ハイ、高位再生者 |
| [[./entities/characters/E_char_ライブ|ライブ]] | 3 | 儀式呪術、呪術儀式、思い出話 |
| [[./entities/characters/E_char_エミリニェロギッポロネーシャ|エミリニェロギッポロネーシャ]] | 3 | タマ、タマちゃん先生、白黒兎 |
| **植物神レルプレア** | 3 | 朱の翼、マンモス、毛長曲牙象 |
| [[./entities/characters/E_char_オルヴァ|オルヴァ]] | 3 | カシュラム王(オルヴァ)、臣下たち、髭太夫 |
| [[./entities/characters/E_char_楽園|楽園]] | 2 | 洞窟浄界、浄界の神 |
| [[./entities/characters/E_char_ミルーニャ|ミルーニャ]] | 2 | メートリアン、完全祝福者 |
| [[./entities/characters/E_char_呪文|呪文]] | 2 | 疫病型吸血鬼、じんぶんかがく |
| [[./entities/characters/E_char_邪視|邪視]] | 2 | 色付き視線、まなざし |
| [[./entities/characters/E_char_ゼド|ゼド]] | 2 | 盗賊王ゼド、【盗賊王】 |
| [[./entities/characters/E_char_スカルミリオーネ|スカルミリオーネ]] | 2 | ルバーブ様、乱髪 |

## 他層への導線

- 観測元（L1 原文 Wiki・表示層）: [https://allusionistwiki.github.io/AllusionistWiki2/](https://allusionistwiki.github.io/AllusionistWiki2/) / [L1 下位層](https://allusionistwiki.github.io/AllusionistWiki2/L1/)
- 层索引（L2Wiki 系統の一覧）: [https://allusionistwiki.github.io/AllusionistWiki2/layers/](https://allusionistwiki.github.io/AllusionistWiki2/layers/)
- 作業データ（facts/candidates 生データ）: [AllusionistWiki_work](https://github.com/allusionistwiki/AllusionistWiki_work)

## 来歴

L7 観測 → L3 審査 → L2 名前統合（本台帳）→ **正規化 wiki 生成（本層）** → L1 原文（対照）。台帳 run の来歴・run.json は work repo の `work/allusionist_v2/L2/runs/20261116T1700_v144/` に格納。
