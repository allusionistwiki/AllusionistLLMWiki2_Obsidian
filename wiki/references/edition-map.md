---

schema_version: "5.1"
id: edition-map
title: 版対応表





















































type: reflection

description: 解析の典拠を結ぶ、なろう版272話とカクヨム版589話の話対応・段落（¶）アンカー対応表
---

# 版対応表（なろう版 ⇔ カクヨム版）

当 wiki の原文典拠は**カクヨム版を正典**とし、段落は **¶N**（カクヨム episode ページの段落 ID）で参照します。
¶N は `https://kakuyomu.jp/works/16816927859268545348/episodes/<episodeId>#pN` の段落直リンクになります。
下表は解析 baseline（なろう版引用）をカクヨム版 ¶ へ写し替えた対応表で、生成来歴は run `20261017T2011_f863`（L0 引用検索）・`20261018T0040_588c`（L1 再アンカー4パス+裁定）です。

## 数字

- baseline 引用 **38,288** 件のうち **33,725（88.1%）** はカクヨム版で全文一致し即 ¶ 確定
- 残り **4,528 件（ユニーク 4,036）** を再解析 → **回収 3,693（91.5%）/ 削除台帳 343（8.5%）**
- 削除台帳の内訳（カクヨム正典に非存在を全巻全文検索で確認、理由付きで `deleted-ledger.jsonl`（work repo）に保存）: 付録 160・なろう専用幕間 104・改稿削除 73・検証不可 3・章構造メタ 3・幕間題/作者注記 2
- 対応ゼロ章 5・カクヨム専用 27 話（2022 年・第三巻まわりの本文 6 話 + 2025 年・5-70 以降の続編 21 話。なろうは 5-69 凍結）

> **注意**: なろう版 ch 番号・p 番号は正典ではありません。引用参照は必ずカクヨム ¶N で行ってください（なろう版 URL は歴史的参照用）。

## 章対応表（なろう 272 話）

