import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve("Chicago");
const processed = path.join(root, "03_PROCESSED");
const finalDir = path.join(root, "01_FINAL_OUTPUTS");
const outputPath = path.join(root, "04_REPORTS_AND_WORKBOOKS", "Chicago_Partial_MSA_Service_Provider_Screening_20260828.xlsx");

const allCsv = await fs.readFile(path.join(processed, "chicago_msa_partial_service_screen_all_20260828.csv"), "utf8");
const passCsv = await fs.readFile(path.join(finalDir, "chicago_msa_partial_PASS_SERVICE_SCREEN_PREPOSTAL_20260828.csv"), "utf8");
const suppressCsv = await fs.readFile(path.join(finalDir, "chicago_msa_partial_SUPPRESS_SERVICE_PROVIDERS_20260828.csv"), "utf8");
const reviewCsv = await fs.readFile(path.join(finalDir, "chicago_msa_partial_MANUAL_REVIEW_20260828.csv"), "utf8");
const allDataRowCount = allCsv.trim().split(/\r?\n/).length - 1;
const allLastRow = allDataRowCount + 1;

const workbook = await Workbook.fromCSV(allCsv, { sheetName: "All Screened Clusters" });
await workbook.fromCSV(passCsv, { sheetName: "Pass Service Screen" });
await workbook.fromCSV(suppressCsv, { sheetName: "Suppress" });
await workbook.fromCSV(reviewCsv, { sheetName: "Manual Review" });

const summary = workbook.worksheets.add("Summary");
const definitions = workbook.worksheets.add("Definitions");

summary.showGridLines = false;
summary.getRange("A1:H1").merge();
summary.getRange("A1").values = [["CHICAGO PARTIAL-MSA LLC ADDRESS SCREENING"]];
summary.getRange("A2:H2").merge();
summary.getRange("A2").values = [["Cook + Kendall counties only | Service-provider screen completed 2026-08-28 | Postal validation not run"]];
summary.getRange("A4:D4").values = [["Disposition", "Address clusters", "Distinct LLC references", "Property references"]];
summary.getRange("A5:A8").values = [["PASS_SERVICE_SCREEN"], ["SUPPRESS_SERVICE_PROVIDER"], ["MANUAL_REVIEW"], ["TOTAL"]];
summary.getRange("B5").formulas = [[`=COUNTIF('All Screened Clusters'!$L$2:$L$${allLastRow},A5)`]];
summary.getRange("B5:B7").fillDown();
summary.getRange("B8").formulas = [["=SUM(B5:B7)"]];
summary.getRange("C5").formulas = [[`=SUMIF('All Screened Clusters'!$L$2:$L$${allLastRow},A5,'All Screened Clusters'!$F$2:$F$${allLastRow})`]];
summary.getRange("C5:C7").fillDown();
summary.getRange("C8").formulas = [["=SUM(C5:C7)"]];
summary.getRange("D5").formulas = [[`=SUMIF('All Screened Clusters'!$L$2:$L$${allLastRow},A5,'All Screened Clusters'!$G$2:$G$${allLastRow})`]];
summary.getRange("D5:D7").fillDown();
summary.getRange("D8").formulas = [["=SUM(D5:D7)"]];

summary.getRange("A10:H10").merge();
summary.getRange("A10").values = [["CAMPAIGN DECISION"]];
summary.getRange("A11:H14").values = [
  ["PASS_SERVICE_SCREEN", "Eligible for the next postal-validation step; not yet mail-ready.", null, null, null, null, null, null],
  ["SUPPRESS_SERVICE_PROVIDER", "Exclude from campaign because the address is a confirmed or directly signaled lawyer, CPA/accountant, registered agent, broker, filing service, or property manager.", null, null, null, null, null, null],
  ["MANUAL_REVIEW", "Hold. Address format, mailbox/suite use, or five-plus LLC collision requires human confirmation.", null, null, null, null, null, null],
  ["USPS status", "CASS/DPV/NCOA has not been run. None of these files should be sent to a printer yet.", null, null, null, null, null, null],
];
summary.getRange("B11:H14").merge(true);

