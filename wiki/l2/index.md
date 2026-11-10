---
title: "L2Wiki"
id: "L2_WIKI_TOP"
kind: "index"
created: "2026-10-28"
updated: "2026-11-11"
l2_run: "20261110T0603_v5agg"
---
# L2Wiki — 名前統合・正規化 Wiki

L1 wiki の全ページに**名前統合・正規化処理を適用した解析層 wiki** です。同じ名前の人（别名・隠れ名・呼び方の変遷）を代表名に統合した本文と、その判断根拠（来歴・監査）を辿れる構造になっています。

- 正規化 wiki に入る: [正規化Wiki 索引](https://allusionistwiki.github.io/AllusionistWiki2/L2/)
- 台帳 run: `20261110T0603_v5agg`（生成規則の中心）

## 正規化 wiki（メイン構造）

L1 全 15982 ページのミラー（同一相対パス）。高確度帯の别名→代表名のみ本文を置換し、各ページ末尾に置換監査表（元名義→代表名・確度・件数）を付けています。要検証・needs 系は置換せず注記に留め、過剰統合を避けています。

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
- 台帳 run: `20261110T0603_v5agg`（生成規則の中心）

## 生成規則（台帳・索引）— 本 wiki の一要素

台帳そのものは閲覧対象ではなく、上の正規化 wiki を作るための規則の集合です。

- 正規化エンティティ台帳 総計 17337 实体（terminology 6536, character 4222, item 3751, organization 918, location 639, motif 325, creature 257, 未分類 239, relationship 124, phrase 115, event 107, skill 11, spell 8, action 8, ability 7, race 6, group 5, magic 4, celestial_body 4, ritual 4, concept 4, place 4, app 3, emotion 3, phantom 3, character_class 2, system 2, role 2, rule 2, technology 2, phenomenon 2, plan 2, deity 1, software 1, spell_effect 1, event_context 1, game 1, part 1, brand 1, character_ability 1, technique 1, clothing 1, structure 1, unknown 1, building 1, institution 1, strategy 1, effect 1）
- 别名統合マッピング: 高確度帯 1071 件（置換に適用）/ 要検証・needs 185 件（注記のみ）
- 别名統合一覧: [别名統合一覧（RF_l2_aliases_index）](https://allusionistwiki.github.io/AllusionistWiki2/L2/reflections/RF_l2_aliases_index.html)
- 変換の相関・根拠: [RF_l2_correlations](https://allusionistwiki.github.io/AllusionistWiki2/L2/reflections/RF_l2_correlations.html)
- 台帳の設計・手順: [L2 README（work repo）](https://github.com/allusionistwiki/AllusionistWiki_work/blob/main/work/allusionist_v2/L2/README.md)

## 代表名別 統合例（上位）

| 代表名 | 統合别名数 | 代表例 |
|---|---|---|
| [[./entities/characters/E_char_アキラくん|アキラくん]] | 69 | アキラ殿、アキラ（仮称・主語不明）、俺(アキラ) |
| [[./entities/characters/E_char_マラード|マラード]] | 11 | マラード陛下、王の髪、マラード(地竜) |
| [[./entities/characters/E_char_ハルベルト|ハルベルト]] | 10 | 呪文の座、歌姫Spear、歌姫Ｓｐｅａｒ |
| [[./entities/characters/E_char_カーイン|カーイン]] | 10 | カーインの残り滓、カーインの瘴気、カーインの脳内 |
| [[./entities/characters/E_char_ミヒトネッセ|ミヒトネッセ]] | 10 | ミヒトネッセ(狂イ姫)、ミヒトネッセ(シナモリアキラ/九尾)、ミヒトネッセ(ゼドへの変身時) |
| [[./entities/characters/E_char_アズーリア|アズーリア]] | 9 | 守護の九槍アズーリア、全裸の変態(男)、駕籠の中の女性 |
| [[./entities/characters/ME_Organ_Rode|オルガンローデ]] | 8 | オルゴーの滅びの呪文、呪文竜、滅びの呪文 |
| [[./entities/characters/E_char_キロン|キロン]] | 8 | 聖騎士、蝶の翅、転生者殺し |
| [[./entities/characters/E_char_オルヴァ|オルヴァ]] | 7 | 聖油、カシュラム王(オルヴァ)、オルヴァ(髭大夫) |
| [[./entities/characters/E_char_エレクトラ|エレクトラ]] | 6 | ユディーア、キニス、キニスちゃん |
| [[./entities/characters/E_char_呪文|呪文]] | 6 | 炸撃、爆撃、言語魔術 |
| [[./entities/characters/E_char_ペリュトン|ペリュトン]] | 6 | 青い鳥、ラハブ、ペリュトン種族 |
| [[./entities/characters/E_char_邪視|邪視]] | 6 | ファシネイター、邪視呪術、色付き視線 |
| [[./entities/characters/E_char_スカルミリオーネ|スカルミリオーネ]] | 6 | スカルミリョーネ、ルバーブ様、乱髪 |
| [[./entities/characters/E_term_アトリビュート|アトリビュート]] | 6 | 射影三昧耶形・十四番、射影即興喜劇、射影三昧耶形 |
| [[./entities/characters/E_char_カイン|カイン]] | 6 | 狼、彼、カイン(私) |
| [[./entities/characters/E_char_ファル|ファル]] | 5 | ファルファレロ、クリミナトレス、少年神 |
| [[./entities/characters/E_char_カーティス|カーティス]] | 5 | カーティス一世、トリシル一号、カーティス(リールエルバの変身/男装) |
| [[./entities/characters/E_char_ゼド|ゼド]] | 5 | 盗賊王ゼド、ゼド＝アダス、盗賊王 |
| [[./entities/characters/E_term_ゼオーティア|ゼオーティア]] | 5 | ゼオーティア世界、ゼオーティア教圏、ゼオーティアの社会 |

## 他層への導線

- 観測元（L1 原文 Wiki・表示層）: [https://allusionistwiki.github.io/AllusionistWiki2/](https://allusionistwiki.github.io/AllusionistWiki2/) / [L1 下位層](https://allusionistwiki.github.io/AllusionistWiki2/L1/)
- 层索引（L2Wiki 系統の一覧）: [https://allusionistwiki.github.io/AllusionistWiki2/layers/](https://allusionistwiki.github.io/AllusionistWiki2/layers/)
- 作業データ（facts/candidates 生データ）: [AllusionistWiki_work](https://github.com/allusionistwiki/AllusionistWiki_work)

## 来歴

L7 観測 → L3 審査 → L2 名前統合（本台帳）→ **正規化 wiki 生成（本層）** → L1 原文（対照）。台帳 run の来歴・run.json は work repo の `work/allusionist_v2/L2/runs/20261110T0603_v5agg/` に格納。
