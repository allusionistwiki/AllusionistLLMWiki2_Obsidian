# アリュージョニストWiki 特化設計書 v5.2 Final（検索最適化版）

**Version**: 5.2 Final  
**Target**: 「幻想再帰のアリュージョニスト」多層アナロジー分析Wiki  
**Design Focus**: 検索精度最適化と三層分離アーキテクチャ  
**Base**: v5.1 Final + 検索精度分析

---

## 0. 本改訂の位置づけ

v5.1 までの設計は「知識の構造化」に焦点を当てていたが、以下の問いが残っていた：

- **ファイル細分化は検索精度を上げるのか？**
- **「作りまくる」設計は実際に有効か？**
- **検索の観点での最適アーキテクチャは何か？**

v5.2 では、検索精度の観点から設計を再構成し、**三層分離アーキテクチャ**を正式採用する。

---

## 1. 設計思想の再定義

### 1.1 検索精度の3次元モデル

「検索精度」は単一の指標ではなく、以下の3次元で評価する：

| 次元 | 定義 | 重要度 |
|:---|:---|:---:|
| **Recall（再現率）** | 関連するものを**漏らさず**見つけられるか | 機械検索で最重要 |
| **Precision（適合率）** | 見つかったものが**本当に欲しいもの**か | 人間検索で最重要 |
| **Relevancy（関連性）** | 見つかったものの**並び順**が適切か | 両方で重要 |

### 1.2 ファイル細分化の真実

**ファイル細分化自体は検索精度を上げない。**

検索精度を上げるのは：
1. **構造化されたメタデータ**（Frontmatter）
2. **適切なクエリ言語**（SQL的構造化クエリ）
3. **検索クエリとデータ構造の整合性**

### 1.3 三層分離の哲学

```
【第1層：イベント層】 → 機械が処理する（作りまくる層）
【第2層：中間集約層】 → エージェントが統合する（まとめる層）
【第3層：正規層】     → 人間が読む（見せる層）
```

**各層が異なる検索ニーズに対応する。**

---

## 2. 三層分離アーキテクチャ

### 2.1 全体構造図

```
┌─────────────────────────────────────────────────────────────┐
│                    第1層：イベント層                          │
│  形式: JSONL                                                │
│  場所: work/events/                                         │
│  役割: 各エピソード × 各エンティティ × 各属性の原子イベント    │
│  検索: 構造化クエリ（SQL風）                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    第2層：中間集約層                          │
│  形式: YAML                                                 │
│  場所: work/staging/                                        │
│  役割: エピソード単位の集約・重複排除                         │
│  検索: エピソード単位の絞り込み                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    第3層：正規層                             │
│  形式: Markdown（v5.1準拠）                                  │
│  場所: vault/wiki/                                          │
│  役割: 統合された正規ファイル（人間が読む）                    │
│  検索: 全文検索 + GraphRAG + Dataview                       │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 各層の責務

| 層 | 形式 | 場所 | 誰が読むか | 検索方法 | ファイル数 |
|:---|:---:|:---:|:---:|:---:|:---:|
| **第1層** | JSONL | `work/events/` | 機械 | 構造化クエリ | 1エピソード=1ファイル |
| **第2層** | YAML | `work/staging/` | エージェント | エピソード検索 | 1エピソード=1ファイル |
| **第3層** | Markdown | `vault/wiki/` | 人間 | 全文検索+GraphRAG | 正規ファイルのみ |

---

## 3. 第1層：イベント層（JSONL）

### 3.1 設計思想

**「作りまくる」層。ただし、人間は読まない。**

- 各エピソード × 各エンティティ × 各属性の原子イベントを記録
- 1エピソード = 1ファイル（複数行）
- 機械処理に最適なJSONL形式

### 3.2 イベントスキーマ

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Event Record",
  "type": "object",
  "required": ["event_id", "episode", "entity", "aspect", "observation"],
  "properties": {
    "event_id": {
      "type": "string",
      "description": "イベントの一意ID",
      "pattern": "^E_ch\\d{4}_[a-z]+_[^_]+_[A-Z]_[A-Z]$"
    },
    "episode": {
      "type": "string",
      "pattern": "^ch\\d{4}$",
      "description": "由来エピソード"
    },
    "entity": {
      "type": "string",
      "description": "対象エンティティ名"
    },
    "entity_type": {
      "type": "string",
      "enum": ["character", "terminology", "organization", "item", "motif", "relationship", "phrase"],
      "description": "エンティティの種別"
    },
    "aspect": {
      "type": "string",
      "enum": ["visual", "name", "speech", "action", "relationship", "symbolic"],
      "description": "属性の種別"
    },
    "observation": {
      "type": "string",
      "description": "観察内容"
    },
    "quote": {
      "type": "string",
      "description": "原文からの引用"
    },
    "locator": {
      "type": "object",
      "properties": {
        "chapter": {"type": "string", "pattern": "^ch\\d{4}$"},
        "lines": {"type": "string"},
        "paragraph_id": {"type": "string"}
      }
    },
    "spoiler_after": {
      "type": "string",
      "pattern": "^(ch\\d{4}|ch0000|final|meta)$"
    },
    "created": {
      "type": "string",
      "format": "date"
    }
  }
}
```

