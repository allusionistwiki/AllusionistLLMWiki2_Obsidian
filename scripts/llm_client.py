#!/usr/bin/env python3
"""LLM クライアント: OpenAI互換エンドポイント（Strata / MiaAI-Lab）対応.

- A: リトライ（指数バックオフ）+ ストリーミング応答
- D: 分割投入（chunk 抽出 → event_id 重複排除マージ）
- Strata 特性対応: 1リクエスト直列 → グローバルスロットル（min_interval_ms）
"""
from __future__ import annotations

import json
import re
import threading
import time
from pathlib import Path
from typing import Optional

import yaml
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent

# 述語管理語彙（schemas/predicate_vocabulary.yaml）
def _load_predicate_vocab() -> tuple[set[str], dict[str, str]]:
    try:
        data = yaml.safe_load((ROOT / "schemas" / "predicate_vocabulary.yaml").read_text(encoding="utf-8"))
        ids = {p["id"] for p in data.get("predicates", [])}
        alias = {}
        for p in data.get("predicates", []):
            for a in p.get("aliases", []):
                alias[a] = p["id"]
        return ids, alias
    except Exception:
        return {"other"}, {}


PREDICATE_VOCAB, PREDICATE_ALIAS = _load_predicate_vocab()

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
    # Strata: thinking は chat_template_kwargs.enable_thinking（vLLM/llama.cpp 規約、
    # serve/frontend.py:158）。既定 True だと全トークンが reasoning_content に
    # 消費され content が None になる。reasoning_effort は effort_kwargs 経由。
    thinking = llm.get("thinking", "off")
    extra = {}
    if thinking in ("off", "false", False):
        extra["chat_template_kwargs"] = {"enable_thinking": False}
    elif thinking in ("low", "medium", "high"):
        extra["reasoning_effort"] = thinking
    if extra:
        kwargs["extra_body"] = extra
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
3. quote は原文からの**連続した**引用（途中を「...」で省略・連結しない。長い場合は原文の一区切りで切り、長くても1文〜2文まで）
4. 出力は必ずJSON配列形式

【粒度】
- 粗くまとめすぎない: 1イベント=1観察。同一エンティティでも visual/speech/action/relationship 等で分ける
- 会話の発話内容（キャラクターの人となり・知識・関係がわかる発言）、固有名詞の初出、世界設定の説明、物品の機能描写、伏線となる描写は必ず個別に抽出
- 章あたり目安: 2万字の章なら 40〜80 イベント。原文の各場面（シーン）を漏らさない

【SPO構造（最重要）】
各イベントは「誰が(subject)・何をした(predicate)・何を(object)」で記述する:
- subject: 行為者。行為の主体を必ず正しく特定すること（例: ノーペインを起動したのは「ノーペイン」ではなく「アキラ」）
- predicate: 下記【述語語彙】から1つ選ぶ（逸脱する場合は "other"）
- object: 対象（自動詞的イベントでは省略可）。名詞スラッグで簡潔に（例: 金鎖の環、前世の殺人）
- paragraph: 原文の【pN】マーカーの N（イベントが起きたページ番号）
- subject/object のスラッグは 空白・アンダースコア・括弧・長音記号以外の記号を含まない短い名前で（例: アキラ、カイン、金鎖、ノーペイン）

【述語語彙】
kills wounds saves dies fights attacks defeats flees captures escapes gives takes breaks repairs
loses finds hides makes uses activates stops opens wears carries says asks
confesses promises threatens names reveals conceals thinks remembers learns
observes trusts suspects bonds betrays helps teaches deceives loves hates
appears disappears transforms teleports travels arrives departs hopes fears other

【分析の材料（signals、任意）】
以下のどれかに該当するイベントには signals を付ける（判断に迷ったら付けない）:
- analogy: ジャンル・作品・実在の物事への引喩/パロディ（例: トラック運転手の殺し屋→トラック転生クリシェ、転生保険→保険商品/ガチャ、サイバーカラテ→スマホ格ゲー、ノーペイン→SSRI/倫理的緩和ケア）
- foreshadow: 後の展開で回収されそうな伏線（例: 環が4→2に減った金鎖、光を飲み込む左手、消失する闇色の脚）
- motif: 章を超えて反復されそうな主題的イメージ（例: 感謝の言葉、贈与は共通言語）
- theme: この章の主題の候補（1章に高々1〜2件）

【出力形式】
[
  {
    "episode": "ch{NNNN}",
    "subject": "行為者スラッグ",
    "predicate": "述語語彙から1つ",
    "object": "対象スラッグ（省略可）",
    "paragraph": "p{N}",
    "entity_type": "character|terminology|organization|item|motif|relationship|phrase",
    "aspect": "visual|name|speech|action|relationship|symbolic",
    "observation": "観察内容",
    "quote": "原文からの引用",
    "signals": [{"kind": "analogy|foreshadow|motif|theme", "note": "内容"}],
    "spoiler_after": "ch{NNNN}"
  }
]
※ event_id はあなたが作らなくてよい（システムが決定論的に採番する）

