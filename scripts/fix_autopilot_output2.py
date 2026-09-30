#!/usr/bin/env python3
"""autopilot 生成物の後片付け:
1. object slug に / を含み「ディレクトリ化」したクレームファイルを平坦化・改名（id 同期）
2. events 層に実在しない subject を参照するクレームを削除（ログ記録）
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAIMS = ROOT / "wiki" / "claims"
WORK_EVENTS = ROOT.parent / "AllusionistLLMWiki2_Work" / "events"
LOG = ROOT.parent / "AllusionistLLMWiki2_Work" / "reports" / "autopilot_log.md"


def flatten_nested() -> int:
    n = 0
    # 話別フォルダ（chXXXX）は表示層の正規レイアウトなので平坦化しない
    for d in [x for x in CLAIMS.iterdir()
              if x.is_dir() and not re.fullmatch(r"ch\d{4}", x.name)]:
        for md in d.rglob("*.md"):
            safe_name = str(md.relative_to(CLAIMS)).replace("\\", "＼").replace("/", "／")
            target = CLAIMS / safe_name
            content = md.read_text(encoding="utf-8")
            stem = target.stem
            content = re.sub(r"^id: .*$", f"id: {stem}", content, count=1, flags=re.M)
            target.write_text(content, encoding="utf-8")
            md.unlink()
            n += 1
        # 空になったディレクトリを削除
        if not any(d.rglob("*")):
            d.rmdir()
    return n


def drop_hallucinated_subjects() -> int:
    ids_by_ch: dict[str, set[str]] = {}
    for jl in WORK_EVENTS.glob("*.jsonl"):
        ids_by_ch[jl.stem] = {json.loads(l).get("event_id", "")
                              for l in jl.read_text(encoding="utf-8").splitlines()}
    removed = []
    for md in CLAIMS.rglob("*.md"):
        content = md.read_text(encoding="utf-8")
        m = re.search(r"^subject: \"\[\[(E_ch(\d{4})_[^\]]+)\]\]\"", content, re.M)
        if not m:
            continue
        ch, want = f"ch{m.group(2)}", m.group(1)
        if want not in ids_by_ch.get(ch, set()):
            md.unlink()
            removed.append((md.name, want))
    if removed:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"\n## 削除（subject が events 層に実在しない = 分析層幻覚）（{__import__('datetime').date.today()}）\n\n")
            for name, want in removed:
                f.write(f"- 削除: {name} :: subject [[{want}]]\n")
        print(f"削除: {len(removed)} 件（ログ記録済み）")
        for name, want in removed:
            print(f"  - {name} :: {want}")
    return len(removed)


def main() -> None:
    n1 = flatten_nested()
    print(f"平坦化: {n1} ファイル")
    drop_hallucinated_subjects()


if __name__ == "__main__":
    main()