### 3.3 イベントIDの命名規則

```
形式: E_{episode}_{entity_type}_{entity}_{aspect}_{observation_type}

例:
  E_ch0057_char_ハルベルト_V_O  (Visual Observation)
  E_ch0057_char_ハルベルト_N_O  (Name Observation)
  E_ch0057_motif_白銀の髪_S_O   (Symbolic Observation)
```

**aspect の略称:**

| aspect | 略称 | 意味 |
|:---|:---:|:---|
| `visual` | `V` | 視覚描写 |
| `name` | `N` | 名称・呼称 |
| `speech` | `S` | セリフ・発言 |
| `action` | `A` | 行動・動作 |
| `relationship` | `R` | 関係性 |
| `symbolic` | `Y` | 象徴・比喩 |

### 3.4 ファイル配置

```
work/events/
├── ch0057.jsonl
├── ch0058.jsonl
├── ...
└── ch1000.jsonl
```

**1エピソード = 1ファイル、複数行（数十〜数百行）**

---

## 4. 第2層：中間集約層（YAML）

### 4.1 設計思想

**エピソード単位の集約。エージェントが処理する層。**

- 第1層のイベントをエピソード単位で集約
- 重複排除、正規ファイルとの照合
- 統合エージェントへの入力

### 4.2 中間集約スキーマ

```yaml
# work/staging/staging_ch0057.yaml
episode: ch0057
created: "2026-09-28"
status: pending_merge  # pending_merge / normalized / merged

# エンティティの集約
entities:
  - canonical_target: "[[E_char_ハルベルト]]"
    entity_type: character
    aspects:
      visual:
        observations:
          - event_ref: "E_ch0057_char_ハルベルト_V_O"
            quote: "月光を紡いだような白銀の髪"
            locator:
              lines: "45-48"
            spoiler_after: "ch0057"
      name:
        observations:
          - event_ref: "E_ch0057_char_ハルベルト_N_O"
            quote: "ハルベルトと名乗る"
            locator:
              lines: "10-12"
            spoiler_after: "ch0057"
    first_appearance_candidate: true

# 主張候補
claims:
  - canonical_target: "[[A_alludes_to_ハルベルト_アルテミス_ch0057]]"
    predicate: alludes_to
    subject: "[[E_char_ハルベルト]]"
    object: "[[ME_myth_アルテミス]]"
    evidence_strength: moderate
    evidence:
      - event_ref: "E_ch0057_char_ハルベルト_V_O"
        quote: "月光を紡いだような白銀の髪"
    status: candidate

# 伏線候補
mysteries:
  - canonical_target: "[[MY_白銀の髪の由来]]"
    status: candidate
    introduced: ch0057
    evidence:
      - event_ref: "E_ch0057_motif_白銀の髪_Y_O"
        quote: "月光を紡いだような白銀の髪"

# 正規ファイルとの照合結果
matching_results:
  - entity: "ハルベルト"
    matched: true
    target: "[[E_char_ハルベルト]]"
    confidence: high
  - entity: "白銀の髪"
    matched: false
    suggestion: "新規作成候補"
```

### 4.3 ファイル配置

```
work/staging/
├── staging_ch0057.yaml
├── staging_ch0058.yaml
├── ...
└── staging_ch1000.yaml
```

---

## 5. 第3層：正規層（Markdown）

### 5.1 設計思想

**人間が読む層。v5.1の正規ファイル構造を継承。**

- 統合された正規ファイル
- Frontmatterによる構造化メタデータ
- WikiLinkによる関係性の追跡

### 5.2 ファイル構造（v5.1準拠）

