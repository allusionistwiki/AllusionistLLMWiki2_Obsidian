#!/usr/bin/env python3
"""クレームが参照するのに存在しない ME_ 外部参照の骨格ページを生成する.

autopilot が昇格したクレームは object に [[ME_xxx]] を直接書くが、
staging の references 層を通過しないため ME ページが作られず死リンクになる。
→ wiki/claims の ME 参照を収集し、欠けているものを骨格ページとして作成する。
解説文の自動追記パスは保留中（本文は最小、人間追記は AUTO マーカーの外）。
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF_DIR = ROOT / "wiki" / "references"
CLAIMS_DIR = ROOT / "wiki" / "claims"

# 参考: merge_references.py の SUBTYPE_MAP と同じ置き場（骨格は culture に寄せる）
DEFAULT_SUBTYPE = "popular_culture"  # schema enum 準拠


def existing_me_names() -> set[str]:
    return {p.stem for p in REF_DIR.rglob("ME_*.md")}


def collect_claim_me_refs() -> dict[str, list[str]]:
    refs: dict[str, list[str]] = {}
    for p in CLAIMS_DIR.glob("A_*.md"):
        s = p.read_text(encoding="utf-8")
        for m in re.finditer(r"\[\[(ME_[^\]]+)\]\]", s):
            refs.setdefault(m.group(1), []).append(p.stem)
    return refs


def build_stub(me_id: str, claim_ids: list[str]) -> str:
    name = me_id[len("ME_"):]
    today = date.today().isoformat()
    fm = "\n".join([
        "---",
        'schema_version: "5.1"',
        f"id: {me_id}",
        "type: external_reference",
        f'title: "{name}"',
        f"subtype: {DEFAULT_SUBTYPE}",
        f'canonical_name: "{name}"',
        "aliases: []",
        'domain: "culture"',
        "document_status: active",
        f"referenced_by: []",
        "relations: []",
        f'created: "{today}"',
        f'updated: "{today}"',
        "---",
    ])
    body = (
        f"# {name}\n\n"
        "<!-- AUTO:BEGIN -->\n"
        "（骨格ページ: クレームが参照する外部概念。解説は未記入 — 人間追記または解説自動追記パスで補う。）\n\n"
        "## 本作での参照\n\n"
        + "\n".join(f"- [[{c}]]" for c in claim_ids[:10])
        + "\n<!-- AUTO:END -->\n"
    )
    return fm + "\n" + body


def main() -> int:
    have = existing_me_names()
    refs = collect_claim_me_refs()
    missing = {k: v for k, v in refs.items() if k not in have}
    created = 0
    for me_id, claim_ids in sorted(missing.items()):
        path = REF_DIR / f"{me_id}.md"
        if path.exists():
            continue
        path.write_text(build_stub(me_id, claim_ids), encoding="utf-8")
        created += 1
    print(f"ME 骨格ページ生成: {created} 件（欠損 {len(missing)}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
