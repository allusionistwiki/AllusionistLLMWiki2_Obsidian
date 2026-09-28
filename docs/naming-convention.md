# アリュージョニストWiki v5.1 実装仕様：スキーマ定義・命名規則

---

## 1. ファイル命名規則（Naming Convention）

### 1.1 基本原則

1. **ファイル名 = 正規ID + `.md`**
2. **正規IDは一意かつ永続的**（一度付与したら変更しない）
3. **人間可読性を保ちつつ、機械処理可能**にする
4. **ファイル名に意味を持たせすぎない**（情報は Frontmatter に、ファイル名は参照キー）

### 1.2 各型ごとの命名規則

| コア型 | 形式 | 例 | 備考 |
|:---|:---|:---|:---|
| `ARC_` | `ARC_{2桁番号}_{スラッグ}.md` | `ARC_01_女神候補選定編.md` | 番号は作成順 |
| `O_` | `O_{ch4桁}_{スラッグ}.md` | `O_ch0057_初出.md` | 1章複数エピソード時は `O_ch0057a_...` |
| `E_char_` | `E_char_{正規名}.md` | `E_char_ハルベルト.md` | キャラクター |
| `E_term_` | `E_term_{正規名}.md` | `E_term_文彩の魔女.md` | 用語 |
| `E_org_` | `E_org_{正規名}.md` | `E_org_キュトス教団.md` | 組織 |
| `E_item_` | `E_item_{正規名}.md` | `E_item_三叉槍.md` | 物品 |
| `E_motif_` | `E_motif_{正規名}.md` | `E_motif_白銀の髪.md` | 視覚モチーフ |
| `E_relation_` | `E_relation_{主体}_{対象}_{関係性}.md` | `E_relation_シナモリ_アズーリア_対立軸.md` | 関係性 |
| `E_phrase_` | `E_phrase_{正規名}.md` | `E_phrase_幻想再帰.md` | キーフレーズ |
| `ME_myth_` | `ME_myth_{正規名}.md` | `ME_myth_アポロン.md` | 神話 |
| `ME_lit_` | `ME_lit_{正規名}.md` | `ME_lit_オルフェウス譚.md` | 文学 |
| `ME_phil_` | `ME_phil_{正規名}.md` | `ME_phil_ユング心理学.md` | 思想 |
| `A_` | `A_{predicate}_{subject}_{object}_ch{4桁}.md` | `A_alludes_to_ハルベルト_アポロン_ch0124.md` | 分析主張 |
| `MY_` | `MY_{スラッグ}.md` | `MY_二番目の三叉槍の行方.md` | 伏線 |
| `RF_` | `RF_{スラッグ}.md` | `RF_合わせ鏡の隐喻_20260928.md` | 考察 |
| `SRC_` | `SRC_ch{4桁}.yaml` | `SRC_ch0057.yaml` | 出典台帳（YAML） |

### 1.3 正規名（canonical_name）の定義

正規名をファイル名用スラッグに変換するルール：

```
正規名 → スラッグ変換:
1. 全角スペース → 半角アンダースコア (_)
2. 記号（・、（）、【】等）を除去またはアンダースコアに置換
3. 長さ制限: 最大50文字（超える場合は省略形を使用し、canonical_name に正式名を保持）
4. 大文字小文字を区別（日本語はそのまま）
```

**例：**

| 正規名 | スラッグ |
|:---|:---|
| `シナモリ・アキラ` | `シナモリ_アキラ` |
| `文彩（レトリック）の魔女` | `文彩_レトリック_の魔女` |
| `白銀の髪` | `白銀の髪` |
| `二番目の三叉槍の行方` | `二番目の三叉槍の行方` |

### 1.4 衝突回避ルール

**原則：同名ファイルの作成は禁止（Lint で検出）**

やむを得ず衝突する場合の優先順位：

1. **canonical_name の見直しを最優先**（本当に別エンティティか再確認）
2. **コンテキスト修飾子の付与**
   ```
   E_char_ハルベルト_第2形態
   E_motif_白銀の髪_変身後
   ```
3. **連番付与は禁止**（`E_char_ハルベルト_2` のような形式は使わない）

### 1.5 文字コードとエスケープ

```
文字コード: UTF-8 (NFC)
改行コード: LF (\n)
禁止文字: \ / : * ? " < > |
空白: ファイル名には使用しない（アンダースコアに置換）
```

