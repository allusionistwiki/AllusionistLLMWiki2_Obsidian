#!/usr/bin/env python3
"""v5 aggregation: episode reading records (v7 run) -> ledger v5 + work pages.

Deterministic pipeline (the LLM only produced evidence; decisions are here):
 1. quote verify  : 逐語引用を原文 part 照合（照合不能は strong へ降格）
 2. explicit gate : explicit は名乗り/呼称宣言/括弧同格/すなわち パターン一致のみ
 3. merge rule    : alias→canonical 統合は (a) verified explicit 証拠 (b) alias の全出現章が読了 の両方でのみ適用
 4. separations   : 分離証拠で既存 applied pair を降格、同一名分離は人物群 __S として記録
 5. pages         : pages/chapters/<ch>.md（統合根拠ページ）と pages/entities/<id>.md（判定履歴）を生成
Outputs: run dir with entities.json, decision-log.jsonl, pages/, run.json.
"""
import sys, json, re, io, time, glob
from pathlib import Path
from collections import defaultdict, Counter

LEDGER = Path(sys.argv[1])           # v4 entities.json
EPIDIR = Path(sys.argv[2])           # episodes/*.json (v7 run)
NAMEIDX = Path(sys.argv[3])          # name->ch ground truth
OUT = Path(sys.argv[4])              # run out dir
PAGES = Path(sys.argv[5])            # work/allusionist_v2/L2/pages
KAKUYOMU = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_raw/raw/novel/kakuyomu/16816927859268545348_幻想再帰のアリュージョニスト")
MAIN_WORK = "幻想再帰のアリュージョニスト"

EXPLICIT_PAT = re.compile(
    r"(私[はも].{0,4}です|俺[はも].{0,4}です|名前は|名乗(?:り|る)|と呼ばれる|と呼ぶ|と呼んで|すなわち|つまり|[\(（][^\)）]{1,20}[\)）]|である|ということだ)")

def norm(s):
    return re.sub(r"[\s\u3000]+", "", s or "")

def load_text(ep_id):
    g = glob.glob(str(KAKUYOMU / f"ch{ep_id:05d}__*.md"))
    if not g:
        return ""
    return io.open(g[0], encoding="utf-8").read()

