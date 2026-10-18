# NYC multi-LLC research — file map and column guide

## Start here

| Need | File or folder |
|---|---|
| Send the screened, deduplicated population to postal validation | `01_FINAL_OUTPUTS/mailing_ready/NYC_MAILING_READY_DEDUPED_FILTERED.csv` |
| Review the campaign controls and exclusions in Excel | `01_FINAL_OUTPUTS/mailing_ready/NYC_MAILING_READY_DEDUPED_FILTERED.xlsx` |
| Audit every row removed from the automated campaign | `01_FINAL_OUTPUTS/mailing_ready/NYC_MAILING_EXCLUSIONS_AUDIT.csv` |
| Review the original unscreened research shortlist | `01_FINAL_OUTPUTS/mailing_lists/NYC_POSTCARD_TARGETS_ALL_12528_NOT_PRINT_APPROVED.csv` |
| Review the 400-row pilot | `01_FINAL_OUTPUTS/mailing_lists/NYC_POSTCARD_TARGETS_PILOT_400_NOT_PRINT_APPROVED.csv` |
| Browse the analysis in Excel | `01_FINAL_OUTPUTS/workbooks/NYC_Multi_LLC_DOS_Enrichment_ALL.xlsx` |
| Audit each LLC against NY DOS | `01_FINAL_OUTPUTS/evidence/NYC_ENTITY_MATCHES_ALL_CLUSTERS.csv` |
| Audit each property and ACRIS deed party | `01_FINAL_OUTPUTS/evidence/NYC_OWNERSHIP_EVIDENCE_PROPERTY_LEVEL.csv` |
| Review the pre-DOS clusters | `01_FINAL_OUTPUTS/evidence/NYC_PROBABLE_COMMON_OWNER_CLUSTERS.csv` |
| Understand campaign risks before printing | `01_FINAL_OUTPUTS/READ_ME_FIRST.md` |

## Folder map

```text
NYC/
├── 01_FINAL_OUTPUTS/
│   ├── READ_ME_FIRST.md
│   ├── mailing_ready/        Screened and deduplicated campaign list, workbook, audit, and QA previews
│   ├── mailing_lists/        Candidate postcard rows; not print approved
│   ├── workbooks/            Human-readable Excel versions
│   └── evidence/             Entity, parcel, ACRIS, and statistics audit files
├── 02_SOURCE_DATA/           Original NYC assessment extracts and official references
│   └── reference/            Dataset metadata, layouts, and data dictionary
├── 03_PROCESSED_EXPLORATORY/ Cleaned assessment files and early LLC-name analysis
├── 04_REPORTS_AND_WORKBOOKS/ Early assessment-only workbook and preview images
├── 05_PIPELINE_CODE/         Analysis and workbook-building code retained for reproducibility
├── 06_DOCUMENTATION/         Original detailed CSV field guide
└── 99_ARCHIVE/               Generated cache retained so no file was discarded
```

The active pipeline repository remains at `C:\CodexCode\NYCData`. The organized NYC folder contains campaign outputs and a preserved copy of the earlier scattered files. The repository was not moved because doing so could break reproducibility.

## What the mailing-ready output represents

The current automated-campaign output contains 8,362 unique normalized mailing addresses. It consolidates 665 duplicate candidate rows and excludes 3,501 source rows under one or more rules. Exclusion reasons include agent/service or care-of indicators, lawyers/legal destinations, CPAs/accounting destinations, low confidence, manual-review status, and property-address substitution. All exclusions remain in the audit file.

It is ready for the postal-validation stage, not for immediate printing: `postal_validation_status` is `NOT_CASS_OR_DPV_VALIDATED` until an authorized postal vendor completes address validation and final suppressions.

### Mailing-ready columns

File: `01_FINAL_OUTPUTS/mailing_ready/NYC_MAILING_READY_DEDUPED_FILTERED.csv`

| Column | Meaning |
|---|---|
| `mailing_id` | Stable campaign-row identifier. |
| `addressee` | Screened recipient; uses `PROPERTY OWNER` when a defensible person is unavailable or conflicting. |
| `mailing_address_full` | Authoritative complete delivery address from the research source. |
| `street_and_unit`, `city`, `state`, `zip_code` | Convenience parsing for a mailing vendor; the full address remains authoritative. |
| `source_cluster_ids` | All original NYC research clusters consolidated into this one address row. |
| `distinct_llcs` | Deduplicated count of LLC names associated with the address. |
| `distinct_properties` | Deduplicated count of property addresses associated with the address. |
| `llc_names` | Pipe-separated LLC entities behind the campaign row. |
| `property_addresses` | Pipe-separated physical properties; evidence only, never the mailing key. |
| `source_confidence` | Conservative source confidence after consolidation. |
| `dos_corroboration` | DOS evidence categories represented by the consolidated source clusters. |
| `exclusion_screen` | `PASS` for every row in this file. |
| `duplicate_address_count_consolidated` | Number of source candidate rows combined into the outbound row. |
| `postal_validation_status` | `NOT_CASS_OR_DPV_VALIDATED` until a postal provider completes validation. |
| `source_url` | Official public source URL retained for auditability. |

