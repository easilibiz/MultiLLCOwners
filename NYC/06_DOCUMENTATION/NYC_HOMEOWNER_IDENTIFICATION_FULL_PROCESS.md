# NYC LLC Property-Owner Research: Complete Reproducible Process

## Purpose and terminology

This document records the full process used to turn the new NYC FY2027 property-tax assessment records into research leads for people or organizations that may control multiple LLC-owned properties.

The process does **not** prove beneficial ownership. NYC tax records usually identify the legal owner as an LLC, not the human behind it. ACRIS supplies deed-grantee mailing addresses, and New York Department of State (DOS) records sometimes supply a service-of-process name. Those names may be owners, managers, employees, lawyers, accountants, or registered agents. Accordingly, the outputs use terms such as **probable common-owner cluster**, **possible named addressee**, and **research lead** rather than verified homeowner.

The key analytical rule is:

> Different LLC names are connected when the latest relevant deed records show the same normalized grantee mailing address, and the group contains at least two distinct LLC names and two distinct properties.

The physical property address is never the primary grouping key.

## End-to-end workflow

```text
NYC FY2027 final assessment roll
        |
        | filter YEAR=2027, PERIOD=3, LLC-like OWNER names
        v
189,340 LLC-owned parcel records
        |
        | build BBL and query ACRIS
        v
latest deed + grantee name + grantee mailing address
        |
        | normalize and require owner/grantee name similarity >= 75
        v
155,869 property-level evidence rows
        |
        | group by normalized grantee mailing address
        | require >=2 LLCs and >=2 BBLs
        v
12,528 probable common-owner address clusters
        |
        | match every LLC name to active NY DOS entities
        v
possible person names + address corroboration + risk flags
        |
        | exclude intermediaries, low confidence, and manual review
        | consolidate duplicate mailing destinations
        v
8,362 screened unique mailing addresses
```

## 1. Extract the new FY2027 tax-assessment records

### Official source

- NYC Open Data dataset: **Property Valuation and Assessment Data**, dataset ID `8y4t-faws`
- Dataset page: `https://data.cityofnewyork.us/d/8y4t-faws`
- Local metadata copy: `NYC/02_SOURCE_DATA/reference/NYC_assessment_dataset_metadata.json`
- Local data dictionary: `NYC/02_SOURCE_DATA/reference/Property_Assessment_Data_Dictionary.xlsx`

The assessment roll contains the parcel owner as recorded for tax-assessment purposes. It does not contain a reliable owner mailing address or a guaranteed human beneficial-owner field.

### Final-roll filter

The retained source was the published final FY2027 roll:

- `YEAR = 2027`
- `PERIOD = 3` (final roll)
- `OWNER` contained an LLC indicator such as `LLC`, `L.L.C.`, or `LIMITED LIABILITY`

No property-type, building-class, tax-class, unit-count, or value prefilter was applied. This matters because filtering for multifamily buildings too early would omit valid LLC portfolios.

The selected fields were:

```text
parid, boro, block, lot, year, period, owner, bldg_class,
fintaxclass, housenum_lo, housenum_hi, street_name, aptno,
zip_code, units, finmkttot, finacttot
```

An equivalent Socrata query is:

```sql
SELECT parid, boro, block, lot, year, period, owner, bldg_class,
       fintaxclass, housenum_lo, housenum_hi, street_name, aptno,
       zip_code, units, finmkttot, finacttot
WHERE year = '2027'
  AND period = '3'
  AND (
       upper(owner) LIKE '%LLC%'
       OR upper(owner) LIKE '%L.L.C.%'
       OR upper(owner) LIKE '%LIMITED LIABILITY%'
  )
```

The exact one-line download command was not preserved, but the saved CSV, its fields, the final-roll conditions, and the implemented downstream code are preserved. The query above reproduces the extraction logic. For large downloads, use Socrata pagination or request CSV from `https://data.cityofnewyork.us/resource/8y4t-faws.csv` with the `$select`, `$where`, `$limit`, and `$offset` parameters.

### Preliminary versus final file

An earlier preliminary extract contained 376,182 rows and was retained only for history:

- `NYC/02_SOURCE_DATA/fy2027_llc_properties_preliminary.csv`

It was superseded by the final-roll extract:

- `NYC/02_SOURCE_DATA/fy2027_final_llc_properties.csv`
- 189,340 data rows
- every saved row has `year=2027` and `period=3`

The final file is the authoritative tax-record input for this run.

## 2. Clean and normalize the assessment records

The exploratory cleaning code is preserved at `NYC/05_PIPELINE_CODE/analyze_llc.py`. The active pipeline implementation is at `C:/CodexCode/NYCData/pipeline.py`.

