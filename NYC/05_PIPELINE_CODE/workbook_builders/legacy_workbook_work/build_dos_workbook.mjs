import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const inputDir = process.argv[2];
const outputPath = process.argv[3];
if (!inputDir || !outputPath) {
  throw new Error("Usage: node build_dos_workbook.mjs <input-dir> <output-xlsx>");
}

const payload = JSON.parse(await fs.readFile(path.join(inputDir, "workbook_data.json"), "utf8"));
const mailingLastRow = payload.mailing_rows.length + 1;
const entityLastRow = payload.entity_rows.length + 1;
const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
const mailing = workbook.worksheets.add("Mailing Shortlist");
const entities = workbook.worksheets.add("DOS Entity Matches");
const method = workbook.worksheets.add("Methodology");

const navy = "#17365D";
const teal = "#0F6B78";
const lightBlue = "#DCE6F1";
const lightTeal = "#DDEBF7";
const lightGreen = "#E2F0D9";
const lightAmber = "#FFF2CC";
const lightRed = "#FCE4D6";
const gray = "#666666";
const border = "#C9D3DF";

function cleanCell(value) {
  if (typeof value !== "string") return value;
  return value.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\uFFFE\uFFFF]/g, " ");
}

function styleTitle(sheet, range, text) {
  sheet.getRange(range).merge();
  const cell = sheet.getRange(range.split(":")[0]);
  cell.values = [[text]];
  cell.format = {
    fill: navy,
    font: { bold: true, color: "#FFFFFF", size: 18 },
    verticalAlignment: "center",
  };
  sheet.getRange(range).format.rowHeight = 32;
}

function styleHeader(range) {
  range.format = {
    fill: teal,
    font: { bold: true, color: "#FFFFFF" },
    verticalAlignment: "center",
    wrapText: true,
    borders: { preset: "outside", style: "thin", color: border },
  };
  range.format.rowHeight = 30;
}

