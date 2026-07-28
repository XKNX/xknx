# Referencing the KNX Standard

Code comments, docstrings and commit/PR text in this repo frequently cite a
specific part of the KNX Standard to justify a byte layout, a state machine,
or a piece of protocol behavior. These citations must be traceable back to an
exact document and an exact version of that document.

## Format

```
KNX v<version> - <Document Title> <document number> - §<paragraph>
```

Examples from the codebase:

```
KNX v02.01.02 - Management Procedures 03.05.02 - §2.19
KNX v01.02.02 - Transport Layer 03.03.04 - §2 TPDU
```

## Why the version matters

The KNX Standard is published as a set of separate documents (one per
volume/part/chapter), and **different documents carry different version
numbers** — they are not all released together under one overall version.
`xknx/telegram/tpci.py` cites Transport Layer (03.03.04) at `v01.02.02`,
while the Management Procedures document (03.05.02) is at `v02.01.02`. A
citation with the document number but no version is ambiguous: the cited
paragraph's content, numbering, or even its existence can differ between
versions of the same document.

## Rule: never guess the version (or the document number/title)

If you (Claude) are adding or fixing a spec citation and don't already have
the version number confirmed for that specific document, **stop and ask the
user** rather than filling in a plausible-looking version, inferring it from
a different document, or reusing another citation's version "for
consistency." The same applies to the document title and number themselves
if they aren't already established elsewhere in the codebase.

## Known documents and confirmed versions

| Document number | Title | Version | Where cited |
|---|---|---|---|
| 03.05.02 | Management Procedures | v02.01.02 | `xknx/management/**` |
| 03.03.07 | Application Layer | v02.01.01 | `xknx/telegram/apci.py`, `xknx/management/management.py`, `xknx/exceptions/exception.py`, `xknx/cemi/cemi_frame.py`, `test/telegram_tests/apci_test.py` |
| 03.03.04 | Transport Layer | v01.02.02 | `xknx/telegram/tpci.py` |
| 03.07.02 | Datapoint Types | v02.02.01 | `docs/changelog.md` (historical entry) |
| 10.1 | Logical Tag Extended | v01.02.02 | `xknx/telegram/apci.py` |
| 3.8.5 | Routing | v01.05.02 | `xknx/io/routing.py` |
| 3.2.6 | Communication Medium KNX IP | v01.01.02 | `xknx/io/routing.py` |

Note that Management Procedures and Application Layer are two different
documents cited side by side in `xknx/management/management.py` and carry
*different* versions (`v02.01.02` vs `v02.01.01`) — don't assume every KNX
document shares one "current" version just because two happen to be close.

## How the KNX Standard is organized

The KNX Standard is split into numbered Volumes, each covering a different
area; a document's number starts with its Volume:

| Volume | Covers | Example document numbers cited in xknx |
|---|---|---|
| 3 — System Specifications | The core protocol stack: physical/data link/network/transport/application layers, management, routing, communication media | 03.02.06, 03.03.04, 03.03.07, 03.05.02, 03.08.05 |
| 10 — Application Specific Standards | Standardized application-level extensions built on top of Volume 3 | 10.1 (Logical Tag Extended) |

Almost everything xknx cites is Volume 3, since that's the wire protocol
itself. Volume 10 documents are extensions layered on top (e.g. LTE adds
`A_GroupPropValue_*` services on top of the Application Layer) and are
versioned independently of Volume 3 — this is why Logical Tag Extended
(10.1) doesn't share a version with Application Layer (03.03.07) even
though the two are closely related.

Document numbers within a volume follow `<volume>.<chapter>[.<subchapter>]`
(e.g. `03.03.07` = Volume 3, chapter 3, subchapter 7). The chapter/
subchapter structure doesn't tell you the version — two documents in the
same volume, even adjacent subchapters, can still be at different versions
(e.g. Transport Layer 03.03.04 at v01.02.02 vs. Application Layer 03.03.07
at v02.01.01), so the numbering scheme is only useful for finding *which*
document to ask about, never for guessing its version.
