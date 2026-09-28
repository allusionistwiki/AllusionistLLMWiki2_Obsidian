#!/usr/bin/env python3
"""LLM クライアント: OpenAI互換エンドポイント（Strata / MiaAI-Lab）対応.

- A: リトライ（指数バックオフ）+ ストリーミング応答
- D: 分割投入（chunk 抽出 → event_id 重複排除マージ）
- Strata 特性対応: 1リクエスト直列 → グローバルスロットル（min_interval_ms）
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Optional

import yaml
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent

# グローバル直列スロットル（Strata は 1リクエストずつしか処理しない）
_request_lock = threading.Lock()
_last_request_time = 0.0


def load_config() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def create_client(config: dict) -> OpenAI:
    llm = config["llm"]
    return OpenAI(
        base_url=llm["base_url"],
        api_key=llm.get("api_key", "local"),
        timeout=llm.get("timeout", 300),
        max_retries=0,  # リトライは call_llm 側で制御
    )


def _throttle(config: dict):
    """リクエスト間隔の下限を確保（スレッドセーフ、直列処理保証）"""
    global _last_request_time
    min_interval = config.get("request_throttle", {}).get("min_interval_ms", 500) / 1000.0
    with _request_lock:
        elapsed = time.time() - _last_request_time
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        _last_request_time = time.time()


def call_llm(client: OpenAI, config: dict, prompt: str,
             system_prompt: Optional[str] = None,
             temperature: Optional[float] = None,
             max_tokens: Optional[int] = None,
             json_mode: bool = False,
             stream: Optional[bool] = None) -> str:
    """LLM を呼ぶ（A: リトライ + ストリーミング対応）"""
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    return call_llm_messages(client, config, messages, temperature=temperature,
                             max_tokens=max_tokens, json_mode=json_mode, stream=stream)


def call_llm_messages(client: OpenAI, config: dict, messages: list[dict],
                      temperature: Optional[float] = None,
                      max_tokens: Optional[int] = None,
                      json_mode: bool = False,
                      stream: Optional[bool] = None) -> str:
    """メッセージ配列を直接渡して LLM を呼ぶ（セッション用）"""
    llm = config["llm"]

    kwargs = {
        "model": llm.get("model"),
        "messages": messages,
        "temperature": temperature if temperature is not None else llm.get("temperature", 0.1),
        "max_tokens": max_tokens if max_tokens is not None else llm.get("max_tokens", 4000),
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    thinking = llm.get("thinking", "off")
    if thinking and thinking != "off":
        kwargs["extra_body"] = {"thinking": thinking}
    use_stream = stream if stream is not None else llm.get("stream", False)

    max_retries = llm.get("max_retries", 3)
    last_err: Optional[Exception] = None
    for attempt in range(max_retries):
        _throttle(config)
        try:
            if use_stream:
                parts = []
                for chunk in client.chat.completions.create(**kwargs, stream=True):
                    if chunk.choices and chunk.choices[0].delta.content:
                        parts.append(chunk.choices[0].delta.content)
                return "".join(parts)
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
        except Exception as e:
            last_err = e
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数バックオフ
    raise RuntimeError(f"LLM 呼び出し失敗（{max_retries} リトライ）: {last_err}")


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


def split_text(text: str, max_chars: int, overlap: int) -> list[str]:
    """D: 分割投入（max_chars <= 0 または原文が小さい場合は1チャンク）"""
    if max_chars <= 0 or len(text) <= max_chars:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(end - overlap, start + 1)
    return chunks


def extract_events(client: OpenAI, config: dict, chapter: str,
                   raw_text: str, temperature: Optional[float] = None) -> list[dict]:
    """章原文からイベントを抽出（D: 分割投入 → event_id 重複排除マージ）.

    pipeline.session_mode: true のとき1セッションにまとめる（Strata の
    Conversation Cache がチャンク1..N-1のプレフィックスを再利用）。
    """
    pipe = config.get("pipeline", {})
    chunks = split_text(raw_text, pipe.get("chunk_max_chars", 0),
                        pipe.get("chunk_overlap_chars", 400))
    session = None
    if pipe.get("session_mode", True) and len(chunks) > 1:
        from llm_session import LlmSession
        session = LlmSession(client, config, system_prompt=SYSTEM_PROMPT)
    events, seen = [], set()
    for i, chunk in enumerate(chunks, 1):
        if len(chunks) == 1:
            user = f"以下の原文（{chapter}）からイベントを抽出してください：\n\n{chunk}"
        else:
            user = (f"以下は {chapter} の原文の一部（{i}/{len(chunks)}）です。"
                    f"この部分の原文からイベントを抽出してください：\n\n{chunk}")
        if session is not None:
            content = session.chat(user, temperature=temperature, json_mode=True)
        else:
            content = call_llm(client, config, user, system_prompt=SYSTEM_PROMPT,
                               temperature=temperature, json_mode=True)
        result = json.loads(content)
        if isinstance(result, dict) and "events" in result:
            part = result["events"]
        elif isinstance(result, list):
            part = result
        else:
            part = [result]
        for ev in part:
            key = ev.get("event_id")
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            events.append(ev)
    return events
