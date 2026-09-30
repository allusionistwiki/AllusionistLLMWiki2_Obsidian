# CLAUDE.md — AllusionistLLMWiki2_Obsidian（vault）での作業規約

このリポジトリは「幻想再帰のアリュージョニスト」分析Wikiの知識核（Obsidian vault）。
AI エージェント（Claude / Hermes 等）がここで作業する際の約束事。

## 最優先の鉄則

1. **原文至上主義**: 原文（`raw/chNNNN.txt`、Git 管理外）にない情報を wiki に書かない。引用には必ず `quote` + `locator` + `source_id`
2. **LLM は提案、人間は承認**: `review_status` を `human_verified` にできるのは人間だけ。エージェントが勝手に上げるな
3. **Lint は検出のみ**: 自動修復（`fix_all.py`）は明示的に依頼されたときだけ。Lint 本体の挙動を修復側に寄せない
4. **`raw/` を公開・コミットしない**: gitignore 済み。README・wiki・ログに原文を転記するのも禁止（引用は quote ルールに従う）
5. **法的注記を消さない**: `LICENSE.md` の未解決注記（Rights Holder Override、無帰属条項の CC 外明示）は意図的に残っている。勝手に「修正」するな

## リポジトリ横断の約束

- 正規層（wiki/・sources/・schemas/・scripts/・docs/）は本 repo。検索DB・events・staging・ログは `../AllusionistLLMWiki2_Work`。**work の派生物を本 repo にコミットしない**（gitignore 済み）
- 両方にコミットする変更は `python scripts/commit_all.py`（相互参照 `work-ref:`/`vault-ref:` + SYNC_LOG を維持）
- Quartz 公開側（GitHub: `allusionistwiki/AllusionistLLMWiki2`、ローカル: `../AllusionistLLMWiki2_Quartz`）はビルド生成物。`node_modules/`・`public/` を触らない
- ブランチ: `main` に直接 push してよい（個人運用）。作業ブランチは `bionic/` 接頭辞

## 環境

- Python: プロジェクトは Hermes の python（3.14）で実行。依存: `pyyaml jsonschema rich requests openai`
- LLM: Strata `http://127.0.0.1:8080/v1`（既定、`config.yaml llm.base_url`）。**1リクエスト直列** — 並列 LLM 呼び出しを書くな（スロットルは `llm_client._throttle` が担う）
- 埋め込み: ollama `localhost:11434`（未起動時は検索が FTS/LIKE のみに自然にフォールバックする。エラーを握りつぶして落ちない設計を崩すな）
- Windows + git-bash。ネイティブツール（git/python/node）には `C:/...` 形式のパスを渡す

## 運用モデル（2026-09-30 改定）: LLM auto-review 標準運用

- **標準**: 抽出→分析→LLM 自己審査→昇格まで自動（`scripts/pipeline.py N`）。生成物は `review_status: llm_verified`
- **人間の担当範囲（これだけ）**: 特定記事の reject / 修正指示 / 承認（human_verified へ）/ 手動追記
  - `python scripts/human_ops.py --list`（レビュー対象一覧）
  - `--reject <file> "理由"` / `--revise <file> "指示"` / `--verify <file>` / `--stats`
  - 手動追記は md 本文を直接編集
- 人間操作は `Work/reports/human_ops_log.md` に記録。LLM 代替は `Work/reports/autopilot_log.md`
- `llm_verified` は `human_verified` への置換対象として常に区別されていること（schema 上の独立値）

## 定型コマンド

```bash
python scripts/extract_chapter.py [N]     # 第1層抽出（1章 or config の chapter_range）
python scripts/aggregate_events.py        # 第1層→第2層
python scripts/merge_all.py [--episode chNNNN]  # 第2層→正規層（べき等）
python scripts/lint.py [--file DIR] [--severity error]
python scripts/search.py --build          # 検索DB再構築
python scripts/search.py "クエリ"         # 自動ルーティング検索
python scripts/generate_bodies.py [--type entity] [--dry-run]
python scripts/review_queue.py [--merges] # レビューキュー / 統合候補
python scripts/commit_all.py -m "msg"     # vault+work 同時コミット
```

## 変更時のルール

- **schema を変えたら**: `docs/samples/` と `lint.py` が通ること確認。既存ファイルが壊れないよう新フィールドは省略可能に（後方互換）
- **ID プレフィックスを増やしたら**: `lint_v51.py` の `ID_PREFIX_DIR` と命名規則ドキュメントに同期
- **LLM プロンプトを変えたら**: 出力が `event.schema.json` / `staging.schema.json` を通過することを確認してから使う
- **SQLite を触ったら**: `references` は予約語（テーブルは `refs`）。external-content FTS5 は直接 DELETE せず `INSERT INTO t(t) VALUES('rebuild')`
- **日本語全文検索**: FTS5 unicode61 は分かち書きしない。FTS 空振り時の LIKE フォールバックを維持する
- 合成テストデータ（ch0057 等）で全工程を回してから掃除する習慣。テスト生成物を commit しない

## 検証の定義

「できた」と言えるのは以下が揃ったときだけ:
1. `py_compile` 通過
2. 対象スクリプトの実行（モック LLM サーバー `scratch/mock_llm.py` で可）
3. `lint.py` 通過（新規エラーを増やさない）
4. 正規層への変更なら `commit_all.py` で相互参照付きコミット

## 言語

- ドキュメント・コメント・コミットメッセージは日本語
- 出力のトーンは簡潔に。設計変更は `docs/knowledge-model-current.md` に反映する（仕様の権威はそこ）