**OS互換性の注意：**
- Windows: 大文字小文字を区別しない（`E_char_ハルベルト.md` と `E_char_はるベルト.md` は衝突とみなす）
- macOS: 大文字小文字を区別しない場合あり（同上）
- Linux: 大文字小文字を区別する（運用上、区別しないものとして扱う）

### 1.6 旧形式からの移行（legacy_id）

v5.0 以前の ID を保持しつつ、新形式に移行する：

```yaml
# 移行後のファイル例
---
id: E_motif_白銀の髪
legacy_id: V_白銀の髪  # ← 旧形式を保持
type: entity
subtype: visual_motif
schema_version: "5.1"
---
```

**移行マッピング：**

| 旧形式 | 新形式 | 移行先ディレクトリ |
|:---|:---|:---|
| `V_xxx` | `E_motif_xxx` | `wiki/entities/motifs/` |
| `R_xxx` | `E_relation_xxx` | `wiki/entities/relationships/` |
| `KEY_xxx` | `E_phrase_xxx` | `wiki/entities/phrases/` |

**移行手順：**
1. 旧ファイルをリネーム（`legacy_id` を付与）
2. `superseded_by` またはリダイレクト設定を追加
3. 旧形式への参照を段階的に置換
4. 死リンクがゼロになった後に `legacy_id` を廃止（ただし履歴は保持）

---

## 2. JSON Schema 定義

### 2.1 共通フィールド（`schemas/common.schema.json`）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "common.schema.json",
  "title": "Common Fields",
  "type": "object",
  "required": ["schema_version", "id", "type"],
  "properties": {
    "schema_version": {
      "type": "string",
      "enum": ["5.1"],
      "description": "設計書のバージョン"
    },
    "id": {
      "type": "string",
      "pattern": "^(ARC|O|E|ME|A|MY|RF|SRC)_[^\\s]+$",
      "description": "正規ID（ファイル名と一致する）"
    },
    "legacy_id": {
      "type": "string",
      "description": "旧形式のID（移行時のみ）"
    },
    "type": {
      "type": "string",
      "enum": ["arc", "episode", "entity", "external_reference", "analytical_claim", "mystery", "reflection", "source"],
      "description": "コア型"
    },
    "created": {
      "type": "string",
      "format": "date",
      "description": "作成日（ISO 8601）"
    },
    "updated": {
      "type": "string",
      "format": "date",
      "description": "最終更新日（ISO 8601）"
    }
  }
}
```

### 2.2 エンティティ（`schemas/entity.schema.json`）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "entity.schema.json",
  "title": "Entity",
  "allOf": [{"$ref": "common.schema.json"}],
  "required": ["subtype", "canonical_name"],
  "properties": {
    "type": {"const": "entity"},
    "subtype": {
      "type": "string",
      "enum": ["character", "terminology", "organization", "item", "visual_motif", "relationship", "key_phrase"],
      "description": "エンティティのサブタイプ"
    },
    "canonical_name": {
      "type": "string",
      "description": "正規名（ファイル名に使用）"
    },
    "aliases": {
      "type": "array",
      "items": {"type": "string"},
      "description": "別名・表記揺れ"
    },
    "first_appearance": {
      "type": "string",
      "pattern": "^ch\\d{4}$",
      "description": "初出章"
    },
    "spoiler_after": {
      "type": "string",
      "pattern": "^(ch\\d{4}|ch0000|final|meta)$",
      "description": "ネタバレ開示条件"
    },
    "document_status": {
      "type": "string",
      "enum": ["draft", "active", "archived", "superseded"],
      "default": "draft"
    },
    "superseded_by": {
      "type": "string",
      "pattern": "^\\[\\[E_[^\\]]+\\]\\]$",
      "description": "統合先のエンティティ（document_status: superseded の場合）"
    }
  },
  "if": {
    "properties": {"subtype": {"const": "relationship"}}
  },
  "then": {
    "required": ["related_entities", "relation_type"],
    "properties": {
      "related_entities": {
        "type": "array",
        "minItems": 2,
        "items": {"type": "string", "pattern": "^\\[\\[E_[^\\]]+\\]\\]$"},
        "description": "関係するエンティティのリスト"
      },
      "relation_type": {
        "type": "string",
        "description": "関係性の種別"
      },
      "timeline": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "episode": {"type": "string", "pattern": "^ch\\d{4}$"},
            "status": {"type": "string"},
            "quote": {"type": "string"}
          }
        },
        "description": "関係性の時系列変化"
      }
    }
  }
}
```