| # | なろう版（歴史的参照） | カクヨム版 episode | 確定・削除/ユニーク | 削除 |
|---|---|---|---|---|
| 001 | [無彩色の左手、鎧の右手](https://ncode.syosetu.com/n9073ca/1/) | [1](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859272464536)–[13](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859272995677)（13話） | 249/251 | 改稿削除1 |
| 002 | [死者を代弁する者](https://ncode.syosetu.com/n9073ca/2/) | [13](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859272995677)–[20](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859273164577)（8話） | 128/129 | 改稿削除1 |
| 003 | [きぐるみの魔女](https://ncode.syosetu.com/n9073ca/3/) | [21](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859273180125) | 93/93 |  |
| 004 | [氷血のコルセスカ](https://ncode.syosetu.com/n9073ca/4/) | [22](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859419475664)–[26](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859419625754)（5話） | 276/277 | 改稿削除1 |
| 005 | [転生者ゼノグラシア](https://ncode.syosetu.com/n9073ca/5/) | [27](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859419675527)–[34](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859419905288)（8話） | 140/140 |  |
| 006 | [悪夢](https://ncode.syosetu.com/n9073ca/6/) | [35](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859419930509) | 37/37 |  |
| 007 | [魔女と狂犬](https://ncode.syosetu.com/n9073ca/7/) | [36](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859420021326)–[40](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859420131037)（5話） | 281/281 |  |
| 008 | [六淫操手](https://ncode.syosetu.com/n9073ca/8/) | [41](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859420168616)–[44](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859420276366)（4話） | 125/126 | 改稿削除1 |
| 009 | [王獣カッサリオ](https://ncode.syosetu.com/n9073ca/9/) | [45](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859420294647)–[48](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859420456106)（4話） | 125/125 |  |
| 010 | [がらくたなんかじゃない](https://ncode.syosetu.com/n9073ca/10/) | [48](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859420456106)–[52](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859420549338)（5話） | 142/142 |  |
| 011 | [炎は黄金を証明する](https://ncode.syosetu.com/n9073ca/11/) | [38](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859420057455)、[53](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859420560584)、[54](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859420586533)、[55](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859420600184) | 99/99 |  |
| 012 | [その視座の名はゆらぎの神話](https://ncode.syosetu.com/n9073ca/12/) | [56](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859420613277)–[61](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859420772005)（6話） | 153/153 |  |
| 013 | [シェイドラン](https://ncode.syosetu.com/n9073ca/13/) | [62](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859769028916)–[64](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859769123781)（3話） | 150/152 |  |
| 014 | [春の魔女](https://ncode.syosetu.com/n9073ca/14/) | [65](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859769157173)–[68](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859769217513)（4話） | 213/214 |  |
| 015 | [欠落と渇望](https://ncode.syosetu.com/n9073ca/15/) | [69](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859769238721)–[72](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859769356288)（4話） | 200/202 |  |
| 016 | [前夜](https://ncode.syosetu.com/n9073ca/16/) | [73](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859769381976) | 111/111 |  |
| 017 | [リナゾラクロウサより](https://ncode.syosetu.com/n9073ca/17/) | [74](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859769437315)–[75](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859769446064)（2話） | 71/72 |  |
| 018 | [メクセトの神滅具](https://ncode.syosetu.com/n9073ca/18/) | [76](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859769535298)–[80](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859769699982)（5話） | 119/120 | 改稿削除1 |
| 019 | [転生者殺し](https://ncode.syosetu.com/n9073ca/19/) | [81](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859769724319)–[84](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859769827118)（4話） | 214/218 | 改稿削除1 |
| 020 | [涙の価値](https://ncode.syosetu.com/n9073ca/20/) | [85](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859769874419)–[88](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860032374026)（4話） | 160/160 |  |
| 021 | [そんなことよりゲムをしよう](https://ncode.syosetu.com/n9073ca/21/) | [37](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927859420038541)、[89](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860024964204)、[90](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860024987511)、[91](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860025007610)、[92](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860025022838)、[93](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860025062867)、[94](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860025075485) | 240/248 | 改稿削除5 |
| 022 | [鏡ミラジュ](https://ncode.syosetu.com/n9073ca/22/) | [95](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860025108221)–[100](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860025206406)（6話） | 247/250 |  |
| 023 | [棒ワンド](https://ncode.syosetu.com/n9073ca/23/) | [101](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860079211997)–[105](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860079372689)（5話） | 433/435 | 改稿削除2 |
| 024 | [レジンキャストエピゴネン](https://ncode.syosetu.com/n9073ca/24/) | [106](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860111893795)–[110](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860112138083)（5話） | 255/261 | 改稿削除1 検証不可1 |
| 025 | [参照のアリュジョン](https://ncode.syosetu.com/n9073ca/25/) | [111](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860112160471)–[113](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860112358553)（3話） | 90/90 |  |
| 026 | [サイバネティクスとオカルティズムの幸福なマリアジュ](https://ncode.syosetu.com/n9073ca/26/) | [114](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860112459891)–[117](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860112557913)（4話） | 155/155 |  |
| 027 | [その名はアズリア](https://ncode.syosetu.com/n9073ca/27/) | [118](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860112597335) | 92/92 |  |
| 028 | [もし狂犬が戦国乱世に転生したら](https://ncode.syosetu.com/n9073ca/28/) | — | 0/103 | なろう専用幕間87 |
| 029 | [どうして空は青いの?](https://ncode.syosetu.com/n9073ca/29/) | [119](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860284382922) | 92/93 |  |
| 030 | [未来回想、あるいはこれからのあらすじ](https://ncode.syosetu.com/n9073ca/30/) | [120](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860311093698) | 66/67 |  |
| 031 | [もうひとつの左手](https://ncode.syosetu.com/n9073ca/31/) | [121](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860311222661)–[122](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860311331923)（2話） | 202/210 |  |
| 032 | [もうひとつの悪夢](https://ncode.syosetu.com/n9073ca/32/) | [123](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860311491673)–[124](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860311505747)（2話） | 79/79 |  |
| 033 | [言の葉遣いは躊躇わない](https://ncode.syosetu.com/n9073ca/33/) | [125](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860311685154)–[128](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860311770535)（4話） | 92/92 |  |
| 034 | [半熟英雄](https://ncode.syosetu.com/n9073ca/34/) | [129](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860726615931)–[131](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860726740455)（3話） | 185/185 |  |
| 035 | [天の鴉と月の兎](https://ncode.syosetu.com/n9073ca/35/) | [132](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860726856658)–[139](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860727295457)（8話） | 252/255 |  |
| 036 | [言語魔術師の弟子前編](https://ncode.syosetu.com/n9073ca/36/) | [140](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860727415461)–[141](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860727428897)（2話） | 116/117 |  |
| 037 | [魔女と英雄](https://ncode.syosetu.com/n9073ca/37/) | [142](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860728490873)–[148](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860728722872)（7話） | 223/232 | 改稿削除2 |
| 038 | [言理の妖精語りて曰く](https://ncode.syosetu.com/n9073ca/38/) | [149](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927861376512652)–[159](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554469046309)（11話） | 354/357 | 改稿削除1 |
| 039 | [幻想再起のイリュジョニスト](https://ncode.syosetu.com/n9073ca/39/) | [148](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860728722872)、[149](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927861376512652)、[160](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554469212174)、[161](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554469283061) | 96/98 | 改稿削除1 |
| 040 | [フォビットの魔獣](https://ncode.syosetu.com/n9073ca/40/) | [162](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554637267696) | 89/93 |  |
| 041 | [色無しマリ](https://ncode.syosetu.com/n9073ca/41/) | [163](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554637278900) | 106/106 |  |
| 042 | [松明の騎士](https://ncode.syosetu.com/n9073ca/42/) | — | 85/97 | 幕間短縮6 |
| 043 | [再びの未来回想、そして来るべき次回予告](https://ncode.syosetu.com/n9073ca/43/) | [167](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554637323798)–[168](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554637333784)（2話） | 113/114 |  |
| 044 | [トライアンドエラ](https://ncode.syosetu.com/n9073ca/44/) | [169](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554637348194) | 86/87 |  |
| 045 | [青の空、黒の空白](https://ncode.syosetu.com/n9073ca/45/) | [170](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554637361132)–[171](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554637371452)（2話） | 120/121 | 改稿削除1 |
| 046 | [チョコレトリリ](https://ncode.syosetu.com/n9073ca/46/) | [172](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554950976742)–[173](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554951112246)（2話） | 151/153 |  |
| 047 | [隠れた変数オクルトゥム](https://ncode.syosetu.com/n9073ca/47/) | [174](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554980836607)–[175](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554981037278)（2話） | 132/134 | 改稿削除1 |
| 048 | [この戦いが終わったら](https://ncode.syosetu.com/n9073ca/48/) | [175](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554981037278)–[176](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554981096524)（2話） | 83/84 | 改稿削除1 |
| 049 | [砂漠の花](https://ncode.syosetu.com/n9073ca/49/) | [177](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554981465648) | 93/97 | 章構造メタ1 検証不可1 |
| 050 | [パレルノ山六千人殺し](https://ncode.syosetu.com/n9073ca/50/) | [178](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555191819574) | 88/89 | 改稿削除1 |
| 051 | [静謐なる多弁](https://ncode.syosetu.com/n9073ca/51/) | [119](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860284382922)、[124](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860311505747)、[145](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860728527501)、[156](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927861376945839)、[179](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555191847777) | 293/297 | 改稿削除2 |
| 052 | [死の囀りカタルマリナ](https://ncode.syosetu.com/n9073ca/52/) | [176](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554981096524)、[180](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555191910766)、[181](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555191997774)、[182](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555192015489) | 122/123 | 検証不可1 |
| 053 | [黒いアネモネの花言葉](https://ncode.syosetu.com/n9073ca/53/) | [183](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555192091815) | 154/156 |  |
| 054 | [無造作な死](https://ncode.syosetu.com/n9073ca/54/) | [184](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555192255824)–[185](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555192269836)（2話） | 106/107 |  |
| 055 | [祈りの価値](https://ncode.syosetu.com/n9073ca/55/) | [186](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555192611982)–[187](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555193240978)（2話） | 143/144 |  |
| 056 | [言震ワドクェイク](https://ncode.syosetu.com/n9073ca/56/) | — | 147/166 | 幕間短縮5 |
| 057 | [激光レイジ](https://ncode.syosetu.com/n9073ca/57/) | [119](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860284382922)、[190](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555192863440)、[191](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555193084665) | 167/169 | 改稿削除1 章構造メタ1 |
| 058 | [青空](https://ncode.syosetu.com/n9073ca/58/) | [192](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555193323185) | 134/134 |  |
| 059 | [夢幻の果て](https://ncode.syosetu.com/n9073ca/59/) | [193](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555201895016)–[194](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555201930365)（2話） | 130/130 |  |
| 060 | [言語魔術師の弟子後編](https://ncode.syosetu.com/n9073ca/60/) | [195](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555202120776)–[197](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555202148900)（3話） | 117/119 | 改稿削除1 |
| 061 | [第五階層より第一階層へ](https://ncode.syosetu.com/n9073ca/61/) | [124](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860311505747)、[198](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555202270882) | 107/110 |  |
| 062 | [シナモリアキラより](https://ncode.syosetu.com/n9073ca/62/) | [199](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555202424805)–[200](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555202438096)（2話） | 97/97 |  |
| 063 | [睥睨するエクリオベレッカ](https://ncode.syosetu.com/n9073ca/63/) | [201](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555202825989)–[202](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556390970460)（2話） | 134/135 |  |
| 064 | [十三階段](https://ncode.syosetu.com/n9073ca/64/) | [203](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556391181479)–[205](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556391321780)（3話） | 164/175 |  |
| 065 | [オンステジ](https://ncode.syosetu.com/n9073ca/65/) | [119](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860284382922)、[198](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555202270882)、[205](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556391321780)、[206](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622317585)、[207](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622358630)、[208](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622364757) | 264/281 | 改稿削除2 |
| 066 | [奈落に飲まれ、闇に包まれる](https://ncode.syosetu.com/n9073ca/66/) | [205](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556391321780)、[209](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622421093)、[211](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622425957) | 149/161 |  |
| 067 | [影に沈み、振り返らずに去っていく](https://ncode.syosetu.com/n9073ca/67/) | [205](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556391321780)、[210](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622484544)、[212](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622499947) | 149/160 |  |
| 068 | [言葉は断ち切られ、絶望は感染する。そして――](https://ncode.syosetu.com/n9073ca/68/) | [142](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860728490873)、[182](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555192015489)、[183](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555192091815)、[198](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555202270882)、[205](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556391321780)、[207](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622358630)、[213](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622543699) | 208/217 | 改稿削除8 |
| 069 | [この夜が明けるまであと百万の祈り](https://ncode.syosetu.com/n9073ca/69/) | [214](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622606787) | 100/100 |  |
| 070 | [黒百合の子供たち](https://ncode.syosetu.com/n9073ca/70/) | [157](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554468898438)、[215](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622667376)、[216](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622715858)、[217](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622763250) | 109/109 |  |
| 071 | [その名はサイバカラテ](https://ncode.syosetu.com/n9073ca/71/) | [218](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622827818)–[219](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622861077)（2話） | 186/193 |  |
| 072 | [それは、世界がこんなにも光に満ち溢れているから](https://ncode.syosetu.com/n9073ca/72/) | [220](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622921145)–[222](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556622961348)（3話） | 157/161 | 改稿削除1 |
| 073 | [澄明なる青空に](https://ncode.syosetu.com/n9073ca/73/) | [223](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556623063525)–[225](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556623201280)（3話） | 250/255 |  |
| 074 | [特権者の英雄症候群、さもなくば――](https://ncode.syosetu.com/n9073ca/74/) | [129](https://kakuyomu.jp/works/16816927859268545348/episodes/16816927860726615931)、[226](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556623273459)、[227](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556623298787)、[228](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556623380713) | 161/161 |  |
| 075 | [第九魔将](https://ncode.syosetu.com/n9073ca/75/) | [229](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556623425945) | 203/204 |  |
| 076 | [黒血のハルベルト](https://ncode.syosetu.com/n9073ca/76/) | — | 57/65 | 幕間短縮5 |
| 077 | [死人の森](https://ncode.syosetu.com/n9073ca/77/) | [231](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655650963993) | 410/411 |  |
| 078 | [道場](https://ncode.syosetu.com/n9073ca/78/) | [232](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655670570093) | 169/169 |  |
| 079 | [風の吹く丘](https://ncode.syosetu.com/n9073ca/79/) | [233](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655670607535) | 99/103 | 改稿削除1 |
| 080 | [王国](https://ncode.syosetu.com/n9073ca/80/) | [234](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655670646927) | 82/83 |  |
| 081 | [ダモクレスの剣](https://ncode.syosetu.com/n9073ca/81/) | [235](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655670761687)–[236](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655670816610)（2話） | 173/173 |  |
| 082 | [工場](https://ncode.syosetu.com/n9073ca/82/) | [237](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655670979446)–[238](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655670992551)（2話） | 125/126 | 改稿削除1 |
| 083 | [白骨迷宮](https://ncode.syosetu.com/n9073ca/83/) | [239](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655671147193)–[240](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655671262114)（2話） | 105/105 |  |
| 084 | [花街](https://ncode.syosetu.com/n9073ca/84/) | [241](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655671296987) | 102/104 |  |
| 085 | [黒百合館](https://ncode.syosetu.com/n9073ca/85/) | [242](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655671385527)–[243](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655671405371)（2話） | 62/62 |  |
| 086 | [ステュクス](https://ncode.syosetu.com/n9073ca/86/) | [244](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655671528624)–[246](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655671691507)（3話） | 172/172 |  |
| 087 | [空の玉座](https://ncode.syosetu.com/n9073ca/87/) | [247](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655671797238) | 97/97 |  |
| 088 | [二人の距離](https://ncode.syosetu.com/n9073ca/88/) | [248](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655672109962) | 96/98 |  |
| 089 | [星見の塔トナメント前編](https://ncode.syosetu.com/n9073ca/89/) | [231](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655650963993)、[232](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655670570093)、[249](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656441979542)、[250](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656441990694)、[251](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442004676)、[252](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442016619) | 279/285 |  |
| 090 | [TCG](https://ncode.syosetu.com/n9073ca/90/) | [253](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442035853)–[258](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442096722)（6話） | 193/193 |  |
| 091 | [不在の二人](https://ncode.syosetu.com/n9073ca/91/) | [259](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442593365)–[260](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442607674)（2話） | 105/105 |  |
| 092 | [冥道の幼姫](https://ncode.syosetu.com/n9073ca/92/) | [260](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442607674)–[261](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442902819)（2話） | 43/43 |  |
| 093 | [妄想妖精のプロンプタ](https://ncode.syosetu.com/n9073ca/93/) | [261](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442902819)–[262](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442914345)（2話） | 103/103 |  |
| 094 | [境界に立つ者](https://ncode.syosetu.com/n9073ca/94/) | [263](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442928357) | 73/73 |  |
| 095 | [過去から過去へ、劇から劇へ](https://ncode.syosetu.com/n9073ca/95/) | [264](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442936532) | 69/69 |  |
| 096 | [病的グランギニョル](https://ncode.syosetu.com/n9073ca/96/) | [265](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657291173845)–[267](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657291517627)（3話） | 98/98 |  |
| 097 | [微睡む太陽と月のパペットリ](https://ncode.syosetu.com/n9073ca/97/) | [268](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657291742631)–[270](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657291819147)（3話） | 113/114 |  |
| 098 | [昔々あるところに](https://ncode.syosetu.com/n9073ca/98/) | [271](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657292048246) | 67/67 |  |
| 099 | [正邪の双竜王](https://ncode.syosetu.com/n9073ca/99/) | [272](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657292179737) | 92/92 |  |
| 100 | [外なる法](https://ncode.syosetu.com/n9073ca/100/) | [265](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657291173845)、[273](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657292681847)、[274](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657292694693) | 107/107 |  |
| 101 | [雷が鳴っている間は](https://ncode.syosetu.com/n9073ca/101/) | [275](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657292642524) | 82/83 |  |
| 102 | [冥道の番犬](https://ncode.syosetu.com/n9073ca/102/) | [276](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657894186248) | 109/109 |  |
| 103 | [禁忌と罰](https://ncode.syosetu.com/n9073ca/103/) | [277](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657894287900) | 81/81 |  |
| 104 | [栄光の手](https://ncode.syosetu.com/n9073ca/104/) | [278](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657895472385)–[279](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657895488820)（2話） | 199/200 |  |
| 105 | [食い千切られた左腕](https://ncode.syosetu.com/n9073ca/105/) | [260](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442607674)、[280](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657895618015) | 79/81 | 改稿削除1 |
| 106 | [畏怖](https://ncode.syosetu.com/n9073ca/106/) | [256](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442073909)、[281](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658133202167) | 126/126 |  |
| 107 | [終端は弑された](https://ncode.syosetu.com/n9073ca/107/) | [282](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658133542878)–[283](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658133559456)（2話） | 116/116 |  |
| 108 | [不似合いな結びつき](https://ncode.syosetu.com/n9073ca/108/) | [284](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658134098535)–[285](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658134163994)（2話） | 105/105 |  |
| 109 | [睥睨する藍色](https://ncode.syosetu.com/n9073ca/109/) | [286](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658134445427) | 89/91 |  |
| 110 | [冗長性ファントムペイン](https://ncode.syosetu.com/n9073ca/110/) | [287](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658134854989)–[288](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658134874874)（2話） | 104/104 |  |
| 111 | [暗がりの中へ](https://ncode.syosetu.com/n9073ca/111/) | [289](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658136305682)–[290](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658136392938)（2話） | 123/123 |  |
| 112 | [熱病のような加虐が彼女の望み](https://ncode.syosetu.com/n9073ca/112/) | [291](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658136637410)–[292](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658136616519)（2話） | 135/140 |  |
| 113 | [集い](https://ncode.syosetu.com/n9073ca/113/) | [293](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658136784055) | 75/77 |  |
| 114 | [コキュトス](https://ncode.syosetu.com/n9073ca/114/) | [294](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658136944960)–[296](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658137266871)（3話） | 106/106 |  |
| 115 | [生と死トライアンドエラ](https://ncode.syosetu.com/n9073ca/115/) | [297](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658137965992)–[303](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658138055592)（7話） | 118/118 |  |
| 116 | [9-∞必ず貴方を迎えにいくから](https://ncode.syosetu.com/n9073ca/116/) | [304](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658138071188)–[306](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658138219683)（3話） | 99/99 |  |
| 117 | [トリシュラカムバック](https://ncode.syosetu.com/n9073ca/117/) | [307](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658138344720)–[308](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658138376817)（2話） | 141/147 |  |
| 118 | [女王と錬鉄者](https://ncode.syosetu.com/n9073ca/118/) | [309](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658159387747)–[311](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658159564774)（3話） | 129/134 | 改稿削除3 |
| 119 | [星見の塔の大比武さいごの戦い](https://ncode.syosetu.com/n9073ca/119/) | [268](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657291742631)、[312](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658159777541)、[313](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658159910060)、[314](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658160015920) | 177/181 | 改稿削除2 |
| 120 | [死人の森の/断章取義のアリュジョニスト](https://ncode.syosetu.com/n9073ca/120/) | [315](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658160182943)–[317](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658160362397)（3話） | 106/106 |  |
| 121 | [未来転生](https://ncode.syosetu.com/n9073ca/121/) | [318](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658160426539) | 94/94 |  |
| 122 | [TH](https://ncode.syosetu.com/n9073ca/122/) | [319](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660528458028) | 101/102 |  |
| 123 | [一時の平穏](https://ncode.syosetu.com/n9073ca/123/) | [271](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657292048246)、[320](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660528557008)、[321](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660528668581) | 85/85 |  |
| 124 | [悪夢の饗宴](https://ncode.syosetu.com/n9073ca/124/) | [322](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660528711194) | 73/73 |  |
| 125 | [六人の王さま](https://ncode.syosetu.com/n9073ca/125/) | [233](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655670607535)、[234](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655670646927)、[235](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655670761687)、[239](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655671147193)、[245](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655671570216)、[266](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657291442206)、[323](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660528818227) | 157/160 | 改稿削除2 |
| 126 | [未来の過失](https://ncode.syosetu.com/n9073ca/126/) | [324](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660528898897) | 105/105 |  |
| 127 | [ガイノイドの魔女](https://ncode.syosetu.com/n9073ca/127/) | [325](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660529687551)–[327](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660529707950)（3話） | 120/120 |  |
| 128 | [予兆](https://ncode.syosetu.com/n9073ca/128/) | [328](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660529800543) | 85/85 |  |
| 129 | [脆弱性、あるいは仕様](https://ncode.syosetu.com/n9073ca/129/) | [329](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660529965322)–[330](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660529975375)（2話） | 84/84 |  |
| 130 | [皆殺しのデデェイア](https://ncode.syosetu.com/n9073ca/130/) | [232](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655670570093)、[325](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660529687551)、[331](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660530070101)、[332](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660530211681) | 94/94 |  |
| 131 | [異界転生](https://ncode.syosetu.com/n9073ca/131/) | [333](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660530383398)–[334](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660530507902)（2話） | 124/124 |  |
| 132 | [欲望の在処](https://ncode.syosetu.com/n9073ca/132/) | [235](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655670761687)、[293](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658136784055)、[335](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660530730549) | 207/216 |  |
| 133 | [囚われの氷晶姫](https://ncode.syosetu.com/n9073ca/133/) | [231](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655650963993)、[336](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660530840584) | 120/121 |  |
| 134 | [二人で](https://ncode.syosetu.com/n9073ca/134/) | [317](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658160362397)、[337](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660531047511)、[338](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660531059514) | 95/95 |  |
| 135 | [ゲムスタト](https://ncode.syosetu.com/n9073ca/135/) | [237](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655670979446)、[339](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661522906134)、[340](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661522926767) | 118/121 | 改稿削除2 |
| 136 | [左右一対の邪眼姫](https://ncode.syosetu.com/n9073ca/136/) | [341](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661523015724)–[342](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661523056573)（2話） | 100/100 |  |
| 137 | [嵐の前](https://ncode.syosetu.com/n9073ca/137/) | [343](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661523402737) | 97/97 |  |
| 138 | [ラフディボル前半](https://ncode.syosetu.com/n9073ca/138/) | [232](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655670570093)、[344](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661523674966)、[345](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661523690758) | 89/91 | 改稿削除1 |
| 139 | [ラフディボル後半](https://ncode.syosetu.com/n9073ca/139/) | [346](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661523773857)–[347](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661523789390)（2話） | 141/147 |  |
| 140 | [騒乱](https://ncode.syosetu.com/n9073ca/140/) | [348](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661523976930)–[349](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661524043142)（2話） | 136/137 |  |
| 141 | [醜い野獣](https://ncode.syosetu.com/n9073ca/141/) | [247](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655671797238)、[350](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661524224964)、[351](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661524425609)、[352](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661524439281) | 114/119 |  |
| 142 | [業](https://ncode.syosetu.com/n9073ca/142/) | [353](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661524592673)–[354](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661524694712)（2話） | 98/99 |  |
| 143 | [王と物乞い](https://ncode.syosetu.com/n9073ca/143/) | [316](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658160303562)、[355](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661524963863)、[356](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661525035336)、[357](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661525065213) | 87/88 |  |
| 144 | [祈りは流星に似て](https://ncode.syosetu.com/n9073ca/144/) | [358](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661526161536)–[359](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661526302605)（2話） | 137/137 |  |
| 145 | [ガロアンディアンの真竜王](https://ncode.syosetu.com/n9073ca/145/) | [360](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330662817326044)–[361](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330662817355025)（2話） | 131/131 |  |
| 146 | [チョコレトリリのスイツ事件簿S2C.14アズチョコに挑め!](https://ncode.syosetu.com/n9073ca/146/) | [362](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330662817418593) | 119/120 |  |
| 147 | [死人の森の父](https://ncode.syosetu.com/n9073ca/147/) | [272](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330657292179737)、[281](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658133202167)、[363](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330662911809735)、[364](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330662911870510)、[365](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330662911902353) | 118/119 | 幕間題1 |
| 148 | [オルヴァ王と十二人のシナモリアキラ1](https://ncode.syosetu.com/n9073ca/148/) | [366](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330662911973627) | 41/42 |  |
| 149 | [オルヴァ王と十二人のシナモリアキラ2](https://ncode.syosetu.com/n9073ca/149/) | [367](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330662912068890)–[368](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330662912081515)（2話） | 111/122 |  |
| 150 | [オルヴァ王と十二人のシナモリアキラ3](https://ncode.syosetu.com/n9073ca/150/) | [369](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663293167561)–[370](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663293180102)（2話） | 121/121 |  |
| 151 | [オルヴァ王と十二人のシナモリアキラ4](https://ncode.syosetu.com/n9073ca/151/) | [371](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663293281683) | 98/99 | 改稿削除1 |
| 152 | [オルヴァ王と十二人のシナモリアキラ5](https://ncode.syosetu.com/n9073ca/152/) | [372](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663293403397)–[373](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663293435047)（2話） | 94/94 |  |
| 153 | [オルヴァ王と十二人のシナモリアキラ6](https://ncode.syosetu.com/n9073ca/153/) | [374](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663521694193)–[377](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663522262131)（4話） | 167/170 | 改稿削除3 |
| 154 | [オルヴァ王と十二人のシナモリアキラ7](https://ncode.syosetu.com/n9073ca/154/) | [378](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663658272034)–[379](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663658292044)（2話） | 121/122 |  |
| 155 | [オルヴァ王と十二人のシナモリアキラ8](https://ncode.syosetu.com/n9073ca/155/) | [380](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663658396764)–[381](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663658424369)（2話） | 98/99 |  |
| 156 | [オルヴァ王と十二人のシナモリアキラ9](https://ncode.syosetu.com/n9073ca/156/) | [342](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330661523056573)、[382](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663658492135) | 156/156 |  |
| 157 | [オルヴァ王と十二人のシナモリアキラ10](https://ncode.syosetu.com/n9073ca/157/) | [383](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663658573298)–[384](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663658585531)（2話） | 125/125 |  |
| 158 | [オルヴァ王と十二人のシナモリアキラ11](https://ncode.syosetu.com/n9073ca/158/) | [385](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663658696522)–[388](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663658891917)（4話） | 136/136 |  |
| 159 | [オルヴァ王と十二人のシナモリアキラ12](https://ncode.syosetu.com/n9073ca/159/) | [291](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330658136637410)、[379](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663658292044)、[389](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663659016980)、[390](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663659063914)、[391](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663659157507) | 165/166 |  |
| 160 | [オルヴァ王と十二人のシナモリアキラ0](https://ncode.syosetu.com/n9073ca/160/) | [392](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663659578842)–[393](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663659595761)（2話） | 84/84 |  |
| 161 | [狂姫乱舞](https://ncode.syosetu.com/n9073ca/161/) | [363](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330662911809735)、[394](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665313417217) | 91/91 |  |
| 162 | [カクリ世の宴](https://ncode.syosetu.com/n9073ca/162/) | [395](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665321644112) | 77/77 |  |
| 163 | [檻の感触だきしめて](https://ncode.syosetu.com/n9073ca/163/) | [396](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665349567493)、[397](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665349595821)、[404](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665350241182) | 88/88 |  |
| 164 | [悪夢の継承者](https://ncode.syosetu.com/n9073ca/164/) | [398](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665349697936) | 94/94 |  |
| 165 | [あなたのアイは独りよがり](https://ncode.syosetu.com/n9073ca/165/) | [399](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665349753275) | 64/65 |  |
| 166 | [純な炎を胸に燃やして](https://ncode.syosetu.com/n9073ca/166/) | [400](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665349811883) | 88/90 |  |
| 167 | [血も凍りつく眠りの中で](https://ncode.syosetu.com/n9073ca/167/) | [396](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665349567493)、[401](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665350006555)、[402](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665350032334)、[404](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665350241182) | 124/125 | 改稿削除1 |
| 168 | [燃え上がる夢の終わりに](https://ncode.syosetu.com/n9073ca/168/) | [403](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665350127335) | 125/128 |  |
| 169 | [目指すは奈落、一直線に](https://ncode.syosetu.com/n9073ca/169/) | [396](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665349567493)、[401](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665350006555)、[404](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665350241182) | 125/125 |  |
| 170 | [栄えある女王の凱旋](https://ncode.syosetu.com/n9073ca/170/) | [405](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665350412760)–[406](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665350474731)（2話） | 98/98 |  |
| 171 | [甘い果実は腐り堕ちて](https://ncode.syosetu.com/n9073ca/171/) | [407](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665350539121) | 75/75 |  |
| 172 | [メスブタノパン/ブタノマンジュウ](https://ncode.syosetu.com/n9073ca/172/) | [408](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665350721612)–[409](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665350740539)（2話） | 140/141 |  |
| 173 | [裸の自分、服を着た誰か](https://ncode.syosetu.com/n9073ca/173/) | [410](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665350908553)–[411](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665350932502)（2話） | 72/72 |  |
| 174 | [あなたは理想の王子さま、私の素敵な王子さま](https://ncode.syosetu.com/n9073ca/174/) | [412](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665351114053) | 173/175 |  |
| 175 | [私たちを始めましょう](https://ncode.syosetu.com/n9073ca/175/) | [319](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660528458028)、[413](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665351330703)、[414](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665351539098)、[415](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665351573516) | 178/179 |  |
| 176 | [C](https://ncode.syosetu.com/n9073ca/176/) | [416](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665352002495) | 112/112 |  |
| 177 | [チョコレトリリのスイツ事件簿2第14話デツミツナッツ](https://ncode.syosetu.com/n9073ca/177/) | [464](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665373805089)–[465](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665373839433)（2話） | 121/121 |  |
| 178 | [罪貨の略奪者](https://ncode.syosetu.com/n9073ca/178/) | [417](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665352100454) | 98/99 |  |
| 179 | [狂姫と狂犬](https://ncode.syosetu.com/n9073ca/179/) | [418](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665352376743)–[419](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665352390267)（2話） | 108/108 |  |
| 180 | [夢に向かって](https://ncode.syosetu.com/n9073ca/180/) | [420](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665352678263)–[421](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665352767555)（2話） | 200/201 | 改稿削除1 |
| 181 | [女王の器](https://ncode.syosetu.com/n9073ca/181/) | [422](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665352904180)–[423](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665352962966)（2話） | 139/139 |  |
| 182 | [チェンジリングケットシ](https://ncode.syosetu.com/n9073ca/182/) | [424](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665353128717)–[425](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665353146439)（2話） | 110/111 |  |
| 183 | [愛の切っ先](https://ncode.syosetu.com/n9073ca/183/) | [426](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665356945559)–[428](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665357004841)（3話） | 101/103 |  |
| 184 | [第五階層のシナモリアキラ](https://ncode.syosetu.com/n9073ca/184/) | [429](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665361456833)–[431](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665361528468)（3話） | 139/139 |  |
| 185 | [夜空裂くキャスケット](https://ncode.syosetu.com/n9073ca/185/) | [432](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665362156210)–[434](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665362505840)（3話） | 102/103 |  |
| 186 | [序TOIHM](https://ncode.syosetu.com/n9073ca/186/) | [260](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442607674)、[417](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665352100454)、[435](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665365061873)、[436](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665365094989) | 146/146 |  |
| 187 | [破TWG](https://ncode.syosetu.com/n9073ca/187/) | [319](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660528458028)、[437](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665368954513) | 81/81 |  |
| 188 | [急ETF](https://ncode.syosetu.com/n9073ca/188/) | [438](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665369115792)–[439](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665369126469)（2話） | 111/111 |  |
| 189 | [抒P/F](https://ncode.syosetu.com/n9073ca/189/) | [260](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330656442607674)、[440](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665369175138) | 129/129 |  |
| 190 | [刃O/S](https://ncode.syosetu.com/n9073ca/190/) | [440](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665369175138)–[442](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665369306771)（3話） | 141/142 |  |
| 191 | [救PTBFB](https://ncode.syosetu.com/n9073ca/191/) | [393](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330663659595761)、[443](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665369573932)、[444](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665369738263)、[445](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665369754951) | 243/243 |  |
| 192 | [除UTL](https://ncode.syosetu.com/n9073ca/192/) | [446](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665369901640)–[448](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665369975099)（3話） | 108/110 |  |
| 193 | [端A](https://ncode.syosetu.com/n9073ca/193/) | [449](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665372292896)–[451](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665372483227)（3話） | 150/150 |  |
| 194 | [窮PMFOOYC](https://ncode.syosetu.com/n9073ca/194/) | [231](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330655650963993)、[452](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665372694271)、[453](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665372723224)、[454](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665372892450)、[455](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665372983203)、[456](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665373019455) | 171/175 |  |
| 195 | [シナモリアキラはここにいる](https://ncode.syosetu.com/n9073ca/195/) | [319](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330660528458028)、[457](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665373240659)、[458](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665373251548)、[459](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665373362717)、[460](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665373379974) | 158/159 |  |
| 196 | [それは素朴で純粋な当たり前の](https://ncode.syosetu.com/n9073ca/196/) | [461](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665373631719)–[463](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330665373664619)（3話） | 123/125 | 改稿削除1 |
| 197 | [エレクトラには向いてない](https://ncode.syosetu.com/n9073ca/197/) | [466](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668909790342) | 64/64 |  |
| 198 | [枯れ木激して死灰に至り、苗木人立ちて雲路を砕く](https://ncode.syosetu.com/n9073ca/198/) | [467](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668909867518)–[469](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668910048485)（3話） | 527/540 | 改稿削除2 |
| 199 | [怒りについて前編](https://ncode.syosetu.com/n9073ca/199/) | [470](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668910400502)–[471](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668910422995)（2話） | 104/104 |  |
| 200 | [自称、幼馴染み](https://ncode.syosetu.com/n9073ca/200/) | [472](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668910449835) | 156/158 |  |
| 201 | [裏切り者の誓い](https://ncode.syosetu.com/n9073ca/201/) | [473](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668910595674) | 192/195 |  |
| 202 | [第一の誘拐](https://ncode.syosetu.com/n9073ca/202/) | [474](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668910652024)–[475](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668910789267)（2話） | 77/77 |  |
| 203 | [神話の子供たち](https://ncode.syosetu.com/n9073ca/203/) | [476](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668910854746) | 118/121 |  |
| 204 | [夢界の兇手](https://ncode.syosetu.com/n9073ca/204/) | [477](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668910930114)–[478](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668910971672)（2話） | 104/104 |  |
| 205 | [トリシュラ暗殺計画](https://ncode.syosetu.com/n9073ca/205/) | [479](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668911069093)–[481](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668911117612)（3話） | 85/87 |  |
| 206 | [怪物退治](https://ncode.syosetu.com/n9073ca/206/) | [482](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668911268043)–[483](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668911304480)（2話） | 87/87 |  |
| 207 | [夜明け前の沈黙](https://ncode.syosetu.com/n9073ca/207/) | [484](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668911356011)–[486](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668911442615)（3話） | 196/198 | 改稿削除1 |
| 208 | [1死者への慰め](https://ncode.syosetu.com/n9073ca/208/) | [487](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668911510499)–[489](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668911718070)（3話） | 163/163 |  |
| 209 | [2今、ここにある断絶](https://ncode.syosetu.com/n9073ca/209/) | [490](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668911803315)–[492](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668911976126)（3話） | 158/158 |  |
| 210 | [3黒蟲騎士団](https://ncode.syosetu.com/n9073ca/210/) | [493](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912062692)–[494](https://kakuyomu.jp/works/16816927859268545348/episodes/16818023212090476756)（2話） | 150/153 |  |
| 211 | [4正しい神の殺し方](https://ncode.syosetu.com/n9073ca/211/) | [495](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912125949)–[496](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912165315)（2話） | 119/120 |  |
| 212 | [正しい未来の選び方](https://ncode.syosetu.com/n9073ca/212/) | [497](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912272414)–[498](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912380198)（2話） | 154/154 |  |
| 213 | [空使いは知らんぷり](https://ncode.syosetu.com/n9073ca/213/) | [499](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912457397) | 120/120 |  |
| 214 | [万獣祭開幕](https://ncode.syosetu.com/n9073ca/214/) | [485](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668911425959)、[500](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912546848) | 66/68 | 改稿削除2 |
| 215 | [テキストベスサキット](https://ncode.syosetu.com/n9073ca/215/) | [501](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912583454) | 116/117 |  |
| 216 | [オルゴの飛翔の呪文](https://ncode.syosetu.com/n9073ca/216/) | [478](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668910971672)、[502](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912595999) | 105/108 | 作者注記1 改稿削除1 |
| 217 | [未来回想、それは破綻した青写真](https://ncode.syosetu.com/n9073ca/217/) | [503](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912620701) | 43/43 |  |
| 218 | [古びた真珠](https://ncode.syosetu.com/n9073ca/218/) | [466](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668909790342)、[504](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912644007) | 101/101 |  |
| 219 | [ペラティアの末裔](https://ncode.syosetu.com/n9073ca/219/) | [505](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912661266) | 210/212 |  |
| 220 | [緑の求婚](https://ncode.syosetu.com/n9073ca/220/) | [506](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912671587) | 69/69 |  |
| 221 | [踏み付けられた死](https://ncode.syosetu.com/n9073ca/221/) | [507](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912681666) | 129/132 |  |
| 222 | [転生都市と冥府システム](https://ncode.syosetu.com/n9073ca/222/) | [508](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912762062)–[509](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912773332)（2話） | 103/103 |  |
| 223 | [転活体験アプリウィズメモリ](https://ncode.syosetu.com/n9073ca/223/) | [510](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912787724) | 103/103 |  |
| 224 | [転活体験アプリウィズメモリ](https://ncode.syosetu.com/n9073ca/224/) | [510](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912787724)–[511](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912803348)（2話） | 83/83 |  |
| 225 | [舞台裏の死角](https://ncode.syosetu.com/n9073ca/225/) | [512](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912815894) | 92/93 |  |
| 226 | [舞台裏の死角](https://ncode.syosetu.com/n9073ca/226/) | [483](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668911304480)、[513](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912835388) | 129/129 |  |
| 227 | [舞台裏の死角](https://ncode.syosetu.com/n9073ca/227/) | [514](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912860427)–[515](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912873682)（2話） | 124/130 |  |
| 228 | [舞台裏の死角](https://ncode.syosetu.com/n9073ca/228/) | [516](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912914293) | 124/126 |  |
| 229 | [舞台裏の死角](https://ncode.syosetu.com/n9073ca/229/) | [515](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912873682)、[517](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912997089)、[518](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913009766) | 147/153 | 改稿削除1 |
| 230 | [誘拐婚1:メトリアン](https://ncode.syosetu.com/n9073ca/230/) | [519](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913024558) | 59/59 |  |
| 231 | [余白と名前](https://ncode.syosetu.com/n9073ca/231/) | [476](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668910854746)、[520](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913070812)、[521](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913083673) | 205/215 | 付録9 |
| 232 | [五章キャラ一覧暫定](https://ncode.syosetu.com/n9073ca/232/) | — | 0/272 | 付録149 |
| 233 | [本選開幕](https://ncode.syosetu.com/n9073ca/233/) | [522](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913096670) | 106/106 |  |
| 234 | [本選開幕](https://ncode.syosetu.com/n9073ca/234/) | [511](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912803348)、[523](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913105414) | 64/64 |  |
| 235 | [本選開幕](https://ncode.syosetu.com/n9073ca/235/) | [524](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913132596)–[525](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913150523)（2話） | 87/88 |  |
| 236 | [本選開幕](https://ncode.syosetu.com/n9073ca/236/) | [526](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913162604) | 108/111 |  |
| 237 | [義憤について](https://ncode.syosetu.com/n9073ca/237/) | [527](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913190205)–[529](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913249611)（3話） | 140/141 |  |
| 238 | [呪文の座として](https://ncode.syosetu.com/n9073ca/238/) | [486](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668911442615)、[530](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913309293)、[531](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913321752) | 85/87 |  |
| 239 | [名無しの王争奪戦](https://ncode.syosetu.com/n9073ca/239/) | [474](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668910652024)、[532](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913361946)、[533](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913374943) | 213/215 |  |
| 240 | [名無しの王争奪戦](https://ncode.syosetu.com/n9073ca/240/) | [533](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913374943)–[535](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913450207)（3話） | 113/120 | 改稿削除1 |
| 241 | [アルトイヴニルと五人の騎士](https://ncode.syosetu.com/n9073ca/241/) | [536](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913470923) | 97/97 |  |
| 242 | [アルトイヴニルと五人の騎士](https://ncode.syosetu.com/n9073ca/242/) | [469](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668910048485)、[537](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913512152)、[538](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913530159) | 101/102 |  |
| 243 | [アルトイヴニルと五人の騎士](https://ncode.syosetu.com/n9073ca/243/) | [533](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913374943)、[539](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913544692) | 170/173 | 改稿削除1 |
| 244 | [名無しの王の行方](https://ncode.syosetu.com/n9073ca/244/) | [540](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913556124) | 97/98 |  |
| 245 | [ユディア対チリアット](https://ncode.syosetu.com/n9073ca/245/) | [541](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913569046) | 86/87 |  |
| 246 | [ユディア対チリアット](https://ncode.syosetu.com/n9073ca/246/) | [468](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668910033188)、[507](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912681666)、[541](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913569046)、[542](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913578617) | 195/207 | 付録2 改稿削除5 |
| 247 | [ユディア対チリアット](https://ncode.syosetu.com/n9073ca/247/) | [505](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912661266)、[543](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913589870) | 76/77 |  |
| 248 | [ユディア対チリアット](https://ncode.syosetu.com/n9073ca/248/) | [544](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913600000) | 73/77 |  |
| 249 | [レジェンド対モレツタボババア](https://ncode.syosetu.com/n9073ca/249/) | [530](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913309293)、[545](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913611443) | 79/81 |  |
| 250 | [レジェンド対モレツタボババア](https://ncode.syosetu.com/n9073ca/250/) | [501](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668912583454)、[546](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913620614) | 95/95 |  |
| 251 | [暴走無人機夜路四駆デッドヒト](https://ncode.syosetu.com/n9073ca/251/) | [547](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913631262) | 111/111 |  |
| 252 | [槍と翼](https://ncode.syosetu.com/n9073ca/252/) | [548](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913641255) | 194/195 |  |
| 253 | [空に架かる虹](https://ncode.syosetu.com/n9073ca/253/) | [549](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913651913) | 84/84 |  |
| 254 | [新時代の風](https://ncode.syosetu.com/n9073ca/254/) | [550](https://kakuyomu.jp/works/16816927859268545348/episodes/16817330668913663503) | 83/83 |  |
| 255 | [ピットイン](https://ncode.syosetu.com/n9073ca/255/) | [551](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093073744018556) | 76/77 |  |
| 256 | [同病相憎む](https://ncode.syosetu.com/n9073ca/256/) | [552](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093073744052530) | 83/86 |  |
| 257 | [虹弓のレメス](https://ncode.syosetu.com/n9073ca/257/) | [553](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093074711504901) | 89/90 |  |
| 258 | [獣、森、洞窟](https://ncode.syosetu.com/n9073ca/258/) | [554](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093074721454194) | 64/66 | 改稿削除1 |
| 259 | [自称、幼馴染リタンズ](https://ncode.syosetu.com/n9073ca/259/) | [555](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093078468680534) | 111/114 |  |
| 260 | [死せる生殖](https://ncode.syosetu.com/n9073ca/260/) | [556](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093085834692098) | 64/64 |  |
| 261 | [人形たちの飛躍、あるいは墜落](https://ncode.syosetu.com/n9073ca/261/) | [557](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093085592509625) | 55/55 |  |
| 262 | [ジグザグリディング](https://ncode.syosetu.com/n9073ca/262/) | [558](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093086356524410) | 75/76 |  |
| 263 | ch00263 | [559](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093087219554377) | 51/51 |  |
| 264 | [垂直落下の飛ばし読み](https://ncode.syosetu.com/n9073ca/264/) | [560](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093087344278343) | 50/51 |  |
| 265 | ch00265 | [561](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093087344311227) | 64/64 |  |
| 266 | [台詞だけで飛べばいいっ!](https://ncode.syosetu.com/n9073ca/266/) | [562](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093087344947692) | 74/74 |  |
| 267 | [そして翼は天へと昇る](https://ncode.syosetu.com/n9073ca/267/) | [563](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093087344958380) | 54/55 | 改稿削除1 |
| 268 | ch00268 | [564](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093088461582603) | 53/53 |  |
| 269 | [天獄藍域](https://ncode.syosetu.com/n9073ca/269/) | [565](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093087345478677) | 86/86 |  |
| 270 | [悪夢の星より来たる](https://ncode.syosetu.com/n9073ca/270/) | [566](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093088060077686) | 79/79 |  |
| 271 | [炎の翼](https://ncode.syosetu.com/n9073ca/271/) | [567](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093089615706986) | 94/94 |  |
| 272 | [永劫線セルアデス](https://ncode.syosetu.com/n9073ca/272/) | [568](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093088060088512) | 64/64 |  |

## カクヨム専用話（27 話・なろう側に該当話なし）

| カクヨム | 章題 | 公開 | 段落 | 解析 |
|---|---|---|---|---|
| [164](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554637292202) | 3-43　松明の騎士① | 2022-05-18 | 227 | 未着手 |
| [165](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554637302344) | 3-44　松明の騎士② | 2022-05-19 | 197 | 未着手 |
| [166](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139554637313387) | 3-45　松明の騎士③ | 2022-05-20 | 176 | 未着手 |
| [188](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555192681166) | 3-64　言震《ワードクェイク》① | 2022-06-11 | 293 | 未着手 |
| [189](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139555192709122) | 3-65　言震《ワードクェイク》② | 2022-06-12 | 216 | 未着手 |
| [230](https://kakuyomu.jp/works/16816927859268545348/episodes/16817139556623473718) | エピローグ　黒血のハルベルト | 2022-08-09 | 340 | 未着手 |
| [569](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093088060408832) | 5-70　リーナちゃんのお人形遊び① | 2025-04-07 | 365 | 未着手 |
| [570](https://kakuyomu.jp/works/16816927859268545348/episodes/16818622172582177277) | 5-71　リーナちゃんのお人形遊び② | 2025-04-08 | 220 | 未着手 |
| [571](https://kakuyomu.jp/works/16816927859268545348/episodes/16818622172582212966) | 5-72　リーナちゃんのお人形遊び③ | 2025-11-12 | 350 | 未着手 |
| [572](https://kakuyomu.jp/works/16816927859268545348/episodes/822139838561099734) | 5-73　リーナちゃんのお人形遊び④ | 2025-11-13 | 264 | 未着手 |
| [573](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093088060219401) | 5-74　『猛禽は群をなさず』 | 2025-11-14 | 204 | 未着手 |
| [574](https://kakuyomu.jp/works/16816927859268545348/episodes/16818093088060207083) | 5-75　愛はさだめ、さだめは血 | 2025-11-16 | 147 | 未着手 |
| [575](https://kakuyomu.jp/works/16816927859268545348/episodes/822139839511170560) | 5-76　天には父、地には母 | 2025-11-17 | 174 | 未着手 |
| [576](https://kakuyomu.jp/works/16816927859268545348/episodes/822139839653092492) | 5-77　横並び | 2025-11-18 | 161 | 未着手 |
| [577](https://kakuyomu.jp/works/16816927859268545348/episodes/822139839590705036) | 5-78　特権の答案、抵抗の呪文 | 2025-11-18 | 183 | 未着手 |
| [578](https://kakuyomu.jp/works/16816927859268545348/episodes/822139839455437598) | 5-79　天空叙述戦 | 2025-11-19 | 199 | 未着手 |
| [579](https://kakuyomu.jp/works/16816927859268545348/episodes/822139839722902529) | 5-80　名前を巡る攻防 | 2025-11-20 | 207 | 未着手 |
| [580](https://kakuyomu.jp/works/16816927859268545348/episodes/822139839838402682) | 5-81　鍵の名はフローラとファウナ | 2025-11-21 | 172 | 未着手 |
| [581](https://kakuyomu.jp/works/16816927859268545348/episodes/822139839788298005) | 5-82　混線稲妻 | 2025-11-23 | 208 | 未着手 |
| [582](https://kakuyomu.jp/works/16816927859268545348/episodes/822139840027364226) | 5-83　大いなる歴史を超えて | 2025-11-23 | 223 | 未着手 |
| [583](https://kakuyomu.jp/works/16816927859268545348/episodes/822139840034345377) | 5-84　白百合の夢 | 2025-11-24 | 232 | 未着手 |
| [584](https://kakuyomu.jp/works/16816927859268545348/episodes/822139840104569183) | 5-85　藍緑血戦 | 2025-11-25 | 205 | 未着手 |
| [585](https://kakuyomu.jp/works/16816927859268545348/episodes/822139840171010016) | 5-86　希望の祈りよ夜明けに届け | 2025-11-26 | 152 | 未着手 |
| [586](https://kakuyomu.jp/works/16816927859268545348/episodes/822139840170906076) | 5-87　舞台裏の約定 | 2025-11-27 | 305 | 未着手 |
| [587](https://kakuyomu.jp/works/16816927859268545348/episodes/822139839840024500) | 5-88　融血天主・紀気混沌 | 2025-11-28 | 351 | 未着手 |
| [588](https://kakuyomu.jp/works/16816927859268545348/episodes/822139840292977248) | 5-89　穢れた風を切って飛べ | 2025-11-29 | 222 | 未着手 |
| [589](https://kakuyomu.jp/works/16816927859268545348/episodes/822139840355665693) | 5-90　愛の森を越えろ | 2025-11-30 | 134 | 未着手 |

## 参照

- 生成: `AllusionistWiki_work/scripts/build_edition_article.py`（データ: `work/allusionist_v2/L0/runs/20261017T2011_f863/`、`work/allusionist_v2/L1/runs/20261018T0040_588c/`）
- ¶ アンカー: カクヨム episode ページの段落 ID `#pN` と 1:1。なろう版 p 番号（baseline 旧来歴）とは巻内で非対応。
- 削除台帳の理由分類: 付録=キャラ一覧・プロフィール・章構造メタ・作者注記（カクヨム正典は本文のみ）/ なろう専用幕間=カクヨムに同名作品なし / 幕間短縮=同名カクヨム話で削除された場面 / 改稿削除=カクヨム全巻全文検索で非存在確認。

