import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";
import fs from "node:fs/promises";

const out = "C:/Users/ofirm/OneDrive/Documents/ChatGPT/find Multi LLC owners/Chicago/04_REPORTS_AND_WORKBOOKS/Chicago_MSA_Source_Matrix_and_Data_Dictionary.xlsx";
const wb = Workbook.create();

const BLACK = "#000000";
const WHITE = "#FFFFFF";
const LIGHT = "#E7E6E6";
const MID = "#BFBFBF";

function title(sheet, text, subtitle, endCol) {
  sheet.mergeCells(`A1:${endCol}1`);
  sheet.getRange("A1").values = [[text]];
  sheet.getRange("A1").format = { fill: BLACK, font: { bold: true, color: WHITE, size: 16 }, verticalAlignment: "center" };
  sheet.getRange("A1").format.rowHeight = 28;
  sheet.mergeCells(`A2:${endCol}2`);
  sheet.getRange("A2").values = [[subtitle]];
  sheet.getRange("A2").format = { fill: WHITE, font: { italic: true, color: BLACK, size: 10 }, wrapText: true };
  sheet.getRange("A2").format.rowHeight = 32;
}

function table(sheet, startRow, headers, rows, widths) {
  const endRow = startRow + rows.length;
  const endCol = String.fromCharCode(64 + headers.length);
  sheet.getRange(`A${startRow}:${endCol}${endRow}`).values = [headers, ...rows];
  sheet.getRange(`A${startRow}:${endCol}${startRow}`).format = { fill: BLACK, font: { bold: true, color: WHITE }, wrapText: true, verticalAlignment: "center" };
  sheet.getRange(`A${startRow}:${endCol}${endRow}`).format.borders = { top: { style: "thin", color: MID }, bottom: { style: "thin", color: MID }, left: { style: "thin", color: MID }, right: { style: "thin", color: MID }, insideHorizontal: { style: "thin", color: MID }, insideVertical: { style: "thin", color: MID } };
  sheet.getRange(`A${startRow + 1}:${endCol}${endRow}`).format = { wrapText: true, verticalAlignment: "top" };
  headers.forEach((_, i) => sheet.getRange(`${String.fromCharCode(65 + i)}:${String.fromCharCode(65 + i)}`).format.columnWidth = widths[i]);
  sheet.freezePanes.freezeRows(startRow);
  sheet.getRange(`A${startRow}:${endCol}${endRow}`).format.autofitRows();
  return { endRow, endCol };
}

const readme = wb.worksheets.add("READ ME");
title(readme, "Chicago MSA LLC Portfolio Research", "Control workbook • August 28, 2026 • governed by the generic master specification in 00_MASTER_SPECIFICATION", "F");
table(readme, 4,
  ["Item", "Status", "Location / value", "Meaning", "Owner", "Next gate"],
  [
    ["Official market", "Confirmed", "Chicago-Naperville-Elgin, IL-IN (CBSA 16980)", "13 counties in the July 2023 Census/OMB delineation", "Research", "Recheck if OMB publishes a newer delineation"],
    ["Cook adapter", "Executed", "Tax year 2026", "Official Cook County Parcel Addresses API", "Data pipeline", "Source freshness review"],
    ["LLC parcels", "71,355", "03_PROCESSED/cook_2026_llc_parcels.csv", "Normalized owner name ends in LLC; all parcel classes retained", "Data pipeline", "Evidence and suppression"],
    ["Cook clusters", "3,505", "03_PROCESSED/cook_2026_address_clusters.csv", "County-level threshold passed", "Data pipeline", "Service-provider and USPS checks"],
    ["Kendall adapter", "Executed", "Snapshot 2026-08-28", "5,043 LLC parcels; 110 county-level clusters", "Data pipeline", "Source freshness review"],
    ["Partial MSA", "3,627", "Cook + Kendall; 25 cross-county clusters", "One normalized owner-mail grouping across both completed counties", "Data pipeline", "Complete remaining 11 counties"],
    ["Mailing file", "NOT READY", "01_FINAL_OUTPUTS/...RESEARCH_ONLY.csv", "One row per candidate address; not approved for print", "Campaign QA", "Lawyer/agent/CPA suppression + CASS/DPV"],
    ["Other 11 counties", "Source discovery", "SOURCE MATRIX tab", "Access methods vary; no county is silently omitted", "Research", "Build and validate adapters"],
  ], [22, 15, 38, 54, 18, 34]);

