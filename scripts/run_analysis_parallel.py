#!/usr/bin/env python3
"""章並列の解析ランナー（Strata 0.1.41 バッチスロット活用）.

  Phase1（並列 4）: events/facts/analysis — 話別ファイルのみへ書くので安全
  Phase2（逐列）  : autopilot — 共有正規層（エンティティ/クレーム/参照）へ昇格
  Phase3          : fixers 1回 + commit_all + progress 記録

Strata サーバーは単一 GPU でも --batch で 8 スロット同時処理できる
（0.1.41 で穴埋めバッチ・デッドロック修正・backlog 256 済み）。
llm_client._throttle はプロセス内グローバルなので、この 1 プロセス内の
全スレッドでリクエスト間隔が守られる（開始直列・応答重複）。

使い方:
  python scripts/run_analysis_parallel.py            # progress+1 から 272 まで
  python scripts/run_analysis_parallel.py 164 200    # 明示範囲
"""
from __future__ import annotations

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from llm_client import create_client, load_config
from validate_event import load_schema
from extract_chapter import process_chapter
from extract_facts import process_facts
from analyze_chapter import analyze_chapter
from autopilot_review import process as autopilot_process
from pipeline import run_fixers

ROOT = Path(__file__).resolve().parent.parent
PROGRESS = ROOT / "data" / "analysis_progress.txt"
END_DEFAULT = 272
CHUNK = 10
WORKERS = 4


def phase1(c: int, config: dict, client, schema) -> tuple[int, str]:
    stages = []
    for name, fn in (
        ("events", lambda: process_chapter(c, config, client, schema)),
        ("facts", lambda: process_facts(c, config, client)),
        ("analysis", lambda: analyze_chapter(c, config, client)),
    ):
        try:
            ok = fn()
            stages.append(f"{name}={'ok' if ok else 'skip'}")
        except Exception as e:
            stages.append(f"{name}=ERR({e})")
    line = " ".join(stages)
    print(f"[ch{c:04d}] {line}", flush=True)
    return c, line


def main() -> None:
    argv = sys.argv[1:]
    if argv and argv[0] == "--only":
        chapters = [int(x) for x in argv[1].split(",")]
        run_chunk(chapters)
        print("REDO DONE", flush=True)
        return
    config = load_config()
    start = 0
    if PROGRESS.exists():
        start = int(PROGRESS.read_text(encoding="utf-8").strip() or 0)
    start = (int(argv[0]) if len(argv) >= 1 else start + 1)
    end = int(argv[1]) if len(argv) >= 2 else END_DEFAULT
    print(f"開始: ch{start:04d}（progress 完了 {PROGRESS.read_text() if PROGRESS.exists() else 0}）", flush=True)
    for lo in range(start, end + 1, CHUNK):
        hi = min(lo + CHUNK - 1, end)
        run_chunk(list(range(lo, hi + 1)))
    print("ALL DONE", flush=True)


def run_chunk(chapters: list[int]) -> None:
    config = load_config()
    schema = load_schema("event.schema.json")
    client = create_client(config)
    lo, hi = chapters[0], chapters[-1]
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        results = list(ex.map(lambda c: phase1(c, config, client, schema), chapters))
    failed = [c for c, line in results if "ERR" in line]
    # Phase2: autopilot は逐列（共有正規層への書き込み）
    for c in chapters:
        try:
            autopilot_process(c, config, client)
        except Exception as e:
            print(f"[ch{c:04d}] autopilot=ERR({e})", flush=True)
            failed.append(c)
    run_fixers()
    if lo == hi + 1 - len(chapters) and lo <= (int(PROGRESS.read_text()) if PROGRESS.exists() else 0) + 1:
        # 連続チャンクのときだけ progress を進める
        PROGRESS.write_text(str(hi), encoding="utf-8")
    print(f"[chunk ch{lo:04d}-ch{hi:04d}] done (failed: {failed})", flush=True)
    subprocess.run([sys.executable, "scripts/commit_all.py", "-m",
                    f"ch{lo:04d}-ch{hi:04d} 解析（章並列4: events/facts/analysis 並列 + autopilot 逐列）"],
                   cwd=ROOT, check=False)
    print(f"[chunk ch{lo:04d}-ch{hi:04d}] committed", flush=True)


if __name__ == "__main__":
    main()
