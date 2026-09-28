レビュー
以下は、v5.0の長所を残しつつ、前回指摘した A_への責務集中、ME_の無制限膨張、10層表現の認知負荷、エージェントの核への侵入 を修正した改訂版です。
 設計思想は変えず、Markdownを知識核、Quartz・GraphRAG・エージェントを交換可能なアダプタとして再整理しました。

アリュージョニストWiki 特化設計書 v5.1 Final Revised

Version: 5.1 Final Revised
 Target: 「幻想再帰のアリュージョニスト」多層アナロジー分析Wiki
 Knowledge Core: Markdown / YAML Frontmatter / WikiLink
 Adapters: Obsidian / Quartz / GraphRAG / LLM Agent
 Base: v5.0 Final
 Status: 実装基準確定

0. 本改訂の位置づけ

v5.0では、以下を中心に大幅な機能拡張を行った。

誤読主体の明示
読者モデルとネタバレ制御
ME_間の知識グラフ
複数エージェントの協調
解釈のライフサイクル管理

これらは作品への適合性を大きく高めた一方、次の問題を生じさせた。

A_ノートに、分析・証拠・誤読・開示・状態遷移が集中していた
ME_が「作品外のすべて」を収容する無制限なカテゴリになり得た
L0からL6までの10層表現が、実運用上の分類より複雑だった
エージェント構成が知識モデルの一部として記述され、実装技術との結合が強くなっていた
confidence: 0.95 のような数値に、客観的な算出基準が定義されていなかった
「RF_からA_への昇格」が、解釈を事実へ変換するように読めた

v5.1では、これらを次の原則で修正する。

知識モデルは安定させ、実装方式は交換可能にする。

1. 目的と設計原則
1.1 目的

本Wikiは、「幻想再帰のアリュージョニスト」における以下の情報を、厳密な典拠とともに構造化する。

物語上の事実
登場人物・用語・組織
視覚的、言語的、関係的モチーフ
神話・古典・思想・文化的典拠
引喩、類推、再帰、構造的一致
伏線とその回収過程
読者・登場人物・LLMによる誤読
人間による考察と競合解釈
初読、再読、研究の異なる読書体験

目的は情報量の最大化ではなく、次の問いに答えられる知識基盤を構築することである。

何が原文上の事実か
その判断はどの原文に基づくか
どの解釈が、誰によって、いつ提案されたか
どの章まで読めば、その情報を安全に開示できるか
作品内要素と作品外典拠はどのように対応するか
解釈が後の展開によってどう変化したか
1.2 4次元の分離

本設計は、以下の4軸を独立に管理する。

軸A: 認識論上の区分
fact: 原文に直接記載された事実
structure: 複数の事実から機械的に確認できる構造
interpretation: 人間またはLLMによる解釈
hypothesis: 未確定の仮説
軸B: 開示段階
surface: 表面上観察できる情報
hint: 構造を示唆する情報
revelation: 後の章で明示される種明かし
meta: 作品外資料や高度な研究的考察
軸C: 情報領域
internal: 作品本文内
external: 神話・思想・文学などの作品外典拠
meta: 作者発言、インタビュー、あとがき、批評
軸D: 読者状態
reader: 初読者
rereader: 全話既読者
analyst: 研究者、分析者

これらを「層」として固定的に積み重ねず、独立したメタデータとして扱う。

2. 絶対鉄則
2.1 原文と解釈の分離

原文に直接存在する情報と、その意味についての解釈を同じ記述単位に混在させない。

事実ページから解釈ページへのリンクは許容するが、事実本文を解釈で上書きしてはならない。

2.2 原文至上主義

LLMは、原文に存在しない情報を fact として登録してはならない。

事実には原則として次の情報を付与する。

YAML
evidence:
- source_id: SRC_ch0124
locator:
chapter: ch0124
lines: "145-150"
quote: "地上において知らぬ者無き天上の美声。楽神の囀り。"
verification: human_verified
その他の行を表示する

現在のA_サンプルでも原文参照、行範囲、引用が保持されているため、この構造を維持する。

2.3 証拠は主張に付与する