const scope = wb.worksheets.add("MSA SCOPE");
title(scope, "Official Chicago MSA County Scope", "Source: U.S. Census Bureau July 2023 delineation workbook, list1_2023.xlsx. CBSA 16980.", "G");
const scopeRows = [
  ["Cook", "IL", "17031", "Chicago-Naperville-Schaumburg, IL", "Central", "Cook", "1"],
  ["DuPage", "IL", "17043", "Chicago-Naperville-Schaumburg, IL", "Central", "DuPage", "2"],
  ["Grundy", "IL", "17063", "Chicago-Naperville-Schaumburg, IL", "Outlying", "Grundy", "8"],
  ["McHenry", "IL", "17111", "Chicago-Naperville-Schaumburg, IL", "Central", "McHenry", "6"],
  ["Will", "IL", "17197", "Chicago-Naperville-Schaumburg, IL", "Central", "Will", "5"],
  ["DeKalb", "IL", "17037", "Elgin, IL", "Outlying", "DeKalb", "7"],
  ["Kane", "IL", "17089", "Elgin, IL", "Central", "Kane", "4"],
  ["Kendall", "IL", "17093", "Elgin, IL", "Central", "Kendall", "9"],
  ["Lake", "IL", "17097", "Lake County, IL", "Central", "Lake IL", "3"],
  ["Jasper", "IN", "18073", "Lake County-Porter County-Jasper County, IN", "Outlying", "Jasper IN", "12"],
  ["Lake", "IN", "18089", "Lake County-Porter County-Jasper County, IN", "Central", "Lake IN", "10"],
  ["Newton", "IN", "18111", "Lake County-Porter County-Jasper County, IN", "Outlying", "Newton IN", "13"],
  ["Porter", "IN", "18127", "Lake County-Porter County-Jasper County, IN", "Central", "Porter IN", "11"],
];
table(scope, 4, ["County", "State", "County FIPS", "Metropolitan division", "Central/outlying", "Adapter key", "Proposed phase"], scopeRows, [18, 10, 15, 48, 18, 18, 15]);

