#!/usr/bin/env python3
"""Generate the deterministic public Prompt Atlas artifacts."""

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

from check_contract import APPROVED_DESTINATION_HOST, ROOT, validate

OUTPUT = ROOT / "generated"


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode()


def refuse(path, reason):
    print(f"REFUSE {path}: {reason}", file=sys.stderr)
    raise SystemExit(1)


def load(paths):
    records = []
    ids = set()
    for path in paths:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            refuse(path, f"input gate ({error})")

        destination = record.get("destination", {}) if isinstance(record, dict) else {}
        url = destination.get("url") if isinstance(destination, dict) else None
        try:
            hostname = urlsplit(url).hostname if isinstance(url, str) else None
        except ValueError:
            refuse(path, "population guard (malformed destination URL)")
        if hostname not in {None, APPROVED_DESTINATION_HOST}:
            refuse(path, "population guard")

        try:
            errors = validate(record)
        except (AttributeError, TypeError, ValueError) as error:
            refuse(path, f"contract gate ({error})")
        if errors:
            refuse(path, ", ".join(errors))
        if record["id"] in ids:
            refuse(path, f"population guard (duplicate id {record['id']})")
        ids.add(record["id"])
        records.append(record)
    return sorted(records, key=lambda record: record["id"])


def render(records):
    collections = {"categories": {}, "models": {}, "styles": {}}
    for record in records:
        record_id = record["id"]
        model = record["model"]
        collections["models"].setdefault(model["provider"], {}).setdefault(model["name"], {}).setdefault(model["version"], []).append(record_id)
        for category in sorted(record["tags"]["categories"]):
            collections["categories"].setdefault(category, []).append(record_id)
        for style in sorted(record["tags"]["styles"]):
            collections["styles"].setdefault(style, []).append(record_id)

    return {
        "collections.json": canonical(collections),
        "links.json": canonical({record["id"]: record["destination"]["url"] for record in records}),
        "records.jsonl": b"".join(canonical(record) for record in records),
    }


def check(expected):
    actual_names = sorted(path.name for path in OUTPUT.iterdir()) if OUTPUT.is_dir() else []
    expected_names = sorted(expected)
    if actual_names != expected_names:
        print(f"DIFF generated file set: expected {expected_names}, found {actual_names}", file=sys.stderr)
        return 1
    for name in expected_names:
        if (OUTPUT / name).read_bytes() != expected[name]:
            print(f"DIFF generated/{name}", file=sys.stderr)
            return 1
    print("PASS generated tree matches")
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("records", nargs="*", type=Path, default=[ROOT / "fixtures/valid.json"])
    args = parser.parse_args()
    expected = render(load([path.resolve() for path in args.records]))
    if args.check:
        return check(expected)
    OUTPUT.mkdir(exist_ok=True)
    for name in sorted(expected):
        (OUTPUT / name).write_bytes(expected[name])
    print(f"WROTE {len(expected)} files from {len(args.records)} record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
