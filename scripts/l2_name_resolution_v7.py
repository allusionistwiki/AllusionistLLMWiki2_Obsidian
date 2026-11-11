#!/usr/bin/env python3
"""v7: 検索エージェント（サブステップ）→ 深思考 → 判定。1 話ずつの逐次実読。

Pipeline per episode:
  Phase 1 検索（軽量 LLM・thinking OFF）: 台帳索引の候補章（スニペット付き）から、
          その登場人物Relatedの章を検索エージェントが選び、理由を記録する。
  Phase 2 想起抽出: 選ばれた章から名義出現段落を引用抽出（決定論）。
  Phase 3 深思考: thinking ON・大予算で熟読し、reason 付き判定 JSON を出力。
  Phase 4 記録: episodes/<id>.json（thinking 全文・search trace 含む）と
          episodes/<id>.thinking.md（思考の中身と長さを見られるように）。
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
MAX_TOKENS = int(__import__("os").environ.get("V7_MAX_TOKENS", "8000"))
SHARD = int(__import__("os").environ.get("V7_SHARD", "0"))
SHARDS = int(__import__("os").environ.get("V7_SHARDS", "1"))
TEMP = 0.7
SELECT_MAX = 10
MAX_RECALL_PARAS = 30

d = json.load(io.open(str(LEDGER), encoding="utf-8"))
MAIN_WORK = "幻想再帰のアリュージョニスト"
NAMEIDX_PATH = Path(__import__("os").environ.get("V7_NAMEIDX", ""))
NAMEIDX = {}
if NAMEIDX_PATH.exists():
    NAMEIDX = json.load(io.open(str(NAMEIDX_PATH), encoding="utf-8"))
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

ch_idx = defaultdict(set)
def norm_ch(s):
    # cites use "ch0038" (file index) and "ch5301" (ledger index) both; canonicalize to ledger
    m = re.match(r"ch0*(\d+)", str(s))
    if not m:
        return None
    v = int(m.group(1))
    return v + 5000 if v < 5000 else v
for e in d["entities"]:
    for a in e.get("aliases", []):
        for cite in (a.get("cites") or []) if isinstance(a, dict) else []:
            if isinstance(cite, list) and cite:
                ch = norm_ch(cite[0])
                if ch:
                    ch_idx[e["canonical"]].add(ch)
    fs = e.get("first_seen")
    if fs:
        ch = norm_ch(fs)
        if ch:
            ch_idx[e["canonical"]].add(ch)

def file_for(ch_id):
    idx = ch_id - 5000
    if idx < 1:
        return None
    g = glob.glob(str(KAKUYOMU / f"ch{idx:05d}__*.md"))
    return g[0] if g else None

def lines_of(ch_id):
    f = file_for(ch_id)
    if not f:
        return None
    return io.open(f, encoding="utf-8").read().splitlines()

def title_of(ch_id):
    f = file_for(ch_id)
    return Path(f).name.split("__", 1)[-1] if f else ""

def chapters_for_name(name):
    # ground-truth per-name chapters (main work), + ledger cites as fallback
    out = set()
    w = NAMEIDX.get(name, {}).get(MAIN_WORK, {})
    for ch_str in w:
        v = int(ch_str)
        out.add(v + 5000 if v < 5000 else v)
    for c in name_to_canon.get(name, ()):
        out.update(ch_idx.get(c, ()))
    return out

def build_candidates(ep_ledger, present_names):
    cands = []
    seen = set()
    scored = []
    for n in present_names:
        chs = chapters_for_name(n)
        if chs:
            scored.append((len(chs), n, sorted(chs)))
    scored.sort(key=lambda x: -x[0])
    for _, n, chs in scored[:14]:
        target = [ch for ch in chs if ch != ep_ledger][:3]
        for ch in target:
            if ch in seen:
                continue
            seen.add(ch)
            ls = lines_of(ch)
            snip = ""
            for line in ls or []:
                if len(line) >= 6:
                    hits = {nn for _, nn in A.iter(line)}
                    if n in hits:
                        snip = line[:100]
                        break
            cands.append({"ch": ch, "title": title_of(ch), "for": n, "snippet": snip})
            if len(cands) >= 40:
                return cands
    return cands

SEARCH_PROMPT = """あなたは逐次実読の検索担当（検索エージェント）です。今から読む話のために、登場人物の過去記述を持つ関連chを選んでください。

## 今読む話: ch{ep}（{title}）
## 観測名義（抜粋）: {names}
## 候補ch（名義索引由来・スニペット付き）:
{cands}

