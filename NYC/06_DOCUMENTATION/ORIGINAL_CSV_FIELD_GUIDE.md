# NYC Multi-LLC Research — CSV Field Guide

This guide explains the purpose and columns of every CSV file in the project. Fields created by our analysis are labeled as such; they are not official ownership determinations.

## Important distinctions

- **Property address / situs address:** the physical location of the assessed property.
- **Deed-party mailing address:** the address supplied for a grantee on an ACRIS deed. This is the main pre-DOS signal used to group differently named LLCs.
- **Service-of-process address:** the address maintained by NY Department of State for delivering legal documents to an entity.
- **Normalized values:** cleaned uppercase text used for matching. Punctuation and minor formatting differences are removed.
- A shared address is a research signal, not proof that the LLCs have the same beneficial owner.

## 1. `fy2027_llc_properties.csv`

Purpose: preliminary NYC FY2027 property-assessment extract limited to owner names that appear to be LLCs.

| Field | Meaning |
|---|---|
| `parid` | NYC parcel identifier. In this extract it is the 10-digit borough-block-lot identifier. |
| `boro` | Borough code: 1 Manhattan, 2 Bronx, 3 Brooklyn, 4 Queens, 5 Staten Island. |
| `block` | NYC tax block number. |
| `lot` | NYC tax lot number. |
| `year` | Assessment/fiscal year. |
| `owner` | Owner name shown on the assessment roll; normally the LLC name, not a person behind it. |
| `bldg_class` | NYC building-classification code. |
| `curtaxclass` | Current tax-class code in this version of the assessment data. |
| `housenum_lo` | Beginning or lower house number. |
| `housenum_hi` | Ending or upper house number when the property uses a number range. |
| `street_name` | Property street name. |
| `aptno` | Apartment or unit identifier, when supplied. |
| `zip_code` | Property ZIP code. |
| `units` | Number of units reported for the tax lot. |
| `curmkttot` | Current total market value in this version of the roll. |
| `curacttot` | Current total actual assessed value in this version of the roll. |

## 2. `fy2027_final_llc_properties.csv`

Purpose: final NYC FY2027 property-assessment extract limited to apparent LLC owners. The copy at `data/input/fy2027_final_llc_properties.csv` has the same layout and is the pipeline input.

| Field | Meaning |
|---|---|
| `parid` | NYC parcel identifier; the 10-digit borough-block-lot identifier in this extract. |
| `boro` | Borough code: 1 Manhattan, 2 Bronx, 3 Brooklyn, 4 Queens, 5 Staten Island. |
| `block` | NYC tax block number. |
| `lot` | NYC tax lot number. |
| `year` | Assessment/fiscal year. |
| `period` | Assessment-roll period supplied by NYC. |
| `owner` | Owner name shown on the final assessment roll; normally the legal LLC name. |
| `bldg_class` | NYC building-classification code. |
| `fintaxclass` | Final tax-class code. |
| `housenum_lo` | Beginning or lower house number. |
| `housenum_hi` | Ending or upper house number when applicable. |
| `street_name` | Property street name. |
| `aptno` | Apartment or unit identifier, when supplied. |
| `zip_code` | Property ZIP code. |
| `units` | Number of units reported for the tax lot. |
| `finmkttot` | Final total market value. |
| `finacttot` | Final total actual assessed value. |

## 3. `processed/fy2027_final_llc_properties_clean.csv`

Purpose: cleaned, analysis-ready version of the final assessment extract with a constructed BBL, borough name, normalized LLC name, and formatted property address.

| Field | Meaning |
|---|---|
| `parid` | Original parcel identifier. |
| `bbl` | Constructed 10-digit borough-block-lot key used to join the property to ACRIS. |
| `borough` | Borough name instead of the numeric borough code. |
| `block` | NYC tax block number. |
| `lot` | NYC tax lot number. |
| `owner` | LLC owner name exactly as listed in the assessment data. |
| `owner_normalized` | Cleaned LLC name used for grouping and name comparisons. |
| `property_address` | Constructed physical property address using house number, street, apartment, and ZIP. |
| `bldg_class` | NYC building-classification code. |
| `fintaxclass` | Final tax-class code. |
| `units` | Reported number of units. |
| `finmkttot` | Final total market value. |
| `finacttot` | Final total actual assessed value. |

## 4. `processed/llc_owner_summary_all.csv`

Purpose: one row for every distinct normalized LLC name, summarizing all properties listed under that exact cleaned name.

| Field | Meaning |
|---|---|
| `owner_normalized` | Cleaned LLC name used as the grouping key. |
| `owner_as_listed` | A representative original spelling from the assessment roll. |
| `property_records` | Count of distinct assessment parcel records associated with the LLC name. |
| `tax_lots` | Count of distinct BBL tax lots associated with the LLC name. |
| `borough_count` | Number of boroughs in which the LLC name appears. |
| `boroughs` | Comma-separated borough names in which it appears. |
| `total_units` | Sum of reported units across the LLC's assessment records. |
| `total_market_value` | Sum of final market values across the LLC's records. |
| `total_assessed_value` | Sum of final assessed values across the LLC's records. |
| `multiple_properties` | `True` when the same normalized LLC name has more than one property record. |