For each row, the process:

1. Removed exact duplicate records.
2. Kept parcel identifiers as text so leading zeroes would not be lost.
3. Constructed the 10-digit BBL as one borough digit, five block digits, and four lot digits.
4. Constructed a readable physical property address from house number, street, apartment/unit, and ZIP.
5. Normalized owner names by uppercasing, converting `&` to `AND`, removing punctuation, collapsing spaces, and standardizing `L L C` and `LIMITED LIABILITY COMPANY/CO` to `LLC`.
6. Retained building class, tax class, unit count, market value, and assessed value as descriptive evidence. None of them controlled inclusion.

The assessment-only exploration found 133,061 distinct normalized LLC names and 16,833 LLC names appearing on more than one property record. It also tested shared **physical property addresses**, but those results were not used as the final common-owner method because a situs address is not an owner mailing address.

## 3. Load a restartable local database

The final assessment CSV was imported into a SQLite database so the very large ACRIS lookup could stop and resume safely:

```powershell
python pipeline.py init --assessment-csv data/input/fy2027_final_llc_properties.csv
```

The database is `C:/CodexCode/NYCData/data/state/nyc_llc.sqlite`. It contains:

- assessment parcels;
- a BBL work queue with pending/complete/error status;
- selected latest deeds;
- deed parties;
- property-level ownership evidence.

Only boroughs 1–4 were queued for ACRIS: Manhattan, Bronx, Brooklyn, and Queens. Staten Island assessment rows were retained in the source data but excluded from these ACRIS calls because its land-record coverage differs.

## 4. Retrieve the latest relevant ACRIS deed for every BBL

Three NYC Open Data sources were joined:

- ACRIS Real Property Legals, `8h5j-fqxa`: locate document IDs by borough, block, and lot.
- ACRIS Real Property Master, `bnx9-e6tj`: obtain document type and recording date.
- ACRIS Real Property Parties, `636b-3b5g`: obtain Party Type `2`, the buyer/grantee, including the name and mailing address written on the recorded document.

For each queued BBL, the code:

1. Queried the ACRIS legal table for document IDs tied to that BBL.
2. Queried the master table for those documents.
3. Kept only recognized deed/transfer document types (`DEED`, `DEEDO`, `DEEDP`, `DEED COR`, `CONDEED`, `REIT`, and the other deed types listed in `pipeline.py`).
4. Sorted by `recorded_datetime` and selected the newest deed. If multiple deeds shared the same newest timestamp, it retained all of them rather than choosing arbitrarily.
5. Queried the parties table for Party Type `2` only.
6. Saved the grantee name and all address components.
7. Marked the BBL complete. Failed API batches were marked `error` and retried on a later pass.

The full run used decreasing batch sizes to retry transient API failures:

```powershell
python pipeline.py fetch --batch-size 12
python pipeline.py fetch --batch-size 8
python pipeline.py fetch --batch-size 4
python pipeline.py build
python pipeline.py status
```

The wrapper is preserved as `C:/CodexCode/NYCData/run_full.ps1`. Authentication used either a Socrata application token or API-key ID/secret stored in an ignored `.env` file; credentials were not written to project outputs.

Final retrieval status:

- 178,192 of 178,192 ACRIS-eligible BBLs completed.
- 161,751 BBLs had a latest deed.
- 142,216 distinct latest-deed documents were retained.
- 142,042 latest deeds had grantee-party data.

## 5. Link the tax-roll LLC to the deed grantee

The assessment owner and ACRIS grantee strings were normalized with the same rules. A name-match score was then assigned:

- `100`: normalized strings exactly equal.
- `95`: equal after removing generic legal tokens such as LLC, company, corporation, and “the.”
- `80`: one normalized name contains the other.
- `75`: non-generic token overlap is at least 85%.
- `0`: none of the above.

Only scores of 75 or higher became ownership-evidence rows. This prevented an unrelated grantee on the deed from being attached to the assessment LLC merely because both appeared under the same BBL.

The property-level evidence output contains the parcel, BBL, situs address, assessment LLC, latest deed, grantee name, grantee mailing address, match score, and agent-risk marker:

- `NYC/01_FINAL_OUTPUTS/evidence/NYC_OWNERSHIP_EVIDENCE_PROPERTY_LEVEL.csv`

Results:

- 155,869 matched ownership-evidence rows.
- 154,892 assessment property records represented.
- 120,331 LLC names represented.
- 155,292 evidence rows (99.6%) were exact normalized name matches.

## 6. Form probable common-owner clusters

The grouping key was the **normalized ACRIS grantee mailing address**. Normalization uppercased the text, removed punctuation, standardized whitespace, and combined address components consistently while preserving unit/suite information.