### 2.3 外部参照（`schemas/reference.schema.json`）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "reference.schema.json",
  "title": "External Reference",
  "allOf": [{"$ref": "common.schema.json"}],
  "required": ["subtype", "canonical_name", "domain"],
  "properties": {
    "type": {"const": "external_reference"},
    "subtype": {
      "type": "string",
      "enum": ["mythology", "religion", "literature", "philosophy", "psychology", "history", "folklore", "occult", "popular_culture", "internet_culture", "author_material", "scholarly_source"],
      "description": "外部参照のサブタイプ"
    },
    "canonical_name": {"type": "string"},
    "aliases": {
      "type": "array",
      "items": {"type": "string"}
    },
    "domain": {
      "type": "string",
      "description": "領域（例: Greek Mythology, Jungian Psychology）"
    },
    "relations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["predicate", "target"],
        "properties": {
          "predicate": {
            "type": "string",
            "enum": ["influenced_by", "derived_from", "syncretized_with", "reinterpreted_by", "parodied_in"],
            "description": "ME_間の関係述語"
          },
          "target": {
            "type": "string",
            "pattern": "^\\[\\[ME_[^\\]]+\\]\\]$"
          },
          "evidence": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["source_id"],
              "properties": {
                "source_id": {"type": "string", "pattern": "^SRC_external_\\d{3}$"},
                "quote": {"type": "string"}
              }
            },
            "description": "外部関係主張の証拠（外部典拠必須）"
          }
        }
      }
    },
    "referenced_by": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "entity": {"type": "string", "pattern": "^\\[\\[E_[^\\]]+\\]\\]$"},
          "context": {"type": "string"},
          "detail": {"type": "string", "pattern": "^\\[\\[A_[^\\]]+\\]\\]$"}
        }
      },
      "description": "作品内での参照情報"
    }
  }
}
```

### 2.4 分析主張（`schemas/claim.schema.json`）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "claim.schema.json",
  "title": "Analytical Claim",
  "allOf": [{"$ref": "common.schema.json"}],
  "required": ["subject", "predicate", "object", "epistemic_status", "review_status", "document_status", "spoiler_after"],
  "properties": {
    "type": {"const": "analytical_claim"},
    "subject": {
      "type": "string",
      "pattern": "^\\[\\[E_[^\\]]+\\]\\]$",
      "description": "主語（作品内エンティティ）"
    },
    "predicate": {
      "type": "string",
      "enum": ["alludes_to", "analogous_to", "recurs_as", "structurally_matches", "misreads_as", "foreshadows", "inverts", "parodies", "sublates"],
      "description": "述語（関係の種別）"
    },
    "object": {
      "type": "string",
      "pattern": "^\\[\\[(E|ME)_[^\\]]+\\]\\]$",
      "description": "対象（作品内エンティティまたは外部参照）"
    },
    "valid_from": {
      "type": "string",
      "pattern": "^ch\\d{4}$",
      "description": "この主張が有効になる開始章"
    },
    "spoiler_after": {
      "type": "string",
      "pattern": "^(ch\\d{4}|ch0000|final|meta)$"
    },
    "epistemic_status": {
      "type": "string",
      "enum": ["hypothesized", "supported", "confirmed", "disputed", "refuted", "sublated"]
    },
    "review_status": {
      "type": "string",
      "enum": ["unreviewed", "pending", "human_verified", "needs_revision"]
    },
    "document_status": {
      "type": "string",
      "enum": ["draft", "active", "archived", "superseded"]
    },
    "evidence_strength": {
      "type": "string",
      "enum": ["weak", "moderate", "strong", "explicit"],
      "description": "証拠の強度（数値の代わりに使用）"
    },
    "evidence": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["source_id", "locator"],
        "properties": {
          "source_id": {
            "type": "string",
            "pattern": "^SRC_(ch\\d{4}|external_\\d{3})$",
            "description": "出典ID"
          },
          "locator": {
            "type": "object",
            "required": ["chapter"],
            "properties": {
              "chapter": {"type": "string", "pattern": "^ch\\d{4}$"},
              "lines": {"type": "string", "description": "行番号（補助情報）"},
              "paragraph_id": {"type": "string", "description": "段落ID（安定ID）"}
            }
          },
          "quote": {
            "type": "string",
            "description": "原文からの引用"
          },
          "evidence_type": {
            "type": "string",
            "enum": ["direct_quote", "explicit_statement", "repeated_pattern", "structural_correspondence", "external_source", "author_statement"]
          }
        }
      }
    },
    "mapping": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["subject_feature", "object_feature", "relation"],
        "properties": {
          "subject_feature": {"type": "string"},
          "object_feature": {"type": "string"},
          "relation": {
            "type": "string",
            "enum": ["attribute_correspondence", "structural_equivalence", "functional_equivalence", "narrative_parallel", "iconographic_match"],
            "description": "対応関係の種別"
          }
        }
      }
    },
    "misreading": {
      "type": "object",
      "description": "predicate: misreads_as の場合のみ",
      "properties": {
        "agent_type": {
          "type": "string",
          "enum": ["in_story_character", "reader", "llm", "critic", "authorial_feint"]
        },
        "agent": {
          "type": "string",
          "pattern": "^\\[\\[E_[^\\]]+\\]\\]$",
          "description": "誤読の主体（in_story_character の場合）"
        },
        "content": {
          "type": "string",
          "description": "誤読の内容"
        },
        "actual_target": {
          "type": "string",
          "pattern": "^\\[\\[(E|ME)_[^\\]]+\\]\\]$",
          "description": "本来の対象（判明している場合）"
        },
        "corrected_by": {
          "type": "string",
          "pattern": "^\\[\\[A_[^\\]]+\\]\\]$",
          "description": "訂正した主張"
        },
        "narrative_function": {
          "type": "string",
          "description": "誤読の物語的機能"
        }
      }
    },
    "conflicting_claims": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["claim_id", "reason"],
        "properties": {
          "claim_id": {"type": "string", "pattern": "^\\[\\[A_[^\\]]+\\]\\]$"},
          "reason": {"type": "string"},
          "resolution_status": {
            "type": "string",
            "enum": ["unresolved", "sublated", "refuted", "coexisting"]
          }
        }
      }
    },
    "provenance": {
      "type": "object",
      "properties": {
        "proposed_by": {
          "type": "object",
          "properties": {
            "kind": {"type": "string", "enum": ["human", "agent"]},
            "id": {"type": "string"}
          }
        },
        "reviewed_by": {
          "type": "object",
          "properties": {
            "kind": {"type": "string", "enum": ["human", "agent"]},
            "id": {"type": "string"},
            "date": {"type": "string", "format": "date"}
          }
        }
      }
    },
    "superseded_by": {
      "type": "string",
      "pattern": "^\\[\\[A_[^\\]]+\\]\\]$"
    }
  },
  "if": {
    "properties": {"predicate": {"const": "misreads_as"}}
  },
  "then": {
    "required": ["misreading"]
  }
}
```

