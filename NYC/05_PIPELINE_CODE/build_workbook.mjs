import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const data = JSON.parse(await fs.readFile(path.join(root, "processed", "workbook_data.json"), "utf8"));
const outputDir = path.join(root, "outputs", "llc_analysis");
await fs.mkdir(outputDir, { recursive: true });

const workbook = Workbook.create();
const dashboard = workbook.worksheets.add("Dashboard");
const multi = workbook.worksheets.add("Multi-Property LLCs");
const shared = workbook.worksheets.add("Shared Property Addresses");
const metrics = workbook.worksheets.add("Metrics");
const method = workbook.worksheets.add("Methodology");

const navy = "#17324D";
const blue = "#1F4E78";
const teal = "#0F766E";
const paleBlue = "#EAF2F8";
const paleTeal = "#E8F5F2";
const paleGold = "#FFF4CC";
const gray = "#667085";
const lightBorder = "#D0D5DD";

function addTableSheet(sheet, columns, rows, tableName) {
  const matrix = [columns, ...rows];
  const range = sheet.getRangeByIndexes(0, 0, matrix.length, columns.length);
  range.values = matrix;
  const table = sheet.tables.add(range, true, tableName);
  table.style = "TableStyleMedium2";
  table.showBandedRows = true;
  table.showFilterButton = true;
  sheet.freezePanes.freezeRows(1);
  sheet.showGridLines = false;
  sheet.getRangeByIndexes(0, 0, 1, columns.length).format = {
    fill: blue,
    font: { bold: true, color: "#FFFFFF" },
    rowHeight: 28,
    wrapText: true,
  };
  return range;
}

// Metrics source sheet
addTableSheet(metrics, data.metrics.columns, data.metrics.data, "MetricsTable");
metrics.getRange("A1:A7").format.columnWidth = 48;
metrics.getRange("B1:B7").format.columnWidth = 18;
metrics.getRange("B2:B7").format.numberFormat = "#,##0";

// Multi-property LLC summary
const multiColumns = data.multi_property.columns.slice(0, 9);
const multiRows = data.multi_property.data.map((row) => row.slice(0, 9));
addTableSheet(multi, multiColumns, multiRows, "MultiPropertyLLCsTable");
multi.getRange(`A1:A${multiRows.length + 1}`).format.columnWidth = 38;
multi.getRange(`B1:B${multiRows.length + 1}`).format.columnWidth = 38;
multi.getRange(`C1:E${multiRows.length + 1}`).format.columnWidth = 15;
multi.getRange(`F1:F${multiRows.length + 1}`).format.columnWidth = 40;
multi.getRange(`G1:I${multiRows.length + 1}`).format.columnWidth = 19;
multi.getRange(`C2:G${multiRows.length + 1}`).format.numberFormat = "#,##0";
multi.getRange(`H2:I${multiRows.length + 1}`).format.numberFormat = '"$"#,##0';

// Same situs/property address candidates
addTableSheet(
  shared,
  data.shared_property_addresses.columns,
  data.shared_property_addresses.data,
  "SharedPropertyAddressesTable",
);
const sharedLast = data.shared_property_addresses.data.length + 1;
shared.getRange(`A1:A${sharedLast}`).format.columnWidth = 38;
shared.getRange(`B1:C${sharedLast}`).format.columnWidth = 18;
shared.getRange(`D1:D${sharedLast}`).format.columnWidth = 80;
shared.getRange(`E1:E${sharedLast}`).format.columnWidth = 34;
shared.getRange(`F1:F${sharedLast}`).format.columnWidth = 20;
shared.getRange(`B2:C${sharedLast}`).format.numberFormat = "#,##0";
shared.getRange(`F2:F${sharedLast}`).format.numberFormat = '"$"#,##0';
shared.getRange(`D2:D${sharedLast}`).format.wrapText = true;

// Dashboard title and description
dashboard.showGridLines = false;
dashboard.mergeCells("A1:H2");
dashboard.getRange("A1:H2").values = [["NYC FY2027 LLC Property Holdings"]];
dashboard.getRange("A1:H2").format = {
  fill: navy,
  font: { bold: true, color: "#FFFFFF", size: 20 },
  verticalAlignment: "center",
  horizontalAlignment: "left",
  rowHeight: 32,
};
dashboard.mergeCells("A3:H3");
dashboard.getRange("A3:H3").values = [[
  "Final assessment roll (PERIOD = 3). LLC names are normalized for punctuation and common legal-suffix variants.",
]];
dashboard.getRange("A3:H3").format = { font: { color: gray, italic: true }, rowHeight: 24 };

const cards = [
  ["A5:B5", "A6:B7", "Distinct LLC names", "='Metrics'!B4", paleBlue],
  ["C5:D5", "C6:D7", "Multi-property LLC names", "='Metrics'!B5", paleTeal],
  ["E5:F5", "E6:F7", "Properties in multi-LLC groups", "='Metrics'!B6", paleBlue],
  ["G5:H5", "G6:H7", "Shared property addresses", "='Metrics'!B7", paleGold],
];
for (const [labelRange, valueRange, label, formula, fill] of cards) {
  dashboard.mergeCells(labelRange);
  dashboard.mergeCells(valueRange);
  dashboard.getRange(labelRange).values = [[label]];
  dashboard.getRange(valueRange).formulas = [[formula]];
  dashboard.getRange(labelRange).format = {
    fill,
    font: { bold: true, color: navy },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: lightBorder },
  };
  dashboard.getRange(valueRange).format = {
    fill,
    font: { bold: true, color: navy, size: 20 },
    numberFormat: "#,##0",
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "outside", style: "thin", color: lightBorder },
  };
}

