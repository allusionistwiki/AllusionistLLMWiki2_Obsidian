#!/usr/bin/env python3
"""L1 側再生成: events ノードページ生成（work → vault wiki/events/）。

入力: work/allusionist_v2/L1/runs/<latest>/events/*.jsonl（run.json 来歴は各ページに記録）
出力: vault wiki/events/E_*.md（type: entity + subtype: event 相当の独立ページではなく、
      claims の subject が参照する `E_chNNNN_*` ノードを実ページ化し LNK003 を解消する）。
      frontmatter: id=E_..., type: event, title=観測行, episode, subject/predicate/object,
      paragraph, quote, created。
設計: claim の subject は graph ノード（event_id）参照。v5.3 では graph ノードは
      frontmatter 参照でページ化しない運用だったが、claims の参照を実解決するため
      ノードページを生成する（追加専用・冪等・決定論・LLM 不使用）。
"""
import json
import re
import sys
from pathlib import Path

WORK = Path(r"C:/Users/d5dx/Downloads/Code/AllusionistWiki_work")
VAULT = Path(r"C:/Users/d5dx/Downloads/Code/AllusionistLLMWiki2")
RUNS = WORK / "work" / "allusionist_v2" / "L1" / "runs"
OUT_DIR = VAULT / "wiki" / "events"


def load_events():
    ev = {}
    for run_dir in sorted(RUNS.iterdir()):
        ev_dir = run_dir / "events"
        if not ev_dir.is_dir():
            continue
        for f in sorted(ev_dir.glob("ch*.jsonl")):
            for line in f.read_text(encoding="utf-8").splitlines():
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                eid = d.get("event_id")
                if eid:
                    d["_run"] = run_dir.name
                    ev[eid] = d  # 後勝ち（新しい run 優先）
    return ev


def page_text(d):
    eid = d["event_id"]
    ep = str(d.get("episode") or "")
    para = d.get("paragraph")
    obs = str(d.get("observation") or "").strip()
    quote = str(d.get("quote") or "").strip()
    subj = str(d.get("subject") or "")
    pred = str(d.get("predicate") or "")
    obj = str(d.get("object") or "")
    etype = str(d.get("entity_type") or "character")
    title = obs[:60] if obs else f"{subj} {pred} {obj}".strip()
    fm = [
        "---",
        "schema_version: '5.1'",
        f"id: {eid}",
        "type: event",
        f"title: {json.dumps(title, ensure_ascii=False)}",
        f"episode: {ep}",
        f"subject: \"[[{subj}]]\"",
        f"predicate: {pred}",
    ]
    if obj:
        fm.append(f"object: \"{json.dumps(str(obj), ensure_ascii=False)}\"")
    if para is not None:
        fm.append(f"paragraph: {para}")
    fm += [
        f"entity_type: {etype}",
        f"source_run: {d['_run']}",
        f"created: '{d.get('created') or ''}'",
        "document_status: active",
        "---",
    ]
    body = [f"# {title}", "", "## 観測", "", obs, ""]
    if quote:
        body += ["## 原文引用", "", f"> ¶{para}: {quote}", ""]
    body += [
        "## 関連",
        "",
        f"- エピソード: [[{ep}]]",
        f"- 主語: [[{subj}]]",
        f"- 生成元: work L1 run `{d['_run']}`（追加専用 run 出力）",
        "",
    ]
    return "\n".join(fm) + "\n\n" + "\n".join(body)


def main():
    ev = load_events()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    n = 0
    for eid, d in ev.items():
        p = OUT_DIR / f"{eid}.md"
        txt = page_text(d)
        if p.exists() and p.read_text(encoding="utf-8") == txt:
            continue
        p.write_text(txt, encoding="utf-8")
        n += 1
    print(f"events pages: total={len(ev)} written={n}")
    print("=== BUILD EVENTS PAGES DONE ===")


if __name__ == "__main__":
    main()