const sources = wb.worksheets.add("SOURCE MATRIX");
title(sources, "County Source and Access Matrix", "A county is production-ready only when owner name, owner mailing address, parcel ID, completeness, and permitted bulk access are verified.", "I");
const sourceRows = [
  ["Cook", "IL", "Official Socrata API", "Owner + taxpayer mailing fields; parcel + situs", "Yes", "Executed", "https://datacatalog.cookcountyil.gov/d/3723-97qp", "Owner/mailing fields intermittently updated per publisher", "Freshness evidence + USPS/service-provider screening"],
  ["DuPage", "IL", "ArcGIS REST + paid full database", "Parcel service; full database lists billing name/address", "Partial/paid", "Verified lead", "https://gis.dupageco.org/arcgis/rest/services/DuPage_County_IL/ParcelsWithRealEstateCC/MapServer", "REST field coverage must be tested; full database requires purchase", "Inspect layer fields and licensing; choose API or purchase"],
  ["Lake", "IL", "Interactive tax search + open GIS", "Owner/billing lookup available interactively", "Restricted", "Blocked for automated extraction", "https://tax.lakecountyil.gov/search/commonsearch.aspx?mode=realprop", "Site expressly prohibits mining/extraction", "Request authorized bulk data or FOIA; do not scrape"],
  ["Kane", "IL", "Interactive DevNet / paid GIS data", "Owner search and property tax detail", "No open bulk found", "Blocked pending acquisition", "https://www.kanecountyil.gov/Pages/gis-faq.aspx", "County states no open-data sharing policy; data available for fee", "Obtain quote/permission and field specification"],
  ["Will", "IL", "Official shapefile downloads", "Parcel geometry available", "No owner mailing verified", "Partial", "https://willcounty.gov/County-Offices/Administration/GIS-Division/Data/Vector", "Parcel download does not yet prove owner-mail fields", "Inspect shapefile; request assessment roll if absent"],
  ["McHenry", "IL", "Athena interactive GIS", "Ownership and mailing address maintained; CSV export in viewer", "Interactive/export", "Needs access test", "https://www.mchenrycountyil.gov/departments/assessments/parcel-maintenance-and-mapping", "Bulk endpoint and terms not yet verified", "Inspect service calls/terms or request bulk file"],
  ["DeKalb", "IL", "COMPASS / wEDGE interactive", "Owner search, assessment and tax details", "Interactive", "Needs authorized bulk route", "https://dekalbcounty.org/services/property-data-and-maps/", "No official bulk owner-mail download verified", "Identify service/API or submit data request"],
  ["Grundy", "IL", "County property/GIS research", "Not yet field-verified", "Unknown", "Discovery pending", "https://www.grundycountyil.gov/", "Official bulk owner-mail source not yet verified", "Contact assessor/GIS; document terms and fields"],
  ["Kendall", "IL", "Official ArcGIS FeatureServer", "owner_name, owner_addr1/2, owner_csz, PIN, situs", "Yes", "Executed", "https://maps.co.kendall.il.us/server/rest/services/Hosted/Current_Cadastral_Features/FeatureServer/1", "Live snapshot has no explicit source tax year", "Monitor freshness and retain extraction date"],
  ["Lake", "IN", "Official county parcel search / GIS request", "Assessor and tax record search", "Unknown", "Discovery pending", "https://lakecountyin.gov/services/find/", "Bulk terms and owner-mail fields not yet verified", "Request GIS/assessment extract; avoid unapproved scraping"],
  ["Porter", "IN", "ArcGIS FeatureServer lead", "Owner and mailing fields present", "Yes, stale lead", "Needs freshness validation", "https://services8.arcgis.com/AEmQjtoRrdw8PP1H/ArcGIS/rest/services/Porter_County_Parcel_with_Owner_Info/FeatureServer/0", "Layer name indicates 2022 vintage; not current enough for mail", "Locate current official service or obtain fresh extract"],
  ["Jasper", "IN", "Official GIS property site", "Public-record GIS and property cards", "Interactive", "Needs access test", "https://www.jaspercountyin.gov/residents-pages/306-gis-data-property-record-cards", "Publisher warns data may not be current", "Identify current downloadable table/service"],
  ["Newton", "IN", "Official GIS link", "GIS data portal listed", "Unknown", "Discovery pending", "https://www.newtoncounty.in.gov/", "Owner-mail fields and bulk access unverified", "Open GIS service and test schema/terms"],
];
table(sources, 4, ["County", "State", "Official access", "Relevant fields", "Bulk/API", "Status", "Official URL", "Risk / constraint", "Next action"], sourceRows, [16, 9, 30, 42, 16, 24, 58, 48, 48]);

const fields = wb.worksheets.add("COOK FIELD MAP");
title(fields, "Cook County Field Adapter", "Dataset 3723-97qp • Assessor - Parcel Addresses • current source checked August 28, 2026", "E");
const fieldRows = [
  ["pin", "parcel_id", "Parcel identifier", "Text; preserve 14 digits", "Required"],
  ["year", "tax_year", "Source tax year", "Select latest published year", "Required"],
  ["owner_address_name", "legal_owner_raw", "Owner mailing name", "Suffix filter after trim/normalization", "Required"],
  ["owner_address_full", "owner_mailing_address_raw", "Owner mailing street", "Grouping source; never substitute situs", "Required"],
  ["owner_address_city_name", "owner_mailing_city_raw", "Owner mailing city", "Grouping source", "Required"],
  ["owner_address_state", "owner_mailing_state_raw", "Owner mailing state", "Grouping source", "Required"],
  ["owner_address_zipcode_1", "owner_mailing_zip_raw", "Owner mailing ZIP", "Use five-digit base for initial key", "Required"],
  ["prop_address_full", "property_address", "Situs street", "Evidence only; prohibited as grouping substitute", "Evidence"],
  ["prop_address_city_name", "property_city", "Situs city", "Evidence only", "Evidence"],
  ["prop_address_state", "property_state", "Situs state", "Evidence only", "Evidence"],
  ["prop_address_zipcode_1", "property_zip", "Situs ZIP", "Evidence only", "Evidence"],
  ["row_id", "source_row_id", "Source row lineage", "Retain for audit", "Required"],
];
table(fields, 4, ["Source field", "Canonical field", "Meaning", "Rule", "Use"], fieldRows, [28, 34, 34, 54, 16]);