def verify_quote(q, text):
    q = norm(q)
    if len(q) < 6:
        return False
    if q[:40] in norm(text):
        return True
    # part-level: split on ellipsis/punctuation connectors, require each part present
    parts = [p for p in re.split(r"[…\.]{2,}|→|※", q) if len(p) >= 6]
    if len(parts) >= 2:
        t = norm(text)
        return all(p[:25] in t for p in parts)
    return False

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "episodes").mkdir(exist_ok=True)
    PAGES.mkdir(parents=True, exist_ok=True)
    (PAGES / "chapters").mkdir(exist_ok=True)
    (PAGES / "entities").mkdir(exist_ok=True)

    ledger = json.load(io.open(str(LEDGER), encoding="utf-8"))
    nameidx = json.load(io.open(str(NAMEIDX), encoding="utf-8"))
    episodes = {}
    for p in sorted(EPIDIR.glob("*.json")):
        r = json.load(io.open(p, encoding="utf-8"))
        if r.get("pending_retry"):
            continue
        episodes[int(r["episode"])] = r
    read_eps = set(episodes.keys())
    print("episodes:", len(episodes))

    # name -> chapters (main work)
    def chs_of(name):
        w = nameidx.get(name, {}).get(MAIN_WORK, {})
        return {int(c) for c in w}

    # index entities by canonical & alias
    by_canon = {e["canonical"]: e for e in ledger["entities"]}
    alias_owner = defaultdict(set)
    for e in ledger["entities"]:
        c = e["canonical"]
        for a in e.get("aliases", []):
            n = a["name"] if isinstance(a, dict) else a
            if n != c:
                alias_owner[n].add(c)

    stats = Counter()
    decisions = []
    merge_edges = defaultdict(list)      # alias -> [(canon, ep, quote, verified, pattern)]
    sep_edges = defaultdict(list)        # (a,b) -> [ep, reason]
    same_name = defaultdict(list)        # name -> [ep, lines]
    narrator_notes = {}

    for ep, r in sorted(episodes.items()):
        text = load_text(ep)
        a = r.get("analysis") or {}
        for it in a.get("identity", []):
            na, nb = it.get("a", ""), it.get("b", "")
            q = it.get("quote", "")
            ok = verify_quote(q, text)
            typ = it.get("type", "strong")
            pat = bool(EXPLICIT_PAT.search(norm(q)))
            if typ == "explicit" and not (ok and pat):
                typ = "strong"
                stats["explicit_downgraded"] += 1
            target = None
            for cand in (nb, na):
                if cand in by_canon:
                    target = cand
                    break
            if target is None:
                for cand in (nb, na):
                    if cand in alias_owner:
                        target = sorted(alias_owner[cand])[0]
                        break
            alias = na if target == nb else (nb if target == na else None)
            decisions.append({"ep": ep, "kind": "identity", "a": na, "b": nb, "type": typ,
                              "verified": ok, "pattern": pat, "quote": q[:160],
                              "lines": it.get("lines", []), "reason": (it.get("reason") or "")[:200]})
            if typ == "explicit" and alias and target:
                merge_edges[alias].append({"to": target, "ep": ep, "quote": q[:160], "verified": ok})
                stats["explicit_edges"] += 1
        for s in a.get("separations", []):
            na, nb = s.get("a", ""), s.get("b", "")
            decisions.append({"ep": ep, "kind": "separation", "a": na, "b": nb,
                              "lines": s.get("lines", []), "reason": (s.get("reason") or "")[:200]})
            sep_edges[(na, nb)].append({"ep": ep, "reason": (s.get("reason") or "")[:200]})
            stats["separations"] += 1
            if na and na == nb:
                same_name[na].append({"ep": ep, "lines": s.get("lines", [])})
        n = a.get("narrator") or {}
        if n.get("refers_to"):
            narrator_notes[ep] = {"refers_to": n["refers_to"], "quote": (n.get("quote") or "")[:200],
                                  "lines": n.get("lines", [])}

    # apply merges: verified explicit + all-alias-chapters read
    demotions, promotions, applied = [], [], []
    for alias, edges in merge_edges.items():
        ac = chs_of(alias)
        unread = ac - read_eps
        good = [e for e in edges if e["verified"]]
        if not good:
            stats["merge_rejected_unverified"] += 1
            continue
        if unread:
            stats["merge_deferred_unread"] += 1
            stats["deferred_unread_ch"] += len(unread)
            continue
        # majority target
        tc = Counter(e["to"] for e in good)
        target = tc.most_common(1)[0][0]
        applied.append({"alias": alias, "to": target, "evidence": good[:5], "chapters": sorted(ac)})
        stats["merges_applied"] += 1

    # separations demote existing applied pairs
    HIGH = {"高", "明言", "表記一致", "蓋然性高"}
    dem = 0
    for (na, nb), ev in sep_edges.items():
        for e in ledger["entities"]:
            c = e["canonical"]
            for al in e.get("aliases", []):
                if not isinstance(al, dict):
                    continue
                n = al["name"]
                pair = {na, nb}
                if n in pair and c in pair and al.get("confidence") in HIGH:
                    al["confidence"] = "要検証"
                    al["reason"] = (al.get("reason", "") + f" [v5 分離証拠 ch{ev[0]['ep']}: {ev[0]['reason'][:100]}]")
                    dem += 1
                    demotions.append({"alias": n, "from": c, "ep": ev[0]["ep"]})
    stats["ledger_demotions"] = dem

    # apply merges into ledger
    for m in applied:
        target = by_canon.get(m["to"])
        if not target:
            continue
        existing = {a["name"] for a in target.get("aliases", []) if isinstance(a, dict)}
        if m["alias"] in existing:
            for a in target["aliases"]:
                if isinstance(a, dict) and a["name"] == m["alias"] and a.get("confidence") not in HIGH:
                    a["confidence"] = "明言"
                    a["source"] = "v5-逐次実読"
                    a["reason"] = " ".join(e["quote"][:80] for e in m["evidence"][:2])
            continue
        target.setdefault("aliases", []).append({
            "name": m["alias"], "confidence": "明言", "source": "v5-逐次実読",
            "reason": " ".join(e["quote"][:80] for e in m["evidence"][:2]),
            "cites": [[f"ch{e['ep']:05d}", 0] for e in m["evidence"][:5]], "verify": []})
        promotions.append({"alias": m["alias"], "to": m["to"]})

    # identity_links for strong (verified) pairs -> store as correlation notes, not merges
    strong_links = []
    seen = set()
    for d in decisions:
        if d["kind"] == "identity" and d["type"] == "strong" and d["verified"]:
            key = tuple(sorted([d["a"], d["b"]]))
            if key in seen:
                continue
            seen.add(key)
            strong_links.append({"pair": list(key), "ep": d["ep"], "quote": d["quote"][:120], "reason": d["reason"][:120]})

    # write decision log
    with io.open(str(OUT / "decision-log.jsonl"), "w", encoding="utf-8") as f:
        for d in decisions:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    # same-name collision records
    with io.open(str(OUT / "same-name-collisions.json"), "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in same_name.items()}, f, ensure_ascii=False, indent=1)
    with io.open(str(OUT / "narrator-notes.json"), "w", encoding="utf-8") as f:
        json.dump(narrator_notes, f, ensure_ascii=False, indent=1)
    with io.open(str(OUT / "identity-links-strong.json"), "w", encoding="utf-8") as f:
        json.dump(strong_links, f, ensure_ascii=False, indent=1)

    # ledger v5
    ledger["schema"] = 5
    ledger["run"] = OUT.name
    with io.open(str(OUT / "entities.json"), "w", encoding="utf-8") as f:
        json.dump(ledger, f, ensure_ascii=False, indent=1)

    # pages: chapters
    dec_by_ep = defaultdict(list)
    for d in decisions:
        dec_by_ep[d["ep"]].append(d)
    for ep, r in sorted(episodes.items()):
        rows = dec_by_ep.get(ep, [])
        st = io.StringIO()
        st.write(f"# ch{ep:05d} 統合記録ページ\n\n")
        t = load_text(ep)
        title = r.get("file", "").split("__", 1)[-1]
        st.write(f"対象: {title}\n\n## 検索（関連ch想起）\n\n")
        for c in r.get("search_trace", []):
            st.write(f"- ch{c.get('ch')} — {c.get('why','')}\n")
        st.write("\n## 想起された引用\n\n")
        for q in r.get("recall_paras", []):
            st.write(f"- {q}\n")
        st.write("\n## 判定と使用した情報\n\n")
        for d in rows:
            if d["kind"] == "identity":
                st.write(f"- [identity/{d['type']}{'・検証済' if d['verified'] else '・未検証'}] {d['a']} ↔ {d['b']}: 「{d['quote']}」 行:{','.join(d['lines'])} — {d['reason']}\n")
            else:
                st.write(f"- [separation] {d['a']} / {d['b']}: {d['reason']} 行:{','.join(d['lines'])}\n")
        n = narrator_notes.get(ep)
        if n:
            st.write(f"\n## 語り手\n\n- 指示対象: {n['refers_to']}（行 {','.join(str(x) for x in n['lines'])}）: 「{n['quote']}」\n")
        st.write("\n## 思考（全文）\n\n")
        st.write((r.get("thinking") or "")[:20000])
        io.open(str(PAGES / "chapters" / f"ch{ep:05d}.md"), "w", encoding="utf-8").write(st.getvalue())

    # pages: entities (decision history per canonical)
    by_entity = defaultdict(list)
    for d in decisions:
        for nm in (d["a"], d["b"]):
            if nm in by_canon:
                by_entity[nm].append(d)
    for canon, ds in by_entity.items():
        safe = re.sub(r'[<>:"/\\|?*]', "_", canon)
        io.open(str(PAGES / "entities" / f"{safe}.md"), "w", encoding="utf-8").write(
            "\n".join(f"- ch{d['ep']:05d} [{d['kind']}/{d.get('type','')}] {d['a']} ↔ {d['b']}: {d.get('reason','')[:150]}" for d in ds[:200]))

    # run.json
    run = {"kind": "name-integration-v5", "run_id": OUT.name,
           "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
           "derived_from": [ledger.get("run"), "20261108T2140_v7read"],
           "strategy": "STRATEGY-resolution-v5.md + STRUCTURE-proposal-v0.2.md",
           "stats": dict(stats),
           "notes": "merges: verified explicit + all-chapters-read; separations demote applied pairs; strong links kept as identity-links (not merged)"}
    io.open(str(OUT / "run.json"), "w", encoding="utf-8").write(json.dumps(run, ensure_ascii=False, indent=1) + "\n")

    # update latest + runs-index
    l2root = PAGES.parent
    io.open(str(l2root / "latest.txt"), "w", encoding="utf-8").write(OUT.name + "\n")
    ipath = l2root.parent / "index" / "runs-index.json"
    idx = json.load(io.open(str(ipath), encoding="utf-8"))
    idx.setdefault("L2", {})[OUT.name] = {"path": f"work/allusionist_v2/L2/runs/{OUT.name}",
        "status": "active", "kind": "name-integration-v5",
        "derived_from": [ledger.get("run"), "20261108T2140_v7read"], "stats": dict(stats)}
    io.open(str(ipath), "w", encoding="utf-8").write(json.dumps(idx, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(dict(stats), ensure_ascii=False))
    print("applied merges:", len(applied), "demotions:", dem, "pages:", len(episodes))

if __name__ == "__main__":
    main()
