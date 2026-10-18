# NYC postcard campaign outputs — read before printing

## Where the screened postcard recipients are

Use these new campaign-control files:

- `mailing_ready/NYC_MAILING_READY_DEDUPED_FILTERED.csv` — vendor-facing screened population, one row per normalized mailing address
- `mailing_ready/NYC_MAILING_READY_DEDUPED_FILTERED.xlsx` — review workbook with Summary, Mailing Ready, Excluded, and Rules sheets
- `mailing_ready/NYC_MAILING_EXCLUSIONS_AUDIT.csv` — every source row removed and every rule that triggered

Current result: 8,362 unique mailing addresses. The process excluded 3,501 source rows and consolidated 665 duplicate surviving rows.

The authoritative destination field is `mailing_address_full`. The split street/city/state/ZIP fields are convenience columns and should be reconciled to the postal vendor's standardized result.

## Original research shortlist

The primary research shortlist is:

`mailing_lists/NYC_POSTCARD_TARGETS_ALL_12528_NOT_PRINT_APPROVED.csv`

Each row is one probable multi-LLC cluster and contains:

- `recommended_addressee` — the proposed name for the postcard
- `mailing_address` — the proposed delivery address
- `llc_names` — the LLC entities associated with the cluster
- `property_addresses` — the properties associated with those LLCs
- `distinct_llcs` and `distinct_properties` — the cluster size
- DOS corroboration and risk-marker fields

The 400-row pilot subset is:

`mailing_lists/NYC_POSTCARD_TARGETS_PILOT_400_NOT_PRINT_APPROVED.csv`

## Current scale

- 12,528 candidate mailing rows
- 12,118 unique mailing-address strings
- 41,773 unique LLC names represented
- 1,303 rows with a proposed named addressee
- 11,225 rows addressed to `PROPERTY OWNER`
- 4,356 clusters with strong DOS address corroboration
- 3,185 clusters sharing a DOS address
- 4,058 clusters with active-name matches only
- 929 clusters marked `Needs manual review`

## Do not send either file directly to a printer yet

The original shortlist is not print-approved. The new mailing-ready CSV has completed duplicate and intermediary screening, but it is still marked `NOT_CASS_OR_DPV_VALIDATED`. Before spending on postage:

1. Run USPS CASS/DPV validation and, when appropriate, NCOA.
2. Apply campaign suppression, returned-mail, opt-out, do-not-contact, and duplicate-household rules.
3. Review vendor corrections and undeliverable records.
4. Freeze a dated print-approved copy; do not overwrite the screened research output or exclusion audit.

The automated screen removes source agent markers, registered-agent address matches, legal/lawyer indicators, CPA/accounting indicators, filing-service indicators, care-of destinations, property/situs substitutions, low confidence, and records already designated for manual review. A rule-based screen cannot guarantee that every professional intermediary is detected, which is why postal/vendor QA and campaign suppression remain release gates.

`original_confidence` is research confidence in the cluster, not authorization to mail.

## What created the NYC clusters

The NYC portfolio key is the normalized ACRIS deed-party/grantee mailing address. Different LLC names are grouped when the same grantee mailing address connects at least two LLCs and at least two properties. The physical property address is evidence only and is not the grouping key.

NY Department of State records are a later corroboration layer. A registered agent, service company, attorney, or process address is not proof of beneficial ownership.

For the complete folder map and column definitions, open `../NYC_FILE_MAP_AND_COLUMN_GUIDE.md`.
