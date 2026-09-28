#!/usr/bin/env python3
"""統合コミットスクリプト: vault / work の両リポジトリを相互コミット参照付きで同時コミット.

コミットメッセージ規約:
  vault 側: <message>\n\nwork-ref: <workコミットハッシュ>
  work  側: <message>\n\nvault-ref: <vaultコミットハッシュ（前）>
対応関係は両リポジトリの SYNC_LOG.md に記録する。

使い方:
  python scripts/commit_all.py -m "ch0057 の抽出と統合"
  python scripts/commit_all.py -m "feat: xxx" --push
  python scripts/commit_all.py --status
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paths import ROOT, load_config, resolve


def run_git(repo_path: Path, *args: str) -> tuple[int, str, str]:
    result = subprocess.run(
        ["git"] + list(args),
        cwd=repo_path, capture_output=True, text=True, encoding="utf-8",
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def get_current_commit(repo_path: Path) -> str:
    rc, out, _ = run_git(repo_path, "rev-parse", "--short", "HEAD")
    return out if rc == 0 else "0000000"


def has_changes(repo_path: Path) -> bool:
    rc, out, _ = run_git(repo_path, "status", "--porcelain")
    return bool(out.strip())


def commit_repo(repo_path: Path, message: str) -> str | None:
    if not has_changes(repo_path):
        return None
    rc, _, stderr = run_git(repo_path, "add", "-A")
    if rc != 0:
        print(f"❌ git add 失敗: {stderr}")
        return None
    rc, out, err = run_git(repo_path, "commit", "-m", message)
    if rc != 0:
        if "nothing to commit" in out or "nothing to commit" in err:
            return None
        print(f"❌ git commit 失敗: {err}")
        return None
    return get_current_commit(repo_path)


def update_sync_log(repo_path: Path, vault_commit: str, work_commit: str, message: str) -> None:
    sync_log = repo_path / "SYNC_LOG.md"
    line = f"| {vault_commit} | {work_commit} | {datetime.now():%Y-%m-%d} | {message} |"
    if sync_log.exists():
        lines = sync_log.read_text(encoding="utf-8").split("\n")
        header_end = 0
        for i, l in enumerate(lines):
            if l.startswith("|:---|"):
                header_end = i + 1
                break
        lines.insert(header_end, line)
        sync_log.write_text("\n".join(lines), encoding="utf-8")
    else:
        sync_log.write_text(
            f"# Sync Log\n\n| vault commit | work commit | 日付 | 内容 |\n|:---|:---|:---|:---|\n{line}\n",
            encoding="utf-8",
        )


def show_status(vault_path: Path, work_path: Path) -> None:
    for name, p in [("vault", vault_path), ("work", work_path)]:
        changes = "変更あり" if has_changes(p) else "変更なし"
        print(f"{name}: {get_current_commit(p)} ({changes})")


def main() -> int:
    parser = argparse.ArgumentParser(description="統合コミットスクリプト")
    parser.add_argument("-m", "--message", help="コミットメッセージ")
    parser.add_argument("--push", action="store_true", help="コミット後にプッシュ")
    parser.add_argument("--status", action="store_true", help="状態表示のみ")
    args = parser.parse_args()

    cfg = load_config()
    repos = cfg.get("repos", {})
    vault_path = resolve(repos.get("vault", "."))
    work_path = resolve(repos.get("work", "../AllusionistLLMWiki2_Work"))

    for name, p in [("vault", vault_path), ("work", work_path)]:
        if not (p / ".git").exists():
            print(f"❌ {name} が Git リポジトリではない: {p}")
            return 1

    if args.status:
        show_status(vault_path, work_path)
        return 0
    if not args.message:
        print("❌ -m でコミットメッセージを指定してください")
        return 1

    prev_vault = get_current_commit(vault_path)
    prev_work = get_current_commit(work_path)
    print(f"前回: vault={prev_vault} work={prev_work}")

    # 1. work をコミット（vault の前回ハッシュへ参照）
    work_commit = commit_repo(work_path, f"{args.message}\n\nvault-ref: {prev_vault}")
    print(f"work: {work_commit or '変更なし'}")
    work_commit = work_commit or prev_work

    # 2. vault をコミット（work の新ハッシュへ参照）
    vault_commit = commit_repo(vault_path, f"{args.message}\n\nwork-ref: {work_commit}")
    print(f"vault: {vault_commit or '変更なし'}")
    vault_commit = vault_commit or prev_vault

    # 3. SYNC_LOG 更新（両リポジトリ）
    update_sync_log(vault_path, vault_commit, work_commit, args.message)
    update_sync_log(work_path, vault_commit, work_commit, args.message)
    commit_repo(vault_path, "chore: update SYNC_LOG")
    commit_repo(work_path, "chore: update SYNC_LOG")

    # 4. プッシュ
    if args.push:
        for name, p in [("vault", vault_path), ("work", work_path)]:
            rc, _, err = run_git(p, "push")
            print(f"{name} push: {'OK' if rc == 0 else '失敗 ' + err}")

    print(f"🎉 統合コミット完了 vault={vault_commit} work={work_commit}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
