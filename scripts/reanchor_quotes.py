#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reanchor_quotes.py — quote-map 再解析キュー（引用全文一致しなかった fact）を
LLM でカクヨム版 ¶ アンカーへ再アンカーする。

方式:
  - 同一章のヒット済み引用（s_para 順）でカクヨム位置を補間し、±WINDOW¶ 窓を提示
  - LLM はカクヨム文から対応一節を「原文のまま」抽出（引用改変は検証で弾く）
  - 検証: 返された引用が窓（→ 失敗時 巻全文）に正規化一致 → (ch, ¶start..¶end) を
    位置から導出（LLM の ¶ 番号は信用しない）
  - 見つからない = カクヨム版で削除/大改稿 → status: not_found（人間レビュー行き）

出力: work repo work/L1/runs/<run_id>/reanchor/chNNNNN.jsonl + run.json
使い方: python scripts/reanchor_quotes.py [開始ch 終了ch]  ※ 途中再開対応（既存章ファイルスキップ）
"""
from __future__ import annotations

import json, re, sys, os, unicodedata, bisect, hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm_client import create_client, load_config, call_llm, parse_json_lenient

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT.parent / "AllusionistWiki_work"
RAW = ROOT.parent / "AllusionistWiki_raw/raw/novel"
KAK = RAW / "kakuyomu/16816927859268545348_幻想再帰のアリュージョニスト"
VAULT_RAW = ROOT / "raw"
QMAP_RUN = WORK / "work/L0/runs/20261017T2011_f863"
WINDOW = int(os.environ.get("REANCHOR_WINDOW", "60"))   # 補間位置の前後 ¶ 数
WORKERS = 8

def norm(s):
    s = re.sub(r"（空）|\(空\)|⏎", "", s)
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"[\s\u3000]+", "", s)

def sp_int(x):
    m = re.search(r"\d+", str(x))
    return int(m.group()) if m else 0

def kakuyomu_paras(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    body, idx, started = [], [], False
    for l in lines:
        if re.match(r"^【(kakuyomu ep|公開|章|URL|段落数|¶索引)", l.strip()):
            continue
        if l.strip().startswith("¶"):
            started = True
        (idx if started else body).append(l)
    index = {}
    for l in idx:
        m = re.match(r"^¶(\d+)\s*(.*)$", l.strip())
        if m:
            index[int(m.group(1))] = m.group(2)
    text_idx = [n for n in sorted(index)
                if index[n] not in ("⏎", "⏎⏎", "（空）")
                and not re.fullmatch(r"[⏎（空）]+", index[n])]
    out, k = [], 0
    for l in body:
        if l.strip() == "":
            continue
        n = text_idx[k]
        assert l.strip().startswith(index[n][:12]), f"{path.name} ¶{n}"
        out.append((n, l.strip()))
        k += 1
    return out

kak, kak_vol = {}, {}
for p in sorted(KAK.glob("*.md")):
    ch = int(re.match(r"ch(\d+)", p.name).group(1))
    kak[ch] = kakuyomu_paras(p)
    m = re.match(r"^(\d+)-\d+", re.match(r"ch\d+__(.+)\.md$", p.name).group(1))
    kak_vol[ch] = int(m.group(1)) if m else None
prev = 0
for ch in sorted(kak_vol):
    if kak_vol[ch] is None:
        kak_vol[ch] = prev
    prev = kak_vol[ch]

vol_corpus = {}   # v -> (text, pos[(start, kc, ¶N)], labeled[(start, kc, ¶N, text)], pos_index{(kc,¶N): offset})
for v in sorted(set(kak_vol.values())):
    text, pos, labeled = "", [], []
    for kc in sorted(c for c in kak if kak_vol[c] == v):
        for n, txt in kak[kc]:
            nt = norm(txt)
            if not nt:
                continue
            pos.append((len(text), kc, n))
            labeled.append((len(text), kc, n, txt))
            text += nt
    pos_index = {(kc, n): off for off, kc, n in pos}
    vol_corpus[v] = (text, pos, labeled, pos_index)

# グローバルモード（REANCHOR_GLOBAL=1）: 全巻連結コーパス + 記号除去ファストパス
GLOBAL = os.environ.get("REANCHOR_GLOBAL") == "1"
PUNCT_RE = re.compile(r"[「」『』（）()。、！？…〜ー−—―－・〈〉《》【】“”\"'｛｝{}\-–＿＊＃━─┼※＋\s]+")
def norm2(s):
    return PUNCT_RE.sub("", norm(s))
GLOBAL2 = None
if GLOBAL:
    T, POS, LAB = "", [], []
    T2, POS2 = "", []
    for vv in sorted(vol_corpus):
        for off, kc, n, txt in vol_corpus[vv][2]:
            nt = norm(txt)
            if not nt:
                continue
            POS.append((len(T), kc, n))
            LAB.append((len(T), kc, n, txt))
            T += nt
            nt2 = norm2(txt)
            if nt2:
                POS2.append((len(T2), kc, n))
                T2 += nt2
    vol_corpus[0] = (T, POS, LAB, {(kc, n): off for off, kc, n in POS})
    GLOBAL2 = (T2, POS2)

def locate(pos, start, length):
    ends = [p[0] for p in pos]
    i = bisect.bisect_right(ends, start) - 1
    j = bisect.bisect_right(ends, start + length - 1) - 1
    return pos[i][1], pos[i][2], pos[j][1], pos[j][2]

def sy_vol_map():
    vols = {}
    for p in sorted((RAW / "syosetu/n9073ca_幻想再帰のアリュージョニスト").glob("*.md")):
        ch = int(re.match(r"ch(\d+)_", p.name).group(1))
        m = re.search(r" - (\d+)-\d+", p.name)
        vols.setdefault(ch, int(m.group(1)) if m else None)
    prev = 0
    for ch in sorted(vols):
        if vols[ch] is None:
            vols[ch] = prev
        prev = vols[ch]
    return vols

SY_VOL = sy_vol_map()

def vault_context(ch, s_para, span=3):
    """なろう vault raw から対象 ¶ 周辺の原文を返す."""
    f = VAULT_RAW / f"ch{ch:04d}.txt"
    if not f.exists():
        return ""
    blocks = {}
    cur = None
    for l in f.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^【p(\d+)】$", l.strip())
        if m:
            cur = int(m.group(1)); blocks[cur] = []
        elif cur is not None and not re.match(r"^\d+$", l.strip()):
            blocks[cur].append(l.strip())
    out = []
    for n in sorted(blocks):
        if abs(n - s_para) <= span:
            out.append(f"p{n} " + "　".join(blocks[n]))
    return "\n".join(out)

def main():
    config = load_config()
    client = create_client(config)

    # キューとヒット読み込み（env REANCHOR_QUEUE で差し替えキュー = pass2 対応）
    qf = Path(os.environ.get("REANCHOR_QUEUE", QMAP_RUN / "needs-reanalysis.jsonl"))
    queue = []
    for l in qf.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        it = json.loads(l)
        if "ch" in it:  # 章集計行 (verify-failed/not-found 一覧) を queue 形式へ
            it = {"episode": it["ch"], "s_para": it["s_para"],
                  "quote_head": it["quote_head"], "type": it.get("type")}
        queue.append(it)
    hits = {}  # ch -> [(s_para, kc, ¶s, kc, ¶e)]
    for f in (QMAP_RUN / "quote-map").glob("*.jsonl"):
        ch = int(re.match(r"ch(\d+)", f.name).group(1))
        rows = []
        for l in f.read_text(encoding="utf-8").splitlines():
            r = json.loads(l)
            if r.get("k"):
                sp = sp_int(r["s_para"])
                rows.append((sp, *r["k"]))
        rows.sort()
        hits[ch] = rows

    now = datetime.now()

    by_ch = {}
    for item in queue:
        by_ch.setdefault(item["episode"], []).append(item)

    lo = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    hi = int(sys.argv[3]) if len(sys.argv) > 3 else 10**9

    # run_dir: 引数1 に既存 run_id を渡すと再開（同じディレクトリにブロック追記）
    if len(sys.argv) > 1 and sys.argv[1] and not sys.argv[1].isdigit():
        run_id = sys.argv[1]
        run_dir = WORK / "work/L1/runs" / run_id / "reanchor"
        run_dir.mkdir(parents=True, exist_ok=True)
    else:
        now = datetime.now()
        h = hashlib.sha1((str(now) + str(len(queue))).encode()).hexdigest()[:4]
        run_id = now.strftime("%Y%m%dT%H%M_") + h
        run_dir = WORK / "work/L1/runs" / run_id / "reanchor"
        run_dir.mkdir(parents=True, exist_ok=True)

    def interp_pos(ch, s_para):
        """ヒット群 (s_para -> corpus offset) を線形補間しコーパス絶対位置を返す."""
        v = 0 if GLOBAL else SY_VOL.get(ch)
        if v not in vol_corpus:
            return None
        pos_index = vol_corpus[v][3]
        pts = []
        for sp, kc, ps, kc2, pe in hits.get(ch, []):
            off = pos_index.get((kc, ps))
            if off is not None:
                pts.append((sp, off))
        pts.sort()
        if not pts:
            return None
        xs = [p[0] for p in pts]
        i = bisect.bisect_left(xs, s_para)
        if i == 0:
            return pts[0][1]
        if i >= len(pts):
            return pts[-1][1]
        a, b = pts[i - 1], pts[i]
        if b[0] == a[0]:
            return b[1]
        t = (s_para - a[0]) / (b[0] - a[0])
        return a[1] + t * (b[1] - a[1])

    def process_block(ch, b_idx, items):
        """16件ブロック: 並列単位・ファイル出力 (chNNNNN.bNN.jsonl)、既存はスキップ (再開)."""
        out_file = run_dir / f"ch{ch:05d}.b{b_idx:02d}.jsonl"
        if out_file.exists():
            return len(items), 0
        v = 0 if GLOBAL else SY_VOL.get(ch)
        if v not in vol_corpus:
            return 0, 0
        text, pos, labeled, _pidx = vol_corpus[v]
        results = []
        for item in items:
            s_para = sp_int(item["s_para"])
            # ファストパス: 記号除去で全巻一致 → LLM 不要で ¶ 確定
            rec = {"s_para": s_para, "quote_head": item["quote_head"], "type": item.get("type")}
            if GLOBAL2:
                nq2 = norm2(item["quote_head"])
                if len(nq2) >= 12:
                    i2 = GLOBAL2[0].find(nq2)
                    if i2 >= 0:
                        rec["status"] = "reanchored"
                        rec["k"] = list(locate(GLOBAL2[1], i2, len(nq2)))
                        rec["new_quote_head"] = item["quote_head"][:40]
                        rec["method"] = "punct"
                        results.append(rec)
                        continue
            center = interp_pos(ch, s_para)
            ctx = vault_context(ch, s_para)
            # 窓 ¶ 選択
            if center is None:
                lo_i, hi_i = 0, len(labeled)
            else:
                idx = bisect.bisect_left([p[0] for p in pos], int(center))
                lo_i, hi_i = max(0, idx - WINDOW), min(len(labeled), idx + WINDOW)
            window = "\n".join(f"[{kc}¶{n}] {txt}" for _, kc, n, txt in labeled[lo_i:hi_i])
            prompt = (
                "なろう版の引用（改変されてカクヨム版と全文一致しない）に相当する一節を、"
                "以下のカクヨム版テキストから特定してください。\n"
                "引用（なろう版・参考）: " + item["quote_head"] + "\n"
                "なろう版の周辺原文:\n" + ctx[:1500] + "\n"
                "カクヨム版テキスト（[ch¶N] 付き）:\n" + window[:12000] + "\n"
                "カクヨム版に存在しない/大きく書き換えられている場合は found:false。\n"
                'JSON のみ: {"found": true, "quote": "カクヨム版の原文そのまま1〜3文（改変禁止）"} '
                'または {"found": false, "note": "理由"}'
            )
            try:
                resp = call_llm(client, config, prompt, json_mode=True, max_tokens=600)
                obj = parse_json_lenient(resp, 0)
                if isinstance(obj, list):
                    obj = obj[0] if obj else {}
            except Exception as e:
                obj = {"found": False, "note": f"llm_error:{e}"}
            rec = {"s_para": s_para, "quote_head": item["quote_head"], "type": item.get("type")}
            q = norm(obj.get("quote", ""))
            if obj.get("found") and q:
                wtext = norm("".join(t for _, _, _, t in labeled[lo_i:hi_i]))
                i = wtext.find(q)
                if i >= 0:
                    off = labeled[lo_i][0]
                    rec["status"] = "reanchored"
                    rec["k"] = list(locate(pos, off + i, len(q)))
                    rec["new_quote_head"] = obj["quote"][:40]
                else:
                    i2 = text.find(q)
                    if i2 >= 0:
                        rec["status"] = "reanchored"
                        rec["k"] = list(locate(pos, i2, len(q)))
                        rec["new_quote_head"] = obj["quote"][:40]
                        rec["method"] = "full"
                    else:
                        rec["status"] = "verify_failed"
            else:
                rec["status"] = "not_found"
                rec["note"] = obj.get("note", "")[:80]
            results.append(rec)
        out_file.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in results) + "\n",
                            encoding="utf-8")
        return len(results), sum(1 for r in results if r["status"] == "reanchored")

    tasks = []
    for ch, items in sorted(by_ch.items()):
        if not (lo <= ch <= hi):
            continue
        if (run_dir / f"ch{ch:05d}.jsonl").exists():  # 旧章単位出力 = 完了扱い
            continue
        for b in range(0, (len(items) + 15) // 16):
            tasks.append((ch, b, items[b * 16:(b + 1) * 16]))
    total = done = ok = 0
    with ThreadPoolExecutor(WORKERS) as ex:
        futs = [ex.submit(process_block, ch, b, its) for ch, b, its in tasks]
        for fu in as_completed(futs):
            n, k = fu.result()
            done += n; ok += k; total += 1
            if total % 20 == 0:
                print(f"blocks {total}/{len(tasks)}, items {done}, reanchored {ok}", flush=True)

    (WORK / "work/L1/runs" / run_id / "run.json").write_text(json.dumps({
        "run_id": run_id, "layer": "L1", "kind": "reanchor",
        "created": now.isoformat(timespec="seconds"),
        "derived_from": {"l1_run": "20261012T0000_baseline", "l0_run": QMAP_RUN.name},
        "tool": "scripts/reanchor_quotes.py",
        "model": config["llm"]["model"],
        "stats": {"queue": len(queue), "processed": done, "reanchored": ok},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("run:", run_id, "| processed:", done, "| reanchored:", ok)

if __name__ == "__main__":
    main()