A group was exported only if it contained:

- at least two distinct normalized LLC names; and
- at least two distinct BBLs/properties.

For each group the code retained all supporting LLC names, BBLs, physical property addresses, deed addresses, and the minimum owner-to-grantee match score.

Risk and confidence rules were then applied:

- An address containing registered-agent, corporation-service, `C/O`, or `ATTN` markers received an agent flag.
- If the address's numbered street segment matched at least 80% of the physical property addresses, it received a situs-address flag.
- **High:** no agent flag, no situs flag, at most 10 LLC names, and minimum name-match score at least 95.
- **Medium:** no agent flag and at most 20 LLC names, but not High.
- **Low:** agent/intermediary risk, unusually large address fanout, or otherwise outside those limits.

This produced `NYC_PROBABLE_COMMON_OWNER_CLUSTERS.csv` with 12,528 clusters:

- 10,500 High confidence;
- 390 Medium confidence;
- 1,638 Low confidence;
- 41,773 unique LLC names across all clusters.

Confidence is a research-ranking measure, not an ownership adjudication.

## 7. Match LLC names to active New York DOS records

The enrichment code is `NYC/05_PIPELINE_CODE/dos_enrich.py`. It queried the New York Open Data **Active Corporations Beginning 1800** dataset, ID `n9v6-gdp6`:

- API: `https://data.ny.gov/resource/n9v6-gdp6.json`
- Dataset page: `https://data.ny.gov/Economic-Development/Active-Corporations-Beginning-1800/n9v6-gdp6`

The all-cluster run was equivalent to:

```powershell
python dos_enrich.py --output-dir <output-folder> --all-clusters
```

For all 41,773 distinct LLC names, the code:

1. Recovered the most common original tax-roll spelling for the normalized LLC name.
2. Queried DOS in batches for exact current-entity-name matches.
3. For names not found, performed a conservative text search and accepted only results whose normalized current entity name exactly equaled the normalized target name.
4. Cached every completed lookup in `dos_match_cache.json`, allowing interruption and restart without repeating successful calls.
5. When several active DOS entities shared a name, ranked candidates by agreement with the ACRIS mailing address, LLC entity type, New York jurisdiction, and relevant New York county.

The DOS-to-ACRIS address score was:

- `3`: exact normalized full address;
- `2`: matching street plus five-digit ZIP;
- `1`: ZIP only;
- `0`: no address agreement.

Each LLC was labeled as one of:

- Address-corroborated active match;
- Active name match;
- Ambiguous active-name match; or
- No active DOS match.

The complete audit is:

- `NYC/01_FINAL_OUTPUTS/evidence/NYC_ENTITY_MATCHES_ALL_CLUSTERS.csv`

Results:

- 42,321 LLC/entity evidence rows (some names had multiple candidate records).
- 39,875 matched rows.
- 94.2% match rate.
- 16,982 address-corroborated entity rows.

The DOS dataset contains active entities and is updated monthly. A missing match may mean an inactive entity, a foreign entity, a spelling difference, or missing coverage; it does not mean the LLC never existed.

## 8. Extract possible human names

The only person-name candidate used by the automated workflow was `dos_process_name`, the DOS service-of-process name associated with a matched LLC.

The code rejected a value as a possible person when it:

- was blank;
- contained common service-company or registered-agent markers;
- contained entity terms such as `LLC`, `INC`, `CORP`, `COMPANY`, `PLLC`, `LP`, `LTD`, `ASSOCIATES`, or `REALTY`;
- contained digits; or
- did not look like a two-to-six-word personal name.

Within each address cluster, candidate names were counted across the matched LLC records:

- the most frequent plausible person became `possible_named_addressee`;
- it became `recommended_addressee` only when at least two LLC records independently supported the same name;
- otherwise the safe default remained `PROPERTY OWNER`.

This produced 1,303 clusters with a proposed named addressee and 11,225 clusters addressed to `PROPERTY OWNER`.

Important: even two matching DOS process-name records do not prove beneficial ownership. The named value remains a lead for human review. The DOS source did not supply campaign email addresses or phone numbers, so those fields were deliberately left blank.

## 9. Choose the mailing address and characterize corroboration

For each cluster:

- If at least two matched LLCs shared a DOS process address and at least one of those records matched the ACRIS address, the displayed mailing address could use the DOS version.
- Otherwise, the original ACRIS grantee mailing address was retained.

The cluster-level DOS result was categorized as:

- **Strong DOS address corroboration:** at least two LLCs had DOS addresses matching the ACRIS address at score 2 or 3.
- **Shared DOS address:** at least two matched LLCs shared the same DOS address.
- **Active-name matches only:** enough entities matched by name, without strong shared-address support.
- **Needs manual review:** insufficient or ambiguous support.