## 5. `processed/llc_multi_property_summary.csv`

Purpose: filtered version of `llc_owner_summary_all.csv` containing only normalized LLC names with more than one property record.

| Field | Meaning |
|---|---|
| `owner_normalized` | Cleaned LLC name used as the grouping key. |
| `owner_as_listed` | Representative original spelling of the LLC name. |
| `property_records` | Number of distinct assessment parcels listed under that LLC name. |
| `tax_lots` | Number of distinct BBL tax lots. |
| `borough_count` | Number of boroughs represented. |
| `boroughs` | Borough names represented. |
| `total_units` | Sum of reported units. |
| `total_market_value` | Sum of final market values. |
| `total_assessed_value` | Sum of final assessed values. |
| `multiple_properties` | Always `True` in this filtered file. |

## 6. `processed/shared_property_address_candidates.csv`

Purpose: early-stage candidates where different LLC names appear at the same **physical property address** in the assessment roll. These are the 816 shared-property-address candidates. This is not the same as grouping LLCs by owner mailing address.

| Field | Meaning |
|---|---|
| `property_address` | Shared physical/situs property address used as the grouping key. |
| `distinct_llc_names` | Number of different normalized LLC names found at that property address. |
| `property_records` | Number of distinct assessment parcel records at the address. |
| `llc_names` | Pipe-separated list of normalized LLC names at the address. |
| `boroughs` | Borough or boroughs represented. |
| `total_market_value` | Sum of final market values for the grouped records. |

## 7. `processed/metrics.csv`

Purpose: compact counts describing the original assessment analysis.

| Field | Meaning |
|---|---|
| `metric` | Name of the measurement. |
| `value` | Calculated count or result for that measurement. |

## 8. `data/output/ownership_evidence.csv`

Purpose: detailed property-by-property evidence joining the assessment owner to the latest relevant ACRIS deed and grantee party. This is the audit trail behind the probable common-owner clusters.

| Field | Meaning |
|---|---|
| `parid` | Assessment parcel identifier. |
| `bbl` | Borough-block-lot key used to connect the assessed property to ACRIS. |
| `property_address` | Physical/situs address of the property. |
| `assessment_owner` | LLC owner name as listed on the NYC assessment roll. |
| `owner_normalized` | Cleaned assessment-owner name. |
| `document_id` | Unique ACRIS document identifier for the deed. |
| `doc_type` | ACRIS document type, such as `DEED`. |
| `recorded_datetime` | Date and time the document was recorded in ACRIS. |
| `grantee_name` | Buyer/grantee name listed on the deed. |
| `grantee_normalized` | Cleaned grantee name used for comparison with the assessment owner. |
| `grantee_address` | Mailing address listed for the deed grantee. |
| `address_normalized` | Cleaned grantee mailing address used to group different LLC names. This is the main pre-DOS common-group key. |
| `name_match_score` | Internal 0–100 similarity score between assessment owner and deed grantee; higher is stronger. |
| `agent_marker` | Internal 1/0 flag indicating that the address contains an agent/intermediary pattern; `1` means extra caution. |

## 9. `data/output/probable_common_owner_clusters.csv`

Purpose: one row per shared normalized ACRIS grantee mailing address when that address connects at least two different LLC names and at least two properties.

| Field | Meaning |
|---|---|
| `confidence` | Internal `High`, `Medium`, or `Low` research rating based on name quality, address type, group size, and risk markers. Not an official ownership conclusion. |
| `distinct_llc_names` | Number of different normalized LLC names in the address group. |
| `distinct_bbls` | Number of distinct tax lots/properties in the group. |
| `property_records` | Number of distinct assessment parcel records in the group. |
| `deed_party_address` | Human-readable ACRIS grantee mailing address; multiple formatting variants may be separated by ` | `. |
| `llc_names` | Pipe-separated list of normalized LLC names linked to the shared mailing address. |
| `property_addresses` | Pipe-separated list of physical property addresses owned by those LLCs. |
| `minimum_name_match` | Lowest LLC-to-grantee name-match score among the evidence rows in the group. |
| `agent_address_marker` | `1` when an agent/intermediary address pattern was detected; otherwise `0`. |
| `situs_address_marker` | `1` when the shared mailing address appears to be the property/situs address for most records; otherwise `0`. This helps identify condominium or building-address groupings. |
| `address_normalized` | Cleaned ACRIS grantee mailing address and the main key connecting the LLCs in the cluster. |

## 10. `data/output/dos_enrichment_400/dos_entity_matches.csv`

Purpose: one row per LLC in the 400-address pilot, showing the selected NY DOS active-entity match and its supporting fields.