### 2.5 伏線（`schemas/mystery.schema.json`）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "mystery.schema.json",
  "title": "Mystery",
  "allOf": [{"$ref": "common.schema.json"}],
  "required": ["mystery_status", "timeline"],
  "properties": {
    "type": {"const": "mystery"},
    "mystery_status": {
      "type": "string",
      "enum": ["candidate", "open", "partially_resolved", "resolved", "invalidated", "unresolved_at_end"]
    },
    "timeline": {
      "type": "object",
      "required": ["introduced"],
      "properties": {
        "introduced": {
          "type": "string",
          "pattern": "^ch\\d{4}$",
          "description": "伏線が提示された章"
        },
        "hinted": {
          "type": "array",
          "items": {"type": "string", "pattern": "^ch\\d{4}$"},
          "description": "ヒントが提示された章のリスト"
        },
        "resolved": {
          "type": "string",
          "pattern": "^ch\\d{4}$",
          "description": "回収された章"
        },
        "invalidated": {
          "type": "string",
          "pattern": "^ch\\d{4}$",
          "description": "無効化された章（誤認だった場合）"
        }
      }
    },
    "related_facts": {
      "type": "array",
      "items": {"type": "string", "pattern": "^\\[\\[O_[^\\]]+\\]\\]$"}
    },
    "related_claims": {
      "type": "array",
      "items": {"type": "string", "pattern": "^\\[\\[A_[^\\]]+\\]\\]$"}
    },
    "resolution_summary": {
      "type": "string",
      "description": "回収時の要約（resolved の場合）"
    },
    "disclosure": {
      "type": "object",
      "properties": {
        "minimum_progress": {"type": "string", "pattern": "^(ch\\d{4}|ch0000|final)$"},
        "audience": {
          "type": "array",
          "items": {"type": "string", "enum": ["reader", "rereader", "analyst"]}
        },
        "level": {
          "type": "string",
          "enum": ["surface", "hint", "revelation", "meta"]
        }
      }
    }
  }
}
```

### 2.6 出典台帳（`schemas/source.schema.json`）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "source.schema.json",
  "title": "Source Registry",
  "allOf": [{"$ref": "common.schema.json"}],
  "required": ["chapter", "local_path"],
  "properties": {
    "type": {"const": "source"},
    "chapter": {
      "type": "string",
      "pattern": "^ch\\d{4}$"
    },
    "local_path": {
      "type": "string",
      "description": "原文ファイルへの相対パス"
    },
    "checksum": {
      "type": "string",
      "pattern": "^sha256:[a-f0-9]{64}$",
      "description": "原文ファイルのSHA256ハッシュ"
    },
    "source_type": {
      "type": "string",
      "enum": ["primary_text", "external_source", "author_statement"],
      "default": "primary_text"
    }
  }
}
```

