---
title: "L2Wiki"
id: "L2_WIKI_TOP"
kind: "index"
created: "2026-10-28"
updated: "2026-10-29"
l2_run: "20261029T0843_c8bb"
---
# L2Wiki — 名前統合・正規化 Wiki

L1 wiki の全ページに**名前統合・正規化処理を適用した解析層 wiki** です。同じ名前の人（别名・隠れ名・呼び方の変遷）を代表名に統合した本文と、その判断根拠（来歴・監査）を辿れる構造になっています。

- 正規化 wiki に入る: [正規化Wiki 索引](https://allusionistwiki.github.io/AllusionistWiki2/L2/)
- 台帳 run: `20261029T0843_c8bb`（生成規則の中心）

## 正規化 wiki（メイン構造）

L1 全 15982 ページのミラー（同一相対パス）。高確度帯の别名→代表名のみ本文を置換し、各ページ末尾に置換監査表（元名義→代表名・確度・件数）を付けています。要検証・needs 系は置換せず注記に留め、過剰統合を避けています。

## 入り口

L1 と同一のセクション構造です（内容は名前統合・正規化処理適用済み）。

- [正規化索引（normalized.md）](https://allusionistwiki.github.io/AllusionistWiki2/L2/normalized.html) — 名前統合の監査・統計・代表名表
- [話ナビゲーション](nav/index.md) — 話ごとのアナロジー・伏線一覧（正規化後）
- [登場人物一覧](characters/index.md) — キャラクター入口（正規化後）
- [関係性マップ](relationships/index.md) — キャラ間の関係グラフ（正規化後）
- [エンティティ総覧](entities/index.md) — 用語・組織・アイテム・モチーフ（正規化後）
- [アナロジークレーム全集](claims/index.md) — 引喩の主張すべて（正規化後）
- [伏線台帳](mysteries/index.md) — 仕掛けられた謎の追跡（正規化後）
- [観測章索引](episodes/index.md) — 章別観測索引（正規化後）
- [アーカイブ](arcs/index.md) — 章アーク構造
- [外部参照](references/index.md) — 引喩先の現代文化・思想の解説（正規化後）
- [「今はまだ」先延ばし索引](deferrals/index.md) — 原文中の先延ばしモティーフ（正規化後）
- [キャラ容姿描写索引](appearances/index.md) — 容姿・外見描写のキャラ別索引（正規化後）
- 台帳 run: `20261029T0843_c8bb`（生成規則の中心）

## 生成規則（台帳・索引）— 本 wiki の一要素

台帳そのものは閲覧対象ではなく、上の正規化 wiki を作るための規則の集合です。

- 正規化エンティティ台帳 総計 17337 实体（terminology 6536, character 4222, item 3751, organization 918, location 639, motif 325, creature 257, 未分類 239, relationship 124, phrase 115, event 107, skill 11, spell 8, action 8, ability 7, race 6, group 5, magic 4, celestial_body 4, ritual 4, concept 4, place 4, app 3, emotion 3, phantom 3, character_class 2, system 2, role 2, rule 2, technology 2, phenomenon 2, plan 2, deity 1, software 1, spell_effect 1, event_context 1, game 1, part 1, brand 1, character_ability 1, technique 1, clothing 1, structure 1, unknown 1, building 1, institution 1, strategy 1, effect 1）
- 别名統合マッピング: 高確度帯 805 件（置換に適用）/ 要検証・needs 166 件（注記のみ）
- 别名統合一覧: [别名統合一覧（RF_l2_aliases_index）](https://allusionistwiki.github.io/AllusionistWiki2/L2/reflections/RF_l2_aliases_index/)
- 変換の相関・根拠: [RF_l2_correlations](https://allusionistwiki.github.io/AllusionistWiki2/L2/reflections/RF_l2_correlations/)
- 台帳の設計・手順: [L2 README（work repo）](https://github.com/allusionistwiki/AllusionistWiki_work/blob/main/work/allusionist_v2/L2/README.md)

## 代表名別 統合例（上位）

| 代表名 | 統合别名数 | 代表例 |
|---|---|---|
| [[E_char_アキラくん|アキラくん]] | 70 | アキラ、アキラ殿、アキラ（仮称・主語不明） |
| [[E_char_マラード|マラード]] | 12 | マラード王、マラード陛下、王の髪 |
| [[E_char_アズーリア|アズーリア]] | 10 | アズーリア・ヘレゼクシュ、アズ、守護の九槍アズーリア |
| [[E_char_カーイン|カーイン]] | 10 | カーインの残り滓、カーインの瘴気、カーインの脳内 |
| [[E_char_ハルベルト|ハルベルト]] | 8 | 呪文の座、歌姫Spear、歌姫Ｓｐｅａｒ |
| [[ME_Organ_Rode|オルガンローデ]] | 7 | オルゴーの滅びの呪文、呪文竜、滅びの呪文 |
| [[E_char_キロン|キロン]] | 7 | 聖騎士、蝶の翅、転生者殺し |
| [[E_char_カイン|カイン]] | 7 | 狼、男、彼 |
| [[E_char_ミヒトネッセ|ミヒトネッセ]] | 7 | ミヒトネッセ(狂イ姫)、ミヒトネッセ(シナモリアキラ/九尾)、ミヒトネッセ(ゼドへの変身時) |
| [[E_char_ミルーニャ|ミルーニャ]] | 6 | メートリアン、呪文使い、呪文使いの美少女 |
| [[E_char_エレクトラ|エレクトラ]] | 6 | ユディーア、キニス、キニスちゃん |
| [[E_char_ファル|ファル]] | 6 | ファルファレロ、クリミナトレス、中傷者 |
| [[E_char_ペリュトン|ペリュトン]] | 6 | 青い鳥、ラハブ、ペリュトン種族 |
| [[E_char_スカルミリオーネ|スカルミリオーネ]] | 6 | スカルミリョーネ、ルバーブ様、乱髪 |
| [[E_char_フィリス|フィリス]] | 6 | 金鎖、魔将、第一魔将 |
| [[E_char_呪文|呪文]] | 5 | 炸撃、爆撃、言語魔術 |
| [[E_char_カーティス|カーティス]] | 5 | リールエルバ、カーティス一世、トリシル一号 |
| [[E_char_ゼド|ゼド]] | 5 | 盗賊王ゼド、ゼド＝アダス、盗賊王 |
| [[E_char_アヴロノ|アヴロノ]] | 5 | アヴロノ・ローザ、半妖精、虫態 |
| [[E_char_六人の王|六人の王]] | 5 | 六人の王さまたち、六人の王たち、六人の男たち |

## 他層への導線

- 観測元（L1 原文 Wiki・表示層）: [https://allusionistwiki.github.io/AllusionistWiki2/](https://allusionistwiki.github.io/AllusionistWiki2/) / [L1 下位層](https://allusionistwiki.github.io/AllusionistWiki2/L1/)
- 层索引（L2Wiki 系統の一覧）: [https://allusionistwiki.github.io/AllusionistWiki2/layers/](https://allusionistwiki.github.io/AllusionistWiki2/layers/)
- 作業データ（facts/candidates 生データ）: [AllusionistWiki_work](https://github.com/allusionistwiki/AllusionistWiki_work)

## 来歴

L7 観測 → L3 審査 → L2 名前統合（本台帳）→ **正規化 wiki 生成（本層）** → L1 原文（対照）。台帳 run の来歴・run.json は work repo の `work/allusionist_v2/L2/runs/20261029T0843_c8bb/` に格納。