// Summary
summary.showGridLines = false;
styleTitle(summary, "A1:F1", "NYC Multi-LLC Research — Complete NY DOS Enrichment");
summary.getRange("A2:F2").merge();
summary.getRange("A2").values = [["All 12,528 ACRIS shared-address candidate clusters across every confidence level and group size"]];
summary.getRange("A2").format = { fill: lightBlue, font: { italic: true, color: navy }, wrapText: true };
summary.getRange("A4:B4").values = [["Key statistic", "Result"]];
styleHeader(summary.getRange("A4:B4"));
summary.getRange("A5:A11").values = [
  ["Mailing addresses"],
  ["LLC rows checked against DOS"],
  ["Active DOS matches"],
  ["DOS match rate"],
  ["Strong DOS/address-corroborated groups"],
  ["Groups with a supported named addressee"],
  ["Email or phone records supplied by DOS"],
];
summary.getRange("B5:B11").formulas = [
  [`=COUNTA('Mailing Shortlist'!$A$2:$A$${mailingLastRow})`],
  [`=COUNTA('DOS Entity Matches'!$E$2:$E$${entityLastRow})`],
  [`=SUM('Mailing Shortlist'!$R$2:$R$${mailingLastRow})`],
  ["=B7/B6"],
  [`=COUNTIF('Mailing Shortlist'!$V$2:$V$${mailingLastRow},\"Strong DOS address corroboration\")`],
  [`=COUNTIF('Mailing Shortlist'!$H$2:$H$${mailingLastRow},\"<>PROPERTY OWNER\")`],
  [`=COUNTIF('Mailing Shortlist'!$Y$2:$Y$${mailingLastRow},\"Yes\")`],
];
summary.getRange("B8").format.numberFormat = "0.0%";
summary.getRange("A5:A11").format = { fill: "#F5F7FA", font: { color: navy } };
summary.getRange("B5:B11").format = { font: { bold: true, color: navy }, horizontalAlignment: "right" };
summary.getRange("A11:B11").format.fill = lightAmber;
summary.getRange("A13:E13").values = [["Original confidence", "Groups", "DOS matches", "LLC rows", "Match rate"]];
styleHeader(summary.getRange("A13:E13"));
summary.getRange("A14:A16").values = [["High"], ["Medium"], ["Low"]];
for (let row = 14; row <= 16; row += 1) {
  summary.getRange(`B${row}`).formulas = [[`=COUNTIF('Mailing Shortlist'!$B$2:$B$${mailingLastRow},A${row})`]];
  summary.getRange(`C${row}`).formulas = [[`=SUMIF('Mailing Shortlist'!$B$2:$B$${mailingLastRow},A${row},'Mailing Shortlist'!$R$2:$R$${mailingLastRow})`]];
  summary.getRange(`D${row}`).formulas = [[`=SUMIF('Mailing Shortlist'!$B$2:$B$${mailingLastRow},A${row},'Mailing Shortlist'!$M$2:$M$${mailingLastRow})`]];
  summary.getRange(`E${row}`).formulas = [[`=C${row}/D${row}`]];
}
summary.getRange("A17:D17").values = [["Total", null, null, null]];
summary.getRange("B17:D17").formulas = [["=SUM(B14:B16)", "=SUM(C14:C16)", "=SUM(D14:D16)"]];
summary.getRange("E17").formulas = [["=C17/D17"]];
summary.getRange("A17:E17").format = { fill: lightBlue, font: { bold: true, color: navy }, borders: { preset: "doubleBottom", style: "thin", color: navy } };
summary.getRange("E14:E17").format.numberFormat = "0.0%";
summary.getRange("A20:B20").values = [["DOS corroboration category", "Groups"]];
styleHeader(summary.getRange("A20:B20"));
summary.getRange("A21:A24").values = [
  ["Strong DOS address corroboration"],
  ["Shared DOS address"],
  ["Active-name matches only"],
  ["Needs manual review"],
];
for (let row = 21; row <= 24; row += 1) {
  summary.getRange(`B${row}`).formulas = [[`=COUNTIF('Mailing Shortlist'!$V$2:$V$${mailingLastRow},A${row})`]];
}
summary.getRange("A26:F26").merge();
summary.getRange("A26").values = [["Important interpretation"]];
summary.getRange("A26").format = { fill: lightAmber, font: { bold: true, color: "#7F6000" } };
summary.getRange("A27:F30").merge();
summary.getRange("A27").values = [[
  "A DOS match confirms an active legal entity and provides service-of-process or agent information; it does not prove that the LLCs have the same beneficial owner. Email and phone are not fields in this DOS dataset. A named addressee is recommended only when the same plausible person appears for at least two LLCs in a group."
]];
summary.getRange("A27").format = { wrapText: true, verticalAlignment: "top", fill: "#FFF9E6", font: { color: "#7F6000" } };
summary.getRange("A32:F32").merge();
summary.getRange("A32").values = [["Source: https://data.ny.gov/Economic-Development/Active-Corporations-Beginning-1800/n9v6-gdp6"]];
summary.getRange("A32").format = { font: { color: "#0563C1", size: 9 }, wrapText: true };
summary.getRange("A1:F32").format.font.name = "Aptos";
summary.getRange("A:A").format.columnWidth = 38;
summary.getRange("B:B").format.columnWidth = 16;
summary.getRange("C:E").format.columnWidth = 14;
summary.getRange("F:F").format.columnWidth = 18;
summary.freezePanes.freezeRows(2);

