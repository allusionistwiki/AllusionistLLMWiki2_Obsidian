#!/usr/bin/env python3
"""v6: per-episode reading with search/recall of related chapters + explicit reasoning.

For each main episode (kakuyomu chNNNN):
  Phase 1 検索: build recall context — paragraphs from related chapters
          (chapter ranges from the ledger evidence index AND prior resolved episodes)
          that mention the observed names. Deterministic retrieval, cited.
  Phase 2+3 思考→判定: the model must write per-decision reasoning citing the
          lines/recall used, then output strict JSON.
Appends one evidence record per episode (append-only). Deterministic aggregation
into ledger v5 happens later.
"""
import sys, json, re, time, glob, io
from pathlib import Path
from collections import defaultdict
import ahocorasick
sys.path.insert(0, str(Path(__file__).resolve().parent))
import llm_client
CFG = llm_client.load_config()
CLIENT = llm_client.create_client(CFG)

LEDGER = Path(sys.argv[1])
OUTDIR = Path(sys.argv[2])
KAKUYOMU = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_raw/raw/novel/kakuyomu/16816927859268545348_幻想再帰のアリュージョニスト")
EPISODES = sorted(KAKUYOMU.glob("*.md"))
MAX_TOKENS = 24000
TEMP = 0.7
MAX_RECALL_PARAS = 24
MAX_RECALL_CHS = 8

d = json.load(io.open(str(LEDGER), encoding="utf-8"))
name_to_canon = {}
for e in d["entities"]:
    c = e["canonical"]
    name_to_canon.setdefault(c, set()).add(c)
    for a in e.get("aliases", []):
        n = a["name"] if isinstance(a, dict) else a
        if n != c:
            name_to_canon.setdefault(n, set()).add(c)

A = ahocorasick.Automaton()
for n in name_to_canon:
    if len(n) >= 2:
        A.add_word(n, n)
A.make_automaton()

# static ledger evidence index: canonical -> set(chapters)
ch_idx = defaultdict(set)
for e in d["entities"]:
    for ev in e.get("evidence", []):
        ch = ev.get("chapter")
        if isinstance(ch, int):
            ch_idx[e["canonical"]].add(ch)

def file_for(ch_id):
    # ledger chapter ids are 5001.. mapped to files ch00001.. (offset 5000)
    idx = ch_id - 5000
    if idx < 1:
        return None
    g = glob.glob(str(KAKUYOMU / f"ch{idx:05d}__*.md"))
    return g[0] if g else None

def paragraphs_of(ch_id):
    f = file_for(ch_id)
    if not f:
        return None
    return f, io.open(f, encoding="utf-8").read().splitlines()

def build_recall(ep_ch, present_names):
    """Select related chapters per canon (excluding current) and extract name-mentioning paragraphs."""
    canons = set()
    for n in present_names:
        canons.update(name_to_canon.get(n, set()))
    # prioritize by frequency
    freq = {c: len(ch_idx.get(c, ())) for c in canons}
    ranked = sorted(canons, key=lambda c: -freq[c])[:12]
    chosen = {}  # (ch, canon) -> None
    for c in ranked:
        lst = []
        for ch in sorted(ch_idx.get(c, ())):
            if ch == ep_ch:
                continue
            lst.append(ch)
        chosen[c] = lst[:2]
    # flatten, cap chapters
    per_ch = defaultdict(list)
    for c, chs in chosen.items():
        for ch in chs:
            per_ch[ch].append(c)
    use_chs = sorted(per_ch.keys(), key=lambda ch: -len(per_ch[ch]))[:MAX_RECALL_CHS]
    out = []
    for ch in use_chs:
        got = paragraphs_of(ch)
        if not got:
            continue
        f, lines = got
        cnt = 0
        for i, line in enumerate(lines, 1):
            if len(line) < 6:
                continue
            hits = {n for _, n in A.iter(line)}
            rel = [c for c in per_ch[ch] if any(c in name_to_canon.get(n, ()) for n in hits)]
            if rel:
                out.append(f"ch{ch:05d} p{i} (related:{','.join(rel[:2])}): {line[:120]}")
                cnt += 1
                if cnt >= 3:
                    break
        if len(out) >= MAX_RECALL_PARAS:
            break
    return out