【aspect（観測チャネル）】
- visual: 見た目/描写 / name: 名前・呼称 / speech: 発話内容 / action: 行為
- relationship: 関係の変化 / symbolic: 象徴・寓意
※ predicate（何が起きたか）と aspect（どう観測されたか）は別軸。台詞による告白なら predicate=confesses, aspect=speech
"""


def strip_code_fence(text: str) -> str:
    """LLM 出力が ```json ... ``` フェンスに包まれている場合に取り除く"""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t[3:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()


def slug(s: str) -> str:
    """スラッグ正規化: 空白・括弧・記号を除去（entity 名の表記ゆれ対策の第一歩）"""
    s = re.sub(r"[（）()\[\]【】「」『』\s]+", "", s or "")
    return s or "unknown"


def canonical_event_id(ev: dict, counter: dict) -> dict:
    """event_id を SPO+定位子から決定論的に構築（再現性・重複検出・クエリ可能性）.

    正規形: E_{chapter}_{subject}_{predicate}_{object}_p{page}
    - object 省略時は E_{chapter}_{subject}_{predicate}_p{page}
    - 同一 SPO+page の複数件は _2, _3 連番（ソート順で決定的）
    - predicate は管理語彙外なら other に落として review フラグ
    """
    episode = ev.get("episode", "")
    subject = slug(ev.get("subject") or ev.get("entity", "unknown"))
    predicate = ev.get("predicate", "other")
    if predicate not in PREDICATE_VOCAB:
        predicate = PREDICATE_ALIAS.get(predicate, "other")
        if predicate == "other":
            ev["needs_review"] = "predicate 逸脱"
    ev["predicate"] = predicate
    etype = ev.get("entity_type", "character")
    if etype not in {"character", "terminology", "organization", "item", "motif", "relationship", "phrase"}:
        etype = "terminology"  # location 等の逸脱は terminology に写す（7コア型維持）
    ev["entity_type"] = etype
    obj = slug(ev.get("object", "")) if ev.get("object") else ""
    para = ev.get("paragraph") or (ev.get("locator") or {}).get("paragraph_id") or "p0"
    para = re.sub(r"[^0-9]", "", str(para))
    para = f"p{para}"
    base = f"E_{episode}_{subject}_{predicate}" + (f"_{obj}" if obj else "")
    key = base + f"_{para}"
    n = counter.get(key, 0)
    counter[key] = n + 1
    ev["event_id"] = key if n == 0 else f"{base}_{n + 1}_{para}"
    ev.setdefault("entity", subject)
    ev["paragraph"] = para
    return ev


def parse_json_lenient(content: str, chunk_idx: int) -> list | dict:
    """JSON 解析（max_tokens で切られた応答は末尾の完全オブジェクトまで切り捨てて救済）"""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    is_array = content.lstrip().startswith("[")
    tail = "]" if is_array else "}}"
    pos = len(content)
    while True:
        cut = content.rfind("},", 0, pos)
        if cut <= 0:
            break
        try:
            return json.loads(content[:cut + 1] + tail)
        except json.JSONDecodeError:
            pos = cut
    print(f"   WARN chunk {chunk_idx}: JSON 解析不能（{len(content)} chars）→ スキップ")
    return []


def normalize_quote(ev: dict, raw_norm: str) -> dict:
    """quote 正規化: 「...」「……」で連結された引用を、原文に実在する最長連続断片に縮退.

    幻覚（原文にない引用）は検出できないが、連結による原文不在は機械的に救える。
    raw_norm は norm_text(raw_text) で事前計算（章ごとに1回）。
    """
    q = ev.get("quote", "")
    if not q:
        return ev
    if norm_text(q) in raw_norm:
        return ev
    parts = [p for p in re.split(r"\.{2,}|…{2,}", q) if p.strip()]
    best = ""
    for p in parts:
        if norm_text(p) in raw_norm and len(p) > len(best):
            best = p
    if best:
        ev["quote"] = best.strip()
    return ev


def norm_text(s: str) -> str:
    s = re.sub(r"【p\d+】", "", s)
    return re.sub(r"\s+", "", s)


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
        content = strip_code_fence(content)
        result = parse_json_lenient(content, i)
        if isinstance(result, dict) and "events" in result:
            part = result["events"]
        elif isinstance(result, list):
            part = result
        else:
            part = [result]
        for ev in part:
            # 重複排除は SPO+quote キーで（チャンク重複部で同一イベントが二重抽出される）
            key = (ev.get("episode"), slug(ev.get("subject") or ev.get("entity", "")),
                   ev.get("predicate"), slug(ev.get("object", "")),
                   norm_text(ev.get("quote", "")))
            if key in seen:
                continue
            seen.add(key)
            events.append(ev)
    # event_id は SPO+定位子から決定論的に採番（ソートで再現性を保証）
    events.sort(key=lambda e: (e.get("episode", ""), str(e.get("paragraph", "p0")),
                               slug(e.get("subject") or e.get("entity", "")),
                               e.get("predicate", ""), slug(e.get("object", ""))))
    counter: dict = {}
    raw_norm = norm_text(raw_text)
    events = [canonical_event_id(normalize_quote(ev, raw_norm), counter) for ev in events]
    return events
