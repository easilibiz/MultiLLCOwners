# Chicago MSA LLC Portfolio Research

Status date: 2026-08-28  
Market: Chicago-Naperville-Elgin, IL-IN (CBSA 16980)  
Governance: `../../00_MASTER_SPECIFICATION/LLC_Portfolio_Identification_and_Mailing_Master_Specification.docx`

## Current status

Chicago is active. Cook County and Kendall County are the first executed county adapters.

- 71,355 Cook County 2026 parcels passed the normalized `*LLC` suffix rule and had a usable owner-mailing street.
- 3,505 owner-mailing-address clusters contain at least two distinct LLCs and two distinct parcels.
- 5,043 Kendall County parcels passed the same rule in the 2026-08-28 live-service snapshot, producing 110 county-level clusters.
- Re-grouping Cook and Kendall together produced 3,627 first-pass partial-MSA clusters, including 25 cross-county clusters.
- Improved street-suffix and suite normalization consolidated those into 3,348 screening clusters.
- Service-provider screening currently produces 2,139 `PASS_SERVICE_SCREEN` addresses, 54 suppressed service-provider addresses, and 1,155 addresses held for manual review.
- The 25 suppressed addresses represent 823 distinct LLC references and 1,448 property references. The screen includes researched law firms, registered agents, brokers/agents, accountants and third-party property managers.
- Zero Chicago rows are approved for printing. USPS CASS/DPV/NCOA has not been run, and only Cook and Kendall of the 13 MSA counties are present.

## Core rule

All parcel classes are eligible. Do not filter for multifamily or unit count.

1. Keep a parcel when the normalized legal owner ends in `LLC`.
2. Normalize the **owner mailing address**.
3. Group different LLC names by that owner mailing address.
4. Require at least two distinct LLCs and two distinct parcel IDs.
5. Never use the property/situs address as a substitute grouping key.
6. Suppress lawyers, registered agents, CPAs/accountants, filing services, C/O and other service-provider destinations.
7. Run USPS CASS/DPV and final campaign suppressions.
8. Produce one mail row per validated mailing address.

## Folder map

| Folder | Contents |
|---|---|
| `00_MARKET_ADAPTER` | Chicago-specific boundary, source, field and execution documentation |
| `01_FINAL_OUTPUTS` | Only final or explicitly labeled research-only outbound-address files |
| `02_SOURCE_DATA` | Immutable official source downloads and boundary references |
| `03_PROCESSED` | Parcel-level evidence and address-level research clusters |
| `04_REPORTS_AND_WORKBOOKS` | Source matrix, data dictionary and operating workbooks |
| `05_PIPELINE_CODE` | Reproducible county adapters |
| `06_DOCUMENTATION` | Human-readable maps and run instructions |
| `99_SUPPORT_FILES` | Builders, QA renders, intermediate support and archive |

## Current files

