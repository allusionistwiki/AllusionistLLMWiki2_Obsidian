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

- [正規化索引（normalized.md）](https://allusionistwiki.github.io/AllusionistWiki2/L2/normalized.html) — 名前統合の監査・統計・代表名表
- [話ナビゲーション(https://allusionistwiki.github.io/AllusionistWiki2/L2/nav/index.html) — 話ごとのアナロジー・伏線一覧（正規化後）
- [登場人物一覧(https://allusionistwiki.github.io/AllusionistWiki2/L2/characters/index.html) — キャラクター入口（正規化後）
- [関係性マップ(https://allusionistwiki.github.io/AllusionistWiki2/L2/relationships/index.html) — キャラ間の関係グラフ（正規化後）
- [エンティティ総覧(https://allusionistwiki.github.io/AllusionistWiki2/L2/entities/index.html) — 用語・組織・アイテム・モチーフ（正規化後）
- [アナロジークレーム全集(https://allusionistwiki.github.io/AllusionistWiki2/L2/claims/index.html) — 引喩の主張すべて（正規化後）
- [伏線台帳(https://allusionistwiki.github.io/AllusionistWiki2/L2/mysteries/index.html) — 仕掛けられた謎の追跡（正規化後）
- [観測章索引(https://allusionistwiki.github.io/AllusionistWiki2/L2/episodes/index.html) — 章別観測索引（正規化後）
- [アーカイブ(https://allusionistwiki.github.io/AllusionistWiki2/L2/arcs/index.html) — 章アーク構造
- [外部参照(https://allusionistwiki.github.io/AllusionistWiki2/L2/references/index.html) — 引喩先の現代文化・思想の解説（正規化後）
- [「今はまだ」先延ばし索引(https://allusionistwiki.github.io/AllusionistWiki2/L2/deferrals/index.html) — 原文中の先延ばしモティーフ（正規化後）
- [キャラ容姿描写索引(https://allusionistwiki.github.io/AllusionistWiki2/L2/appearances/index.html) — 容姿・外見描写のキャラ別索引（正規化後）
- 台帳 run: `20261116T1700_v144`（生成規則の中心）

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
