# Prompt Atlas public case contract v1

This contract describes one synthetic or approved public image/prompt case. A
producer MUST omit a case unless every gate below passes. Consumers MUST reject
unknown fields, unsupported schema versions, and malformed values.

## Identity

1. The production destination host and format are pending Artinspire approval
   and are therefore not yet fixed. All synthetic fixtures use the reserved
   `atlas-synthetic.invalid` host.
2. Set `slug` to the final URL path segment. It MUST be lowercase ASCII kebab
   case.
3. Set `id` to `atlas_` plus the first 20 lowercase hexadecimal characters of
   `SHA-256(canonical destination URL encoded as UTF-8)`.

The destination URL, slug, and id become immutable at first publication. A
correction before publication recomputes all three; a later migration preserves
the original URL or redirects it permanently rather than minting a new identity.

## Mandatory fail-closed gates

A case is publishable only when all five gates pass:

1. **Rights:** `rights.status` is `cleared`, `rights.clearanceBasis` is one of
   `creator-owned`, `licensed`, or `public-domain`, `rights.evidenceUrl` is
   present, and `license` is allowlisted by the schema.
2. **Prompt visibility:** `prompt.visibility` is `approved` and prompt text is
   non-empty.
3. **Provenance:** kind, source label, and source URL are all present.
4. **Creator attribution:** creator name and Artinspire profile URL are present.
5. **Permanent destination:** `destination.url` is a canonical Artinspire URL,
   `destination.permanent` is `true`, and its final path segment equals `slug`.

Missing, blank, unknown, or unrecognized values fail their gate. Passing one
gate never compensates for another.

## Versioning

Every record carries `schemaVersion`. Version numbers follow semantic
versioning: major for breaking field or meaning changes, minor for backward-
compatible additions or allowlist changes, and patch for non-semantic
clarifications. Producers emit one exact supported version; consumers fail
closed on any unsupported version.

Every schema change MUST update `CHANGELOG.md` in the same commit. The entry
records the date, version, changed validation or meaning, migration impact, and
whether existing identifiers remain valid. Published versions are never edited
in place; a new version gets a new schema artifact.

## Fixture check

Run `python3 check_contract.py <fixture.json>`. It exits zero only when every
supplied case passes; each `fixtures/invalid-*.json` file is expected to exit
one and names the single publication gate it violates.