---

## 3. WikiLink 解決ルール

### 3.1 基本ルール

```
[[E_char_ハルベルト]] → vault/wiki/entities/characters/E_char_ハルベルト.md
[[ME_myth_アポロン]] → vault/wiki/references/mythology/ME_myth_アポロン.md
[[A_alludes_to_ハルベルト_アポロン_ch0124]] → vault/wiki/claims/A_alludes_to_ハルベルト_アポロン_ch0124.md
```

**解決順序：**
1. WikiLink の ID を抽出（`[[...]]` の中身）
2. コア型のプレフィックスからディレクトリを決定
3. ディレクトリ内で該当ファイルを検索
4. 見つからない場合は死リンクとして Lint に報告

### 3.2 同名異義語の処理

**原則：同名ファイルの作成は禁止**

ただし、以下の場合のみコンテキスト修飾子を付与して区別：

```
E_char_ハルベルト_第2形態
E_motif_白銀の髪_変身後
```

### 3.3 リダイレクトと統合

```yaml
# 統合されたファイル例
---
id: E_char_旧ハルベルト
legacy_id: V_ハルベルト_白銀
type: entity
subtype: character
document_status: superseded
superseded_by: "[[E_char_ハルベルト]]"
---

# このページは [[E_char_ハルベルト]] に統合されました。
```

**Obsidian での処理：**
- `superseded_by` のリンクを辿って転送
- Obsidian の alias 機能を活用（`aliases` に旧名を保持）

---

## 4. ディレクトリとファイルの対応表

```
vault/
├── raw/                                    # 原文（Git管理外可）
│   └── chNNNN.txt
│
├── wiki/
│   ├── arcs/                               # ARC_
│   │   └── ARC_01_女神候補選定編.md
│   ├── episodes/                           # O_
│   │   └── O_ch0057_初出.md
│   ├── entities/                           # E_
│   │   ├── characters/                     # E_char_
│   │   │   └── E_char_ハルベルト.md
│   │   ├── terminology/                    # E_term_
│   │   │   └── E_term_文彩の魔女.md
│   │   ├── organizations/                  # E_org_
│   │   ├── items/                          # E_item_
│   │   ├── motifs/                         # E_motif_
│   │   │   └── E_motif_白銀の髪.md
│   │   ├── relationships/                  # E_relation_
│   │   │   └── E_relation_シナモリ_アズーリア_対立軸.md
│   │   └── phrases/                        # E_phrase_
│   │       └── E_phrase_幻想再帰.md
│   ├── references/                         # ME_
│   │   ├── mythology/                      # ME_myth_
│   │   │   └── ME_myth_アポロン.md
│   │   ├── literature/                     # ME_lit_
│   │   ├── philosophy/                     # ME_phil_
│   │   ├── psychology/                     # ME_psych_
│   │   ├── culture/                        # ME_pop_, ME_net_
│   │   └── author-material/                # ME_author_
│   ├── claims/                             # A_
│   │   └── A_alludes_to_ハルベルト_アポロン_ch0124.md
│   ├── mysteries/                          # MY_
│   │   └── MY_二番目の三叉槍の行方.md
│   └── reflections/                        # RF_
│       └── RF_合わせ鏡の隐喻_20260928.md
│
├── sources/                                # SRC_
│   └── source-registry/
│       ├── SRC_ch0057.yaml
│       └── SRC_external_001.yaml
│
├── schemas/                                # JSON Schema
│   ├── common.schema.json
│   ├── entity.schema.json
│   ├── reference.schema.json
│   ├── claim.schema.json
│   ├── mystery.schema.json
│   ├── episode.schema.json
│   ├── arc.schema.json
│   ├── reflection.schema.json
│   └── source.schema.json
│
├── work/                                   # 派生物（Git管理外可）
│   ├── candidates/
│   ├── changesets/
│   ├── locks/
│   └── reports/
│
└── docs/
    ├── knowledge-model.md
    ├── naming-convention.md                # 本ドキュメント
    ├── spoiler-policy.md
    └── runtime/
```

