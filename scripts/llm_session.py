#!/usr/bin/env python3
"""LLM セッション（Strata 内部の会話キャッシュ活用）.

Strata の prefix caching は Conversation Cache（チェックポイント方式、
一度に1会話、プレフィックス完全一致）で実装されている。
OpenAI 互換プロトコル上、messages は毎回全送する必要があるため、
クライアント側で「送らない」ことはできない。効くのは Strata 側の
プレフィックス再利用だけで、その条件は:

1. 同一セッション（会話履歴を append-only で積み上げる）
2. プレフィックス固定（system → 原文コンテキスト → 変数は最後）

→ 同じ章の複数タスク（抽出チャンク、ページ書き下ろし）は1セッションにまとめる。
→ SQLite 等のプロンプトキャッシュは作らない（効果なしと結論済み）。
"""
from __future__ import annotations

from typing import Optional

from openai import OpenAI

from llm_client import call_llm_messages


class LlmSession:
    """同一プレフィックスで連続呼び出しするセッション（append-only 履歴）"""

    def __init__(self, client: OpenAI, config: dict,
                 system_prompt: Optional[str] = None):
        self.client = client
        self.config = config
        self.messages: list[dict] = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})

    def add_context(self, content: str) -> None:
        """原文コンテキストを追加（初回のみフル読み込み、以降は KV キャッシュ）"""
        self.messages.append({"role": "user", "content": content})

    def chat(self, prompt: str, temperature: Optional[float] = None,
             max_tokens: Optional[int] = None, json_mode: bool = False,
             stream: Optional[bool] = None) -> str:
        """セッション内で1タスク実行（応答も履歴に積む → プレフィックスが伸びる）"""
        self.messages.append({"role": "user", "content": prompt})
        content = call_llm_messages(
            self.client, self.config, self.messages,
            temperature=temperature, max_tokens=max_tokens,
            json_mode=json_mode, stream=stream)
        self.messages.append({"role": "assistant", "content": content})
        return content

    def reset(self) -> None:
        self.messages = [m for m in self.messages if m["role"] == "system"]
