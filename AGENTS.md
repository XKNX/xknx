# xknx contributor conventions

## Referencing the KNX Standard

Code comments, docstrings and commit/PR text in this repo frequently cite a
specific part of the KNX Standard to justify a byte layout, a state machine,
or a piece of protocol behavior. These citations must be traceable back to an
exact document and an exact version of that document.

### Format

```
KNX v<version> - <Document Title> <document number> - §<paragraph>
```

Examples from the codebase:

```
KNX v02.01.02 - Management Procedures 03.05.02 - §2.19
KNX v01.02.02 - Transport Layer 03.03.04 - §2 TPDU
```

### Why the version matters

The KNX Standard is published as a set of separate documents (one per
volume/part/chapter), and **different documents carry different version
numbers** — they are not all released together under one overall version.
Transport Layer (03.03.04) is at `v01.02.02`, while the Management
Procedures document (03.05.02) is at `v02.01.02`. A citation with the
document number but no version is ambiguous: the cited paragraph's
content, numbering, or even its existence can differ between versions of
the same document.

### Rule: never guess the version (or the document number/title)

If you (Claude) are adding or fixing a spec citation and don't already have
the version number confirmed for that specific document, **stop and ask the
user** rather than filling in a plausible-looking version, inferring it from
a different document, or reusing another citation's version "for
consistency." The same applies to the document title and number themselves
if they aren't already established elsewhere in the codebase.

### Known documents and confirmed versions

| Spec version | Title | Document number |
|---|---|---|
| v02.01.02 | Management Procedures | 03.05.02 |
| v02.01.01 | Application Layer | 03.03.07 |
| v01.02.02 | Transport Layer | 03.03.04 |
| v02.02.01 | Datapoint Types | 03.07.02 |
| v01.02.02 | Logical Tag Extended | 10.01 |
| v01.05.02 | Routing | 03.08.05 |
| v01.01.02 | Communication Medium KNX IP | 03.02.06 |
| v01.06.02 | Core | 03.08.02 |
| v01.07.03 | Device Management | 03.08.03 |
| v01.07.01 | Tunnelling | 03.08.04 |
| v01.01.02 | KNX IP Secure | 03.08.09 |

Note that Management Procedures and Application Layer are two different
documents, cited side by side in places, that carry *different* versions
(`v02.01.02` vs `v02.01.01`) — don't assume every KNX document shares one
"current" version just because two happen to be close.

### How the KNX Standard is organized

The KNX Standard is split into numbered Volumes, each covering a different
area; a document's number starts with its Volume:

| Volume | Covers | Example document numbers cited in xknx |
|---|---|---|
| 3 — System Specifications | The core protocol stack: physical/data link/network/transport/application layers, management, routing, communication media | 03.02.06, 03.03.04, 03.03.07, 03.05.02, 03.08.05 |
| 10 — Application Specific Standards | Standardized application-level extensions built on top of Volume 3 | 10.01 (Logical Tag Extended) |

Almost everything xknx cites is Volume 3, since that's the wire protocol
itself. Volume 10 documents are extensions layered on top (e.g. LTE adds
`A_GroupPropValue_*` services on top of the Application Layer) and are
versioned independently of Volume 3 — this is why Logical Tag Extended
(10.01) doesn't share a version with Application Layer (03.03.07) even
though the two are closely related.

Document numbers within a volume follow `<volume>.<chapter>[.<subchapter>]`
(e.g. `03.03.07` = Volume 3, chapter 3, subchapter 7). The chapter/
subchapter structure doesn't tell you the version — two documents in the
same volume, even adjacent subchapters, can still be at different versions
(e.g. Transport Layer 03.03.04 at v01.02.02 vs. Application Layer 03.03.07
at v02.01.01), so the numbering scheme is only useful for finding *which*
document to ask about, never for guessing its version.

Every segment is zero-padded to two digits — `03.08.02`, not `3.8.2`;
`10.01`, not `10.1` — matching the KNX Association's own document
filenames (e.g. `03_08_02 Core`, `10_01 Logical Tag Extended`). Write new
citations this way even where an existing one in the codebase doesn't.

## Management procedures naming convention

`xknx/management/procedures/` implements KNX management procedures (DM_*,
NM_*, ...). The full convention — package layout, the workflow for adding a
new procedure, and the two function forms every procedure comes in — is
documented in the package docstring at
`xknx/management/procedures/__init__.py`; that's the canonical version, kept
in sync with the code. Summary:

- `<spec_name>(xknx: XKNX, ...)` opens (and closes) its own connection or
  broadcast via `xknx.management`.
- `<spec_name>_conn(conn: P2PConnection, ...)` operates on an already-open
  connection, for chaining several procedures over one connection. The
  `_conn` suffix is an xknx-only naming convention, not a KNX spec name —
  `dm_restart_r_co` is the one exception, since `RCo` is the real KNX name
  for that connection-based variant of DM_Restart.

## Changelog

Every user-facing change belongs in `docs/changelog.md`, under the
`# Unreleased changes` heading at the top of the file (a new numbered
release heading and date are added by the maintainer at release time, not
by a PR). Group entries under a `### <Category>` heading matching what's
already used nearby — common ones are `Protocol`, `DPT`, `Devices`,
`Connection`, `New Features`, `Breaking Changes`, `Deprecation notes`, and
`Internals` for anything with no user-visible behavior change. Breaking
changes should include a short before/after code snippet, not just prose.

## Pull requests

Copy `.github/pull_request_template.md` for the PR description — don't
write a free-form description instead. Fill in the "Description",
"Type of change" and "Checklist" sections for real (tick what actually
applies, don't leave every box checked or unchecked by default).