---

## 5. 実装ガイド

### 5.1 ファイル作成フロー

```
1. エンティティの種別を判定（E_, ME_, A_, MY_, RF_, ...）
2. 正規名を決定（canonical_name）
3. スラッグ化（命名規則に従う）
4. ファイル名を生成（{type}_{subtype}_{slug}.md）
5. ディレクトリを決定（対応表に従う）
6. Frontmatter を作成（JSON Schema に準拠）
7. Lint でバリデーション
```

### 5.2 命名規則の自動適用スクリプト例

```python
import re
from pathlib import Path

def slugify(name: str) -> str:
    """正規名をファイル名用スラッグに変換"""
    # 全角スペース → 半角アンダースコア
    slug = name.replace("　", "_").replace(" ", "_")
    # 記号の除去・置換
    slug = re.sub(r"[・（）【】「」（）]", "_", slug)
    # 連続アンダースコアの除去
    slug = re.sub(r"_+", "_", slug)
    # 長さ制限
    if len(slug) > 50:
        slug = slug[:50]
    return slug

def generate_filename(core_type: str, subtype: str, canonical_name: str, chapter: str = None) -> str:
    """ファイル名を生成"""
    slug = slugify(canonical_name)
    
    if core_type == "ARC":
        return f"ARC_{slug}.md"
    elif core_type == "O":
        return f"O_{chapter}_{slug}.md"
    elif core_type == "E":
        return f"E_{subtype}_{slug}.md"
    elif core_type == "ME":
        return f"ME_{subtype}_{slug}.md"
    elif core_type == "A":
        return f"A_{subtype}_{slug}_{chapter}.md"  # subtype = predicate
    elif core_type == "MY":
        return f"MY_{slug}.md"
    elif core_type == "RF":
        return f"RF_{slug}.md"
    else:
        raise ValueError(f"Unknown core type: {core_type}")

def determine_directory(core_type: str, subtype: str = None) -> Path:
    """ファイルを配置するディレクトリを決定"""
    base = Path("vault/wiki")
    
    if core_type == "ARC":
        return base / "arcs"
    elif core_type == "O":
        return base / "episodes"
    elif core_type == "E":
        subtype_map = {
            "char": "characters",
            "term": "terminology",
            "org": "organizations",
            "item": "items",
            "motif": "motifs",
            "relation": "relationships",
            "phrase": "phrases"
        }
        return base / "entities" / subtype_map[subtype]
    elif core_type == "ME":
        subtype_map = {
            "myth": "mythology",
            "lit": "literature",
            "phil": "philosophy",
            "psych": "psychology",
            "pop": "culture",
            "net": "culture",
            "author": "author-material"
        }
        return base / "references" / subtype_map[subtype]
    elif core_type == "A":
        return base / "claims"
    elif core_type == "MY":
        return base / "mysteries"
    elif core_type == "RF":
        return base / "reflections"
    else:
        raise ValueError(f"Unknown core type: {core_type}")
```

### 5.3 バリデーションスクリプト例

