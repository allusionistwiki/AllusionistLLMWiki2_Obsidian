#!/usr/bin/env python3
"""クレーム（A_）変換スクリプト: staging claims → wiki/claims/A_*.md.

Usage:
    python scripts/merge_claims.py [--episode ch0057] [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import yaml
from rich.console import Console
from rich.table import Table

console = Console()

ROOT = Path(__file__).resolve().parent.parent
VAULT_ROOT = ROOT / "wiki"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT, VAULT_ROOT, STAGING_DIR
CLAIMS_DIR = VAULT_ROOT / "claims"

VALID_PREDICATES = {
    "alludes_to", "analogous_to", "recurs_as", "structurally_matches",
    "misreads_as", "foreshadows", "inverts", "parodies", "sublates",
}

PREDICATE_LABELS = {
    "alludes_to": "引喩", "analogous_to": "類推", "recurs_as": "作品内再帰",
    "structurally_matches": "構造的一致", "misreads_as": "誤読", "foreshadows": "予告",
    "inverts": "反転", "parodies": "パロディ", "sublates": "止揚",
}


def parse_frontmatter(content: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", content, re.DOTALL)
    if not m:
        return {}, content
    try:
        return yaml.safe_load(m.group(1)) or {}, m.group(2)
    except yaml.YAMLError:
        return {}, m.group(2)


def build_frontmatter(frontmatter: dict) -> str:
    yaml_str = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_str}---\n"


def extract_wikilink_name(wikilink: str) -> str:
    m = re.match(r"\[\[(?:E|ME)_\w+_(.+?)\]\]", wikilink)
    return m.group(1) if m else wikilink.replace("[[", "").replace("]]", "")


def normalize_evidence(evidence: list) -> list:
    """staging の証拠 → claim.schema.json 準拠（source_id 必須）へ正規化."""
    out = []
    for ev in evidence:
        ev = dict(ev)
        locator = ev.get("locator", {})
        chapter = locator.get("chapter", "")
        if "source_id" not in ev and re.match(r"^ch\d{4}$", chapter):
            ev["source_id"] = f"SRC_{chapter}"
        out.append(ev)
    return out


def find_existing_claim(predicate: str, subject_slug: str, object_slug: str) -> Optional[Path]:
    matches = sorted(CLAIMS_DIR.glob(f"A_{predicate}_{subject_slug}_{object_slug}_ch*.md"))
    return matches[0] if matches else None


def build_claim_file_path(predicate: str, subject_slug: str, object_slug: str, chapter: str) -> Path:
    return CLAIMS_DIR / f"A_{predicate}_{subject_slug}_{object_slug}_{chapter}.md"


def build_evidence_section(evidence_list: list) -> str:
    if not evidence_list:
        return ""
    lines = ["## 証拠", ""]
    for i, ev in enumerate(evidence_list, 1):
        locator = ev.get("locator", {})
        chapter = locator.get("chapter", "unknown")
        lines_range = locator.get("lines", "")
        lines.append(f"{i}. **{chapter}** (lines {lines_range}):")
        lines.append(f'   > "{ev.get("quote", "")}"')
        lines.append("")
    return "\n".join(lines)


def build_mapping_section(mapping_list: list) -> str:
    if not mapping_list:
        return ""
    lines = ["## 構造マッピング", "", "| 主語の特徴 | 対象の特徴 | 関係 |", "|:---|:---|:---|"]
    for mp in mapping_list:
        lines.append(f"| {mp.get('subject_feature','')} | {mp.get('object_feature','')} | {mp.get('relation','')} |")
    lines.append("")
    return "\n".join(lines)


def build_body(frontmatter: dict) -> str:
    predicate = frontmatter.get("predicate", "")
    label = PREDICATE_LABELS.get(predicate, predicate)
    subject_slug = extract_wikilink_name(frontmatter.get("subject", ""))
    object_slug = extract_wikilink_name(frontmatter.get("object", ""))
    body = f"# {subject_slug} は {object_slug} を{label}している\n\n"
    body += f"**述語**: `{predicate}` ({label})\n**初出**: {frontmatter.get('valid_from','')}\n**状態**: {frontmatter.get('epistemic_status','hypothesized')}\n\n"
    body += "（本文：主張の補足説明、根拠の詳細、競合解釈の可能性など）\n\n"
    body += build_evidence_section(frontmatter.get("evidence", []))
    body += build_mapping_section(frontmatter.get("mapping", []))
    return body


def build_new_claim_file(claim_data: dict, episode: str) -> str:
    subject = claim_data.get("subject", "")
    predicate = claim_data.get("predicate", "")
    obj = claim_data.get("object", "")
    subject_slug = extract_wikilink_name(subject)
    object_slug = extract_wikilink_name(obj)
    evidence = normalize_evidence(claim_data.get("evidence", []))
    evidence_strength = claim_data.get("evidence_strength", "moderate")
    epistemic_status = {
        "explicit": "confirmed",
        "strong": "supported",
    }.get(evidence_strength, "hypothesized")

    frontmatter = {
        "schema_version": "5.1",
        "id": f"A_{predicate}_{subject_slug}_{object_slug}_{episode}",
        "type": "analytical_claim",
        "subject": subject,
        "predicate": predicate,
        "object": obj,
        "valid_from": episode,
        "spoiler_after": episode,
        "epistemic_status": epistemic_status,
        "review_status": "unreviewed",
        "document_status": "active",
        "evidence_strength": evidence_strength,
        "evidence": evidence,
        "mapping": claim_data.get("mapping", []),
        "provenance": {
            "proposed_by": {"kind": "agent", "id": "extraction_agent_v3"},
        },
        "created": date.today().isoformat(),
        "updated": date.today().isoformat(),
    }
    return build_frontmatter(frontmatter) + build_body(frontmatter)


def update_claim_file(file_path: Path, claim_data: dict, episode: str) -> tuple[str, bool]:
    existing_content = file_path.read_text(encoding="utf-8")
    frontmatter, _ = parse_frontmatter(existing_content)

    existing_evidence = frontmatter.get("evidence", [])
    has_new = False
    for new_ev in normalize_evidence(claim_data.get("evidence", [])):
        new_chapter = new_ev.get("locator", {}).get("chapter", "")
        new_quote = new_ev.get("quote", "")
        is_duplicate = any(
            ev.get("locator", {}).get("chapter") == new_chapter and ev.get("quote") == new_quote
            for ev in existing_evidence
        )
        if not is_duplicate:
            existing_evidence.append(new_ev)
            has_new = True

    if not has_new:
        return existing_content, False

    frontmatter["evidence"] = existing_evidence
    frontmatter["updated"] = date.today().isoformat()

    # 証拠蓄積による昇格: 3件以上で moderate→strong, hypothesized→supported
    if len(existing_evidence) >= 3 and frontmatter.get("evidence_strength") == "moderate":
        frontmatter["evidence_strength"] = "strong"
        if frontmatter.get("epistemic_status") == "hypothesized":
            frontmatter["epistemic_status"] = "supported"

    return build_frontmatter(frontmatter) + build_body(frontmatter), True


def process_staging_file(staging_path: Path, dry_run: bool = False) -> dict:
    staging_data = yaml.safe_load(staging_path.read_text(encoding="utf-8"))
    episode = staging_data.get("episode", "unknown")
    claims = staging_data.get("claims", [])

    console.print(f"\n[bold cyan]📖 {episode}[/bold cyan] のクレームを処理中...")
    results = {"episode": episode, "claims": [], "created": 0, "updated": 0, "skipped": 0}

    for claim_data in claims:
        predicate = claim_data.get("predicate", "")
        subject = claim_data.get("subject", "")
        obj = claim_data.get("object", "")

        if predicate not in VALID_PREDICATES:
            console.print(f"  [yellow]⚠️  不明な述語: {predicate}[/yellow]")
            results["skipped"] += 1
            continue

        subject_slug = extract_wikilink_name(subject)
        object_slug = extract_wikilink_name(obj)
        existing_file = find_existing_claim(predicate, subject_slug, object_slug)

        if existing_file:
            content, has_new = update_claim_file(existing_file, claim_data, episode)
            if not has_new:
                console.print(f"  [dim]  - {predicate} {subject_slug}→{object_slug}: 新しい証拠なし（スキップ）[/dim]")
                results["skipped"] += 1
                continue
            action, file_path = "update", existing_file
        else:
            content = build_new_claim_file(claim_data, episode)
            action = "create"
            file_path = build_claim_file_path(predicate, subject_slug, object_slug, episode)

        if dry_run:
            console.print(f"  [magenta]  [DRY-RUN] {action}: {file_path.name}[/magenta]")
        else:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            icon = "✨" if action == "create" else "🔄"
            console.print(f"  {icon} {action}: {file_path.name}")

        results["claims"].append({"predicate": predicate, "subject": subject_slug,
                                  "object": object_slug, "action": action, "file": str(file_path)})
        results["created" if action == "create" else "updated"] += 1

    return results


def main():
    parser = argparse.ArgumentParser(description="クレーム（A_）変換スクリプト")
    parser.add_argument("--episode", help="特定のエピソードのみ処理（例: ch0057）")
    parser.add_argument("--dry-run", action="store_true", help="書き込まずに差分のみ表示")
    args = parser.parse_args()

    if not STAGING_DIR.exists():
        console.print(f"[red]❌ {STAGING_DIR} が存在しません[/red]")
        sys.exit(1)

    staging_files = sorted(STAGING_DIR.glob("staging_*.yaml"))
    if args.episode:
        staging_files = [f for f in staging_files if args.episode in f.name]
    if not staging_files:
        console.print("[yellow]⚠️  処理対象の staging ファイルが見つかりません[/yellow]")
        sys.exit(0)

    console.print(f"[bold]🔧 {len(staging_files)} 件の staging ファイルからクレームを処理[/bold]")
    if args.dry_run:
        console.print("[magenta bold]🔍 DRY-RUN モード（書き込みなし）[/magenta bold]")

    all_results = []
    for staging_file in staging_files:
        try:
            all_results.append(process_staging_file(staging_file, dry_run=args.dry_run))
        except Exception as e:
            console.print(f"[red]❌ {staging_file.name} の処理に失敗: {e}[/red]")
            continue

    console.print("\n" + "=" * 60)
    console.print("[bold]📊 クレーム処理サマリー[/bold]")
    table = Table()
    table.add_column("エピソード", style="cyan")
    table.add_column("新規作成", style="green")
    table.add_column("更新", style="yellow")
    table.add_column("スキップ", style="dim")
    for r in all_results:
        table.add_row(r["episode"], str(r["created"]), str(r["updated"]), str(r["skipped"]))
    console.print(table)


if __name__ == "__main__":
    main()