The full unscreened research list is:

- `NYC/01_FINAL_OUTPUTS/mailing_lists/NYC_POSTCARD_TARGETS_ALL_12528_NOT_PRINT_APPROVED.csv`

It includes the proposed addressee, possible name, support count, mailing address and source, LLCs, properties, DOS metrics, and risk flags.

## 10. Screen intermediaries and deduplicate destinations

The original 12,528-row research list was not safe to send automatically. `NYC/05_PIPELINE_CODE/build_mailing_ready.mjs` applied the campaign controls.

A source row was excluded when any of these applied:

- missing mailing address;
- source agent-address flag;
- property/situs-address substitution flag;
- DOS status of `Needs manual review`;
- Low source confidence;
- lawyer/legal terminology;
- CPA/accounting/bookkeeping/tax-service terminology;
- registered-agent or filing-service terminology;
- care-of or agent terminology;
- target mailing address equaled a populated registered-agent address; or
- matching DOS process/location evidence identified a professional intermediary.

All exclusions, including every triggered reason and relevant detail, were retained in:

- `NYC/01_FINAL_OUTPUTS/mailing_ready/NYC_MAILING_EXCLUSIONS_AUDIT.csv`

Surviving addresses were normalized again for campaign deduplication. Case, punctuation, country suffixes, street types, directions, and unit labels were standardized, while suite and unit identifiers were preserved. All rows sharing the resulting key were consolidated into one outbound record. When consolidated rows disagreed on the named addressee, the result reverted to `PROPERTY OWNER`.

Screening results:

- 12,528 input candidate clusters;
- 3,501 source rows excluded;
- 9,027 survivors before deduplication;
- 665 duplicate surviving rows consolidated;
- 8,362 final unique mailing-address rows.

The output is:

- `NYC/01_FINAL_OUTPUTS/mailing_ready/NYC_MAILING_READY_DEDUPED_FILTERED.csv`

It is ready for postal validation, not immediate printing.

## 11. Required manual verification and release controls

Before treating a name as a person controlling the LLC, manually review:

1. The recorded deed image and any transfer forms.
2. The current DOS entity record and filing history.
3. Whether the service-of-process name is actually an owner/manager or an intermediary.
4. Conflicts among multiple people or multiple DOS candidates.
5. Whether the address is a law office, accountant, management company, filing service, registered agent, or unrelated shared office.

Before printing or mailing:

1. Run USPS CASS/DPV validation and, where appropriate, NCOA.
2. Apply returned-mail, opt-out, do-not-contact, duplicate-household, campaign-history, and legal/compliance suppressions.
3. Review material changes to unit, city, state, ZIP, or deliverability.
4. Freeze a dated print-approved file instead of overwriting the research output.

## 12. Reproduction order and authoritative files

Use the following order for a fresh tax year:

1. Download the new final assessment roll with the year, final-period, and LLC-name filters.
2. Save it as a new immutable source CSV; do not overwrite the prior year.
3. Run the assessment cleaning and verify year, period, headers, row count, duplicate count, and LLC suffix distribution.
4. Initialize a fresh SQLite state database for that tax year.
5. Fetch ACRIS legals, master records, and Party Type 2 records until every eligible BBL is complete.
6. Build owner/grantee evidence with the name-score threshold.
7. Group by normalized grantee mailing address, requiring at least two LLCs and two properties.
8. Assign agent, situs, fanout, and confidence flags.
9. Run DOS enrichment against all cluster LLC names and preserve the cache.
10. Extract only conservative possible person names and require support from at least two LLC records before recommending a name.
11. Generate the unscreened research shortlist and full evidence tables.
12. Apply intermediary exclusions and one-address/one-postcard deduplication.
13. Complete postal validation, suppressions, manual review, and dated authorization.

Authoritative audit chain:

```text
fy2027_final_llc_properties.csv
  -> NYC_OWNERSHIP_EVIDENCE_PROPERTY_LEVEL.csv
  -> NYC_PROBABLE_COMMON_OWNER_CLUSTERS.csv
  -> NYC_ENTITY_MATCHES_ALL_CLUSTERS.csv
  -> NYC_POSTCARD_TARGETS_ALL_12528_NOT_PRINT_APPROVED.csv
  -> NYC_MAILING_EXCLUSIONS_AUDIT.csv
  -> NYC_MAILING_READY_DEDUPED_FILTERED.csv
```

The analysis identifies probable relationships and possible contact names. It should never be described as a definitive list of human homeowners or beneficial owners without the manual verification described above.
