#!/usr/bin/env python3
"""Mechanical PR gate for AllusionistWikiLab.

Usage: pr_gate_checks.py <base_sha> <head_sha>
Prints GITHUB_OUTPUT lines:
  verdict=PASS|FAIL
  reasons=<semicolon separated>

Checks (all deterministic, no LLM):
  - protected files untouched (build/config/workflow surface)
  - all changed paths under content/
  - deletion ratio vs base content size (only when base is large enough
    to make the ratio meaningful; the playground is a rewrite-heavy layer)
  - new external links: ADDED lines only (+ lines), unique unknown hosts,
    playground exempted (free-text layer; promotion protocol gates later)
  - raw HTML/XSS patterns on added lines (Quartz outputs page HTML)

Security invariants:
  - git is invoked with LIST args only (no shell=True): attacker-controlled
    file names (from git's own output) cannot execute commands.
  - --no-renames: renames surface as delete+add, so protected-path checks
    cannot be bypassed via the "a => b" numstat form.
  - non-zero git exit raises: a silent "" must never produce a PASS.
"""
import re
import subprocess
import sys

PROTECTED = (
    "quartz/",
    ".github/",
    "scripts/",
    "audit/",
    "quartz.config.ts",
    "quartz.layout.ts",
    "package.json",
    "package-lock.json",
    ".gitignore",
    "globals.d.ts",
)
ALLOWED_PREFIX = "content/"
ALLOWED_HOSTS = (
    "github.com",
    "github.io",
    "tally.so",
    "echothread.io",
)
MAX_DELETE_RATIO = 0.30
MIN_BASE_LINES = 500
MAX_NEW_EXT_LINKS = 5
URL_RE = re.compile(r"https?://[^\s\)\]\"'<>。，、）】」』]+")
XSS_PATTERNS = (
    re.compile(r"<\s*(script|iframe|object|embed|meta|link)\b", re.I),
    re.compile(r"\son[a-z]+\s*=", re.I),
    re.compile(r"javascript:", re.I),
    re.compile(r"vbscript:", re.I),
    re.compile(r"data:text/html", re.I),
)


def git(*args: str) -> str:
    r = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed rc={r.returncode}: {(r.stderr or '')[:200]}"
        )
    return r.stdout


def changed_files(base: str, head: str):
    out = git("diff", "--no-renames", "--numstat", "-z", f"{base}...{head}")
    for rec in out.split("\0"):
        if not rec.strip():
            continue
        parts = rec.split("\t", 2)
        if len(parts) != 3:
            continue
        yield parts[0], parts[1], parts[2]


def added_lines(base: str, head: str, path: str) -> str:
    diff = git("diff", "--no-renames", f"{base}...{head}", "--", path)
    keep = [
        ln[1:]
        for ln in diff.splitlines()
        if ln.startswith("+") and not ln.startswith("+++")
    ]
    return "\n".join(keep)


def base_content_lines(ref: str) -> int:
    out = git("grep", "-c", "-z", "", ref, "--", "content")
    total = 0
    for tok in out.split("\0"):
        tok = tok.strip()
        if tok.isdigit():
            total += int(tok)
    return total


def main() -> int:
    base, head = sys.argv[1], sys.argv[2]
    reasons = []
    total_deleted = 0
    ext_hosts = set()
    for a, d, path in changed_files(base, head):
        if path.startswith(PROTECTED):
            reasons.append(f"protected file changed: {path}")
        if not path.startswith(ALLOWED_PREFIX):
            reasons.append(f"path outside content/: {path}")
        if d != "-":
            total_deleted += int(d)
        if a != "-" and int(a) > 0:
            added = added_lines(base, head, path)
            for m in XSS_PATTERNS:
                if m.search(added):
                    reasons.append(f"raw HTML/xss pattern in added lines: {path}")
                    break
            if not path.startswith("content/playground/"):
                for m in URL_RE.finditer(added):
                    host = m.group(0).split("//")[1].split("/")[0].lower()
                    if not any(host == h or host.endswith("." + h) for h in ALLOWED_HOSTS):
                        ext_hosts.add(host)
    if len(ext_hosts) > MAX_NEW_EXT_LINKS:
        reasons.append(
            f"new external hosts: {len(ext_hosts)} > {MAX_NEW_EXT_LINKS}"
        )
    base_lines = base_content_lines(base)
    if (
        base_lines >= MIN_BASE_LINES
        and total_deleted / base_lines > MAX_DELETE_RATIO
    ):
        reasons.append(
            f"deletion ratio {total_deleted}/{base_lines} > {MAX_DELETE_RATIO}"
        )
    verdict = "PASS" if not reasons else "FAIL"
    print(f"verdict={verdict}")
    print("reasons=" + "; ".join(reasons).replace("\n", " "))
    return 0


if __name__ == "__main__":
    sys.exit(main())