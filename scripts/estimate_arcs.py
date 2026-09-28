#!/usr/bin/env python3
"""アーク推定スクリプト: エピソードのテーマ・頻出エンティティからアーク境界を LLM に推定させ、
schemas/arc_definitions.yaml に書き出す（人間レビュー後、確定）.

使い方:
  python scripts/estimate_arcs.py --dry-run   # 推定結果表示のみ
  python scripts/estimate_arcs.py             # arc_definitions.yaml へ書き出し（既存はバックアップ）
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
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import VAULT_ROOT, SCHEMAS_DIR, load_config

console = Console()

EPISODES_DIR = VAULT_ROOT / "episodes"

ARC_ESTIMATION_PROMPT = """あなたは「幻想再帰のアリュージョニスト」の物語構造を分析する専門家です。
以下のエピソードリスト（各エピソードの主要エンティティ・テーマを含む）から、
物語の自然な区切り（アーク）を推定してください。

【鉄則】
1. 各アークは20-50章程度を目安とする
2. アークの境界は、物語の転換点（新しいキャラクターの登場、テーマの変化など）に置く
3. アーク名とテーマは簡潔に記述
4. 日本語で記述

【エピソードリスト】
{episodes_data}

【出力形式】
```yaml
arcs:
  - id: ARC_01
    name: "アーク名"
    slug: "アーク名"
    chapters:
      start: ch0001
      end: ch0050
    theme: "テーマ"
    description: |
      アークの簡単な説明
```"""


def parse_frontmatter(content: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not m:
        return {}, content
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2)


def extract_episodes_data() -> str:
    lines = []
    if not EPISODES_DIR.exists():
        return ""
    for ep_file in sorted(EPISODES_DIR.glob("O_ch*.md")):
        try:
            fm, _ = parse_frontmatter(ep_file.read_text(encoding="utf-8"))
            chars = ", ".join(fm.get("characters", [])[:5]) or "（なし）"
            claims = ", ".join(fm.get("claims", [])[:3]) or "（なし）"
            lines.append(f"- {fm.get('chapter','')}: 登場人物: {chars} / 主張: {claims}")
        except Exception:
            continue
    return "\n".join(lines)


def call_llm(client: OpenAI, model: str, prompt: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "あなたは「幻想再帰のアリュージョニスト」の物語構造を分析する専門家です。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=2000,
    )
    return response.choices[0].message.content.strip()


def parse_llm_response(response: str) -> dict:
    m = re.search(r"```yaml\n(.*?)\n```", response, re.DOTALL)
    yaml_str = m.group(1) if m else response
    try:
        return yaml.safe_load(yaml_str) or {}
    except yaml.YAMLError:
        return {}


def main():
    parser = argparse.ArgumentParser(description="アーク推定スクリプト")
    parser.add_argument("--min-chapters", type=int, default=20, help="最小章数（デフォルト: 20）")
    parser.add_argument("--dry-run", action="store_true", help="書き込まずに推定結果表示")
    args = parser.parse_args()

    config = load_config()
    client = OpenAI(base_url=config["llm"]["base_url"], api_key=config["llm"]["api_key"])
    model = config["llm"]["model"]

    episodes_data = extract_episodes_data()
    if not episodes_data:
        console.print("[yellow]⚠️ エピソードデータが見つかりません[/yellow]")
        sys.exit(1)

    console.print("[bold cyan]🔮 LLMにアークの境界を推定中...[/bold cyan]")
    response = call_llm(client, model, ARC_ESTIMATION_PROMPT.format(episodes_data=episodes_data))
    arcs_data = parse_llm_response(response)
    if not arcs_data:
        console.print(f"[red]❌ LLMの応答をパースできませんでした[/red]\n[dim]{response}[/dim]")
        sys.exit(1)

    arcs = arcs_data.get("arcs", [])
    if not arcs:
        console.print("[yellow]⚠️ アークが推定されませんでした[/yellow]")
        sys.exit(0)

    table = Table(title="アーク推定結果")
    table.add_column("ID", style="cyan")
    table.add_column("名前", style="green")
    table.add_column("章範囲", style="yellow")
    table.add_column("テーマ", style="magenta")
    for arc in arcs:
        ch = arc.get("chapters", {})
        table.add_row(arc.get("id", ""), arc.get("name", ""), f"{ch.get('start','')}〜{ch.get('end','')}", arc.get("theme", ""))
    console.print(table)

    if args.dry_run:
        console.print("\n[magenta bold]🔍 DRY-RUN モード（書き込みなし）[/magenta bold]")
        return

    SCHEMAS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = SCHEMAS_DIR / "arc_definitions.yaml"
    if output_file.exists():
        backup = SCHEMAS_DIR / f"arc_definitions.yaml.bak.{date.today().isoformat()}"
        output_file.rename(backup)
        console.print(f"[dim]既存ファイルをバックアップ: {backup}[/dim]")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# arc_definitions.yaml\n")
        f.write("# アークの定義ファイル（LLM推定 + 人間レビュー）\n")
        f.write(f"# 推定日: {date.today().isoformat()}\n")
        f.write("# ⚠️  このファイルはLLMによる推定結果です。人間がレビューしてください。\n\n")
        yaml.dump(arcs_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    console.print(f"\n[green]✅ {output_file} に推定結果を書き出しました[/green]")
    console.print("[yellow]⚠️ 人間がレビューして確定してください[/yellow]")


if __name__ == "__main__":
    main()
