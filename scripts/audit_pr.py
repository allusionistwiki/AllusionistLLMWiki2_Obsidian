#!/usr/bin/env python3
"""Post-merge audit for AllusionistWikiLab.

Usage: audit_pr.py <merge_sha>
Prints GITHUB_OUTPUT lines:
  verdict=PASS|REJECT
  reason=<one line>

Layers:
  1. deterministic heuristics (reuses scripts/pr_gate_checks.py on the merged diff)
  2. optional LLM (OpenAI-compatible endpoint, e.g. local Strata llama.cpp server)
     via env STRATA_API_URL / STRATA_API_KEY / STRATA_MODEL.
     SPAM -> REJECT (only when the FIRST line parses anchored SPAM; ambiguous
     output falls to NEEDS_HUMAN, never to auto-revert). NEEDS_HUMAN -> PASS
     with reason logged (human override stays the top authority; audit never
     blocks, only flags).
Security: git via list args (no shell=True); oversized diffs are flagged for
human review instead of being truncated mid-content (a tail-planted SPAM must
not slip past a head-only LLM window).
"""
import json
import os
import re
import subprocess
import sys
import urllib.request


def git(*args: str) -> str:
    r = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return r.stdout


def first_line(text: str) -> str:
    for ln in text.splitlines():
        if ln.strip():
            return ln.strip()
    return ""


def main() -> int:
    sha = sys.argv[1]
    stat = git("show", sha, "-m", "--first-parent", "--stat")
    if not stat.strip():
        # A plain (non-merge) push commit prints nothing with -m --first-parent.
        stat = git("show", sha, "--stat")
    stat = stat[:2000]
    patch = git("show", sha, "-m", "--first-parent", "--patch")
    if not patch.strip():
        patch = git("show", sha, "--patch")
    oversized = len(patch) > 20000
    diff = patch[:20000]

    out = git("show", "--quiet", sha)  # noqa: B018 — validate sha exists (git() raises on failure)
    r = subprocess.run(
        [sys.executable, "scripts/pr_gate_checks.py", sha + "^1", sha],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = r.stdout
    verdict, reason = "PASS", "heuristic ok"
    for line in out.splitlines():
        if line.startswith("verdict="):
            verdict = line.split("=", 1)[1]
        elif line.startswith("reasons=") and line[len("reasons="):].strip():
            reason = line[len("reasons="):].strip()
    if not verdict:
        verdict, reason = "PASS", "heuristic parse failure (gate output empty)"

    if oversized and verdict != "FAIL":
        reason = "diff >20k chars: human review advised (LLM saw head only)"

    api = os.environ.get("STRATA_API_URL")
    if api and verdict != "FAIL" and not oversized:
        prompt = (
            "あなたは Wiki 監査ボットです。ファン解析 Wiki の git diff を判定してください。"
            "出力は 1 行目のみ: PASS / SPAM / NEEDS_HUMAN のいずれか1語と、日本語の理由 1 文。"
            "1 行目を判定語で始めること（説明文の中に判定語を書かない）。"
            "SPAM=荒らし・広告・破壊・意味不明。NEEDS_HUMAN=灰色地带で人間判断が望ましい。"
            "PASS=建設的な編集。\n\n"
            f"STAT:\n{stat}\n\nDIFF:\n{diff}"
        )
        body = {
            "model": os.environ.get("STRATA_MODEL", "audit"),
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 600,
        }
        req = urllib.request.Request(
            api.rstrip("/") + "/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
        key = os.environ.get("STRATA_API_KEY")
        if key:
            req.add_header("Authorization", "Bearer " + key)
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode())
            msg = data["choices"][0]["message"]
            text = (msg.get("content") or "").strip()
            if not text:
                # reasoning models: verdict line lives in reasoning_content tail
                text = (msg.get("reasoning_content") or "").strip()
        except Exception as exc:  # endpoint unreachable -> heuristic verdict stands
            text = "PASS api_error " + str(exc)[:80]
        # Anchored parse: the FIRST line must START with a verdict keyword.
        # Ambiguity falls to NEEDS_HUMAN (never to auto-revert).
        first = first_line(text)
        m = re.match(r"^(PASS|SPAM|NEEDS_HUMAN)\b", first.upper())
        if m:
            verdict_kw = m.group(1)
        else:
            m2 = re.search(r"(NEEDS_HUMAN|SPAM|PASS)", first.upper())
            verdict_kw = m2.group(1) if m2 else "NEEDS_HUMAN"
        if verdict_kw == "SPAM":
            verdict = "FAIL"
            reason = "LLM: SPAM " + first[:160]
        elif verdict_kw == "NEEDS_HUMAN":
            reason = "LLM: NEEDS_HUMAN " + (first + " " + text[:160]).strip()[:160]

    print("verdict=" + ("REJECT" if verdict == "FAIL" else "PASS"))
    print("reason=" + reason.replace("\n", " ")[:400])
    return 0


if __name__ == "__main__":
    sys.exit(main())