summary.getRange("A16:H16").merge();
summary.getRange("A16").values = [["IMPORTANT SCOPE NOTE"]];
summary.getRange("A17:H19").merge();
summary.getRange("A17").values = [["This is not the complete Chicago MSA. It covers Cook and Kendall counties only. A shared mailing address is treated as a portfolio lead, not proof of common beneficial ownership. The PASS file is a service-provider-screened, pre-postal candidate list; USPS-certified address validation and the remaining 11 MSA counties are still outstanding."]];

definitions.showGridLines = false;
definitions.getRange("A1:E1").merge();
definitions.getRange("A1").values = [["SCREENING RULES AND COLUMN MAP"]];
definitions.getRange("A3:E3").values = [["Rule order", "Condition", "Disposition", "Reason code", "Meaning"]];
definitions.getRange("A4:E9").values = [
  [1, "Exact researched address is a lawyer, accountant/CPA, registered agent, real-estate broker/agent, filing service, or third-party property manager", "SUPPRESS", "CONFIRMED_SERVICE_PROVIDER_ADDRESS", "Do not mail"],
  [2, "LLC-name cluster contains a direct professional-service term", "SUPPRESS", "DIRECT_PROFESSIONAL_NAME_SIGNAL", "Do not mail unless later disproved"],
  [3, "Missing ZIP", "MANUAL_REVIEW", "MISSING_ZIP", "Incomplete postal address"],
  [4, "PO Box/lockbox or suite/unit/mailbox", "MANUAL_REVIEW", "PO_BOX_OR_LOCKBOX / SUITE_UNIT_OR_MAILBOX", "Possible owner office or professional intermediary"],
  [5, "Five or more distinct LLCs at unresolved address", "MANUAL_REVIEW", "HIGH_ADDRESS_COLLISION_5_PLUS_LLCS", "Collision risk requires evidence"],
  [6, "Two to four LLCs, simple street address, no direct service signal", "PASS_SERVICE_SCREEN", "LOW_COLLISION_NO_SERVICE_SIGNAL", "Proceed only to postal validation"],
];
definitions.getRange("A11:E11").values = [["Column", "Description", "Source/derivation", "Campaign use", "Notes"]];
definitions.getRange("A12:E22").values = [
  ["screening_address_key_v2", "Normalized shared mailing-address key", "Address standardization", "Deduplication key", "Street suffix and common suite variants consolidated"],
  ["mail_address/city/state/zip", "Owner mailing address from tax records", "Cook/Kendall source data", "Postcard destination after validation", "Not property address unless source happens to match"],
  ["distinct_llc_count", "Unique LLC owner names at the mailing address", "Distinct LLC-name count", "Portfolio-size signal", "Different LLCs, not one LLC repeated"],
  ["property_count", "Unique parcel/property references", "Distinct parcel-key count", "Scale signal", "Can exceed LLC count"],
  ["counties", "Covered counties contributing parcels", "Source data", "Coverage context", "Current output: Cook and/or Kendall"],
  ["llc_names", "All LLC owner names in the cluster", "Tax-owner names", "Entity review", "Separated with vertical bars"],
  ["parcel_keys", "County-qualified parcel identifiers", "Tax parcel records", "Audit trail", "Separated with vertical bars"],
  ["screening_status/reason", "Service-provider disposition and rule", "Screening logic + web evidence", "Campaign gate", "PASS is pre-postal only"],
  ["evidence_summary/url/confidence", "Why a researched address was classified", "Public source", "Auditability", "Blank where research has not been performed"],
  ["usps_cass_dpv_status", "Postal deliverability validation", "USPS or certified vendor", "Required final gate", "Currently NOT_RUN"],
  ["mailing_status", "Overall readiness", "Derived", "Printer handoff gate", "Currently NOT_MAIL_READY"],
];

const dataSheetNames = ["All Screened Clusters", "Pass Service Screen", "Suppress", "Manual Review"];
for (const name of dataSheetNames) {
  const sheet = workbook.worksheets.getItem(name);
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  sheet.freezePanes.freezeColumns(2);
  const used = sheet.getUsedRange();
  used.format.font = { name: "Aptos", size: 9, color: "#000000" };
  used.format.wrapText = false;
  sheet.getRange("A1:W1").format = {
    fill: "#000000",
    font: { name: "Aptos", size: 9, bold: true, color: "#FFFFFF" },
    wrapText: true,
    verticalAlignment: "center",
    borders: { preset: "all", style: "thin", color: "#808080" },
  };
  sheet.getRange("A:W").format.rowHeight = 18;
  sheet.getRange("A:A").format.columnWidth = 34;
  sheet.getRange("B:B").format.columnWidth = 25;
  sheet.getRange("C:E").format.columnWidth = 13;
  sheet.getRange("F:H").format.columnWidth = 12;
  sheet.getRange("I:I").format.columnWidth = 18;
  sheet.getRange("J:K").format.columnWidth = 45;
  sheet.getRange("L:N").format.columnWidth = 25;
  sheet.getRange("O:P").format.columnWidth = 42;
  sheet.getRange("Q:W").format.columnWidth = 22;
}