dashboard.mergeCells("A9:H9");
dashboard.getRange("A9:H9").values = [["Largest LLC holdings by assessment-roll property records"]];
dashboard.getRange("A9:H9").format = {
  fill: teal,
  font: { bold: true, color: "#FFFFFF", size: 13 },
  rowHeight: 26,
};
dashboard.getRange("A10:E10").values = [[
  "Owner as listed", "Property records", "Tax lots", "Boroughs", "Total market value",
]];
dashboard.getRange("A10:E10").format = { fill: blue, font: { bold: true, color: "#FFFFFF" } };
for (let i = 0; i < 12; i += 1) {
  const row = 11 + i;
  const src = 2 + i;
  dashboard.getRange(`A${row}:E${row}`).formulas = [[
    `='Multi-Property LLCs'!B${src}`,
    `='Multi-Property LLCs'!C${src}`,
    `='Multi-Property LLCs'!D${src}`,
    `='Multi-Property LLCs'!F${src}`,
    `='Multi-Property LLCs'!H${src}`,
  ]];
}
dashboard.getRange("B11:C22").format.numberFormat = "#,##0";
dashboard.getRange("E11:E22").format.numberFormat = '"$"#,##0';
dashboard.getRange("A10:E22").format.borders = { preset: "inside", style: "thin", color: lightBorder };
dashboard.getRange("A1:A22").format.columnWidth = 38;
dashboard.getRange("B1:C22").format.columnWidth = 18;
dashboard.getRange("D1:D22").format.columnWidth = 38;
dashboard.getRange("E1:E22").format.columnWidth = 21;
dashboard.getRange("F1:H22").format.columnWidth = 18;
dashboard.freezePanes.freezeRows(3);

// Methodology and limitations
method.showGridLines = false;
method.mergeCells("A1:F2");
method.getRange("A1:F2").values = [["Methodology, Sources, and Limitations"]];
method.getRange("A1:F2").format = {
  fill: navy,
  font: { bold: true, color: "#FFFFFF", size: 18 },
  verticalAlignment: "center",
};
const notes = [
  ["Scope", "FY2027 published final assessment roll only: YEAR = 2027 and PERIOD = 3."],
  ["LLC filter", "OWNER contains LLC, L.L.C., or LIMITED LIABILITY. This is a practical name filter, not a legal-entity determination."],
  ["Normalization", "Uppercase; punctuation collapsed; L L C, L.L.C., and LIMITED LIABILITY COMPANY normalized to LLC. Distinct spellings can still remain."],
  ["Multi-property definition", "One normalized OWNER name associated with more than one distinct PARID assessment record."],
  ["Shared-address candidates", "Different LLC names listed at the same property situs address. This is NOT the owner's mailing address and does not prove common control."],
  ["Mailing-address limitation", "The assessment dataset and raw record layout provide property address, not owner mailing address."],
  ["ACRIS enrichment", "ACRIS deed-party records include party mailing addresses. A title-oriented enrichment should use the latest applicable deed, Party Type 2 (grantee/buyer), and join by document ID and BBL. ACRIS coverage differs for Staten Island."],
  ["Assessment source", "https://data.cityofnewyork.us/d/8y4t-faws"],
  ["Assessment dictionary", "https://data.cityofnewyork.us/api/views/8y4t-faws/files/2e925830-8a86-453a-9072-1e6045ed92a4?download=true&filename=Property_Assessment_Data_Dictionary.xlsx"],
  ["ACRIS parties", "https://data.cityofnewyork.us/d/636b-3b5g"],
  ["ACRIS legals", "https://data.cityofnewyork.us/d/8h5j-fqxa"],
  ["Prepared", "2026-08-21"],
];
method.getRange(`A4:B${notes.length + 3}`).values = notes;
method.getRange(`A4:A${notes.length + 3}`).format = { fill: paleBlue, font: { bold: true, color: navy } };
method.getRange(`A4:B${notes.length + 3}`).format.borders = { preset: "inside", style: "thin", color: lightBorder };
method.getRange(`A4:A${notes.length + 3}`).format.columnWidth = 28;
method.getRange(`B4:B${notes.length + 3}`).format = { columnWidth: 110, wrapText: true };
method.getRange(`A4:B${notes.length + 3}`).format.autofitRows();

// Compact verification and visual previews for every sheet.
const dashboardCheck = await workbook.inspect({
  kind: "table",
  range: "Dashboard!A1:H22",
  include: "values,formulas",
  tableMaxRows: 24,
  tableMaxCols: 8,
});
console.log(dashboardCheck.ndjson);

const errorCheck = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(errorCheck.ndjson);

const previews = [
  ["Dashboard", "A1:H22"],
  ["Multi-Property LLCs", "A1:I18"],
  ["Shared Property Addresses", "A1:F18"],
  ["Metrics", "A1:B7"],
  ["Methodology", `A1:B${notes.length + 3}`],
];
for (const [sheetName, range] of previews) {
  const blob = await workbook.render({ sheetName, range, scale: 1.2, format: "png" });
  const safe = sheetName.toLowerCase().replace(/[^a-z0-9]+/g, "-");
  await fs.writeFile(path.join(outputDir, `${safe}.png`), new Uint8Array(await blob.arrayBuffer()));
}

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(path.join(outputDir, "NYC_FY2027_LLC_Property_Analysis.xlsx"));
console.log(path.join(outputDir, "NYC_FY2027_LLC_Property_Analysis.xlsx"));