PROMPT = """あなたは長編小説の 1 話を読む解析者です。台帳の名義状態を扱い、統合・分離の根拠を厳密に記録する。

## 台帳: この話に出現しうる名義（抜粋）
{ledger_excerpt}

## 関連ch検索・想起（その登場人物の過去のchからの引用）
{recall}

## 読者: この話の全文（行番号付き）
{chapter}

課題:
1. この話に実際に登場する人物/存在/用語（名義）を列挙。
2. 同一性の明示（名乗り「私、Xです」・呼称宣言「AはBと呼ばれる」・「AはBである」）を全件。
3. 質感/個体の分離の証拠（同一人物だが別名義で語られる質感、AではなくB、同名の別人物、人称の分離）。
4. 語り手（俺）の指示対象が本文から特定できる場合、その根拠。
5. 上記判定に**使用した思考**を各項目の reason に書くこと。関連ch想起を使った場合はそのch番号と使った行を明記。使わなかった名義は空listでよい。

出力は JSON のみ（他テキスト勿論）。schema:
{"mentions":[{"name":"表層名義","role":"人物|語り手|比喩|一般語","group_hint":"同一人物系列ヒント"}],
"identity":[{"a":"名義A","b":"名義B","type":"explicit|strong","quote":"行引用","lines":["chNNNNN pN"],"reason":"使用した思考（1-2文）"}],
"separations":[{"a":"名義A","b":"名義B","reason":"分離の理由（1-2文）","lines":["chNNNNN pN"]}],
"narrator":{"refers_to":"特定できる場合のみ","quote":"引用","lines":["pN"]},
"recall_used":[使用した関連ch番号]}
"""

def chapter_text_with_lines(text, max_chars=14000):
    out = []
    total = 0
    for i, line in enumerate(text.splitlines(), 1):
        if len(line) < 2:
            continue
        s = f"p{i} {line}"
        total += len(s)
        if total > max_chars:
            break
        out.append(s)
    return "\n".join(out)

def ledger_excerpt(present_names, cap=40):
    lines = []
    rows = []
    for n in present_names:
        for c in name_to_canon.get(n, set()):
            rows.append((c, n, len(ch_idx.get(c, ())), sorted(ch_idx.get(c, ()))[-3:]))
    rows.sort(key=lambda r: -r[2])
    for c, n, k, last in rows[:cap]:
        lines.append(f"- canonical={c} alias={n} chapters={k} last={last}")
    return "\n".join(lines)

def main():
    max_eps = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    OUTDIR.mkdir(parents=True, exist_ok=True)
    rec_f = io.open(str(OUTDIR / "resolution-records.jsonl"), "a", encoding="utf-8")
    done = 0
    for md in EPISODES:
        m = re.match(r"ch(\d+)__", md.name)
        if not m:
            continue
        ep_id = int(m.group(1))
        ep_ledger = ep_id + 5000  # ledger chapter numbering offset
        out_path = OUTDIR / "episodes" / f"{ep_id}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if out_path.exists():
            continue
        text = md.read_text(encoding="utf-8", errors="replace")
        present = sorted({n for _, n in A.iter(text)})
        recall = build_recall(ep_ledger, present)
        excerpt = ledger_excerpt(present)
        ch_text = chapter_text_with_lines(text)
        prompt = (PROMPT.replace("{ledger_excerpt}", excerpt)
                  .replace("{recall}", "\n".join(recall) or "(関連chなし)")
                  .replace("{chapter}", ch_text))
        t0 = time.time()
        try:
            raw, reasoning = llm_client.call_llm_with_thinking(CLIENT, CFG, prompt, max_tokens=MAX_TOKENS, temperature=TEMP)
        except Exception as ex:
            print(f"ch{ep_id}: llm-fail {ex}")
            time.sleep(5)
            continue
        js = re.search(r"\{.*\}", raw, re.S)
        if not js:
            print(f"ch{ep_id}: no-json")
            continue
        try:
            obj = json.loads(js.group(0))
        except Exception as ex:
            print(f"ch{ep_id}: json-fail {ex}")
            continue
        rec = {"episode": ep_id, "file": md.name, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
               "present_names": present, "recall_chapters": recall and [r.split()[0] for r in recall],
               "thinking": reasoning, "analysis": obj}
        io.open(str(out_path), "w", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
        rec_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        rec_f.flush()
        done += 1
        print(f"ch{ep_id}: present={len(present)} recall={len(recall)} identity={len(obj.get('identity', []))} sep={len(obj.get('separations', []))} {time.time()-t0:.1f}s", flush=True)
        if done >= max_eps:
            break
    rec_f.close()
    print(f"done episodes={done}")

if __name__ == "__main__":
    main()