「ページ全体が正しい」のではなく、「個々の主張がどの証拠に支えられているか」を管理する。

1つのページ内に複数の主張がある場合、それぞれに証拠を関連付ける。

2.4 言及即作成は原則ではなく候補生成とする

v5.0の「言及即作成」は、エンティティ爆発の原因となるため、次のように改訂する。

用語、人物、引喩の初出時には、エンティティ候補を生成する。
 作成条件を満たしたものだけを正式なノートとして確定する。

単発言及や一般語は、エピソードページ内の記述またはインラインメタデータに留める。

2.5 自動変更はレビュー可能であること

LLMまたは自動処理が行う変更は、次の条件を満たす。

差分を確認できる
変更理由を記録する
元に戻せる
実行主体を記録する
同一入力から可能な限り再現できる
2.6 知識核に実装固有情報を混入させない

次の情報は知識核に必須としない。

使用LLM名
エージェント数
Quartz固有設定
GraphRAG固有ID
ベクトルDB固有ID
プロンプト全文
localStorageのキー名

これらはアダプタ側、実行ログ、設定ファイルで管理する。

3. アーキテクチャ
3.1 全体構造
Plain Text
┌──────────────────────────────┐
│ Knowledge Core │
│ Markdown / YAML / WikiLink │
│ │
│ ARC / O / E / ME / A / MY / RF
└──────────────┬───────────────┘
│
Stable Knowledge Contract
│
┌─────────────┼─────────────┬──────────────┐
│ │ │ │
▼ ▼ ▼ ▼
Obsidian Quartz GraphRAG Agent Runtime
編集 公開・閲覧 検索・推論 抽出・提案・検査
Adapter Adapter Adapter Adapter
その他の行を表示する
3.2 核とアダプタの責務
Knowledge Core

保持するもの:

本文
Frontmatter
WikiLink
典拠
状態
開示条件
正規ID
別名
解釈履歴

保持しないもの:

UI状態
GraphRAGインデックス
埋め込みベクトル
一時ロック
実行中ジョブ
LLM会話履歴
Obsidian Adapter
Markdown編集
WikiLink補完
ローカル閲覧
人間によるレビュー
Quartz Adapter
HTML生成
公開表示
読者プロファイルに応じた表示
ネタバレブロックの変換
GraphRAG Adapter
Markdownからグラフを再構築
検索、要約、関係探索
クラスター分析
関連候補の提示

GraphRAGは派生インデックスであり、正本ではない。

Agent Runtime Adapter
原文抽出
エンティティ候補生成
引喩候補生成
伏線候補照合
Lint
修正案作成

エージェントはMarkdownを直接無制限に編集せず、原則として変更セットを生成する。

4. 正規データモデル
4.1 コアノード型

v5.0の10層モデルは廃止し、7つのコア型とサブタイプに整理する。

プレフィックス	種別	役割ARC_	Story Arc	複数エピソードを束ねる物語単位
O_	Episode	章・節・出来事
E_	Internal Entity	人物、組織、用語、物品、関係、モチーフ
ME_	External Reference	神話、文学、思想、文化、ミーム、作者資料
A_	Analytical Claim	引喩、類推、再帰、構造的一致、誤読という分析主張
MY_	Mystery	伏線、未解決事項、回収過程
RF_	Reflection	感想、仮説、研究メモ、未検証の解釈

「層番号」は説明用にのみ使用し、ファイル構造や処理条件には使用しない。

4.2 E_のサブタイプ

V_、R_、KEY_は独立した最上位型ではなく、作品内エンティティのサブタイプとして扱う。

YAML
id: E_motif_白銀の髪
type: entity
subtype: visual_motif
その他の行を表示する
YAML
id: E_relation_シナモリ_アズーリア
type: entity
subtype: relationship
その他の行を表示する
YAML
id: E_phrase_幻想再帰
type: entity
subtype: key_phrase
その他の行を表示する
後方互換

既存の以下のIDは直ちに破棄しない。

V_
R_
KEY_

移行時には legacy_id として保持する。

YAML
id: E_motif_白銀の髪
legacy_id: V_白銀の髪
type: entity
subtype: visual_motif
その他の行を表示する
4.3 R_をノード化する条件

