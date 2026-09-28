#!/usr/bin/env python3
"""LLM本文生成スクリプト: 正規層ファイルの本文を Frontmatter+証拠から LLM に生成させる.

生成部分は <!-- LLM-GENERATED --> マーカーで囲み、review_status: unreviewed で人間レビュー対象にする。
鉄則: 証拠（quote）にない情報を書かない / 客観記述 / 人間追記（マーカー外）は保護。

使い方:
  python scripts/generate_bodies.py                 # 全タイプ
  python scripts/generate_bodies.py --type entity
  python scripts/generate_bodies.py --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import yaml
from openai import OpenAI
from rich.console import Console
from rich.progress import Progress

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT, VAULT_ROOT, load_config
from llm_client import call_llm, create_client

console = Console()

LLM_MARKER_START = "<!-- LLM-GENERATED -->"
LLM_MARKER_END = "<!-- /LLM-GENERATED -->"

TYPE_DIRS = {
    "entity": ["entities/characters", "entities/terminology", "entities/organizations",
               "entities/items", "entities/motifs", "entities/relationships", "entities/phrases"],
    "claim": ["claims"],
    "mystery": ["mysteries"],
    "reference": ["references/mythology", "references/literature", "references/philosophy",
                  "references/psychology", "references/culture", "references/author-material"],
    "episode": ["episodes"],
}

ENTITY_PROMPT = """あなたは「幻想再帰のアリュージョニスト」の分析Wikiの編集者です。
以下のエンティティ情報から、簡潔な説明文を生成してください。

【鉄則】
1. イベントの証拠（quote）にない情報は書かない
2. 客観的な記述に留める（解釈は含めない）
3. 3-5文で簡潔に
4. 日本語で記述

【エンティティ情報】
- 名前: {name}
- タイプ: {subtype}
- 初出: {first_appearance}
- 証拠:
{evidence_list}

【出力形式】
説明文のみ（マークダウン記法は使用しない）"""

CLAIM_PROMPT = """あなたは「幻想再帰のアリュージョニスト」の分析Wikiの編集者です。
以下の分析主張（クレーム）情報から、主張の補足説明を生成してください。

【鉄則】
1. 証拠（quote）にない情報は書かない
2. 構造マッピングに基づいて記述する
3. 3-5文で簡潔に
4. 日本語で記述

【クレーム情報】
- 主語: {subject}
- 述語: {predicate} ({predicate_label})
- 対象: {object}
- 証拠:
{evidence_list}
- 構造マッピング:
{mapping_list}

【出力形式】
説明文のみ（マークダウン記法は使用しない）"""

MYSTERY_PROMPT = """あなたは「幻想再帰のアリュージョニスト」の分析Wikiの編集者です。
以下の伏線（ミステリー）情報から、謎の説明を生成してください。

【鉄則】
1. タイムラインに基づいて記述する
2. 推測は「〜と考えられる」のような表現で記述
3. 3-5文で簡潔に
4. 日本語で記述

【ミステリー情報】
- 名前: {name}
- 状態: {status}
- タイムライン:
  - 提示: {introduced}
  - ヒント: {hinted}
  - 解決: {resolved}
- 関連事実: {related_facts}
- 関連主張: {related_claims}

【出力形式】
説明文のみ（マークダウン記法は使用しない）"""

REFERENCE_PROMPT = """あなたは「幻想再帰のアリュージョニスト」の分析Wikiの編集者です。
以下の外部参照（典拠）情報から、簡潔な説明文を生成してください。

【鉄則】
1. 一般的な知識に基づいて記述（外部典拠の説明）
2. 作品との関連を簡潔に記述
3. 3-5文で簡潔に
4. 日本語で記述

【外部参照情報】
- 名前: {name}
- タイプ: {subtype}
- 領域: {domain}
- 作品内での参照:
{referenced_by_list}
- 典拠間の関係:
{relations_list}

