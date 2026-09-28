#!/usr/bin/env python3
"""イベントレコード（第1層 JSONL）のバリデーション + 中間集約（第2層 YAML）検証.

使い方:
  python scripts/validate_event.py            # work/events/*.jsonl を検証
  python scripts/validate_event.py --staging  # work/staging/*.yaml を検証
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent.parent


def load_schema(name: str) -> dict:
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def validate_record(record: dict, schema: dict) -> list[str]:
    return [
        f"{'.'.join(map(str, e.path))}: {e.message}"
        for e in jsonschema.Draft7Validator(schema).iter_errors(record)
    ]


def validate_jsonl_file(file_path: Path, schema: dict) -> tuple[int, int]:
    valid, errors = 0, 0
    for line_num, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as e:
            errors += 1
            print(f"NG {file_path.name}:{line_num} - JSON parse error: {e}")
            continue
        errs = validate_record(event, schema)
        if errs:
            errors += 1
            print(f"NG {file_path.name}:{line_num}")
            for e in errs:
                print(f"   - {e}")
        else:
            valid += 1
    return valid, errors


def validate_staging_file(file_path: Path, schema: dict) -> list[str]:
    data = yaml.safe_load(file_path.read_text(encoding="utf-8"))
    return validate_record(data, schema)


def main() -> int:
    staging_mode = "--staging" in sys.argv
    if staging_mode:
        schema = load_schema("staging.schema.json")
        d = ROOT / "work/staging"
        files = sorted(d.glob("*.yaml"))
        bad = 0
        for f in files:
            errs = validate_staging_file(f, schema)
            if errs:
                bad += 1
                print(f"NG {f.name}")
                for e in errs:
                    print(f"   - {e}")
            else:
                print(f"OK {f.name}")
        print(f"\n{len(files)} staging files, {bad} with errors")
        return 1 if bad else 0

    schema = load_schema("event.schema.json")
    d = ROOT / "work/events"
    files = [f for f in sorted(d.glob("*.jsonl"))]
    if not files:
        print("work/events/ に .jsonl がありません")
        return 0
    total_valid = total_errors = 0
    for f in files:
        v, e = validate_jsonl_file(f, schema)
        total_valid += v
        total_errors += e
        if e == 0:
            print(f"OK {f.name}: {v} events valid")
    print(f"\n合計: {total_valid} valid, {total_errors} errors")
    return 1 if total_errors else 0


if __name__ == "__main__":
    sys.exit(main())
