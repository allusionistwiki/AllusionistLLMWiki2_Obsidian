#!/usr/bin/env python3
"""human_ops.py — 人間の担当範囲のみの操作（LLM auto-review 標準運用の人間介入口）.

人間の担当はこれだけ:
  特定記事の reject / 修正指示（revisal note）/ 手動追記（body 編集は直接 md を触る）

使い方:
  python scripts/human_ops.py --list                     # llm_verified 記事の一覧（レビュー対象）
  python scripts/human_ops.py --reject <file.md> "理由"  # 人間 reject（llm_verified を無効化）
  python scripts/human_ops.py --revise <file.md> "指示"  # 修正指示を添付（LLM 後続処理待ちマーク）
  python scripts/human_ops.py --verify <file.md>         # 人間承認（llm_verified → human_verified）
  python scripts/human_ops.py --stats                    # 層別ステータス集計
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import yaml
from rich.console import Console
from rich.table import Table

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
LOG = ROOT.parent / "AllusionistLLMWiki2_Work" / "reports" / "human_ops_log.md"
console = Console()


def parse_fm(content: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not m:
        return {}, content
    try:
        return yaml.safe_load(m.group(1)) or {}, m.group(2)
    except yaml.YAMLError:
        return {}, content


def dump_fm(fm: dict) -> str:
    return "---\n" + yaml.dump(fm, allow_unicode=True, sort_keys=False,
                               default_flow_style=False) + "---\n"


def log_op(op: str, target: str, note: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    header = "" if LOG.exists() else "# 人間操作ログ（reject / 修正指示 / 承認）\n\n"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(header + f"- {date.today().isoformat()} [{op}] {target}"
                + (f" :: {note}" if note else "") + "\n")


def find_file(name: str) -> Path:
    p = Path(name)
    if not p.is_absolute():
        p = ROOT / name
    if p.exists():
        return p
    hits = list(WIKI.rglob(Path(name).name))
    if len(hits) == 1:
        return hits[0]
    raise SystemExit(f"対象が特定できません: {name}（hits={len(hits)}）")


def main() -> int:
    ap = argparse.ArgumentParser(description="人間の担当範囲の操作のみ")
    ap.add_argument("--list", action="store_true", help="llm_verified 記事一覧")
    ap.add_argument("--reject", metavar="FILE", help="人間 reject")
    ap.add_argument("--revise", metavar="FILE", help="修正指示を添付")
    ap.add_argument("--verify", metavar="FILE", help="人間承認（human_verified へ）")
    ap.add_argument("--stats", action="store_true", help="ステータス集計")
    ap.add_argument("note", nargs="?", default="", help="理由・指示文（--reject/--revise と併用）")
    args = ap.parse_args()

    if args.stats:
        table = Table(title="review_status 集計")
        table.add_column("層"); table.add_column("llm_verified"); table.add_column("human_verified"); table.add_column("human_rejected"); table.add_column("revise指示")
        for layer in ("claims", "mysteries", "references", "entities"):
            d = WIKI / layer
            c = {"llm": 0, "human": 0, "rej": 0, "rev": 0}
            for md in d.rglob("*.md") if d.exists() else []:
                fm, _ = parse_fm(md.read_text(encoding="utf-8"))
                s = fm.get("review_status", "")
                if s == "llm_verified": c["llm"] += 1
                elif s == "human_verified": c["human"] += 1
                if fm.get("human_rejected"): c["rej"] += 1
                if fm.get("revise_instruction"): c["rev"] += 1
            table.add_row(layer, str(c["llm"]), str(c["human"]), str(c["rej"]), str(c["rev"]))
        console.print(table)
        return 0

    if args.list:
        table = Table(title="レビュー対象（llm_verified）")
        table.add_column("file"); table.add_column("type")
        n = 0
        for md in sorted(WIKI.rglob("*.md")):
            fm, _ = parse_fm(md.read_text(encoding="utf-8"))
            if fm.get("review_status") == "llm_verified" and not fm.get("human_rejected"):
                table.add_row(str(md.relative_to(ROOT)), str(fm.get("type", "")))
                n += 1
                if n >= 60:
                    table.add_row("...", f"(他 {n - 60}+ 件)")
                    break
        console.print(table)
        return 0

    if args.reject:
        p = find_file(args.reject)
        content = p.read_text(encoding="utf-8")
        fm, body = parse_fm(content)
        fm["review_status"] = "needs_revision"
        fm["human_rejected"] = {"date": date.today().isoformat(),
                                "reason": args.note or "理由未記載"}
        p.write_text(dump_fm(fm) + body, encoding="utf-8")
        log_op("reject", p.name, args.note)
        console.print(f"[red]reject[/red] {p.name}（llm_verified 無効化、理由記録）")
        return 0

    if args.revise:
        p = find_file(args.revise)
        content = p.read_text(encoding="utf-8")
        fm, body = parse_fm(content)
        fm["revise_instruction"] = {"date": date.today().isoformat(),
                                    "instruction": args.note or ""}
        p.write_text(dump_fm(fm) + body, encoding="utf-8")
        log_op("revise", p.name, args.note)
        console.print(f"[yellow]revise 指示添付[/yellow] {p.name}（LLM 後続処理待ち）")
        return 0

    if args.verify:
        p = find_file(args.verify)
        content = p.read_text(encoding="utf-8")
        fm, body = parse_fm(content)
        fm["review_status"] = "human_verified"
        prov = fm.get("provenance") or {}
        prov["reviewed_by"] = {"kind": "human", "date": date.today().isoformat()}
        fm["provenance"] = prov
        p.write_text(dump_fm(fm) + body, encoding="utf-8")
        log_op("verify", p.name, args.note)
        console.print(f"[green]human_verified[/green] {p.name}")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