```
vault/wiki/
├── entities/
│   ├── characters/
│   │   └── E_char_ハルベルト.md
│   ├── motifs/
│   │   └── E_motif_白銀の髪.md
│   └── relationships/
│       └── E_relation_シナモリ_アズーリア_対立軸.md
├── claims/
│   └── A_alludes_to_ハルベルト_アルテミス_ch0057.md
├── mysteries/
│   └── MY_白銀の髪の由来.md
└── reflections/
    └── RF_合わせ鏡の隐喻_20260928.md
```

### 5.3 Frontmatter（v5.1準拠）

```yaml
---
schema_version: "5.1"
id: E_char_ハルベルト
type: entity
subtype: character
canonical_name: "ハルベルト"
aliases:
  - "楽神"
  - "銀髪の魔女"
first_appearance: "ch0057"
spoiler_after: "ch0057"
document_status: active
created: "2026-09-28"
updated: "2026-09-28"
---
```

---

## 6. 検索アーキテクチャ

### 6.1 検索インデックス設計

```yaml
# search/indexes.yaml
indexes:
  # 第1層用：構造化クエリ
  - name: entity_events
    type: sqlite  # or elasticsearch
    source: work/events/*.jsonl
    fields:
      - name: event_id
        type: keyword
      - name: episode
        type: keyword
      - name: entity
        type: keyword
      - name: entity_type
        type: keyword
      - name: aspect
        type: keyword
      - name: observation
        type: text
      - name: quote
        type: text
      - name: spoiler_after
        type: keyword

  # 第2層用：エピソード検索
  - name: episode_staging
    type: yaml
    source: work/staging/*.yaml
    fields:
      - episode
      - entities
      - claims
      - mysteries

  # 第3層用：全文検索 + GraphRAG
  - name: wiki_full_text
    type: obsidian_search  # or graphrag
    source: vault/wiki/**/*.md
    fields:
      - content
      - frontmatter
      - wikilinks
```

### 6.2 クエリルーティング

```
ユーザーの質問 → クエリ分類器 → 適切な層で検索

┌─────────────────────────────────────────────────────────┐
│                    クエリ分類器                          │
│  質問のタイプを判定:                                      │
│  - 特定の属性に関する全言及 → 第1層（JSONL）              │
│  - エピソード単位の検索 → 第2層（YAML）                  │
│  - 包括的な理解・関係性 → 第3層（Markdown + GraphRAG）    │
└─────────────────────────────────────────────────────────┘
```

### 6.3 クエリ例と最適層

| クエリ例 | 最適層 | クエリ方法 |
|:---|:---:|:---|
| 「ハルベルトの視覚描写を全部見たい」 | 第1層 | `SELECT * FROM events WHERE entity='ハルベルト' AND aspect='visual'` |
| 「ch0057で起きたこと全て」 | 第2層 | `staging_ch0057.yaml` を読み込み |
| 「ハルベルトとは何者か？」 | 第3層 | 全文検索 + GraphRAG |
| 「ハルベルトとアポロンの関係」 | 第3層 | `A_alludes_to_...` を参照 |
| 「白銀の髪に関する言及」 | 第1層 | `SELECT * FROM events WHERE entity='白銀の髪'` |

---

## 7. 検索精度の観点からの評価

### 7.1 各設計の比較

| 観点 | ファイル細分化のみ | **三層分離（v5.2）** |
|:---|:---:|:---:|
| **Recall（再現率）** | ○（属性別で網羅） | ◎（構造化クエリで網羅） |
| **Precision（適合率）** | ×（包括的検索でノイズ） | ◎（層の選択で最適化） |
| **Relevancy（関連性）** | △（並び順制御困難） | ◎（クエリ設計で制御） |
| **Obsidian への負荷** | ×（数万ファイル） | ◎（正規ファイルのみ） |
| **機械処理速度** | △（Markdownパース） | ◎（JSONL直接処理） |
| **再構築可能性** | ◎ | ◎ |

### 7.2 検索シナリオ別の評価

**シナリオ1：「ハルベルトの全視覚描写を時系列で見たい」**

| 設計 | 結果 |
|:---|:---|
| ファイル細分化（Markdown） | `E_*_V_O.md` を全文検索 → 時系列ソートが面倒 |
| **三層分離** | **第1層のJSONLをクエリ → 完全一致** |

**シナリオ2：「ハルベルトとは何者か？」**