```python
import yaml
import jsonschema
from pathlib import Path

def validate_frontmatter(file_path: Path) -> list[str]:
    """Frontmatter を JSON Schema でバリデーション"""
    errors = []
    
    # 1. YAML パース
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
        # Frontmatter の抽出（--- で囲まれた部分）
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not match:
            return ["Frontmatter not found"]
        
        try:
            data = yaml.safe_load(match.group(1))
        except yaml.YAMLError as e:
            return [f"YAML parse error: {e}"]
    
    # 2. schema_version 確認
    schema_version = data.get("schema_version")
    if schema_version != "5.1":
        errors.append(f"Unsupported schema_version: {schema_version}")
    
    # 3. type からスキーマを決定
    node_type = data.get("type")
    schema_map = {
        "entity": "entity.schema.json",
        "external_reference": "reference.schema.json",
        "analytical_claim": "claim.schema.json",
        "mystery": "mystery.schema.json",
        "episode": "episode.schema.json",
        "arc": "arc.schema.json",
        "reflection": "reflection.schema.json",
        "source": "source.schema.json"
    }
    
    if node_type not in schema_map:
        return [f"Unknown type: {node_type}"]
    
    schema_path = Path("vault/schemas") / schema_map[node_type]
    if not schema_path.exists():
        return [f"Schema not found: {schema_path}"]
    
    # 4. JSON Schema バリデーション
    with open(schema_path, encoding="utf-8") as f:
        schema = jsonschema.Draft7Validator(json.load(f))
    
    for error in schema.iter_errors(data):
        errors.append(f"Schema validation failed at {'.'.join(map(str, error.path))}: {error.message}")
    
    return errors

if __name__ == "__main__":
    for md_file in Path("vault/wiki").rglob("*.md"):
        errors = validate_frontmatter(md_file)
        if errors:
            print(f"❌ {md_file}")
            for error in errors:
                print(f"   - {error}")
        else:
            print(f"✅ {md_file}")
```

---

## 6. 付録：サンプルファイル

### 6.1 エンティティ（キャラクター）

```markdown
---
schema_version: "5.1"
id: E_char_ハルベルト
type: entity
subtype: character
canonical_name: "ハルベルト"
aliases:
  - "楽神"
  - "銀髪の魔女"
first_appearance: "ch0012"
spoiler_after: "ch0012"
document_status: active
created: "2026-09-27"
updated: "2026-09-28"
---

# ハルベルト

第一の三叉槍の末妹候補。文彩（レトリック）の魔女。

## 関連する主張

- [[A_alludes_to_ハルベルト_アポロン_ch0124|アポロンへの引喩]]

## 関連するモチーフ

- [[E_motif_白銀の髪]]
```

### 6.2 分析主張

```markdown
---
schema_version: "5.1"
id: A_alludes_to_ハルベルト_アポロン_ch0124
type: analytical_claim
subject: "[[E_char_ハルベルト]]"
predicate: alludes_to
object: "[[ME_myth_アポロン]]"
valid_from: "ch0124"
spoiler_after: "ch0124"
epistemic_status: confirmed
review_status: human_verified
document_status: active
evidence_strength: strong
evidence:
  - source_id: SRC_ch0124
    locator:
      chapter: "ch0124"
      lines: "145-150"
      quote: "地上において知らぬ者無き天上の美声。楽神の囀り。"
    evidence_type: direct_quote
mapping:
  - subject_feature: "文彩（レトリック）の魔女"
    object_feature: "音楽と詩の神"
    relation: attribute_correspondence
  - subject_feature: "天上の美声"
    object_feature: "神々の詠唱"
    relation: iconographic_match
provenance:
  proposed_by:
    kind: agent
    id: extraction_agent_v3
  reviewed_by:
    kind: human
    id: local_owner
    date: "2026-09-28"
created: "2026-09-27"
updated: "2026-09-28"
---

# ハルベルトはアポロンを引喩している

## 概要

ハルベルトの「文彩の魔女」としての側面は、ギリシャ神話のアポロン（音楽・詩・予言の神）と構造的に一致する。

## 構造マッピングの詳細

（Frontmatter の `mapping` を人間可読な形式で展開）

## 典拠

> "地上において知らぬ者無き天上の美声。楽神の囀り。" (ch0124, lines 145-150)
```

---

## 7. まとめ

この実装仕様により、以下のことが可能になります：

1. **ファイル命名の自動化**: `generate_filename()` で一貫したファイル名を生成
2. **配置場所の自動決定**: `determine_directory()` で正しいディレクトリに配置
3. **スキーマバリデーション**: `validate_frontmatter()` で JSON Schema に準拠しているか確認
4. **Lint との連携**: 設計書の Lint 仕様とスキーマ定義を対応させ、一貫した品質保証を実現

**次のステップ：**
- `schemas/` ディレクトリに JSON Schema ファイルを作成
- `lint.py` を実装し、サンプルファイルでテスト
- 既存ファイルの移行スクリプトを作成

実装を進める上で不明点があれば、具体的に質問してください。