基準: この話の人物の初出・名乗り・同一性宣言・同名別人の区別に効く章を優先。
10件まで。読み順は古いchから。理由は1短文で。
出力 JSON のみ:
{{"chosen":[{{"ch":5001,"why":"..."}},...]}}
"""

def search_select(ep_ledger, present_names, cands):
    if not cands:
        return []
    prompt = (SEARCH_PROMPT.replace("{ep}", str(ep_ledger))
              .replace("{title}", title_of(ep_ledger))
              .replace("{names}", ",".join(present_names[:30]))
              .replace("{cands}", "\n".join(f"- ch{c['ch']} {c['title']} (for {c['for']}): {c['snippet'][:80]}" for c in cands)))
    try:
        raw = llm_client.call_llm(CLIENT, CFG, prompt, max_tokens=700, temperature=0.3)
    except Exception as ex:
        print(f"  search-fail {ex}")
        return [{"ch": c["ch"], "why": "fallback-deterministic"} for c in cands[:SELECT_MAX]]
    js = re.search(r"\{.*\}", raw, re.S)
    if not js:
        return [{"ch": c["ch"], "why": "fallback-deterministic"} for c in cands[:SELECT_MAX]]
    try:
        obj = json.loads(js.group(0))
        chosen = [c for c in obj.get("chosen", []) if isinstance(c.get("ch"), int)][:SELECT_MAX]
        return chosen if chosen else [{"ch": c["ch"], "why": "fallback-deterministic"} for c in cands[:SELECT_MAX]]
    except Exception:
        return [{"ch": c["ch"], "why": "fallback-deterministic"} for c in cands[:SELECT_MAX]]

def build_recall(chosen, present_names):
    out = []
    for item in chosen:
        ch = item["ch"]
        ls = lines_of(ch)
        if not ls:
            continue
        cnt = 0
        for i, line in enumerate(ls, 1):
            if len(line) < 6:
                continue
            hits = {n for _, n in A.iter(line)}
            if hits & set(present_names):
                out.append(f"ch{ch} p{i}: {line[:120]}")
                cnt += 1
                if cnt >= 4:
                    break
        if len(out) >= MAX_RECALL_PARAS:
            break
    return out

PROMPT = """あなたは長編小説の 1 話を読む解析者です。検索エージェントが選んだ関連chの引用を踏まえ、熟読して統合・分離の判定と根拠を記録してください。

## 台帳: この話に出現しうる名義（抜粋）
{ledger_excerpt}

## 関連ch想起（検索エージェント選択済み・引用）
{recall}

## 読者: この話の全文（行番号付き）
{chapter}

課題:
1. 実際に登場する名義を列挙。
2. 同一性の明示を全件。type=explicit は次のパターン**のみ**: (a) 名乗り「私/俺はX」「名前はX」 (b) 呼称宣言「AはBと呼ばれる/呼ぶ」 (c) 括弧同格「A（B）」 (d) 「すなわち/つまりA」。照応・言い換え・比喩的同一・状況的同一は type=strong とし、自信があっても explicit にしない。
3. 質感/個体の分離証拠（AではなくB、同名の別人物、人称分離）を理由付きで。
4. 語り手（俺）の指示対象が特定できる場合のみ根拠付きで。
5. quote は原文からの**逐語引用**（原文に無い要約引用は禁止、原文の行をそのまま抄）。関連ch想起を使った判定では lines にその ch 番号と行を明記。