| 設計 | 結果 |
|:---|:---|
| ファイル細分化（Markdown） | 数百の断片的ファイル → 全体像が把握困難 |
| **三層分離** | **第3層の正規ファイル → 包括的理解** |

**シナリオ3：「ch0057で何が起きた？」**

| 設計 | 結果 |
|:---|:---|
| ファイル細分化（Markdown） | `E_ch0057_*.md` を全部読む → 認知負荷が高い |
| **三層分離** | **第2層のstaging_ch0057.yaml → エピソード単位の集約** |

---

## 8. エージェント処理フロー（修正版）

```
【Stage 1: Extract（抽出）】
  入力: raw/ch0057.txt
  処理: LLMで事実・エンティティ・アナロジーを抽出
  出力: work/events/ch0057.jsonl ← 「作りまくる」
  
【Stage 2: Aggregate（集約）】
  入力: work/events/ch0057.jsonl
  処理: エピソード単位で集約、重複排除
  出力: work/staging/staging_ch0057.yaml
  
【Stage 3: Normalize（正規化）】
  入力: work/staging/staging_ch0057.yaml + 既存の正規ファイル群
  処理: 正規ファイルとの照合、canonical_target の解決
  出力: work/changesets/changeset_YYYYMMDD_NNN.yaml
  
【Stage 4: Validate（検証）】
  処理: スキーマ検証、Lint、証拠チェック
  出力: work/reports/validation_report.md
  
【Stage 5: Apply（適用）】
  入力: 人間承認済みの changeset
  処理: 正規ファイルへの反映、イベントログの _merged/ への移動
  出力: 更新された正規ファイル
```

---

## 9. ディレクトリ構成（最終版）

```
vault/
├── raw/                                    # 原文（Git管理外可）
│   └── chNNNN.txt
│
├── work/                                   # 派生物（Git管理外可）
│   ├── events/                             # 第1層：イベント層
│   │   ├── ch0057.jsonl
│   │   └── ...
│   ├── staging/                            # 第2層：中間集約層
│   │   ├── staging_ch0057.yaml
│   │   └── ...
│   ├── changesets/                         # 変更セット
│   │   └── changeset_20260928_001.yaml
│   ├── _merged/                            # 統合済み
│   │   └── ch0057/
│   └── reports/
│       └── merge_report_20260928.md
│
├── vault/wiki/                             # 第3層：正規層
│   ├── entities/
│   │   ├── characters/
│   │   ├── terminology/
│   │   ├── organizations/
│   │   ├── items/
│   │   ├── motifs/
│   │   ├── relationships/
│   │   └── phrases/
│   ├── references/
│   │   ├── mythology/
│   │   ├── literature/
│   │   ├── philosophy/
│   │   ├── psychology/
│   │   ├── culture/
│   │   └── author-material/
│   ├── claims/
│   ├── mysteries/
│   └── reflections/
│
├── schemas/                                # JSON Schema
│   ├── event.schema.json
│   ├── staging.schema.json
│   ├── entity.schema.json
│   ├── claim.schema.json
│   └── ...
│
├── search/                                 # 検索インデックス
│   ├── indexes.yaml
│   └── query_router.py
│
└── docs/
    ├── knowledge-model.md
    ├── naming-convention.md
    ├── search-architecture.md
    └── runtime/
```

---

## 10. まとめ：検索最適化版の設計原則

### 10.1 三層分離の哲学

```
第1層（JSONL） → 機械が処理する（作りまくる層）
第2層（YAML）  → エージェントが統合する（まとめる層）
第3層（Markdown）→ 人間が読む（見せる層）
```

### 10.2 検索精度の最大化

- **Recall**: 第1層の構造化クエリで網羅
- **Precision**: 層の選択で最適化
- **Relevancy**: クエリ設計で制御

### 10.3 「作りまくる」の正しい実装

- **Markdown で作りまくるのは Obsidian が死ぬ**
- **JSONL + YAML + Markdown の三層分離が最適解**
- **「作りまくる層」は人間が読まないのだから、機械に優しい形式にする**

---

## 11. 次のアクション

1. **イベントスキーマの確定**: `event.schema.json` を作成
2. **検索インデックスの構築**: SQLite or Elasticsearch で実装
3. **クエリルーティングの実装**: 質問タイプ → 適切な層の振り分け
4. **第1層 → 第2層 → 第3層の変換スクリプト**: エージェント処理フローの実装

この設計書で実装を進めますか？