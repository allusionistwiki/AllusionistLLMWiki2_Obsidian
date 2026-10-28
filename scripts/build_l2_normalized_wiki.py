"""S7 段: L1 wiki 全体へ L2 台帳の名前統合・正規化処理を適用し、正規化 wiki 構造を vault wiki/l2/ 直下へ生成（L2 ⇒ 各要素、normalized 索引は一要素）。

設計:
- 台帳 (work L2 run entities.json) が生成規則。aliases[].name → canonical を
  高確度帯 {高, 明言, 表記一致, 蓋然性高} のみ置換（要検証/needs は注記のみ・置換しない）。
- L1 全ページを wiki/l2/normalized/ に同一相対パスでミラー。
- 本文の別名文字列を代表名へ置換し、置換監査節（元名義→代表名・確度・件数）をページ末尾に追記。
- 相対 wikilink は正規化ツリー内の相対パスへ書き換え（層内自己完結）。
- 自身のタイトルが別名登録のページには統合先へのバナー。
- 台帳ページ（index/correlations/aliases-index）はそのまま残る（台帳は一要素）。

Usage: python scripts/build_l2_normalized_wiki.py <ledger_run_id> [--limit N]
"""
import json
import re
import sys
import hashlib
import datetime
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WIKI_L1 = ROOT / "wiki" / "l1"
OUT = ROOT / "wiki" / "l2"
LEDGER = Path("C:/Users/d5dx/Downloads/Code/AllusionistWiki_work")

HIGH = {"高", "明言", "表記一致", "蓋然性高"}


def fm_split(text):
    m = re.match(r"^---\n(.*?\n)---\n", text, re.S)
    if m:
        return m.group(1), text[m.end():]
    return "", text


def fm_get(fm: str, key: str):
    m = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
    return m.group(1).strip().strip("'\"") if m else None


