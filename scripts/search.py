#!/usr/bin/env python3
"""検索CLI（ハイブリッド検索システム: 構造化SQL + FTS5全文 + ベクトル + RRF）.

使い方:
  python scripts/search.py --build                       # インデックス構築
  python scripts/search.py "ハルベルトの視覚描写"          # 自然言語検索（自動ルーティング）
  python scripts/search.py --entity ハルベルト --aspect visual
  python scripts/search.py --episode ch0057
  python scripts/search.py --fulltext "白銀の髪"
  python scripts/search.py --semantic "月の象徴"          # 要埋め込みプロバイダ起動
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT, VAULT_ROOT, WORK_DIR, load_config
from search_modules.indexer import SearchIndexer
from search_modules.hybrid_search import HybridSearcher
from search_modules.query_router import QueryRouter, QueryType

console = Console()

SEARCH_DIR = WORK_DIR / "search"
SEARCH_DB = SEARCH_DIR / "search_index.db"
VECTOR_DB = SEARCH_DIR / "vector_store.db"


def build_index():
    console.print("[bold]🔨 インデックスを構築中...[/bold]")
    indexer = SearchIndexer(SEARCH_DB)
    indexer.create_schema()
    indexer.index_vault(VAULT_ROOT, WORK_DIR / "events")
    indexer.close()
    console.print(f"\n[green]✅ インデックス構築完了: {SEARCH_DB}[/green]")


def search_structured(searcher: HybridSearcher, entity: str, aspect: str = None):
    console.print(f"[bold]🔍 構造化検索: entity={entity}, aspect={aspect}[/bold]")
    results = searcher.search_events(entity=entity, aspect=aspect)
    if not results:
        console.print("[yellow]結果が見つかりません[/yellow]")
        return
    table = Table(title=f"{entity} のイベント（{len(results)} 件）")
    table.add_column("エピソード", style="cyan")
    table.add_column("アスペクト", style="green")
    table.add_column("観察", style="white")
    for r in results:
        table.add_row(r.get("episode", ""), r.get("aspect", ""), (r.get("observation", "") or "")[:50])
    console.print(table)


def search_episode(searcher: HybridSearcher, episode: str):
    console.print(f"[bold]🔍 エピソード検索: {episode}[/bold]")
    row = searcher.indexer.conn.execute(
        "SELECT * FROM episodes WHERE chapter = ?", (episode,)).fetchone()
    if not row:
        console.print(f"[yellow]エピソード {episode} が見つかりません[/yellow]")
        return
    console.print(f"\n[cyan]エピソード: {episode}[/cyan]")
    console.print(f"アーク: {row['arc'] or '（未所属）'}")
    for label, key in [("登場人物", "characters"), ("分析主張", "claims"), ("伏線", "mysteries")]:
        items = json.loads(row[key] or "[]")
        if items:
            console.print(f"\n[bold]{label}:[/bold]")
            for c in items:
                console.print(f"  - {c}")
    events = searcher.search_events(episode=episode)
    if events:
        console.print(f"\n[bold]イベント（{len(events)} 件）:[/bold]")
        for e in events[:10]:
            console.print(f"  - [{e.get('aspect', '')}] {e.get('observation', '')}")


def search_fulltext(searcher: HybridSearcher, query: str):
    console.print(f"[bold]🔍 全文検索: {query}[/bold]")
    results = searcher.fulltext_search(query)
    if not results:
        console.print("[yellow]結果が見つかりません[/yellow]")
        return
    table = Table(title=f"検索結果（{len(results)} 件）")
    table.add_column("ID", style="cyan")
    table.add_column("タイプ", style="green")
    table.add_column("名前", style="white")
    table.add_column("スコア", style="yellow")
    for r in results:
        table.add_row(r["id"], r.get("type", ""), r.get("name", "")[:40], f"{r['score']:.3f}")
    console.print(table)


def search_semantic(searcher: HybridSearcher, query: str):
    console.print(f"[bold]🔍 意味検索: {query}[/bold]")
    try:
        results = searcher.semantic_search(query)
    except Exception as e:
        console.print(f"[red]埋め込みプロバイダに接続できません: {e}[/red]")
        console.print("[dim]config.yaml の search.embedding_provider（ollama / openai_compatible）を確認[/dim]")
        return
    if not results:
        console.print("[yellow]結果が見つかりません（ベクトルインデックスが空の可能性があります）[/yellow]")
        return
    table = Table(title=f"検索結果（{len(results)} 件）")
    table.add_column("ID", style="cyan")
    table.add_column("タイプ", style="green")
    table.add_column("内容", style="white")
    table.add_column("類似度", style="yellow")
    for r in results:
        table.add_row(r["id"], r.get("doc_type", ""), r.get("text_content", "")[:40],
                      f"{r['similarity']:.3f}")
    console.print(table)


def search_hybrid(searcher: HybridSearcher, router: QueryRouter, query: str):
    query_type = router.route(query)
    console.print(f"[dim]クエリタイプ: {query_type.value}[/dim]")

    if query_type == QueryType.STRUCTURED:
        parsed = router.parse_structured_query(query)
        if parsed:
            search_structured(searcher, parsed["entity"], parsed["aspect"])
            return
    elif query_type == QueryType.EPISODE:
        episode = router.parse_episode_query(query)
        if episode:
            search_episode(searcher, episode)
            return

    console.print(f"[bold]🔍 ハイブリッド検索: {query}[/bold]")
    results = searcher.hybrid_search(query)
    if not results:
        console.print("[yellow]結果が見つかりません[/yellow]")
        return
    table = Table(title=f"検索結果（{len(results)} 件）")
    table.add_column("ID", style="cyan")
    table.add_column("タイプ", style="green")
    table.add_column("名前", style="white")
    table.add_column("スコア", style="yellow")
    table.add_column("ソース", style="magenta")
    for r in results:
        table.add_row(r["id"], r.get("type", ""), r.get("name", "")[:40],
                      f"{r['score']:.4f}", ", ".join(r.get("sources", [])))
    console.print(table)


def main():
    parser = argparse.ArgumentParser(description="検索CLI（ハイブリッド検索）")
    parser.add_argument("query", nargs="?", help="検索クエリ")
    parser.add_argument("--build", action="store_true", help="インデックスを構築")
    parser.add_argument("--entity", help="エンティティ名（構造化検索）")
    parser.add_argument("--aspect", help="アスペクト（構造化検索）")
    parser.add_argument("--episode", help="エピソード（エピソード検索）")
    parser.add_argument("--fulltext", help="全文検索クエリ")
    parser.add_argument("--semantic", help="意味検索クエリ")
    args = parser.parse_args()

    if args.build:
        build_index()
        return

    if not SEARCH_DB.exists():
        console.print("[red]❌ インデックスが存在しません。先に --build を実行してください[/red]")
        sys.exit(1)

    config = load_config()
    searcher = HybridSearcher(SEARCH_DB, VECTOR_DB, config=config)
    router = QueryRouter()

    try:
        if args.entity:
            search_structured(searcher, args.entity, args.aspect)
        elif args.episode:
            search_episode(searcher, args.episode)
        elif args.fulltext:
            search_fulltext(searcher, args.fulltext)
        elif args.semantic:
            search_semantic(searcher, args.semantic)
        elif args.query:
            search_hybrid(searcher, router, args.query)
        else:
            parser.print_help()
    finally:
        searcher.close()


if __name__ == "__main__":
    main()