// Mailing shortlist
mailing.showGridLines = false;
const mailingHeaders = [
  "Cluster ID", "Original Confidence", "Mail Status", "Mail Date", "Response", "Notes",
  "LLCs in Group", "Recommended Addressee", "Possible Named Addressee", "Name Support Count",
  "Mailing Address", "Address Source", "Distinct LLCs", "Distinct Properties", "Property Records",
  "LLC Names", "Property Addresses", "DOS LLCs Matched", "DOS Match Rate",
  "DOS Address-Corroborated LLCs", "Largest Shared DOS Address Count", "DOS Corroboration",
  "Agent Address Marker", "Situs Address Marker", "Email/Phone from DOS",
  "Minimum ACRIS Name Match", "DOS Source URL",
];
const mailingMatrix = payload.mailing_rows.map((row) => [
  row.cluster_id, row.original_confidence, "Not Mailed", null, "No Response", "", row.mailing_tier,
  row.recommended_addressee, row.possible_named_addressee, row.possible_addressee_support_count,
  row.mailing_address, row.mailing_address_source, row.distinct_llcs, row.distinct_properties, row.property_records,
  row.llc_names, row.property_addresses, row.dos_llcs_matched, row.dos_match_rate,
  row.dos_address_corroborated_llcs, row.largest_shared_dos_address_count, row.dos_corroboration,
  row.agent_address_marker, row.situs_address_marker, row.email_phone_available_from_dos,
  row.minimum_acris_name_match, row.source_url,
].map(cleanCell));
mailing.getRange("A1:AA1").values = [mailingHeaders];
mailing.getRangeByIndexes(1, 0, mailingMatrix.length, mailingHeaders.length).values = mailingMatrix;
styleHeader(mailing.getRange("A1:AA1"));
mailing.tables.add(`A1:AA${mailingMatrix.length + 1}`, true, "MailingShortlistTable").style = "TableStyleMedium2";
mailing.freezePanes.freezeRows(1);
mailing.freezePanes.freezeColumns(1);
mailing.getRange(`C2:C${mailingMatrix.length + 1}`).dataValidation = { rule: { type: "list", values: ["Not Mailed", "Mailed", "Returned"] } };
mailing.getRange(`E2:E${mailingMatrix.length + 1}`).dataValidation = { rule: { type: "list", values: ["No Response", "Interested", "Not Interested", "Wrong Address"] } };
mailing.getRange(`D2:D${mailingMatrix.length + 1}`).format.numberFormat = "yyyy-mm-dd";
mailing.getRange(`S2:S${mailingMatrix.length + 1}`).format.numberFormat = "0.0%";
mailing.getRange(`B2:B${mailingMatrix.length + 1}`).conditionalFormats.add("containsText", { text: "High", format: { fill: lightGreen, font: { color: "#375623" } } });
mailing.getRange(`B2:B${mailingMatrix.length + 1}`).conditionalFormats.add("containsText", { text: "Low", format: { fill: lightRed, font: { color: "#9C0006" } } });
mailing.getRange(`V2:V${mailingMatrix.length + 1}`).conditionalFormats.add("containsText", { text: "Strong", format: { fill: lightGreen, font: { color: "#375623" } } });
mailing.getRange(`V2:V${mailingMatrix.length + 1}`).conditionalFormats.add("containsText", { text: "Shared", format: { fill: lightTeal, font: { color: navy } } });
mailing.getRange(`V2:V${mailingMatrix.length + 1}`).conditionalFormats.add("containsText", { text: "Needs", format: { fill: lightRed, font: { color: "#9C0006" } } });
mailing.getRange("A:AA").format.font.name = "Aptos";
const mailingWidths = [15, 14, 14, 12, 16, 24, 12, 24, 24, 12, 38, 28, 12, 14, 14, 42, 48, 14, 12, 18, 18, 30, 14, 14, 18, 16, 38];
mailingWidths.forEach((width, index) => mailing.getRangeByIndexes(0, index, mailingMatrix.length + 1, 1).format.columnWidth = width);

// DOS entity matches
entities.showGridLines = false;
const entityHeaders = payload.entity_fields.map((field) => field.replaceAll("_", " ").replace(/\b\w/g, (m) => m.toUpperCase()));
const numericEntityFields = new Set(["tier_llc_count", "candidate_count", "address_match_score"]);
const entityMatrix = payload.entity_rows.map((row) => payload.entity_fields.map((field) => {
  if (field === "initial_dos_filing_date" && row[field]) return new Date(row[field]);
  if (numericEntityFields.has(field)) return Number(row[field] || 0);
  return cleanCell(row[field] ?? "");
}));
entities.getRangeByIndexes(0, 0, 1, entityHeaders.length).values = [entityHeaders];
entities.getRangeByIndexes(1, 0, entityMatrix.length, entityHeaders.length).values = entityMatrix;
styleHeader(entities.getRange(`A1:Z1`));
entities.tables.add(`A1:Z${entityMatrix.length + 1}`, true, "DosEntityMatchesTable").style = "TableStyleMedium2";
entities.freezePanes.freezeRows(1);
entities.freezePanes.freezeColumns(1);
entities.getRange(`L2:L${entityMatrix.length + 1}`).format.numberFormat = "yyyy-mm-dd";
entities.getRange(`G2:G${entityMatrix.length + 1}`).conditionalFormats.add("containsText", { text: "Address-corroborated", format: { fill: lightGreen, font: { color: "#375623" } } });
entities.getRange(`G2:G${entityMatrix.length + 1}`).conditionalFormats.add("containsText", { text: "No active", format: { fill: lightRed, font: { color: "#9C0006" } } });
entities.getRange("A:Z").format.font.name = "Aptos";
const entityWidths = [15, 14, 10, 38, 28, 30, 30, 12, 12, 12, 32, 14, 14, 14, 30, 28, 38, 24, 38, 28, 38, 24, 38, 16, 16, 38];
entityWidths.forEach((width, index) => entities.getRangeByIndexes(0, index, entityMatrix.length + 1, 1).format.columnWidth = width);