出力は JSON のみ。schema は**フィールド 6 個まで・配列 items は次の文字列入力のみ**（これ以外のフィールド・オブジェクト item は禁止）:
{"fields":[
 "M|表層名義|role(人物|語り手|比喩|一般語)",
 "I|a|b|type(explicit|strong)|逐語引用|使用ch|思考1文",
 "S|a|b|分離理由1文|使用ch",
 "N|語り手が指す人物|逐語引用|使用p行",
 "R|使用した関連ch番号"
]}
"""

def chapter_text_with_lines(text, max_chars=14000):
    out, total = [], 0
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
    rows = []
    for n in present_names:
        for c in name_to_canon.get(n, set()):
            rows.append((c, n, len(ch_idx.get(c, ())), sorted(ch_idx.get(c, ()))[-3:]))
    rows.sort(key=lambda r: -r[2])
    return "\n".join(f"- canonical={c} alias={n} chapters={k} last={last}" for c, n, k, last in rows[:cap])

def parse_fields(obj):
    """Convert the compact 6-field schema into the internal analysis dict."""
    out = {"mentions": [], "identity": [], "separations": [], "narrator": {}, "recall_used": []}
    fields = obj.get("fields")
    if not isinstance(fields, list):
        return None
    for f in fields:
        if not isinstance(f, str):
            continue
        parts = [p.strip() for p in f.split("|")]
        tag = parts[0]
        rest = parts[1:]
        if tag == "M" and len(rest) >= 2:
            out["mentions"].append({"name": rest[0], "role": rest[1]})
        elif tag == "I" and len(rest) >= 5:
            out["identity"].append({"a": rest[0], "b": rest[1], "type": rest[2], "quote": rest[3], "lines": [rest[4]], "reason": rest[5]})
        elif tag == "S" and len(rest) >= 4:
            out["separations"].append({"a": rest[0], "b": rest[1], "reason": rest[2], "lines": [rest[3]]})
        elif tag == "N" and len(rest) >= 3:
            out["narrator"] = {"refers_to": rest[0], "quote": rest[1], "lines": [rest[2]]}
        elif tag == "R" and rest:
            for tok in rest[0].replace(",", " ").split():
                try:
                    out["recall_used"].append(int(tok))
                except ValueError:
                    pass
    if not (out["mentions"] or out["identity"] or out["separations"]):
        return None
    return out


def main():
    max_eps = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    OUTDIR.mkdir(parents=True, exist_ok=True)
    (OUTDIR / "episodes").mkdir(exist_ok=True)
    rec_f = io.open(str(OUTDIR / "resolution-records.jsonl"), "a", encoding="utf-8")
    done = 0
    for md in EPISODES:
        m = re.match(r"ch(\d+)__", md.name)
        if not m:
            continue
        ep_id = int(m.group(1))
        if SHARDS > 1 and ep_id % SHARDS != SHARD:
            continue
        ep_ledger = ep_id + 5000
        out_path = OUTDIR / "episodes" / f"{ep_id}.json"
        if out_path.exists():
            try:
                prev = json.load(io.open(str(out_path), encoding="utf-8"))
                if prev.get("pending_retry"):
                    pass  # reprocess this episode
                else:
                    continue
            except Exception:
                continue
        t0 = time.time()
        text = md.read_text(encoding="utf-8", errors="replace")
        present = sorted({n for _, n in A.iter(text)})
        cands = build_candidates(ep_ledger, present)
        t_search = time.time()
        chosen = search_select(ep_ledger, present, cands)
        search_secs = time.time() - t_search
        recall = build_recall(chosen, present)
        excerpt = ledger_excerpt(present)
        ch_text = chapter_text_with_lines(text)
        prompt = (PROMPT.replace("{ledger_excerpt}", excerpt)
                  .replace("{recall}", "\n".join(recall) or "(関連chなし)")
                  .replace("{chapter}", ch_text))
        t_think = time.time()
        try:
            raw, reasoning = llm_client.call_llm_with_thinking(CLIENT, CFG, prompt, max_tokens=MAX_TOKENS, temperature=TEMP, json_mode=False)
        except Exception as ex:
            print(f"ch{ep_id}: llm-fail {ex}")
            time.sleep(5)
            continue
        think_secs = time.time() - t_think
        js = re.search(r"\{.*\}", raw, re.S)
        if not js:
            print(f"ch{ep_id}: no-json thinking={len(reasoning)}c -> retry next pass")
            io.open(str(OUTDIR / "episodes" / f"{ep_id}.thinking.md"), "w", encoding="utf-8").write(reasoning)
            io.open(str(OUTDIR / "episodes" / f"{ep_id}.json"), "w", encoding="utf-8").write(json.dumps({"episode": ep_id, "analysis": {"mentions": [], "identity": [], "separations": []}, "pending_retry": True}, ensure_ascii=False) + "\n")
            continue
        try:
            obj = json.loads(js.group(0))
        except Exception as ex:
            try:
                obj = llm_client.parse_json_lenient(js.group(0), 0)
                if isinstance(obj, list):
                    obj = obj[0] if obj and isinstance(obj[0], dict) else {}
                if not isinstance(obj, dict):
                    raise ValueError("lenient-not-dict")
                print(f"ch{ep_id}: lenient-parse-ok")
            except Exception as ex2:
                print(f"ch{ep_id}: json-fail {ex} / lenient {ex2} thinking={len(reasoning)}c")
                io.open(str(OUTDIR / "episodes" / f"{ep_id}.thinking.md"), "w", encoding="utf-8").write(reasoning + "\n\n=== RAW ===\n" + raw)
                continue
        obj = parse_fields(obj)
        if obj is None:
            print(f"ch{ep_id}: schema-empty thinking={len(reasoning)}c")
            io.open(str(OUTDIR / "episodes" / f"{ep_id}.thinking.md"), "w", encoding="utf-8").write(reasoning + "\n\n=== RAW ===\n" + raw)
            continue
        rec = {"episode": ep_id, "file": md.name, "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
               "present_names": present, "search_trace": chosen,
               "recall_paras": recall, "thinking_len_chars": len(reasoning),
               "thinking": reasoning, "analysis": obj}
        io.open(str(out_path), "w", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
        io.open(str(OUTDIR / "episodes" / f"{ep_id}.thinking.md"), "w", encoding="utf-8").write(reasoning)
        rec_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        rec_f.flush()
        done += 1
        print(f"ch{ep_id}: present={len(present)} chosen={len(chosen)} recall={len(recall)} identity={len(obj.get('identity', []))} sep={len(obj.get('separations', []))} thinking={len(reasoning)}c search={search_secs:.0f}s think={think_secs:.0f}s total={time.time()-t0:.0f}s", flush=True)
        if done >= max_eps:
            break
    rec_f.close()
    print(f"done episodes={done}")

if __name__ == "__main__":
    main()