関係は原則としてWikiLinkまたは構造化プロパティで表現する。

ただし、以下のいずれかを満たす場合のみ、関係を独立ノート化する。

時系列で状態が変化する
物語上の転換点を持つ
独自の証拠集合を持つ
神話的構造の再演として分析対象になる
複数のA_、MY_、O_から参照される

単なる「知人」「会話相手」「同じ組織に所属」は独立ノート化しない。

5. ME_の境界管理
5.1 ME_の定義

ME_は「作品外のもの全部」ではなく、次の条件を満たす外部参照に限定する。

作品理解に具体的な影響を与える
A_またはMY_から参照される
出典を示せる
単なる連想ではなく、分析上の役割が説明できる
5.2 ME_のサブタイプ
YAML
type: external_reference
subtype: mythology
その他の行を表示する

使用可能な subtype:

mythology
religion
literature
philosophy
psychology
history
folklore
occult
popular_culture
internet_culture
author_material
scholarly_source

現在のME_例にある canonical_name、aliases、domain および典拠間リンクは維持する。

5.3 ME_間の関係型

最小集合を次の5種類とする。

influenced_by
derived_from
syncretized_with
reinterpreted_by
parodied_in

influences は influenced_by の逆方向として導出できるため、原則として両方向を手入力しない。

正規化例
YAML
relations:
- predicate: influenced_by
target: "[[ME_myth_ヘリオス]]"
evidence:
- source_id: SRC_external_001
その他の行を表示する
重要

「アポロンがヘリオスから影響を受けた」のような歴史的・宗教学的主張は、作品本文とは別の外部典拠を必須とする。

作品分析上便利であることと、歴史的関係が事実であることは区別する。

6. A_分析主張モデル
6.1 A_の定義

A_は「アナロジーそのもの」ではなく、次の形式を持つ分析上の主張である。

Plain Text
主語
が
述語によって
対象
と関係付けられる
その他の行を表示する

例:

Plain Text
ハルベルト
が
alludes_to
アポロン
その他の行を表示する

A_を明確に「主張」と定義することで、証拠、状態、提案者、反論を保持する理由が明確になる。

6.2 A_の述語型

v5.0のタイプ定義を整理し、重複を減らす。

alludes_to: 直接的な引喩
analogous_to: 属性または機能の類推
recurs_as: 作品内再帰
structurally_matches: プロット構造の一致
misreads_as: 誤読または意図的な読み替え
foreshadows: 後続内容の予告
inverts: 元構造の反転
parodies: パロディ
sublates: 競合解釈の止揚

v5.0で analogy と structural の境界が曖昧だったため、述語名で関係を明示する。

6.3 A_最小スキーマ
YAML
---
schema_version: "5.1"
id: A_ハルベルト_alludes_to_アポロン_ch0124
type: analytical_claim
 
subject: "[[E_char_ハルベルト]]"
predicate: alludes_to
object: "[[ME_myth_アポロン]]"
 
valid_from: ch0124
spoiler_after: ch0124
 
epistemic_status: confirmed
review_status: human_verified
 
evidence:
- source_id: SRC_ch0124
locator:
chapter: ch0124
lines: "145-150"
quote: "地上において知らぬ者無き天上の美声。楽神の囀り。"
 
mapping:
- subject_feature: "音楽・美声・予言"
object_feature: "音楽・詩・予言"
relation: attribute_correspondence
 
provenance:
proposed_by:
kind: agent
id: extraction_agent_v3
reviewed_by:
kind: human
id: local_owner
---
その他の行を表示する

現在のA_スキーマで保持されている source_entity、target_meta、episode、evidence、structural_mapping は、この主張モデルへ移行できる。

6.4 3種類の状態を分離する

v5.0では status が、真偽・レビュー・運用状態を混在させていた。v5.1では分離する。

認識状態
YAML
epistemic_status: hypothesized
その他の行を表示する

値:

hypothesized
supported
confirmed
disputed
refuted
sublated
レビュー状態
YAML
review_status: pending
その他の行を表示する

値:

