#!/usr/bin/env python3
"""台帳対応節（L2REF）の kind 表示を現行台帳の正準 10 語彙＋日本語ラベルへ更新する後処理。"""
import json
import re
import sys
from pathlib import Path

WIKI = Path("C:/Users/d5dx/Downloads/Code/AllusionistLLMWiki2/wiki")
LEDGER = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_work/work/allusionist_v2/L2/runs/20261112T1500_v97kind/entities.json")

KIND_LABEL = {"character": "キャラクター", "terminology": "用語", "item": "アイテム",
              "organization": "組織", "location": "場所", "motif": "モティーフ",
              "phrase": "フレーズ", "event": "事件", "creature": "生物",
              "relationship": "関係"}
PAT = re.compile(r"(ID `(?P<id>[^`]+)` / kind: )(?P<kind>[a-z_]+)")


def main():
    ents = json.loads(LEDGER.read_text(encoding="utf-8"))["entities"]
    by_id = {e["id"]: e.get("kind", "") for e in ents}
    changed = 0
    scanned = 0
    unknown = 0
    for md in WIKI.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        if "kind: " not in text:
            continue

        def sub(m):
            nonlocal changed, unknown
            eid = m.group("id")
            old = m.group("kind")
            k = by_id.get(eid, "")
            if not k:
                unknown += 1
                return m.group(0)
            label = KIND_LABEL.get(k, k)
            if old != label:
                changed += 1
            return m.group(1) + label

        new = PAT.sub(sub, text)
        scanned += 1
        if new != text:
            md.write_text(new, encoding="utf-8")
    print("files_scanned=%d label_changes=%d ledger_miss=%d" % (scanned, changed, unknown))


if __name__ == "__main__":
    main()
