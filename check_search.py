#!/usr/bin/env python3
"""Discriminating runnable check for search.py."""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
CLI = [sys.executable, "-B", str(ROOT / "search.py")]
RECORD = json.loads((ROOT / "generated/records.jsonl").read_text(encoding="utf-8"))
LINK = json.loads((ROOT / "generated/links.json").read_text(encoding="utf-8"))[RECORD["id"]]


def run(*args):
    result = subprocess.run([*CLI, *args], capture_output=True, check=False)
    assert result.returncode == 0, result.stderr.decode()
    return result.stdout


def positive(label, *args):
    output = run(*args)
    rows = [json.loads(line) for line in output.splitlines()]
    assert rows == [{
        "destination": LINK,
        "id": RECORD["id"],
        "model": RECORD["model"],
        "prompt": RECORD["prompt"]["text"],
    }]
    print(f"PASS positive {label}: {RECORD['id']} {LINK}")


def negative(label, *args):
    assert run(*args) == b""
    print(f"PASS negative {label}: empty, exit 0")


def main():
    positive("exact id", "--id", RECORD["id"])
    positive("id prefix", "--id", RECORD["id"][:12])
    positive("model", "--model", RECORD["model"]["name"])
    positive("style", "--style", RECORD["tags"]["styles"][0])
    positive("category", "--category", RECORD["tags"]["categories"][0])
    positive("prompt", "--prompt", "cobalt rings")
    negative("id prefix", "--id", "atlas_no_match")
    negative("model", "--model", "No Such Model")
    negative("style", "--style", "no-such-style")
    negative("category", "--category", "no-such-category")
    negative("prompt", "--prompt", "no such prompt substring")
    first = run("--prompt", "paper")
    second = run("--prompt", "paper")
    assert first == second
    print("PASS determinism: identical query output is byte-identical")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
