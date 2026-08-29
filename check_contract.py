#!/usr/bin/env python3
"""Validate Prompt Atlas v1 fixtures with Python's standard library."""

import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).parent
SCHEMA = json.loads((ROOT / "schema/case.schema.json").read_text())
VERSION = SCHEMA["properties"]["schemaVersion"]["const"]
LICENSES = set(SCHEMA["properties"]["license"]["enum"])
RIGHTS_BASES = set(
    SCHEMA["properties"]["rights"]["properties"]["clearanceBasis"]["enum"]
)
REQUIRED = set(SCHEMA["required"])
# Pending Artinspire approval; change only under a future WorkItem carrying its exact contract.
APPROVED_DESTINATION_HOST = "atlas-synthetic.invalid"

# ponytail: this executable covers v1 publication gates and identity; use a
# standards-compliant JSON Schema validator when arbitrary exports need full
# structural validation.


def present(value):
    return isinstance(value, str) and bool(value.strip())


def web_url(value, *, artinspire=False):
    if not present(value):
        return False
    url = urlsplit(value)
    return (
        url.scheme == "https"
        and bool(url.path and url.path != "/")
        and not url.query
        and not url.fragment
        and (not artinspire or url.netloc == APPROVED_DESTINATION_HOST)
    )


def validate(case):
    errors = []
    missing = REQUIRED - case.keys() if isinstance(case, dict) else REQUIRED
    if missing:
        errors.append("contract: missing " + ", ".join(sorted(missing)))
    if not isinstance(case, dict):
        return errors

    if case.get("schemaVersion") != VERSION:
        errors.append("contract: unsupported schemaVersion")

    rights = case.get("rights", {})
    if not (
        rights.get("status") == "cleared"
        and rights.get("clearanceBasis") in RIGHTS_BASES
        and web_url(rights.get("evidenceUrl"))
        and case.get("license") in LICENSES
    ):
        errors.append("rights gate")

    prompt = case.get("prompt", {})
    if prompt.get("visibility") != "approved" or not present(prompt.get("text")):
        errors.append("prompt visibility gate")

    provenance = case.get("provenance", {})
    if not (
        provenance.get("kind") in {"original", "authorized-remix"}
        and present(provenance.get("sourceLabel"))
        and web_url(provenance.get("sourceUrl"))
    ):
        errors.append("provenance gate")

    creator = case.get("creator", {})
    if not (
        present(creator.get("name"))
        and web_url(creator.get("profileUrl"), artinspire=True)
    ):
        errors.append("creator attribution gate")

    destination = case.get("destination", {})
    url = destination.get("url")
    slug = case.get("slug")
    canonical = (
        web_url(url, artinspire=True)
        and not url.endswith("/")
        and urlsplit(url).path.rsplit("/", 1)[-1] == slug
    )
    if not canonical or destination.get("permanent") is not True:
        errors.append("permanent destination gate")
    elif case.get("id") != (expected_id := "atlas_" + hashlib.sha256(url.encode()).hexdigest()[:20]):
        errors.append(f"identity derivation (expected {expected_id})")

    return errors


def check(path):
    errors = validate(json.loads(path.read_text()))
    print(f"{'FAIL' if errors else 'PASS'} {path.relative_to(ROOT)}" + (f": {', '.join(errors)}" if errors else ""))
    return bool(errors)


def main():
    paths = [Path(arg).resolve() for arg in sys.argv[1:]]
    if not paths:
        paths = sorted((ROOT / "fixtures").glob("*.json"))
    return any([check(path) for path in paths])


if __name__ == "__main__":
    raise SystemExit(main())