| File | Grain | Status |
|---|---|---|
| `03_PROCESSED/cook_2026_llc_parcels.csv` | One row per qualifying LLC-owned Cook parcel | Research evidence |
| `03_PROCESSED/cook_2026_address_clusters.csv` | One row per qualifying normalized owner mailing address | Research evidence |
| `01_FINAL_OUTPUTS/cook_2026_candidate_mailing_addresses_RESEARCH_ONLY.csv` | One row per candidate owner mailing address | **Not mail-ready** |
| `03_PROCESSED/kendall_20260828_llc_parcels.csv` | One row per qualifying Kendall LLC-owned parcel | Research evidence |
| `03_PROCESSED/kendall_20260828_address_clusters.csv` | One row per qualifying Kendall owner mailing address | Research evidence |
| `03_PROCESSED/chicago_msa_partial_cook_kendall_20260828_address_clusters.csv` | Cook + Kendall regrouped by owner mailing address | Partial-MSA research |
| `01_FINAL_OUTPUTS/chicago_msa_partial_cook_kendall_20260828_candidate_mailing_RESEARCH_ONLY.csv` | One row per partial-market candidate address | **Not mail-ready** |
| `03_PROCESSED/chicago_msa_partial_service_screen_all_20260828.csv` | One row per consolidated address with screening decision and evidence | Partial-MSA screened evidence |
| `01_FINAL_OUTPUTS/chicago_msa_partial_PASS_SERVICE_SCREEN_PREPOSTAL_20260828.csv` | Low-collision addresses with no service-provider signal | **Pre-postal; not mail-ready** |
| `01_FINAL_OUTPUTS/chicago_msa_partial_SUPPRESS_SERVICE_PROVIDERS_20260828.csv` | Confirmed/directly signaled service-provider destinations | **Exclude from campaign** |
| `01_FINAL_OUTPUTS/chicago_msa_partial_MANUAL_REVIEW_20260828.csv` | Ambiguous suites, PO boxes, missing ZIPs and high-collision addresses | **Hold for review** |
| `04_REPORTS_AND_WORKBOOKS/Chicago_Partial_MSA_Service_Provider_Screening_20260828.xlsx` | Summary, rules, column map and all three screening lists | Current screening control workbook |
| `04_REPORTS_AND_WORKBOOKS/Chicago_MSA_Source_Matrix_and_Data_Dictionary.xlsx` | Market control workbook | Current |
| `00_MARKET_ADAPTER/Chicago_MSA_Market_Adapter_and_Execution_Status.docx` | Chicago market adapter | Current |

## Parcel file columns

| Column | Meaning |
|---|---|
| `market` | Chicago MSA name |
| `county`, `state` | Source county and state |
| `tax_year` | Official source tax year |
| `parcel_id` | County parcel identifier |
| `legal_owner_raw` | Owner name exactly as supplied |
| `legal_owner_normalized` | Normalized legal owner used for distinct-LLC counting |
| `owner_mailing_address_raw`, `owner_mailing_city_raw`, `owner_mailing_state_raw`, `owner_mailing_zip_raw` | Official owner-mailing components |
| `owner_mailing_address_key` | Normalized address grouping key |
| `property_address`, `property_city`, `property_state`, `property_zip` | Situs evidence only; never the grouping substitute |
| `source_dataset_id`, `source_row_id` | Audit lineage |

## Cluster file columns

| Column | Meaning |
|---|---|
| `owner_mailing_address_key` | Normalized owner-mailing grouping key |
| `mail_address`, `mail_city`, `mail_state`, `mail_zip` | Representative raw owner-mail destination |
| `distinct_llc_count` | Number of different normalized LLC names at the address |
| `property_count` | Number of distinct parcel IDs at the address |
| `llc_names` | Pipe-delimited LLC evidence list |
| `parcel_ids` | Pipe-delimited parcel evidence list |
| `service_provider_review` | Professional/service-address gate |
| `usps_cass_dpv_status` | Postal validation gate |
| `mailing_status` | Final campaign authorization; currently research-only |
| `source_dataset_id`, `source_tax_year` | Source lineage |

## Re-run Cook County

From the project root, run:

```powershell
python .\Chicago\05_PIPELINE_CODE\build_cook_llc_clusters.py --root .\Chicago --year 2026
```

The script reads the official Cook County Socrata API and overwrites only the three named Cook outputs for the selected year.

Kendall and the two-county merge use:

```powershell
python .\Chicago\05_PIPELINE_CODE\build_kendall_llc_clusters.py --root .\Chicago --snapshot-date 2026-08-28
python .\Chicago\05_PIPELINE_CODE\build_partial_market_clusters.py --root .\Chicago --as-of 2026-08-28
```

## Next work

1. Manually resolve the 1,155 held addresses, prioritizing the largest LLC/property counts.
2. Send only the service-screened candidates through a USPS CASS/DPV/NCOA-capable process and apply undeliverable/vacant/duplicate suppressions.
3. Create the first true mailing-ready partial-market output only after postal validation.
4. Test DuPage and continue the remaining 11 counties using only authorized bulk/API routes; do not scrape sites that prohibit extraction.