def main():
    run_id = sys.argv[1]
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    led_path = LEDGER / f"work/allusionist_v2/L2/runs/{run_id}/entities.json"
    doc = json.load(open(led_path, encoding="utf-8"))
    entities = doc["entities"]

    alias_map = {}  # alias -> (canonical, confidence, entity_id)
    low_map = {}    # 要検証系: alias -> (canonical, confidence)（注記のみ）
    conflicts = []
    for e in entities:
        canon, eid = e["canonical"], e["id"]
        for a in e.get("aliases", []):
            if isinstance(a, str):
                n, c = a, ""  # v2 互換: 確度なし → 注記のみ帯域
            else:
                n, c = a.get("name"), a.get("confidence", "")
            if not n or n == canon:
                continue
            tgt = (canon, c, eid)
            prev = alias_map.get(n)
            if prev and prev[0] != canon:
                conflicts.append(n)
                continue
            if c in HIGH:
                alias_map[n] = tgt
                low_map.pop(n, None)
            else:
                if n not in alias_map and n not in low_map:
                    low_map[n] = (canon, c)

    print(f"ledger: entities={len(entities)} replace-aliases={len(alias_map)} annotate-only={len(low_map)} conflicts={len(set(conflicts))}")

    # scan L1 pages: id/title -> relative path
    pages = sorted(p for p in WIKI_L1.rglob("*.md"))
    if limit:
        pages = pages[:limit]
    title_to_rel = {}
    fm_cache = {}
    for p in pages:
        rel = p.relative_to(WIKI_L1).as_posix()
        text = p.read_text(encoding="utf-8")
        fm, body = fm_split(text)
        fm_cache[rel] = (fm, body)
        t = fm_get(fm, "title")
        if t and t not in title_to_rel:
            title_to_rel[t] = rel

    # wikilink relative-path resolution map (basename -> rel path)
    base_rel = {}
    dup_base = set()
    for rel in fm_cache:
        b = Path(rel).stem
        if b in base_rel:
            dup_base.add(b)
        else:
            base_rel[b] = rel

    pat = re.compile("|".join(re.escape(n) for n in sorted(alias_map, key=len, reverse=True))) if alias_map else None

    OUT.mkdir(parents=True, exist_ok=True)
    stats = Counter()
    page_changes = {}

    def rewrite_links(body, base_of_page):
        def link_repl(m):
            inner = m.group(1)
            target, _, disp = inner.partition("|")
            target = target.strip()
            disp = disp.strip()
            t = target.split("#")[0].strip()
            if t.endswith(".md"):
                new_target = t  # explicit path: mirror as-is
            else:
                new_target = target  # basename 参照は L1 と同一（lint 解決形を変えない）
            return f"[[{new_target}|{disp}]]" if disp else f"[[{new_target}]]"
        return re.sub(r"\[\[([^\[\]]+)\]\]", link_repl, body)

    for rel, (fm, body) in fm_cache.items():
        counts = Counter()
        if pat:
            def repl(m):
                n = m.group(0)
                counts[n] += 1
                return alias_map[n][0]
            body = rewrite_links(body, rel)
            # wikilink のターゲットは置換しない（ターゲット＝ページ id を壊すと
            # lint/Quartz 双方で死リンクになる）。通常テキストと表示文本のみ置換。
            parts = re.split(r"(\[\[[^\[\]]+\]\])", body)
            for i, seg in enumerate(parts):
                if seg.startswith("[["):
                    inner = seg[2:-2]
                    target, _, disp = inner.partition("|")
                    if disp:
                        parts[i] = "[[" + target + "|" + pat.sub(repl, disp) + "]]"
                    # target は無変換
                else:
                    parts[i] = pat.sub(repl, seg)
            body = "".join(parts)
        else:
            body = rewrite_links(body, rel)

        title = fm_get(fm, "title") or Path(rel).stem
        banner = ""
        if title in alias_map:
            canon, conf, eid = alias_map[title]
            # 統合先はページ id（stem）形リンク＋代表名表示。lint の LinkIndex・
            # Quartz 双方で解決できる形（代表名そのものは id として存在しない）。
            canon_rel = title_to_rel.get(canon)
            canon_link = Path(canon_rel).stem if canon_rel else None
            target_md = f"[[{canon_link}|{canon}]]" if canon_link else f"**{canon}**"
            banner = f"\n> [!info] 名前統合（L2 run {run_id}）\n> このページの名義「{title}」は **{canon}** の別名として統合済み（確度: {conf}）。正規化先: {target_md}\n"
        annotations = []
        for n, (canon, conf) in low_map.items():
            if n in body:
                annotations.append(f"- 未置換（要検証）: 「{n}」→ {canon}（{conf}）")
        audit = ""
        if counts or annotations:
            rows = "".join(
                f"| {n} | {alias_map[n][0]} | {alias_map[n][1]} | {c} |\n"
                for n, c in counts.most_common()
            )
            audit = f"\n\n---\n\n## 名前正規化監査（L2 run {run_id}）\n\n| 元名義 | 代表名 | 確度 | 置換件数 |\n|---|---|---|---|\n{rows}"
            if annotations:
                audit += "\n\n注記（置換しない）:\n" + "\n".join(annotations)
        new_fm = fm + f"normalized_from: l1/{rel}\nl2_run: {run_id}\n"
        out_path = OUT / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        if fm:
            out_path.write_text(f"---\n{new_fm}---\n{banner}{body}{audit}", encoding="utf-8")
        else:
            # L1 元が frontmatter なしなら frontmatter を作らない（lint の
            # frontmatter 前提チェックが空ブロックで発火するのを防ぐ）
            out_path.write_text(f"{banner}{body}{audit}", encoding="utf-8")
        if counts:
            page_changes[rel] = sum(counts.values())
            stats["pages_with_replacements"] += 1
            stats["total_replacements"] += sum(counts.values())
        stats["pages_written"] += 1

    print(json.dumps({k: stats[k] for k in stats}, ensure_ascii=False))
    top = sorted(page_changes.items(), key=lambda kv: -kv[1])[:10]
    print("top pages by replacements:", top)
    print(f"written to: {OUT}")


if __name__ == "__main__":
    main()
