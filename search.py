#!/usr/bin/env python3
"""Search the committed Prompt Atlas generated artifacts."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
GENERATED = ROOT / "generated"


def load_json(name):
    return json.loads((GENERATED / name).read_text(encoding="utf-8"))


def nonempty(value):
    if not value:
        raise argparse.ArgumentTypeError("must not be empty")
    return value


def model_ids(models, name):
    return {
        record_id
        for provider in models.values()
        for model_name, versions in provider.items()
        if model_name == name
        for record_ids in versions.values()
        for record_id in record_ids
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    query = parser.add_mutually_exclusive_group(required=True)
    query.add_argument("--id", metavar="ID", type=nonempty, help="exact id or id prefix")
    query.add_argument("--model", metavar="NAME", type=nonempty, help="exact model name")
    query.add_argument("--style", metavar="STYLE", type=nonempty, help="exact style")
    query.add_argument("--category", metavar="CATEGORY", type=nonempty, help="exact category")
    query.add_argument("--prompt", metavar="TEXT", type=nonempty, help="prompt substring")
    try:
        args = parser.parse_args()
    except SystemExit as error:
        return 1 if error.code == 2 else error.code

    try:
        records = [json.loads(line) for line in (GENERATED / "records.jsonl").read_text(encoding="utf-8").splitlines()]
        collections = load_json("collections.json")
        links = load_json("links.json")

        if args.id is not None:
            matches = (record for record in records if record["id"].startswith(args.id))
        elif args.prompt is not None:
            matches = (record for record in records if args.prompt in record["prompt"]["text"])
        else:
            if args.model is not None:
                ids = model_ids(collections["models"], args.model)
            elif args.style is not None:
                ids = set(collections["styles"].get(args.style, []))
            else:
                ids = set(collections["categories"].get(args.category, []))
            matches = (record for record in records if record["id"] in ids)

        for record in sorted(matches, key=lambda item: item["id"]):
            prompt = record["prompt"]["text"]
            print(json.dumps({
                "destination": links[record["id"]],
                "id": record["id"],
                "model": record["model"],
                "prompt": prompt if len(prompt) <= 120 else prompt[:119] + "…",
            }, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    except (OSError, UnicodeError, json.JSONDecodeError, AttributeError, KeyError, TypeError) as error:
        print(f"search.py: error: invalid generated artifacts ({error})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