## What the original research list represents

Each row in the all-clusters shortlist is one address-based candidate cluster—not one property and not one individual LLC. The row answers:

1. What addressee is proposed?
2. Where would the postcard be sent?
3. Which LLC entities are associated with that address?
4. Which physical properties are associated with those LLCs?
5. How much DOS corroboration exists?
6. Which risk markers require review?

Current all-clusters profile:

| Measure | Count |
|---|---:|
| Candidate postcard rows / clusters | 12,528 |
| Unique mailing-address strings | 12,118 |
| Unique LLC names represented | 41,773 |
| Rows addressed to `PROPERTY OWNER` | 11,225 |
| Rows with a proposed named addressee | 1,303 |
| Strong DOS address corroboration | 4,356 |
| Shared DOS address | 3,185 |
| Active-name matches only | 4,058 |
| Needs manual review | 929 |
| Agent-address marker | 1,555 |
| Situs-address marker | 95 |
| Mailing addresses appearing on multiple rows | 324 |
| Extra rows above one row per unique address | 410 |

## Primary mailing-list columns

File: `01_FINAL_OUTPUTS/mailing_lists/NYC_POSTCARD_TARGETS_ALL_12528_NOT_PRINT_APPROVED.csv`

| Column | Meaning |
|---|---|
| `cluster_id` | Stable internal identifier joining the mailing row to entity evidence. |
| `original_confidence` | Pre-DOS cluster confidence: High, Medium, or Low. This is research confidence, not print approval. |
| `mailing_tier` | Number of distinct LLC names represented by the cluster. |
| `recommended_addressee` | Proposed postcard addressee. Usually `PROPERTY OWNER`; a named value requires human review. |
| `possible_named_addressee` | Best name found in DOS process records, even when support is insufficient for recommendation. |
| `possible_addressee_support_count` | Number of LLC entity records supporting the possible name. |
| `mailing_address` | Proposed postcard delivery address. |
| `mailing_address_source` | Whether the selected address is ACRIS-only or corroborated by DOS. |
| `distinct_llcs` | Number of different normalized LLC names in the cluster. |
| `distinct_properties` | Number of distinct BBL properties in the cluster. |
| `property_records` | Number of assessment parcel records represented. |
| `llc_names` | Pipe-separated LLC names associated with the cluster—the entities behind the postcard row. |
| `property_addresses` | Pipe-separated physical property addresses owned by the listed LLCs. Evidence only; not the cluster key. |
| `dos_llcs_matched` | Number of cluster LLCs matched to active DOS entities. |
| `dos_match_rate` | Matched active DOS entities divided by distinct LLCs. |
| `dos_address_corroborated_llcs` | Number of LLCs whose DOS process address agrees with the ACRIS shared address. |
| `largest_shared_dos_address_count` | Largest number of matched LLCs sharing one DOS process address within the cluster. |
| `dos_corroboration` | Strong address corroboration, shared DOS address, active-name matches only, or needs manual review. |
| `email_phone_available_from_dos` | `No`; the official DOS data does not supply campaign email or phone fields. |
| `minimum_acris_name_match` | Lowest assessment-owner-to-ACRIS-grantee name similarity in the cluster. |
| `agent_address_marker` | `1` means the address may be an agent/intermediary address and requires extra caution. |
| `situs_address_marker` | `1` means the shared mailing address resembles the property/situs address for most records. |
| `source_url` | Official NY DOS source URL. |

The pilot-400 shortlist has the same practical mailing fields but omits `original_confidence`, `agent_address_marker`, and `situs_address_marker`.

## Entity-evidence columns

File: `01_FINAL_OUTPUTS/evidence/NYC_ENTITY_MATCHES_ALL_CLUSTERS.csv`

