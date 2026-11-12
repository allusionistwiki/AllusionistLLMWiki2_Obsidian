#!/usr/bin/env python3
"""台帳対応節（L2REF）後処理 v2: kind 表示を現行台帳へ追随＋統合本体（merged_into）は統合先表示。
用法: python scripts/fix_l2ref_kind.py <run_id>"""
import json
import re
import sys
from pathlib import Path

WIKI = Path("C:/Users/d5dx/Downloads/Code/AllusionistLLMWiki2/wiki")
LEDGER = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_work/work/allusionist_v2/L2/runs/%s/entities.json" % sys.argv[1])

KIND_LABEL = {"character": "キャラクター", "terminology": "用語", "item": "アイテム",
              "organization": "組織", "location": "場所", "motif": "モティーフ",
              "phrase": "フレーズ", "event": "事件", "creature": "生物",
              "relationship": "関係"}
PAT = re.compile(r"(ID `(?P<id>[^`]+)` / kind: )(?P<kind>[^\s（]+)")


def main():
    ents = json.loads(LEDGER.read_text(encoding="utf-8"))["entities"]
    ent_by_id = {e["id"]: e for e in ents}
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
            e = ent_by_id.get(eid)
            if not e:
                unknown += 1
                return m.group(0)
            if e.get("merged_into"):
                tgt = ent_by_id.get(e["merged_into"], {})
                label = "統合先 **%s**（%s）" % (tgt.get("canonical", e["merged_into"]), e.get("merged_confidence", ""))
            else:
                k = e.get("kind", "")
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
