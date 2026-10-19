"""Regression tests for scripts/pr_gate_checks.py — the wall between anonymous
input and main. Fixes each P0/P1 found in the 2026-10 code review:
  1. rename content/x -> protected path must FAIL (--no-renames)
  2. attacker-controlled file names must NOT execute (list-arg git, no shell)
  3. deletion ratio / external hosts / protected path FAILs
  4. plain appends touching existing links must PASS (no false positives)
  5. raw HTML/XSS patterns in added lines FAIL
"""
import pathlib
import subprocess
import sys

GATE = str(pathlib.Path(__file__).resolve().parents[1] / "pr_gate_checks.py")


def git(repo, *args):
    r = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert r.returncode == 0, f"git {' '.join(args)} -> {r.stderr[:200]}"
    return r.stdout.strip()


def make_repo(tmp):
    repo = tmp / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    content = repo / "content"
    content.mkdir()
    (content / "a.md").write_text(
        "\n".join(f"line {i} https://example.com/keep{i}" for i in range(600))
        + "\n",
        encoding="utf-8",
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "base")
    return repo


def commit_change(repo):
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "change")
    return git(repo, "rev-parse", "HEAD")


def run_gate(repo, base, head):
    r = subprocess.run(
        [sys.executable, GATE, base, head],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = r.stdout
    verdict = next((l.split("=", 1)[1] for l in out.splitlines() if l.startswith("verdict=")), None)
    reasons = next((l.split("=", 1)[1] for l in out.splitlines() if l.startswith("reasons=")), "")
    return verdict, reasons, out + r.stderr


def test_rename_to_protected_fails(tmp_path):
    repo = make_repo(tmp_path)
    base = git(repo, "rev-parse", "HEAD")
    (repo / "quartz").mkdir()
    (repo / "quartz" / "evil.md").write_text("evil\n", encoding="utf-8")
    (repo / "content" / "a.md").unlink()
    head = commit_change(repo)
    verdict, reasons, _ = run_gate(repo, base, head)
    assert verdict == "FAIL"
    assert "quartz" in reasons


def test_pwned_filename_does_not_execute(tmp_path):
    repo = make_repo(tmp_path)
    base = git(repo, "rev-parse", "HEAD")
    evil = repo / "content" / "$(touch PWNED_BY_PATH).md"
    evil.write_text("hello\n", encoding="utf-8")
    (repo / "content" / "a.md").write_text(
        (repo / "content" / "a.md").read_text(encoding="utf-8") + "append\n",
        encoding="utf-8",
    )
    head = commit_change(repo)
    verdict, reasons, out = run_gate(repo, base, head)
    assert verdict == "PASS", reasons
    side_effects = list(repo.rglob("PWNED_BY_PATH"))
    assert side_effects == [], f"shell injection side effects: {side_effects}"


def test_deletion_ratio_fails(tmp_path):
    repo = make_repo(tmp_path)
    base = git(repo, "rev-parse", "HEAD")
    (repo / "content" / "a.md").write_text("\n".join(f"l{i}" for i in range(350)) + "\n", encoding="utf-8")
    head = commit_change(repo)
    verdict, reasons, _ = run_gate(repo, base, head)
    assert verdict == "FAIL" and "deletion ratio" in reasons


def test_plain_append_with_existing_links_passes(tmp_path):
    repo = make_repo(tmp_path)
    base = git(repo, "rev-parse", "HEAD")
    p = repo / "content" / "a.md"
    text = p.read_text(encoding="utf-8")
    p.write_text(text + "append: see https://example.com/keep0 (unchanged)\n", encoding="utf-8")
    head = commit_change(repo)
    verdict, reasons, _ = run_gate(repo, base, head)
    assert verdict == "PASS", reasons


def test_new_external_hosts_fail(tmp_path):
    repo = make_repo(tmp_path)
    base = git(repo, "rev-parse", "HEAD")
    page = repo / "content" / "links.md"
    hosts = [f"spam{i}.net" for i in range(6)]
    page.write_text("\n".join(f"https://{h}/x" for h in hosts) + "\n", encoding="utf-8")
    head = commit_change(repo)
    verdict, reasons, _ = run_gate(repo, base, head)
    assert verdict == "FAIL" and "new external hosts" in reasons


def test_xss_pattern_fails(tmp_path):
    repo = make_repo(tmp_path)
    base = git(repo, "rev-parse", "HEAD")
    page = repo / "content" / "evil.md"
    page.write_text(
        "ok\n<script>alert(1)</script>\n<a href=\"vbscript:msgbox\">x</a>\n",
        encoding="utf-8",
    )
    head = commit_change(repo)
    verdict, reasons, _ = run_gate(repo, base, head)
    assert verdict == "FAIL" and "xss" in reasons


def test_playground_links_exempt(tmp_path):
    repo = make_repo(tmp_path)
    base = git(repo, "rev-parse", "HEAD")
    pg = repo / "content" / "playground"
    pg.mkdir()
    (pg / "notes.md").write_text(
        "\n".join(f"https://cite{i}.org/paper" for i in range(8)) + "\n",
        encoding="utf-8",
    )
    head = commit_change(repo)
    verdict, reasons, _ = run_gate(repo, base, head)
    assert verdict == "PASS", reasons