// Methodology and cautions
method.showGridLines = false;
styleTitle(method, "A1:B1", "Methodology and Field Guidance");
method.getRange("A3:B3").values = [["Topic", "Explanation"]];
styleHeader(method.getRange("A3:B3"));
method.getRange("A4:B12").values = [
  ["Population", "All ACRIS shared deed-party mailing-address candidate clusters, including High, Medium, and Low confidence and every LLC group size."],
  ["Coverage", "12,528 clusters, 42,321 cluster-to-LLC rows, and 41,773 unique normalized LLC names were processed."],
  ["DOS match", "LLC names were matched to the official Active Corporations dataset. The dataset excludes inactive entities."],
  ["Address corroboration", "A stronger signal is recorded when an LLC's DOS service-of-process street and ZIP agree with the ACRIS shared mailing address."],
  ["Named addressee", "A person-like DOS process name is used as the recommended addressee only when it appears for at least two LLCs in the same cluster."],
  ["Registered agents", "Registered-agent and formation-service names are evidence about administration, not proof of beneficial ownership."],
  ["Email and phone", "The official dataset has no email or phone columns. Those fields remain blank in DOS Entity Matches."],
  ["Legal interpretation", "These are research and marketing leads. Shared addresses and repeated names are not proof that the same person beneficially owns every LLC."],
  ["Refresh", "NY DOS states that the dataset is updated monthly. Re-run the enrichment before a later campaign."],
];
method.getRange("A4:A12").format = { fill: lightBlue, font: { bold: true, color: navy }, verticalAlignment: "top" };
method.getRange("B4:B12").format = { wrapText: true, verticalAlignment: "top" };
method.getRange("A4:B12").format.rowHeight = 36;
method.getRange("A14:B14").values = [["Source", "URL"]];
styleHeader(method.getRange("A14:B14"));
method.getRange("A15:B17").values = [
  ["NY DOS Active Corporations dataset", "https://data.ny.gov/Economic-Development/Active-Corporations-Beginning-1800/n9v6-gdp6"],
  ["Dataset API metadata", "https://data.ny.gov/api/views/n9v6-gdp6"],
  ["Socrata app-token documentation", "https://dev.socrata.com/docs/app-tokens.html"],
];
method.getRange("B15:B17").format = { font: { color: "#0563C1" }, wrapText: true };
method.getRange("A:F").format.font.name = "Aptos";
method.getRange("A:A").format.columnWidth = 28;
method.getRange("B:B").format.columnWidth = 90;
method.getRange("A3:B17").format.borders = { preset: "outside", style: "thin", color: border };
method.freezePanes.freezeRows(3);

// Compact verification before export.
console.log((await workbook.inspect({ kind: "table", range: "Summary!A1:F32", include: "values,formulas", tableMaxRows: 35, tableMaxCols: 8 })).ndjson);
console.log((await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: "formula error scan" })).ndjson);

await fs.mkdir(path.dirname(outputPath), { recursive: true });
const previews = path.join(path.dirname(outputPath), "previews");
await fs.mkdir(previews, { recursive: true });
for (const [sheetName, range] of [
  ["Summary", "A1:F32"],
  ["Mailing Shortlist", "A1:AA22"],
  ["DOS Entity Matches", "A1:Z22"],
  ["Methodology", "A1:B17"],
]) {
  const preview = await workbook.render({ sheetName, range, scale: 1, format: "png" });
  await fs.writeFile(path.join(previews, `${sheetName.replaceAll(" ", "_")}.png`), new Uint8Array(await preview.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({ outputPath, mailingRows: mailingMatrix.length, entityRows: entityMatrix.length }));
