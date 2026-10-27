# 幻想再帰のアリュージョニスト 解析Wiki — L1/L2 知識核（Obsidian vault）

「幻想再帰のアリュージョニスト」多層アナロジー分析の**ソース・オブ・トゥルース**となる解析用 Obsidian vault（リポジトリ: AllusionistLLMWiki2_Obsidian）。v5.x 設計を基盤に、現行は L1（章別観測の素抽出）→ L2（正規化实体台帳）の解析チェーンの生成先です。

- **公開サイト**: [`AllusionistWiki2`](https://github.com/allusionistwiki/AllusionistWiki2)（Quartz）側で CI ビルド。この vault の `wiki/` を層ごとに取得し、表示層＝サイト直下・`/l1/` 下位層・`/l2/`・`/layers/` へ配置する（https://allusionistwiki.github.io/AllusionistWiki2/）
- **作業データ（正）**: 兄弟リポジトリ [`AllusionistWiki_work`](https://github.com/allusionistwiki/AllusionistWiki_work) の `work/allusionist_v2/` 配下（L0〜L6・index、run 単位・追加専用・`run.json` 来歴必須）。整合性は相互コミット参照（`work-ref:` / `vault-ref:` + `SYNC_LOG.md`）で保証
- **小説原文の知識源は `AllusionistWiki_raw`（private）の生テキストのみ**。PDF 版（gensousaiki.pdf）は知識源にしない（読まない。raw が読めない場合はその旨を明記し PDF で代用しない）
- 設計書: [`docs/knowledge-model-v5.1.md`](docs/knowledge-model-v5.1.md)（v5.1 Final Revised）+ [`docs/knowledge-model-v5.2-search.md`](docs/knowledge-model-v5.2-search.md)（v5.2 検索最適化版・三層分離）
- **現行実装の仕様（権威）**: [`docs/knowledge-model-current.md`](docs/knowledge-model-current.md) ／ 今後の課題: [`docs/roadmap-and-risks.md`](docs/roadmap-and-risks.md) ／ AI作業規約: [`CLAUDE.md`](CLAUDE.md)
- 実装ガイド: [`docs/runtime/v5.2-implementation-guide.md`](docs/runtime/v5.2-implementation-guide.md)

## 現行パイプライン（L1 解析チェーン）

- **章解析**: `scripts/run_analysis_parallel.py`（章並列 → `analyze_chapter.py` 解析 → `autopilot_review.py` 自動審査 → fixers）。progress は `data/analysis_progress.txt`、3KB 未満出力は reject 再解析。産出（events / claims / 候補）は work 側 run に追加専用で保存
- **ページ生成**: `scripts/build_*.py`（entities / claims / appearances / folder indexes 等）が vault `wiki/l1/` へ生成。L1 実体ページへの L2 台帳対応節は `scripts/fix_entity_pages_l2ref.py`
- **L2 正規化台帳**: work 側の `build_l2_entities.py` / `adjudicate_l2_*.py` / `apply_l2_v3.py` / `annotate_l2_evidence.py`（台帳・裁定・確度/根拠付与）→ 本 vault の `scripts/build_l2_pages.py` が `wiki/l2/` へ公開ページを生成（設計: work `work/allusionist_v2/L2/README.md`）
- **検証**: `scripts/lint.py`（ERROR 0 が公開ゲート）+ `lint_v51.py`（ID プレフィックス→ディレクトリ対応）
- 検索: `search.py`（構造化SQL + FTS5 + ベクトル + RRF のハイブリッド、`--build` でインデックス構築）+ `build_search_index.py` / `query_cli.py`。設定は `config.yaml`
- 初代パイプライン（`extract_chapter.py` → `aggregate_events.py` → `merge_all.py` の三層分離系）は v5.x レガシーとしてスクリプトを残す

- LLM 接続（`llm_client.py`）: Strata（`http://127.0.0.1:8080/v1`、1リクエスト直列 → `request_throttle.min_interval_ms` でスロットル、GPU 共有環境ではプロセス内グローバルスロットル）/ MiaAI-Lab 両対応。リトライ（指数バックオフ）・ストリーミング対応（`llm.stream`）。`pipeline.parallel_prefetch`、`pipeline.chunk_max_chars`（0=無効）
- LLM セッション（`llm_session.py`）: 同一章の複数タスクは1セッションにまとめ、Strata 内部の Conversation Cache（チェックポイント方式・一度に1会話・プレフィックス完全一致）を再利用。OpenAI互換プロトコル上 messages は毎回全送するため、クライアント側の SQLite プロンプトキャッシュは作らない（トークン削減効果ゼロと結論済み）。プレフィックスは system → 原文 → 変数の順で固定
- 命名規則・実装仕様: [`docs/naming-convention.md`](docs/naming-convention.md)
- スキーマ: [`schemas/`](schemas/)（JSON Schema, draft-07）

## 構成（層並列・2026-10 以降）

```
wiki/
  l1/          # L1 層Wiki（7コア型 ARC_ O_ E_ ME_ A_ MY_ RF_ + 索引）
  l2/          # L2 正規化实体台帳・名相関索引・名義変換表（生成物）
  layers/      # 層索引（L0〜L7 の配置と来歴）
  index.md     # 層索引トップ
sources/       # 出典台帳（SRC_*.yaml）
schemas/       # JSON Schema（Frontmatter バリデーション）
docs/          # 設計書・命名規則・レビュー・サンプル
raw/           # 原文（非公開・Git管理外。正は AllusionistWiki_raw）
```

work リポジトリの `allusionist_v2/<層>/` と 1 層 = 1 対象で対称。L3 以降は同じ型で追加する。

## 執筆ルール（要約）

- ファイル名 = 正規ID + `.md`（`docs/naming-convention.md` 参照）
- Frontmatter は `schemas/*.schema.json` に準拠（`schema_version` 必須）
- 原文引用は `source_id` + `locator` + `quote` で証拠付与（原文至上主義）。原文の照合は `AllusionistWiki_raw` の生テキストのみに行う
- 状態は `epistemic_status` / `review_status` / `document_status` の3系統で分離
- 開示条件は `spoiler_after` / `disclosure`（章進行と矛盾しないこと）
- graph ノード名は frontmatter `title` 必須（mysteries/entities/arcs）

## ライセンス

Wiki本文: CC BY-NC-SA 4.0 / コード・設定: MIT（`LICENSE.md` 参照）