| Column | Meaning |
|---|---|
| `cluster_id` | Joins the entity row to the mailing shortlist. |
| `original_confidence` | Pre-DOS research confidence for the cluster. |
| `tier_llc_count` | Number of LLCs in the address cluster. |
| `acris_shared_mailing_address` | Shared ACRIS grantee/deed-party mailing address that formed the cluster. |
| `llc_name_normalized` | Cleaned LLC name from the property/ACRIS analysis. |
| `assessment_name_used` | Assessment-roll spelling used for DOS matching. |
| `match_status` | Address-corroborated active match, active-name match, ambiguous match, or no active match. |
| `candidate_count` | Number of active DOS candidates for the normalized LLC name. Values over one need review. |
| `address_match_score` | DOS-to-ACRIS address score: 3 exact normalized address, 2 street+ZIP, 1 ZIP only, 0 no agreement. |
| `dos_id` | Official NY DOS entity identifier. |
| `current_entity_name` | Current active entity name in DOS. |
| `initial_dos_filing_date` | Original DOS filing/formation date. |
| `county` | County recorded by DOS. |
| `jurisdiction` | Formation state or country. |
| `entity_type` | DOS legal-entity type. |
| `dos_process_name` | Name on the DOS service-of-process record; may be an LLC, person, attorney, or service company. |
| `dos_process_address` | DOS service-of-process address. |
| `chairman_name` | Chairman/CEO field when present; usually blank for LLCs and not proof of ownership. |
| `chairman_address` | Address linked to the chairman/CEO field when present. |
| `registered_agent_name` | Registered-agent name; not necessarily an owner. |
| `registered_agent_address` | Registered-agent address. |
| `location_name` | DOS physical-location name line when available. |
| `location_address` | DOS physical-location address when available. |
| `email_from_dos` | Blank; official DOS data does not supply email. |
| `phone_from_dos` | Blank; official DOS data does not supply phone. |
| `source_url` | Official NY DOS source URL. |

## Pre-DOS cluster columns

File: `01_FINAL_OUTPUTS/evidence/NYC_PROBABLE_COMMON_OWNER_CLUSTERS.csv`

| Column | Meaning |
|---|---|
| `confidence` | Pre-DOS High/Medium/Low research confidence. |
| `distinct_llc_names` | Number of different normalized LLC names sharing the address. |
| `distinct_bbls` | Number of distinct tax lots/properties. |
| `property_records` | Number of assessment records. |
| `deed_party_address` | Human-readable ACRIS grantee mailing address. |
| `llc_names` | Pipe-separated LLC names in the cluster. |
| `property_addresses` | Pipe-separated physical property addresses. |
| `minimum_name_match` | Lowest assessment-owner-to-grantee name score. |
| `agent_address_marker` | Intermediary/agent risk flag. |
| `situs_address_marker` | Property-address-reuse risk flag. |
| `address_normalized` | Cleaned ACRIS grantee mailing address used as the cluster key. |

## Property-level audit columns

File: `01_FINAL_OUTPUTS/evidence/NYC_OWNERSHIP_EVIDENCE_PROPERTY_LEVEL.csv`

| Column | Meaning |
|---|---|
| `parid` | Assessment parcel identifier. |
| `bbl` | Borough-block-lot join key. |
| `property_address` | Physical property address; evidence only. |
| `assessment_owner` | LLC owner name from the assessment roll. |
| `owner_normalized` | Cleaned assessment owner name. |
| `document_id` | ACRIS deed document identifier. |
| `doc_type` | ACRIS document type. |
| `recorded_datetime` | ACRIS recording date/time. |
| `grantee_name` | Buyer/grantee name on the deed. |
| `grantee_normalized` | Cleaned grantee name. |
| `grantee_address` | Grantee mailing address shown on the deed. |
| `address_normalized` | Cleaned grantee mailing address used for clustering. |
| `name_match_score` | Assessment-owner-to-grantee similarity score from 0 to 100. |
| `agent_marker` | Internal agent/intermediary risk flag. |

## Earlier exploratory files

The material in `03_PROCESSED_EXPLORATORY` and `04_REPORTS_AND_WORKBOOKS` is not the postcard campaign output. It contains earlier assessment-only analysis, including:

- exact same-LLC multi-property summaries; and
- shared physical-property-address candidates.

Those files are retained for history and QA. They do not implement the final cross-LLC mailing-address clustering logic and should not be supplied to a mailing vendor.

## Remaining campaign release steps

Before creating a print-vendor file:

1. Submit the 8,362-row mailing-ready CSV for USPS CASS/DPV validation and, when appropriate, NCOA processing.
2. Apply returned-mail, opt-out, do-not-contact, duplicate-household, campaign-history, and compliance suppressions.
3. Review any postal corrections that materially change unit, city, state, ZIP, or deliverability.
4. Freeze a dated print-approved vendor file containing only the final addressee, postal fields, and internal mailing ID.
