# AllusionistWiki2 設計仕様書（現行実装版）

> 版: 実装基準 2026-09-28（v5.1 知識モデル + v5.2 検索最適化/三層分離 + Strata 対応 + キャラクター状態モデル拡張）
> 権威: 本ファイルは「現在動いているもの」の仕様。理念・詳細は `knowledge-model-v5.1.md`（知識モデル）と `knowledge-model-v5.2-search.md`（検索最適化）が上位設計書。

---

## 1. リポジトリ構成（3リポジトリ分離）

| リポジトリ | 役割 | 内容 |
|:---|:---|:---|
| `AllusionistLLMWiki2`（本repo） | ソース・オブ・トゥルース（Obsidian vault / 知識核） | `wiki/`（正規層）、`sources/`、`schemas/`、`scripts/`、`docs/` |
| `AllusionistLLMWiki2_Work` | 作業派生物（再構築可能） | `events/`（第1層）、`staging/`（第2層）、`search/`（検索DB）、`reports/`、`logs/`、`backups/` |
| `AllusionistLLMWiki2_Quartz` | 公開サイト（CI ビルド） | vault の `wiki/` を取得して Quartz で静的生成 |

- 整合性: 相互コミット参照（`work-ref:` / `vault-ref:` + `SYNC_LOG.md`）。同時コミットは `scripts/commit_all.py`
- `raw/`（原文）は Git 管理外・非公開（gitignore）
- 既定ブランチ `main`。作業ブランチは `bionic/` 接頭辞
- ライセンス: wiki 本文 CC BY-NC-SA 4.0 / コード・設定 MIT / 第三者・原作素材は除外（`LICENSE.md`。未解決の法的注記2件あり: Rights Holder Override の NC 上書き問題、ファン部分利用の無帰属条項は CC 外付与である旨の明示）

## 2. 知識モデル（v5.1 由来・現行）

### 2.1 コア型（7種）と ID 体系

| 型 | ID prefix | ディレクトリ | 用途 |
|:---|:---|:---|:---|
| arc | `ARC_` | `wiki/arcs/` | アーク（章範囲・マクロアナロジー） |
| episode | `O_{chNNNN}_summary` | `wiki/episodes/` | 章の要約・要素リンク |
| entity | `E_char_/E_term_/E_org_/E_item_/E_motif_/E_relation_/E_phrase_` | `wiki/entities/<type>/` | 作品内エンティティ（7サブタイプ） |
| external_reference | `ME_myth_/ME_lit_/ME_phil_/ME_psych_/ME_pop_/ME_author_` | `wiki/references/<domain>/` | 外部典拠 |
| analytical_claim | `A_{predicate}_...` | `wiki/claims/` | 分析主張（9述語: alludes_to / analogous_to / recurs_as / structurally_matches / misreads_as / foreshadows / inverts / parodies / sublates） |
| mystery | `MY_` | `wiki/mysteries/` | 伏線（タイムライン付き状態機械） |
| reflection | `RF_` | `wiki/reflections/` | 考察・メタ |
| source | `SRC_chNNNN` / `SRC_external_NNN` | `sources/` | 出典台帳 |

- ファイル名 = 正規ID + `.md`。Frontmatter は `schemas/*.schema.json`（draft-07）準拠、`schema_version: "5.1"` 必須
- 状態の3系統分離: `epistemic_status`（確からしさ）/ `review_status`（人間レビュー）/ `document_status`（文書ライフサイクル）
- 開示: `spoiler_after`（章進行基準）+ `disclosure`（対象別）
- 証拠: `source_id` + `locator`（chapter/lines/paragraph_id）+ `quote`（原文至上主義）
- リンクは Obsidian wiki-link `[[ID]]`

### 2.2 キャラクター状態モデル（拡張済み・すべて省略可能）

`subtype: character` に限り追加フィールドを許容（後方互換維持）:

- **4層アイデンティティ**: `actor_ref`（背後の実体への参照）、`self_designations[]`（自称 + `reliability: reliable/unreliable/self_deceptive/unknown` + evidence。self_deceptive は `misreads_as` 主張と連携）
- **所属の時間軸**: `affiliations[]`（org / valid_from / valid_to: chNNNN|ongoing|unknown / nature: public/secret/nominal/de_facto/former / role_in_org）
- **物語的状態遷移**: `alive_status`（alive/dead/unknown/transformed/transcended/split + since）、`current_location`、`narrative_role[]`
- **開示管理**: `disclosure`（true_identity_revealed_at / reader_awareness_level: completely_unknown→fully_known 4段階 / spoiler_sensitivity）
- **統合キュー**: `merge_candidates[]`（target / reason / similarity_score 0-1 / status: proposed→under_review→approved/rejected / proposed_by: human|agent）
- **系譜**: `identity_genealogy`（split_from + nature: literal_split/metaphorical/perceived/retconned / merged_into / branched_to / collective_identity）

## 3. 三層分離パイプライン（v5.2）

