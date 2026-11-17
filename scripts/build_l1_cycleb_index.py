# -*- coding: utf-8 -*-
"""cycleb セクション索引生成: wiki/l1/cycleb/index.md + episodes/index.md。
- 層フラット則・index.md 命名（lint 免除）・ディレクトリ形 URL 到達保証準守。
- cycleb 索引の管轄は本スクリプトのみ（1 ファイル 1 生成者）。"""
import json
from pathlib import Path
from collections import Counter

VAULT = Path(r"C:/Users/d5dx/Downloads/Code/AllusionistLLMWiki2")
RUN = Path(r"C:/Users/d5dx/Downloads/Code/AllusionistWiki_work/work/allusionist_v2/L1/runs/20261116T1600_cycleb")
OUT = VAULT / "wiki" / "l1" / "cycleb"
idx = json.loads((RUN / "episodes-index.json").read_text(encoding="utf-8"))
run = json.loads((RUN / "run.json").read_text(encoding="utf-8"))

ep_lines = []
for r in idx:
    label = r["title"]
    gap = "（gap）" if r.get("gap") else ""
    ep_lines.append(f"- [ch]({r['file']}) — {label}{gap}・{r['records']} 件")

ep_dir_index = ["---", 'title: "cycleb 話別索引"', "type: index", "---", "",
                "# cycleb 話別索引", "",
                f"run: {run['run_id']}（work 層 L1 再生成・台帳 v143 接続）。", "",
                "\n".join(ep_lines), ""]
(OUT / "episodes" / "index.md").write_text("\n".join(ep_dir_index), encoding="utf-8")

total_rec = sum(r["records"] for r in idx)
top = ["---", 'title: "cycleb 観測再生成層"', "type: index", "---", "",
       "# cycleb 観測再生成層（L1 内セクション）", "",
       "ページ先行構造推定チェーン（観察ページ→層分離構造適用→機械正規化→400 件監査 99%→台帳射影）で",
       "全コーパスから再生成された観測ページ群。各話ページは観測本文＋正規化済み観測レコード表（台帳 slug 接続）。", "",
       f"- 話ページ: [episodes/index.md](episodes/index.md)（589 話・レコード {total_rec:,} 件・gap 7 話明記）",
       f"- 台帳: https://allusionistwiki.github.io/AllusionistWiki2/L2/ （観測台帳 run 20261116T1500_v143 接続）",
       f"- 来歴: work run {run['run_id']}（derived_from: obs_apply_v9n 582話 + v143）",
       ""]
(OUT / "index.md").write_text("\n".join(top), encoding="utf-8")
print("cycleb indexes written:", (OUT/"index.md").exists(), (OUT/"episodes"/"index.md").exists())