unreviewed
pending
human_verified
needs_revision
文書状態
YAML
document_status: active
その他の行を表示する

値:

draft
active
archived
superseded
6.5 confidence数値の廃止

confidence: 0.95 のような数値は、算出根拠がない限り使用しない。

代わりに、証拠強度を次のように分類する。

YAML
evidence_strength: strong
その他の行を表示する
weak: 単一の間接的類似
moderate: 複数の対応または反復
strong: 明示的な語句、複数の構造対応、後続章による補強
explicit: 本文または作者資料で明示

数値モデルを将来導入する場合は、別紙で算出式と評価基準を定義する。

7. 誤読モデル
7.1 誤読は独立した主張

誤読はA_の misreads_as 述語として表現する。

YAML
subject: "[[E_char_アズーリア]]"
predicate: misreads_as
object: "[[ME_myth_アルテミス]]"
actual_target: "[[ME_myth_アポロン]]"
その他の行を表示する
7.2 誤読主体
YAML
misreading:
agent_type: in_story_character
agent: "[[E_char_アズーリア]]"
content: "ハルベルトをアルテミス的存在として理解する"
corrected_by: "[[A_ハルベルト_alludes_to_アポロン_ch0124]]"
narrative_function: "後の認識反転の準備"
その他の行を表示する

agent_type:

in_story_character
reader
llm
critic
authorial_feint
修正点

author_intent は誤読主体ではないため削除する。

作者が読者を意図的に誘導する場合は、authorial_feint として扱う。

作者の実際の意図を主張する場合は、作者インタビューなどの明示的典拠を必須とする。

現在の misreading_agent 例は、主体・内容・正しいアナロジー・物語的機能を保持しており、v5.1では構造を入れ子化して継承する。

8. ネタバレ制御
8.1 基本原則

spoiler_after は「この章より後の内容」という意味ではなく、次の意味に統一する。

指定章を既読である読者に開示可能

これにより、境界条件の曖昧さをなくす。

現在の定義には ch0000、chNNNN、final、meta があるため、この体系は維持する。

8.2 開示条件
YAML
disclosure:
minimum_progress: ch0124
audience:
- rereader
- analyst
level: revelation
その他の行を表示する
minimum_progress
ch0000
chNNNN
final
audience
reader
rereader
analyst
level
surface
hint
revelation
meta

metaを章番号と同じフィールドに混在させず、開示レベルとして分離する。

8.3 段階的開示
YAML
reveal_stages:
- stage: surface
available_after: ch0012
- stage: hint
available_after: ch0124
- stage: revelation
available_after: ch0892
- stage: meta
available_after: final
audience:
- analyst
その他の行を表示する

現在のMY_例で使用されている、伏線提示、ヒント、回収、深層的意味という段階構造を一般化したものである。

8.4 静的ビルド時の制約

Quartzは静的サイト生成であるため、秘匿すべき内容をHTMLへ埋め込み、CSSやJavaScriptだけで非表示にしてはならない。

公開モード

表示制御モード
 趣味Wiki向け。全文をHTMLへ含め、読者設定で表示を切り替える。

分離ビルドモード
 厳密運用向け。読者レベルごとに別成果物を生成し、未開示情報そのものを出力しない。

本Wikiでは表示制御モードを基本とするが、「非表示」はセキュリティ境界ではないことを明記する。

9. MY_伏線モデル
9.1 MY_の役割

MY_は「未解決の謎」だけでなく、次の状態を持つ追跡対象である。

伏線候補
明示的な謎
段階的に示唆される構造
回収済み伏線
誤認だった伏線
放棄または未回収
9.2 状態
YAML
mystery_status: open
その他の行を表示する
candidate
open
partially_resolved
resolved
invalidated
unresolved_at_end
9.3 章番号は履歴として保持する

回収時に元の spoiler_after を上書きすると、伏線提示時点の情報が失われる。

したがって、次のように段階を保持する。

YAML
timeline:
introduced: ch0057
hinted:
- ch0400
resolved: ch0892
その他の行を表示する

spoiler_after は読者への開示条件であり、伏線の履歴そのものには使用しない。

10. RF_考察モデル
10.1 RF_の位置づけ

