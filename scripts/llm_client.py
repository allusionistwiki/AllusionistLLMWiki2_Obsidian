#!/usr/bin/env python3
"""LLM クライアント（OpenAI互換 / MiaAI-Lab Qwen）とイベント抽出関数."""
from __future__ import annotations

import json
from pathlib import Path

import yaml
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent


def load_config() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def create_client(config: dict) -> OpenAI:
    return OpenAI(base_url=config["llm"]["base_url"], api_key=config["llm"]["api_key"])


SYSTEM_PROMPT = """
あなたは「幻想再帰のアリュージョニスト」の事実抽出エージェントです。

【鉄則】
1. 原文にない情報は絶対に出さない
2. 各事実に証拠（quote）を付与
3. 出力は必ずJSON配列形式

【出力形式】
[
  {
    "event_id": "E_ch{NNNN}_{entity_type}_{entity}_{aspect略称}_O",
    "episode": "ch{NNNN}",
    "entity": "エンティティ名",
    "entity_type": "character|terminology|organization|item|motif|relationship|phrase",
    "aspect": "visual|name|speech|action|relationship|symbolic",
    "observation": "観察内容",
    "quote": "原文からの引用",
    "locator": {
      "chapter": "ch{NNNN}",
      "lines": "行番号（推定で可）"
    },
    "spoiler_after": "ch{NNNN}"
  }
]

【aspect の略称】
- visual → V
- name → N
- speech → S
- action → A
- relationship → R
- symbolic → Y
"""


def extract_events(client: OpenAI, model: str, chapter: str, raw_text: str, temperature: float = 0.1) -> list[dict]:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"以下の原文（{chapter}）からイベントを抽出してください：\n\n{raw_text}"},
        ],
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    if isinstance(result, dict) and "events" in result:
        return result["events"]
    if isinstance(result, list):
        return result
    return [result]