const dict = wb.worksheets.add("OUTPUT DICTIONARY");
title(dict, "Chicago Output Map and Column Dictionary", "Final output remains empty until every automated-mail gate is passed. Research outputs are separated from printable files.", "F");
const dictRows = [
  ["03_PROCESSED/cook_2026_llc_parcels.csv", "parcel_id", "One row per LLC-owned parcel", "Cook PIN", "Traceable source parcel", "Research"],
  ["03_PROCESSED/cook_2026_llc_parcels.csv", "legal_owner_normalized", "Normalized legal owner ending in LLC", "Uppercase; punctuation normalized", "Distinct LLC count", "Research"],
  ["03_PROCESSED/cook_2026_llc_parcels.csv", "owner_mailing_address_key", "Normalized owner-mail grouping key", "Street|city|state|ZIP5", "Portfolio correlation", "Research"],
  ["03_PROCESSED/cook_2026_llc_parcels.csv", "property_address", "Parcel situs", "Never used as grouping key", "Evidence/map", "Research"],
  ["03_PROCESSED/cook_2026_address_clusters.csv", "distinct_llc_count", "Different normalized LLCs at address", ">=2", "Qualification", "Research"],
  ["03_PROCESSED/cook_2026_address_clusters.csv", "property_count", "Distinct PINs at address", ">=2", "Qualification", "Research"],
  ["03_PROCESSED/cook_2026_address_clusters.csv", "llc_names", "LLC evidence list", "Pipe-delimited", "Review", "Research"],
  ["03_PROCESSED/kendall_20260828_llc_parcels.csv", "source_snapshot_date", "Kendall extraction date", "YYYY-MM-DD", "Freshness lineage", "Research"],
  ["03_PROCESSED/chicago_msa_partial_...csv", "county_count", "Counties represented at address", "Integer", "Cross-county correlation", "Research"],
  ["03_PROCESSED/chicago_msa_partial_...csv", "coverage_status", "Completed county coverage", "Cook and Kendall only", "Prevents false full-MSA claim", "Research"],
  ["01_FINAL_OUTPUTS/...RESEARCH_ONLY.csv", "service_provider_review", "Lawyer/agent/CPA/filing-service gate", "Must equal PASS for mail", "Suppression", "Not passed"],
  ["01_FINAL_OUTPUTS/...RESEARCH_ONLY.csv", "usps_cass_dpv_status", "Postal validation", "Must equal DELIVERABLE", "Mail eligibility", "Not run"],
  ["Future mailing-ready file", "mailing_status", "Final campaign decision", "MAIL_READY only after all gates", "Print control", "Not created"],
];
table(dict, 4, ["File", "Column", "Definition", "Rule / format", "Purpose", "Current state"], dictRows, [54, 34, 48, 44, 28, 22]);

for (const sh of wb.worksheets.items) {
  sh.showGridlines = false;
}

const xlsx = await SpreadsheetFile.exportXlsx(wb);
await xlsx.save(out);
const qa = "C:/Users/ofirm/OneDrive/Documents/ChatGPT/find Multi LLC owners/Chicago/99_SUPPORT_FILES/qa_source_matrix";
const renders = [
  ["READ ME", "A1:F13", "read_me.png"],
  ["MSA SCOPE", "A1:G17", "msa_scope.png"],
  ["SOURCE MATRIX", "A1:I17", "source_matrix.png"],
  ["COOK FIELD MAP", "A1:E16", "cook_field_map.png"],
  ["OUTPUT DICTIONARY", "A1:F17", "output_dictionary.png"],
];
for (const [sheetName, range, file] of renders) {
  const image = await wb.render({ sheetName, range, scale: 1 });
  await fs.writeFile(`${qa}/${file}`, new Uint8Array(await image.arrayBuffer()));
}
console.log(out);