```
raw/chNNNN.txt（原文・非公開）
  ↓ extract_chapter.py        … LLM抽出 → 検証通過分のみ
work/events/chNNNN.jsonl      … 第1層: イベント（event.schema.json）
  ↓ aggregate_events.py       … 集約
work/staging/staging_chNNNN.yaml … 第2層: 中間集約（staging.schema.json）
  ↓ merge_all.py（5マージャー）  … 正規層マージ（べき等）
wiki/**.md                    … 第3層: 正規層（entity/claim/mystery/reference/episode/arc）
  ↓ lint.py                   … 検証（検出のみ）
```

- 第1層イベント ID: `E_ch{NNNN}_{entity_type}_{entity}_{aspect略称}_O`（aspect: visual/name/speech/action/relationship/symbolic → V/N/S/A/R/Y）
- 第3層マージはべき等（再実行で重複・劣化なし）。Lint 通過を以て完了とする
- 自動修復は `fix_all.py`（L1-L3 安全レベル・バックアップ・変更ログ）。Lint 本体は検出のみ（分離原則）

## 4. 検索（v5.2 ハイブリッド検索）

`scripts/search.py` + `scripts/search_modules/`（indexer / vector_store / hybrid_search / query_router）

- **構造化SQL**（第1層イベント: entity/aspect/episode 索引）
- **FTS5 全文**（entities/claims/refs/episodes。日本語は unicode61 で分かち書きされないため FTS 空振り時 LIKE フォールバック）
- **ベクトル**（ollama / openai_compatible 埋め込み、`config.yaml search.embedding_provider`）
- **RRF 統合**（k=60）+ 日本語クエリルーティング（構造化/エピソード/意味/ハイブリッド）
- DB は work 側: `work/search/search_index.db`、`work/search/vector_store.db`。`search.py --build` で再構築
- 既知の制約: `references` は SQLite 予約語 → テーブル名 `refs`。external-content FTS5 の直接 DELETE は DB を壊す → `INSERT INTO fts(fts) VALUES('rebuild')`

## 5. LLM 連携（Strata / MiaAI-Lab）

- **接続**: OpenAI 互換。既定 Strata `http://127.0.0.1:8080/v1`（`qwen3.8-flash-next`）。MiaAI-Lab（:8888）にもコメント1行で切替
- **Strata 特性**: 1リクエスト直列（推論エンジン層の物理必然。改造不可と結論）→ `request_throttle.min_interval_ms` でグローバル・スロットル（スレッドセーフ）
- **A 信頼性/UX**: リトライ（指数バックオフ、`llm.max_retries`）+ ストリーミング（`llm.stream`）
- **B パイプライン並列**: `pipeline.parallel_prefetch`（原文読み込みの先読みのみ並列、LLM 推論は直列。効果検証用にオン/オフ可）
- **D 分割投入**: `pipeline.chunk_max_chars`（0=無効）+ overlap → event_id 重複排除マージ
- **セッション**: `llm_session.py`（append-only 履歴、プレフィックス system→原文→変数固定）。Strata の Conversation Cache（チェックポイント方式・一度に1会話・プレフィックス完全一致）を同一章の複数タスクで活用
- **不採用と結論したもの**: クライアント側 SQLite プロンプトキャッシュ（OpenAI 互換では messages を毎回全送するためトークン削減効果ゼロ）、定型プロンプト編集UI（Git/VS Code で代替）

## 6. 人間レビューゲート（自動化の境界）

- LLM 生成本文は `<!-- LLM-GENERATED -->` マーカー + `review_status: unreviewed`。承認は `review_queue.py`（`--approve` / `--file`）でのみ `human_verified` 化
- アーク境界推定（`estimate_arcs.py` → `schemas/arc_definitions.yaml`）は人間レビュー必須
- 統合候補（`merge_candidates`）は `review_queue.py --merges` で一覧、`--merge-approve/--merge-reject` は人間のみ。統合本体（superseded_by 書き換え）は人間作業
- 原則: **LLM は提案・生成、人間は承認**。自動で epistemic_status を confirmed に上げる経路は存在しない

## 7. 検証体系

- `lint.py`: 5カテゴリ（structure / links / evidence / spoiler / semantic）。`--file` で対象限定、`--severity` で重要度絞り込み
- Frontmatter は JSON Schema 検証（$ref 解決: RefResolver base_uri = schemas/）
- 第1層: `validate_event.py`（JSONL 検証、`--staging` で YAML 検証）
- CI: GitHub Actions（deploy は Quartz 側）

## 8. 現状の到達点（正直な棚卸し）

- 足場（schema・命名・lint・パイプライン・検索・レビュー）は揃い、合成データで全工程 exercised 済み
- **実データ（raw/chNNNN.txt）での本運用は未開始**。Strata 起動後の ch0001 実測が最初の関門
- 旧 wiki の記事は移行していない（意図的。v5.1 モデルで新規構築）