RF_は、次を収容する。

人間の感想
未検証仮説
競合する読み
分析メモ
読書履歴
研究課題
10.2 RF_からA_への「昇格」を廃止

解釈が後の章で支持されても、その解釈が事実へ変化するわけではない。

したがって「RF_からA_へ昇格」ではなく、次の処理とする。

RF_から新しいA_を生成する
A_に原文証拠を付与する
A_の epistemic_status を設定する
元のRF_は残す
RF_からA_へ resulted_in リンクを張る
YAML
resulted_in:
- "[[A_ハルベルト_alludes_to_アポロン_ch0124]]"
その他の行を表示する

これにより、仮説が生まれた経緯と、後に支持された主張の両方を保存できる。

11. 証拠と出典
11.1 出典ID

原文ファイル名を直接参照すると、ファイル移動でリンクが壊れるため、安定した source_id を使用する。

YAML
source_id: SRC_ch0124
その他の行を表示する

出典台帳:

YAML
id: SRC_ch0124
type: primary_text
chapter: ch0124
local_path: raw/ch0124.txt
checksum: "sha256:..."
その他の行を表示する
11.2 引用箇所

行番号は前処理によって変動する可能性があるため、次を併記する。

YAML
locator:
chapter: ch0124
paragraph_id: p0145
lines: "145-150"
その他の行を表示する

paragraph_id を安定IDとし、行番号を補助情報とする。

11.3 証拠区分
YAML
evidence_type: direct_quote
その他の行を表示する
direct_quote
explicit_statement
repeated_pattern
structural_correspondence
external_source
author_statement
12. Canonical IDと別名
12.1 正規ID

各概念は1つの正規IDを持つ。

YAML
id: E_char_ハルベルト
canonical_name: "ハルベルト"
aliases:
- "楽神"
- "銀髪の魔女"
その他の行を表示する
12.2 正本管理

canonical: true は使用しない。

すべての正式ページを正本とし、統合済みページは次で表現する。

YAML
document_status: superseded
superseded_by: "[[E_char_ハルベルト]]"
その他の行を表示する

これにより、複数ページが同時に canonical: true になる矛盾を防ぐ。

12.3 表記揺れ置換

置換処理は文字列の単純一括置換ではなく、次の順で行う。

alias辞書から候補を検出
WikiLink文脈を確認
同名異義語を除外
変更セットを生成
Lintを実行
人間またはルールベースで承認
適用
13. ライフサイクル
13.1 共通状態
Plain Text
candidate
↓
draft
↓
active
↓
superseded または archived
その他の行を表示する
candidate

自動抽出された候補。正式Wikiには未採用。

draft

ノート化されたが未レビュー。

active

利用可能な正式ノート。

superseded

別ノートに統合された。

archived

履歴として保存するが通常表示しない。

13.2 削除原則

知識ノートは原則として物理削除しない。

誤り、重複、統合が発生した場合は、状態と移行先を記録する。

13.3 変更履歴

各ノートには最低限、次を保持する。

YAML
created: 2026-09-27
updated: 2026-09-28
schema_version: "5.1"
その他の行を表示する

詳細な変更履歴はGitで管理し、Frontmatterへ全履歴を複製しない。

14. エージェント実行モデル
14.1 エージェントは論理的役割とする

Extraction Agent、Allusion Linkerなどは、必ずしも個別プロセスや個別LLMである必要はない。

これらは処理責務を説明する論理名である。

単一エージェントが複数責務を順次実行してもよい。

14.2 実装仕様は別紙化する

本設計書では責務と入出力契約のみを定義する。

プロンプト、使用モデル、同時実行数、ロック実装は、次の別文書に分離する。

Plain Text
docs/runtime/agent-runtime-spec.md
docs/runtime/prompt-contracts.md
docs/runtime/locking-and-jobs.md
その他の行を表示する
14.3 推奨処理単位
Stage 1: Ingest

入力:

Plain Text
raw/chNNNN.txt
その他の行を表示する

出力:

