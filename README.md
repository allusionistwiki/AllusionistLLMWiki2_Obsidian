# 幻想再帰のアリュージョニスト Wiki 2（Obsidian vault / 知識核）

「幻想再帰のアリュージョニスト」多層アナロジー分析Wikiのリバイス版（v5.1 設計準拠）。**ソース・オブ・トゥルース**となる Obsidian vault です。

- 公開サイトは [`AllusionistLLMWiki2_Quartz`](https://github.com/allusionistwiki/AllusionistLLMWiki2_Quartz) 側で CI ビルド（この vault の `wiki/` を取得）
- 作業派生物（第1層 events / 第2層 staging / 検索DB / レポート）は兄弟リポジトリ [`AllusionistLLMWiki2_Work`](https://github.com/allusionistwiki/AllusionistLLMWiki2_Work) に分離。整合性は相互コミット参照（`work-ref:` / `vault-ref:` + `SYNC_LOG.md`）で保証し、`scripts/commit_all.py` で同時コミットする
- 設計書: [`docs/knowledge-model-v5.1.md`](docs/knowledge-model-v5.1.md)（v5.1 Final Revised）+ [`docs/knowledge-model-v5.2-search.md`](docs/knowledge-model-v5.2-search.md)（v5.2 検索最適化版・三層分離）
- 実装ガイド: [`docs/runtime/v5.2-implementation-guide.md`](docs/runtime/v5.2-implementation-guide.md)
- 三層分離パイプライン: `scripts/extract_chapter.py`（第1層抽出）→ `aggregate_events.py`（第2層集約）→ `merge_all.py`（第3層正規層マージ: エンティティ/クレーム/ミステリー/外部参照/エピソード/アーク）→ `lint.py`（検証）。検索は `search.py`（ハイブリッド検索: 構造化SQL + FTS5全文 + ベクトル + RRF、`--build` でインデックス構築）+ `build_search_index.py` / `query_cli.py`（簡易検索）。設定は `config.yaml`（`search.embedding_provider`: ollama / openai_compatible）
- LLM 自動化: `generate_bodies.py`（本文生成、`<!-- LLM-GENERATED -->` マーカー + `review_status: unreviewed`）、`estimate_arcs.py`（アーク境界推定 → `schemas/arc_definitions.yaml`、人間レビュー必須）、`review_queue.py`（レビューキュー）
- LLM 接続（`llm_client.py`）: Strata（`http://127.0.0.1:8080/v1`、1リクエスト直列 → `request_throttle.min_interval_ms` でスロットル）/ MiaAI-Lab 両対応。リトライ（指数バックオフ）・ストリーミング対応（`llm.stream`）。`pipeline.parallel_prefetch`（前処理の並列化、効果検証用にオン/オフ可）、`pipeline.chunk_max_chars`（分割投入、0=無効）
- LLM セッション（`llm_session.py`）: 同一章の複数タスクは1セッションにまとめ、Strata 内部の Conversation Cache（チェックポイント方式・一度に1会話・プレフィックス完全一致）を再利用。OpenAI互換プロトコル上 messages は毎回全送するため、クライアント側の SQLite プロンプトキャッシュは作らない（トークン削減効果ゼロと結論済み）。プレフィックスは system → 原文 → 変数の順で固定
- 命名規則・実装仕様: [`docs/naming-convention.md`](docs/naming-convention.md)
- スキーマ: [`schemas/`](schemas/)（JSON Schema, draft-07）
- 記事の移行は行わず、v5.1 知識モデルで新規構築する

## 構成

```
wiki/          # 公開対象の知識核（7コア型: ARC_ O_ E_ ME_ A_ MY_ RF_）
sources/       # 出典台帳（SRC_*.yaml）
schemas/       # JSON Schema（Frontmatter バリデーション）
docs/          # 設計書・命名規則・レビュー・サンプル
raw/           # 原文（非公開・Git管理外）
```

## 執筆ルール（要約）

- ファイル名 = 正規ID + `.md`（`docs/naming-convention.md` 参照）
- Frontmatter は `schemas/*.schema.json` に準拠（`schema_version: "5.1"` 必須）
- 原文引用は `source_id` + `locator` + `quote` で証拠付与（原文至上主義）
- 状態は `epistemic_status` / `review_status` / `document_status` の3系統で分離
- 開示条件は `spoiler_after` / `disclosure`（章進行と矛盾しないこと）

## ライセンス

Wiki本文: CC BY-NC-SA 4.0 / コード・設定: MIT（`LICENSE.md` 参照）