【出力形式】
説明文のみ（マークダウン記法は使用しない）"""

EPISODE_PROMPT = """あなたは「幻想再帰のアリュージョニスト」の分析Wikiの編集者です。
以下のエピソード情報から、要約と主要な出来事を生成してください。

【鉄則】
1. イベントの証拠（quote）にない情報は書かない
2. 客観的な記述に留める
3. 要約は2-3文、主要な出来事は箇条書きで3-5個
4. 日本語で記述

【エピソード情報】
- 章: {chapter}
- 登場人物:
{characters_list}
- 主張:
{claims_list}
- 伏線:
{mysteries_list}

【出力形式】
## 概要
（要約）

## 主要な出来事
- （出来事1）
- （出来事2）"""


def parse_frontmatter(content: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not m:
        return {}, content
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2)


def build_frontmatter(fm: dict) -> str:
    return "---\n" + yaml.dump(fm, allow_unicode=True, default_flow_style=False, sort_keys=False) + "---\n"


def extract_evidence_list(fm: dict) -> str:
    evidence = fm.get("evidence", [])
    if not evidence:
        return "（なし）"
    lines = []
    for ev in evidence:
        quote = ev.get("quote", "")
        chapter = ev.get("locator", {}).get("chapter", "")
        lines.append(f"  - {chapter}: 「{quote}」")
    return "\n".join(lines)


def extract_mapping_list(fm: dict) -> str:
    mapping = fm.get("mapping", [])
    if not mapping:
        return "（なし）"
    return "\n".join(
        f"  - {m.get('subject_feature','')} ↔ {m.get('object_feature','')} ({m.get('relation','')})"
        for m in mapping
    )


def extract_referenced_by_list(fm: dict) -> str:
    refs = fm.get("referenced_by", [])
    if not refs:
        return "（なし）"
    return "\n".join(f"  - {r.get('episode','')}: {r.get('claim','')}" for r in refs)


def extract_relations_list(fm: dict) -> str:
    relations = fm.get("relations", [])
    if not relations:
        return "（なし）"
    return "\n".join(f"  - {r.get('predicate','')}: {r.get('target','')}" for r in relations)


def extract_characters_list(fm: dict) -> str:
    characters = fm.get("characters", [])
    return "\n".join(f"  - {c}" for c in characters) if characters else "（なし）"


def generate_body(client: OpenAI, config: dict, file_type: str, fm: dict) -> str:
    if file_type == "entity":
        prompt = ENTITY_PROMPT.format(
            name=fm.get("canonical_name", ""), subtype=fm.get("subtype", ""),
            first_appearance=fm.get("first_appearance", ""), evidence_list=extract_evidence_list(fm))
    elif file_type == "claim":
        predicate = fm.get("predicate", "")
        labels = {"alludes_to": "引喩", "analogous_to": "類推", "recurs_as": "作品内再帰",
                  "structurally_matches": "構造的一致", "misreads_as": "誤読", "foreshadows": "予告",
                  "inverts": "反転", "parodies": "パロディ", "sublates": "止揚"}
        prompt = CLAIM_PROMPT.format(
            subject=fm.get("subject", ""), predicate=predicate,
            predicate_label=labels.get(predicate, predicate), object=fm.get("object", ""),
            evidence_list=extract_evidence_list(fm), mapping_list=extract_mapping_list(fm))
    elif file_type == "mystery":
        timeline = fm.get("timeline", {})
        prompt = MYSTERY_PROMPT.format(
            name=fm.get("canonical_name", ""), status=fm.get("mystery_status", ""),
            introduced=timeline.get("introduced", ""), hinted=", ".join(timeline.get("hinted", [])),
            resolved=timeline.get("resolved", ""),
            related_facts=", ".join(fm.get("related_facts", [])),
            related_claims=", ".join(fm.get("related_claims", [])))
    elif file_type == "reference":
        prompt = REFERENCE_PROMPT.format(
            name=fm.get("canonical_name", ""), subtype=fm.get("subtype", ""),
            domain=fm.get("domain", ""), referenced_by_list=extract_referenced_by_list(fm),
            relations_list=extract_relations_list(fm))
    elif file_type == "episode":
        prompt = EPISODE_PROMPT.format(
            chapter=fm.get("chapter", ""), characters_list=extract_characters_list(fm),
            claims_list=", ".join(fm.get("claims", [])), mysteries_list=", ".join(fm.get("mysteries", [])))
    else:
        return ""
    return call_llm(client, config, prompt,
                    system_prompt="あなたは「幻想再帰のアリュージョニスト」の分析Wikiの編集者です。",
                    max_tokens=500).strip()


def update_file_with_llm_body(file_path: Path, generated_body: str, dry_run: bool = False) -> bool:
    content = file_path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)
    new_section = f"{LLM_MARKER_START}\n{generated_body}\n{LLM_MARKER_END}"
    if LLM_MARKER_START in body:
        pattern = re.escape(LLM_MARKER_START) + r".*?" + re.escape(LLM_MARKER_END)
        body = re.sub(pattern, new_section, body, flags=re.DOTALL)
    else:
        title_match = re.match(r"^# .+\n", body)
        if title_match:
            body = title_match.group(0) + "\n" + new_section + "\n" + body[len(title_match.group(0)):]
        else:
            body = new_section + "\n" + body
    fm["updated"] = date.today().isoformat()
    fm["llm_generated_at"] = date.today().isoformat()
    fm["review_status"] = "unreviewed"
    if dry_run:
        console.print(f"  [magenta][DRY-RUN] {file_path.name}[/magenta]")
        console.print(f"  [dim]{generated_body[:100]}...[/dim]")
        return True
    file_path.write_text(build_frontmatter(fm) + body, encoding="utf-8")
    return True


def process_files(client: OpenAI, config: dict, file_type: str, dry_run: bool = False) -> dict:
    results = {"type": file_type, "processed": 0, "updated": 0, "skipped": 0}
    files: list[Path] = []
    for dir_path in TYPE_DIRS.get(file_type, []):
        full_dir = VAULT_ROOT / dir_path
        if full_dir.exists():
            files.extend(full_dir.glob("*.md"))
    if not files:
        return results

    console.print(f"\n[bold cyan]📝 {file_type} の本文を生成中... ({len(files)} 件)[/bold cyan]")
    with Progress() as progress:
        task = progress.add_task(f"[cyan]{file_type}", total=len(files))
        for file_path in files:
            try:
                fm, _ = parse_frontmatter(file_path.read_text(encoding="utf-8"))
                if fm.get("llm_generated_at") == fm.get("updated") and fm.get("review_status") != "unreviewed":
                    results["skipped"] += 1
                    progress.update(task, advance=1)
                    continue
                generated = generate_body(client, config, file_type, fm)
                if not generated:
                    results["skipped"] += 1
                elif update_file_with_llm_body(file_path, generated, dry_run):
                    results["updated"] += 1
                results["processed"] += 1
            except Exception as e:
                console.print(f"[red]❌ {file_path.name} 処理失敗: {e}[/red]")
                results["skipped"] += 1
            progress.update(task, advance=1)
    return results


def main():
    parser = argparse.ArgumentParser(description="LLM本文生成スクリプト")
    parser.add_argument("--type", help="ファイルタイプ（entity/claim/mystery/reference/episode）")
    parser.add_argument("--dry-run", action="store_true", help="書き込まずに差分のみ表示")
    args = parser.parse_args()

    config = load_config()
    client = create_client(config)

    file_types = [args.type] if args.type else ["entity", "claim", "mystery", "reference", "episode"]
    if args.dry_run:
        console.print("[magenta bold]🔍 DRY-RUN モード（書き込みなし）[/magenta bold]")

    for file_type in file_types:
        r = process_files(client, config, file_type, args.dry_run)
        console.print(f"  {r['type']}: {r['updated']} 更新, {r['skipped']} スキップ")


if __name__ == "__main__":
    main()