| Field | Meaning |
|---|---|
| `cluster_id` | Internal pilot-group identifier connecting this LLC to its row in the mailing shortlist. |
| `tier_llc_count` | Original group size: 3, 4, 5, or 6 LLCs. |
| `acris_shared_mailing_address` | Shared ACRIS deed-party mailing address that created the group. |
| `llc_name_normalized` | Cleaned LLC name from the NYC assessment/ACRIS analysis. |
| `assessment_name_used` | Original assessment spelling used to search the DOS dataset. |
| `match_status` | Result of the DOS match: address-corroborated active match, active name match, ambiguous match, or no active match. |
| `candidate_count` | Number of active DOS entities matching the normalized LLC name. More than one may require review. |
| `address_match_score` | Internal DOS-to-ACRIS address score: 3 exact cleaned address, 2 matching street and ZIP, 1 matching ZIP only, 0 no address agreement. |
| `dos_id` | Official NY Department of State identifier for the matched legal entity. |
| `current_entity_name` | Current entity name in the DOS active-entity dataset. |
| `initial_dos_filing_date` | Entity's original DOS filing/formation date. |
| `county` | County recorded for the entity by DOS. |
| `jurisdiction` | State or country under whose laws the entity was formed. |
| `entity_type` | DOS legal-entity type, such as domestic or foreign limited liability company. |
| `dos_process_name` | Name on the DOS service-of-process record. It may be the LLC, a person, an attorney, or a service company. |
| `dos_process_address` | DOS service-of-process mailing address. |
| `chairman_name` | Chairman/CEO name when present in the DOS dataset; usually blank for LLCs and not proof of LLC ownership. |
| `chairman_address` | Address associated with the chairman/CEO field when present. |
| `registered_agent_name` | Registered-agent name maintained by DOS. A registered agent is not necessarily an owner. |
| `registered_agent_address` | Registered-agent address. |
| `location_name` | Name line for a physical-location record when DOS supplies one. |
| `location_address` | Physical-location address when DOS supplies one. |
| `email_from_dos` | Reserved email field; blank because the official dataset does not supply email addresses. |
| `phone_from_dos` | Reserved phone field; blank because the official dataset does not supply phone numbers. |
| `source_url` | URL of the official NY DOS Active Corporations dataset. |

## 11. `data/output/dos_enrichment_400/dos_mailing_shortlist_400.csv`

Purpose: one mailing row per selected shared-address group for the 400-postcard pilot.

| Field | Meaning |
|---|---|
| `cluster_id` | Internal unique identifier for the pilot group; connects to `dos_entity_matches.csv`. |
| `mailing_tier` | Number of LLCs in the target group: 3, 4, 5, or 6. |
| `recommended_addressee` | Suggested postcard addressee. A person's name is used only when supported across at least two LLC records; otherwise `PROPERTY OWNER`. |
| `possible_named_addressee` | Best plausible person name found in DOS process records, even if support is insufficient for recommendation. Treat cautiously. |
| `possible_addressee_support_count` | Number of LLC records in the group carrying that possible person name. |
| `mailing_address` | Single address selected for the postcard. |
| `mailing_address_source` | Whether the mailing address came from ACRIS alone or was corroborated by DOS. |
| `distinct_llcs` | Number of distinct LLC names in the group. |
| `distinct_properties` | Number of distinct BBL properties in the group. |
| `property_records` | Number of assessment parcel records represented. |
| `llc_names` | Pipe-separated list of LLC names in the group. |
| `property_addresses` | Pipe-separated list of physical property addresses in the group. |
| `dos_llcs_matched` | Number of the group's LLCs matched to active DOS entities. |
| `dos_match_rate` | `dos_llcs_matched` divided by `distinct_llcs`. |
| `dos_address_corroborated_llcs` | Number of LLCs whose DOS service address agrees with the shared ACRIS mailing address. |
| `largest_shared_dos_address_count` | Largest number of matched LLCs sharing one normalized DOS service address within the group. |
| `dos_corroboration` | Internal summary: strong address corroboration, shared DOS address, active-name matches only, or needs manual review. |
| `email_phone_available_from_dos` | `No`; the official DOS dataset does not provide these fields. |
| `minimum_acris_name_match` | Lowest assessment-owner-to-ACRIS-grantee name score in the group. |
| `source_url` | URL of the official NY DOS dataset. |

## 12. Complete DOS enrichment files

The complete counterparts are stored in `data/output/dos_enrichment_all/`:

- `dos_entity_matches_all_clusters.csv`
- `dos_mailing_shortlist_all_clusters.csv`

They use the same DOS and mailing fields described above, but cover all 12,528 candidate clusters rather than the 400-record pilot. The complete files also retain these original research-quality fields:

| Field | Meaning |
|---|---|
| `original_confidence` | Original `High`, `Medium`, or `Low` ACRIS cluster rating before DOS enrichment. |
| `agent_address_marker` | `1` when the original ACRIS address was flagged as agent/intermediary-like; otherwise `0`. Present in the complete mailing file. |
| `situs_address_marker` | `1` when the original shared mailing address appeared to be the physical property address for most records; otherwise `0`. Present in the complete mailing file. |

## Quick key reference

| Task | Best field/key |
|---|---|
| Identify one property | `bbl` or `parid` |
| Identify one recorded deed | `document_id` |
| Group the same cleaned LLC name | `owner_normalized` |
| Connect different LLCs before DOS | `address_normalized` from ACRIS deed parties |
| Connect the two DOS pilot CSV files | `cluster_id` |
| Identify one official NY legal entity | `dos_id` |