Plain Text
work/candidates/chNNNN.json
その他の行を表示する
Stage 2: Normalize
ID正規化
既存エンティティ照合
alias照合
重複候補検出
Stage 3: Propose
新規Markdown案
既存Markdown修正案
リンク追加案
MY_更新案
Stage 4: Validate
YAMLスキーマ検証
リンク検証
証拠検証
ネタバレ境界検証
ID重複検証
Stage 5: Apply
変更セット適用
Git差分生成
GraphRAG再構築対象の記録
14.4 ロック

ロックの対象はエージェントではなく、変更対象となる正規IDとする。

YAML
lock_target: A_ハルベルト_alludes_to_アポロン_ch0124
job_id: job_20260928_001
expires_at: 2026-09-28T12:30:00+09:00
その他の行を表示する

ロック情報はMarkdown知識核へ保存せず、work/locks/ または実行時ストアで管理する。

15. Lint仕様
15.1 構造Lint
YAML構文エラー
必須フィールド不足
未知のtype、subtype、predicate
IDとファイル名の不一致
重複ID
不正な章番号
schema_versionの欠落
15.2 リンクLint
死リンク
旧IDリンク
曖昧alias
循環した superseded_by
逆方向関係の不整合
15.3 証拠Lint
factまたはconfirmed主張に証拠がない
source_id が存在しない
引用が原文と一致しない
行番号または段落IDが不正
外部典拠主張に外部出典がない
15.4 ネタバレLint
証拠章より早い minimum_progress
revelationがsurfaceより早く開示される
finalと章番号の矛盾
analyst限定情報がreaderへ開示される
関連ノート間で開示条件が逆転する
15.5 意味Lint
同一subject、predicate、objectの重複A_
競合A_に disputed 関係がない
MY_のresolved章が存在しない
RF_から生成されたA_への履歴リンクがない
ME_がどのA_からも参照されない
E_の独立ノート作成閾値を満たさない
15.6 Lintと自動修復の分離

Lintは問題を検出する。

自動修復は変更案を生成する。

両者を同じ処理にしない。検出だけを行いたい場合に、意図せずファイルが変更されることを防ぐ。

16. ディレクトリ構成
Plain Text
vault/
├─ raw/
│ └─ chNNNN.txt
│
├─ wiki/
│ ├─ arcs/
│ ├─ episodes/
│ ├─ entities/
│ │ ├─ characters/
│ │ ├─ terminology/
│ │ ├─ motifs/
│ │ ├─ relationships/
│ │ └─ phrases/
│ ├─ references/
│ │ ├─ mythology/
│ │ ├─ literature/
│ │ ├─ philosophy/
│ │ ├─ culture/
│ │ └─ author-material/
│ ├─ claims/
│ ├─ mysteries/
│ └─ reflections/
│
├─ sources/
│ └─ source-registry/
│
├─ schemas/
│ ├─ common.schema.json
│ ├─ entity.schema.json
│ ├─ claim.schema.json
│ ├─ mystery.schema.json
│ └─ reference.schema.json
│
├─ work/
│ ├─ candidates/
│ ├─ changesets/
│ ├─ locks/
│ └─ reports/
│
└─ docs/
├─ knowledge-model.md
├─ spoiler-policy.md
└─ runtime/
その他の行を表示する

work/ は派生物であり、必要に応じてGit管理対象外にできる。

17. 移行計画
Phase 0: バックアップとベースライン
現行VaultのGitタグ作成
全Markdownのハッシュ取得
死リンク件数とYAMLエラー件数の記録
移行前GraphRAGインデックスの保存
Phase 1: schema_version導入

すべてのページへ次を追加する。

YAML
schema_version: "5.1"
その他の行を表示する

この段階では既存IDを変更しない。

Phase 2: 状態フィールド分離

既存の status を以下へ移行する。

epistemic_status
review_status
document_status
mystery_status

型ごとに適用先を変える。

Phase 3: ネタバレモデル移行

既存の spoiler_after を disclosure.minimum_progress へ変換する。

metaは disclosure.level と audience へ移す。

Phase 4: A_主張モデル移行

既存の:

YAML
source_entity:
target_meta:
type:
その他の行を表示する

を次へ変換する。