for (const sheet of [summary, definitions]) {
  sheet.getUsedRange().format.font = { name: "Aptos", size: 10, color: "#000000" };
  sheet.getUsedRange().format.wrapText = true;
}
summary.getRange("A1:H1").format = { fill: "#000000", font: { name: "Aptos Display", size: 18, bold: true, color: "#FFFFFF" }, rowHeight: 30 };
summary.getRange("A2:H2").format = { fill: "#E7E6E6", font: { name: "Aptos", size: 10, italic: true, color: "#000000" }, rowHeight: 28 };
summary.getRange("A4:D4").format = { fill: "#000000", font: { bold: true, color: "#FFFFFF" }, borders: { preset: "all", style: "thin", color: "#808080" } };
summary.getRange("A5:D8").format.borders = { preset: "all", style: "thin", color: "#BFBFBF" };
summary.getRange("A8:D8").format.font = { bold: true, color: "#000000" };
summary.getRange("A10:H10").format = { fill: "#000000", font: { bold: true, color: "#FFFFFF" } };
summary.getRange("A11:H14").format.borders = { preset: "all", style: "thin", color: "#BFBFBF" };
summary.getRange("A16:H16").format = { fill: "#000000", font: { bold: true, color: "#FFFFFF" } };
summary.getRange("A17:H19").format = { fill: "#F2F2F2", font: { bold: true, color: "#000000" }, verticalAlignment: "top", borders: { preset: "outside", style: "thin", color: "#808080" } };
summary.getRange("A:A").format.columnWidth = 27;
summary.getRange("B:D").format.columnWidth = 20;
summary.getRange("E:H").format.columnWidth = 16;
summary.freezePanes.freezeRows(2);

definitions.getRange("A1:E1").format = { fill: "#000000", font: { name: "Aptos Display", size: 17, bold: true, color: "#FFFFFF" }, rowHeight: 30 };
definitions.getRange("A3:E3").format = { fill: "#000000", font: { bold: true, color: "#FFFFFF" } };
definitions.getRange("A11:E11").format = { fill: "#000000", font: { bold: true, color: "#FFFFFF" } };
definitions.getRange("A3:E22").format.borders = { preset: "all", style: "thin", color: "#BFBFBF" };
definitions.getRange("A:A").format.columnWidth = 20;
definitions.getRange("B:B").format.columnWidth = 55;
definitions.getRange("C:E").format.columnWidth = 30;
definitions.freezePanes.freezeRows(3);

await fs.mkdir(path.dirname(outputPath), { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);

const inspection = await workbook.inspect({ kind: "region", sheetId: "Summary", range: "A1:H19", maxChars: 5000 });
console.log(inspection.ndjson);
const preview = await workbook.render({ sheetName: "Summary", autoCrop: "all", scale: 1, format: "png" });
await fs.writeFile(path.join(root, "99_SUPPORT_FILES", "Chicago_Service_Screening_Summary_preview.png"), new Uint8Array(await preview.arrayBuffer()));
const previewRanges = {
  "All Screened Clusters": "A1:W12",
  "Pass Service Screen": "A1:W12",
  "Suppress": "A1:W12",
  "Manual Review": "A1:W12",
  "Definitions": "A1:E22",
};
for (const [sheetName, range] of Object.entries(previewRanges)) {
  const sheetPreview = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  const safeName = sheetName.replaceAll(" ", "_");
  await fs.writeFile(path.join(root, "99_SUPPORT_FILES", `Chicago_Service_Screening_${safeName}_preview.png`), new Uint8Array(await sheetPreview.arrayBuffer()));
}
const formulaErrors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(formulaErrors.ndjson);
console.log(outputPath);
