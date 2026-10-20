# ADR-0003: Source-record identity based on source hash and parsed record ordinal unless a native key is verified

- **Status:** Accepted
- **Date:** 2026-10-19

**Context**

Bronze must preserve original source values and enough lineage to locate the original record, and support reproducible reprocessing from the same source snapshot (§7.1). The default source locator for a file snapshot is `source_record_id = <source_file_sha256>:<parsed_record_ordinal>` (§6.3). A native source key is preferred only after uniqueness, nullability, and stability have been tested and documented (§6.3). Silver rejects duplicate source locators at run level, while business-key collisions are flagged for investigation, not resolved automatically (§7.2).

**Decision**

1. Default source locator: `source_record_id = <source_file_sha256>:<parsed_record_ordinal>` (§6.3).
2. Platform identifier: `platform_event_id = UUIDv5(<project_namespace>, <source_system>:<source_record_id>)` (§6.3).
3. Define the parser's record ordinal consistently; do not assume physical line number equals CSV record number when quoted fields can contain newlines (§6.3).
4. Prefer a native source key only after uniqueness, nullability, and stability have been tested and documented (§6.3).
5. A business-key collision is a duplicate candidate, not automatic proof that two records are the same transaction (§6.3, §7.2).

**Alternatives considered**

- Use physical line number as the record ordinal: rejected; quoted fields containing newlines break the line-number-equals-record assumption (§6.3).
- Trust a native source key without verification: rejected; uniqueness, nullability, and stability must be tested and documented first (§6.3).

**Consequences and trade-offs**

- Stable, reproducible lineage tied to byte-identical source files; a re-exported file with changed bytes intentionally gets a new source snapshot identity (§6.3).
- Native key adoption is deferred until verified, keeping ingestion identity separate from business identity (§6.3).

**Tests/evidence required**

- Source audit records the source file hash, file size, row count, and reproducible parser results (§7.1 acceptance conditions; §14.2 evidence).
- Verify identity is stable for the same byte-identical file and parser convention (§6.3).

**Revisit trigger**

Revisit if a verified native source key is adopted or if identity/ordinal rules change (a MAJOR schema change under §7.5).

