#!/usr/bin/env python3
"""キャラクター関係性マップ生成（Mermaid グラフ、決定論的）.

- イベント層の (subject, predicate, object) 三つ組からキャラ間関係を抽出
  （entity_type=relationship の観測 + subject/object が両方キャラ名のイベント）
- 関係の重み = 観測回数。上位 N エッジのみ描画（見やすさ）
- 出力: wiki/relationships/index.md（Mermaid グラフ + 関係一覧リンク）
- キャラ入口（characters/index.md）とトップページからリンク
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT.parent / "AllusionistLLMWiki2_Work"
EVENTS = WORK / "events"
WIKI = ROOT / "wiki"

PRED_JA = {
    "analogous_to": "類似", "alludes_to": "暗喩", "parodies": "パロディ",
    "inverts": "逆転", "references": "参照", "critiques": "批評",
    "homage_to": "オマージュ", "subverts": "転倒", "echoes": "反響",
    "foreshadows": "伏線", "structurally_matches": "構造対応",
    "recurs_as": "再帰", "misreads_as": "誤読", "sublates": "止揚",
    "defines": "定義", "uses": "使用", "activates": "起動", "other": "関連",
    # 関係動詞
    "kills": "殺す", "attacks": "攻撃", "bonds": "義理を結ぶ", "saves": "救う",
    "protects": "守る", "betrays": "裏切る", "confesses": "告白", "reveals": "明かす",
    "promises": "約束", "threatens": "脅す", "names": "命名", "gives": "与える",
    "takes": "奪う", "finds": "発見", "observes": "観測", "learns": "知る",
    "remembers": "思い出す", "thinks": "考える", "says": "発言", "asks": "尋ねる",
    "helps": "助ける", "manipulates": "操る", "recruits": "勧誘", "kills_self": "自死",
    "inherits": "継承", "summons": "召喚", "appears": "出現", "dies": "死ぬ",
    "revives": "復活", "marries": "結婚", "hates": "憎悪", "loves": "愛",
    "trusts": "信頼", "suspects": "疑う", "follows": "追従", "leads": "率いる",
    "serves": "仕える", "commands": "命令", "negotiates": "交渉", "trades": "取引",
    "creates": "創造", "destroys": "破壊", "seals": "封印", "releases": "解放",
    "searches": "探索", "escapes": "逃走", "pursues": "追跡", "captures": "捕獲",
    "imprisons": "監禁", "exiles": "追放", "judges": "審判", "punishes": "処罰",
    "forgives": "赦す", "avenges": "復讐", "spies": "間諜", "informs": "通報",
    "abandons": "見捨てる", "rescues": "救助", "heals": "治療", "infects": "感染",
    "controls": "支配", "liberates": "解放", "awakens": "覚醒", "sleeps": "休眠",
    "transforms": "変身", "copies": "複製", "merges": "融合", "splits": "分裂",
    "eats": "喰らう", "drains": "吸収", "empowers": "強化", "weakens": "弱体化",
    "tests": "試験", "teaches": "教育", "learns_from": "学ぶ", "imitates": "模倣",
    "worships": "崇拝", "desecrates": "冒涜", "prays": "祈る", "curses": "呪う",
    "blesses": "祝福", "deceives": "欺く", "uncovers": "暴く", "confronts": "対決",
    "allies": "同盟", "enemies": "敵対", "parted": "離別", "reunites": "再会",
    "fights": "戦闘", "defeats": "撃破", "fears": "恐怖", "wears": "装着",
    "breaks": "破壊", "wounds": "傷つける", "stops": "停止", "carries": "運ぶ",
    "departs": "出発", "travels": "移動", "flees": "逃亡", "requires": "要求",
    "opens": "開く", "hides": "隠れる", "arrives": "到着", "conceals": "隠蔽",
    "teleports": "転送", "binds": "束縛", "makes": "作成", "loses": "失う",
    "hopes": "期待", "disappears": "消失", "grants": "付与", "refuses": "拒否",
    "accepts": "受諾", "invades": "侵攻", "occupies": "占拠", "guards": "守護",
    "attacks_self": "自傷", "heals_self": "自己治療",
}
MAX_EDGES = 40
MIN_EDGE = 2


def sanitize(name: str) -> str:
    n = name.strip().strip("『』「」\"'（）() ")
    n = re.sub(r"[/\\:*?<>|.\s]+", "_", n)
    return n[:40]


def main() -> None:
    # キャラ集合（エンティティページ実在 = 公開済みキャラ）
    chars = {p.stem.replace("E_char_", "")
             for p in (WIKI / "entities" / "characters").glob("E_char_*.md")}

    edges: Counter = Counter()
    edge_eps: dict[tuple[str, str, str], set] = defaultdict(set)
    for p in sorted(EVENTS.glob("ch*.jsonl")):
        for line in p.read_text(encoding="utf-8").splitlines():
            e = json.loads(line)
            s, o = e.get("subject", "").strip(), e.get("object", "").strip()
            pred = e.get("predicate", "other")
            ep = e.get("episode", "")
            if s in chars and o in chars and s != o:
                edges[(s, pred, o)] += 1
                edge_eps[(s, pred, o)].add(ep)

    # 同一ペアの逆方向・複数述語をまとめて表示用上位エッジ
    pair_edges: dict[tuple[str, str], list[tuple[str, int]]] = defaultdict(list)
    for (s, pred, o), c in edges.items():
        if c >= MIN_EDGE:
            pair_edges[(s, o)].append((pred, c))

    scored = sorted(pair_edges.items(),
                    key=lambda kv: -sum(c for _, c in kv[1]))[:MAX_EDGES]

    # ---- Mermaid グラフ（Quartz 内蔵 mermaid トランスフォーマで描画）----
    def nid(name: str) -> str:
        return "c_" + re.sub(r"[^0-9A-Za-zぁ-んァ-ン一-龥]", "_", sanitize(name))

    mer = ["```mermaid", "graph LR"]
    for (s, o), preds in scored:
        label = "／".join(f"{PRED_JA.get(p, p)}×{c}" for p, c in preds[:2])
        mer.append(f"    {nid(s)}[\"{s}\"] -->|{label}| {nid(o)}")
    mer.append("```")

    # ---- キャラページへ「関係キャラクター」AUTO セクションを注入（Graph がリンクを可視化）----
    per_char: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    for (s, o), preds in pair_edges.items():
        total = sum(c for _, c in preds)
        pj = "／".join(f"{PRED_JA.get(p, p)}" for p, _ in preds[:2])
        per_char[s].append((o, pj, total))
        per_char[o].append((s, pj + "(受)", total))
    AUTO_START = "<!-- AUTO-REL:BEGIN -->"
    AUTO_END = "<!-- AUTO-REL:END -->"
    n_inject = 0
    for name, rels in per_char.items():
        md_path = WIKI / "entities" / "characters" / f"E_char_{sanitize(name)}.md"
        if not md_path.exists():
            continue
        rels = sorted(rels, key=lambda r: -r[2])[:10]
        sec = [AUTO_START, "## 関係キャラクター", ""]
        for other, pj, total in rels:
            sec.append(f"- [[E_char_{sanitize(other)}|{other}]] — {pj}（{total} 観測）")
        sec += ["", AUTO_END]
        block = "\n".join(sec)
        content = md_path.read_text(encoding="utf-8")
        m = re.search(re.escape(AUTO_START) + r".*?" + re.escape(AUTO_END),
                      content, re.DOTALL)
        if m:
            content = content[:m.start()] + block + content[m.end():]
        elif AUTO_START not in content:
            content = content.rstrip() + "\n\n" + block + "\n"
        md_path.write_text(content, encoding="utf-8")
        n_inject += 1

    # ---- 関係一覧（ページリンク付き）----
    rel_lines = []
    for (s, o), preds in scored:
        total = sum(c for _, c in preds)
        pj = "／".join(f"{PRED_JA.get(p, p)}({c})" for p, c in preds[:3])
        rel_lines.append(f"- [[E_char_{sanitize(s)}|{s}]] → [[E_char_{sanitize(o)}|{o}]]"
                         f" — {pj}、計 {total} 観測")

    doc = ["---", "title: 関係性マップ", "id: relationships/index",
           "description: キャラ間の関係をイベント観測から集約。右のグラフが関係マップ", "---", "",
           "# 関係性マップ", "",
           f"イベント観測（{sum(edges.values())} 三つ組）から、相互に {MIN_EDGE} 回以上観測された"
           f"キャラ間関係を上位 {len(scored)} 件。各キャラページに「関係キャラクター」を注入したため、"
           "右サイドの **グラフ** も関係性マップになります（ノードがキャラ、辺が観測された関係）。", "",
           "## 関係グラフ（観測上位）", "",
           "> 矢印は観測の方向（主語→目的語）。ラベルは関係の種別×観測回数。", ""] + mer + ["",
           "## 上位の関係（観測順）", ""] + rel_lines + [""]
    (WIKI / "relationships").mkdir(exist_ok=True)
    (WIKI / "relationships" / "index.md").write_text("\n".join(doc), encoding="utf-8")
    print(f"関係エッジ: {len(scored)}（元三つ組 {len(edges)}）、キャラページ注入 {n_inject} 件")


if __name__ == "__main__":
    main()