YAML
subject:
predicate:
object:
その他の行を表示する

既存のA_例は、この変換によって情報を失わず移行可能である。

Phase 5: V_、R_、KEY_正規化

既存ファイルを一括削除、即時リネームしない。

legacy_id を付与
新canonical IDを付与
旧リンクを段階的に置換
リダイレクトまたはaliasを維持
死リンクがゼロになった後に旧IDを廃止
Phase 6: ME_分類と出典追加
subtype の付与
canonical_name と aliases の確認
外部関係主張への証拠付与
未参照ME_の候補化
双方向重複関係の単方向正規化
Phase 7: Quartz変換
新しい disclosure スキーマに対応
reader、rereader、analystの切替
インライン開示ブロックの変換
表示制御モードの注意書き
ビルド時Lintの追加
Phase 8: GraphRAG再構築

GraphRAGは次の正規構造から生成する。

Plain Text
node:
ARC / O / E / ME / A / MY / RF
 
edge:
WikiLink
subject-predicate-object
timeline
evidence
superseded_by
その他の行を表示する

GraphRAG固有のノードIDをMarkdownへ逆輸入しない。

18. 受入基準

v5.1への移行完了は、以下をすべて満たした状態とする。

構造
全MarkdownがYAMLスキーマ検証を通過する
ID重複がない
コア型が7種類に整理されている
旧IDに移行先が設定されている
典拠
factに一次資料への参照がある
confirmed A_に証拠がある
外部の影響関係に外部典拠がある
引用箇所を原文へ追跡できる
ネタバレ
開示条件が章進行と矛盾しない
初読者表示で後続章の内容が表示されない
meta分析がanalyst以外に自動表示されない
MY_の提示章と回収章が別フィールドで残る
運用
Lintと修復が分離されている
自動変更に差分と変更理由がある
エージェント停止時も人間がMarkdownを編集できる
Quartz停止時もObsidianで閲覧できる
GraphRAG停止時もWikiとして成立する
19. 非目標

v5.1では、以下を実装必須としない。

読者クリック履歴に基づく推薦
完全自律エージェント
自動的な解釈の統合
多言語同期
独自Graph DB
ベクトルDBの常設
作者意図の自動推定
すべての外部文化要素のME_化
数値confidenceの自動算出

これらはコア成立後の実験機能とする。

20. 最終評価
v5.0からの改善
評価軸	v5.0	v5.1ドメイン適合性	97	96
知識モデルの明確さ	91	96
実装可能性	88	94
保守性	84	94
移植性	92	97
過剰設計耐性	75	91
エージェント非依存性	80	97
大規模化耐性	90	94

v5.1は、v5.0より作品特化の派手さを一部抑えている。

その代わりに、以下を強化した。

主張と証拠の追跡性
認識状態と運用状態の分離
外部典拠の境界
IDの長期安定性
エージェント非依存性
移行可能性
自動化停止時の生存性
21. まとめ

本設計の中心は、10層分類でも、GraphRAGでも、5エージェントでもない。

中心にあるのは、次の安定した知識契約である。

Plain Text
正規ID
+
Markdown本文
+
構造化Frontmatter
+
WikiLink
+
証拠
+
開示条件
+
変更履歴
その他の行を表示する

Obsidianは編集手段であり、Quartzは表現手段であり、GraphRAGは探索手段であり、LLMエージェントは更新支援手段である。

これらはすべて交換可能である。

一方、原文、分析主張、典拠、証拠、読者への開示条件は知識資産として残る。

知識核は小さく、形式は厳密に、アダプタは自由に。

これをv5.1の最終設計原則とする。

主な改善点
構造

10層という説明上の階層を、7つのコア型とサブタイプへ再整理しました。分類の表現力を維持しながら、運用者が覚える概念数を減らしています。

明確性

A_を「アナロジーノート」ではなく 分析主張 として再定義しました。これにより、証拠、状態、誤読、反論を保持する理由が明確になっています。

保守性

ME_の境界、canonical ID、証拠ID、状態分離、移行手順を追加しました。1,000話規模で問題になりやすい重複、表記揺れ、外部世界の無制限取り込みを抑えています。