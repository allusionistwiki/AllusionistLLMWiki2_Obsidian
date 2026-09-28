# 今後の課題と想定される問題点（2026-09-28 時点）

## A. 最重要（次の一手）

1. **実データでの本運用未開始**: 足場は合成データで全工程 exercised 済みだが、`raw/chNNNN.txt` での抽出を一度も走らせていない。ch0001 で extract→aggregate→merge→lint→search の実測が最初の関門
2. **Strata 実機検証**: 会話キャッシュ（`--prompt-cache`）が有効か、同一章セッションでフォローアップが本当に数秒で始まるか。B（parallel_prefetch）とセッションの効果は実機 A/B 測定までオン/オフ判断できない
3. **LLM 抽出品質の未知**: 合成データでは event schema は通るが、実原文での quote 正確性（原文に実在する引用か）は未検証。`lint.py` の evidence チェックに「quote が原文に実在するか」の自動照合を追加すべき（原文が手元にあるので機械照合可能。幻覚検出の最重要ゲート）

## B. 想定される問題点

### データ品質
- **表記揺れ・名前ブレ**: 実運用最大のリスク。`merge_candidates` による統合キューは作ったが、候補を自動提案するスクリプト（類似名・エイリアス衝突検出）が未実装。1000章規模では人力維持不可
- **章番号の対応付け**: raw の章区切りが原作の章と一致する前提。PDF 由来の `gensousaiki.pdf` からの章分割・行番号の安定性が未検証（locator.lines は推定値運用）
- **センテンスID 未実装**: `raw_sentence_ids` は分割実装待ち。locator が行番号頼みで、原文再アップロード時に位置がずれると証拠が腐る。paragraph_id の採番方式を先に決めるべき
- **伏線タイムラインの更新**: MY_ の hinted/resolved は後章の抽出で過去ファイルを書き換える。merge_all のべき等性は担保済みだが、「解決済み伏線の spoiler_after 引き上げ」ルールは未定義

### 検索
- **ベクトル層が未起動**: ollama 埋め込みは一度も実走していない。RRF の効果測定は FTS 単体ベース。日本語埋め込みモデルの選定（nomic-embed は日本語弱い）は要再検討
- **GraphRAG 化は未着手**: affiliations / identity_genealogy の時間軸（valid_from/to）をエッジ重みとして検索に載せる設計がない。キャラクター状態モデル拡張の価値は検索が実装して初めて出る
- **検索DB の陳腐化**: 正規層変更後に `--build` を忘れるとズレる。commit_all へのフック化を検討

### 運用・スケール
- **レビュー・ボトルネック**: LLM 生成は unreviewed で溜まり続ける。1000章×5ページ規模ではレビューキューが人力の限界を超える。優先度付け（similarity_score ならぬ review 優先度）が必要
- **Strata 直列の時間予算**: 1章 30Kトークン≈60秒 + 生成。1000章×複数タスクは数十時間。チェックポイント機構（章単位で完了を記録し再開可能に）が現状パイプラインにない — extract は章単位で冪等なので `work/events/` の存在チェックで十分だが明示化されていない
- **work repo の肥大**: events/staging/search が無制限に増える。検索DB は再生成物なので gitignore 維持でよいが、レポートの保持ポリシー未定義
- **Quartz 側の未整備**: `quartz.config.ts` の baseUrl・フッターリンク・LICENSE 参照が新リポジトリ名で未更新（公開URL確定まで意図的に保留）

### 法・ライセンス
- `LICENSE.md` の未解決2件（Rights Holder Override の NC 上書き不可問題、無帰属条項の CC 外明示）は公開前に決着が必要。Quartz 公開と同時に公になる

## C. 技術的負債（小さいが触るべき）

- `jsonschema.RefResolver` は deprecated（現行は動作するが将来 jsonschema メジャーで消える。`referencing` への移行は lint 一本化後にまとめて）
- `lint.py` と `lint_v51.py` が二系統残存（ID_PREFIX_DIR 定義が lint_v51 側）。統合すべき
- `fix_modules`（自動修復）は合成データでの検証が浅い。実データ投入前に L1 以外は無効化して使うのが安全
- `docs/samples/E_char_ハルベルト.md` に既存の死リンク1件（`[[E_motif_白銀の髪]]`）。サンプル掃除時に解消
- `build_search_index.py` / `query_cli.py`（旧簡易検索）と `search.py`（新）が併存。旧は廃止判断を

## D. 推奨ロードマップ（順当な順）

1. raw 章分割 → ch0001 実抽出 → quote 原文照合 lint 追加 → 実データ A/B（セッション/分割投入の効果測定）
2. 表記揺れ自動提案スクリプト（merge_candidates 提案側）
3. センテンス/段落 ID 採番方式の決定 → locator 安定化
4. レビュー優先度付け + 章単位チェックポイント
5. 検索: 埋め込みモデル選定 → ベクトル層実走 → GraphRAG 風エッジ（affiliations/系譜）
6. Quartz 公開設定 + LICENSE 決着 → 公開
