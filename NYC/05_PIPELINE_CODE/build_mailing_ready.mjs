import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = process.cwd();
const candidatePath = path.join(root, "NYC", "01_FINAL_OUTPUTS", "mailing_lists", "NYC_POSTCARD_TARGETS_ALL_12528_NOT_PRINT_APPROVED.csv");
const evidencePath = path.join(root, "NYC", "01_FINAL_OUTPUTS", "evidence", "NYC_ENTITY_MATCHES_ALL_CLUSTERS.csv");
const outputDir = path.join(root, "NYC", "01_FINAL_OUTPUTS", "mailing_ready");
const qaDir = path.join(outputDir, "qa_previews");
await fs.mkdir(qaDir, { recursive: true });
console.log("stage: initialized");

function parseCsv(text) {
  const rows = [];
  let row = [], parts = [], fieldStart = 0, quoted = false;
  const finishField = (end) => {
    parts.push(text.slice(fieldStart, end));
    let value = parts.join("");
    if (value.endsWith("\r")) value = value.slice(0, -1);
    row.push(value);
    parts = [];
  };
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') {
        parts.push(text.slice(fieldStart, i), '"');
        i += 1;
        fieldStart = i + 1;
      } else if (ch === '"') {
        parts.push(text.slice(fieldStart, i));
        quoted = false;
        fieldStart = i + 1;
      }
    } else if (ch === '"' && i === fieldStart) {
      quoted = true;
      fieldStart = i + 1;
    } else if (ch === ',') {
      finishField(i);
      fieldStart = i + 1;
    } else if (ch === '\n') {
      finishField(i);
      rows.push(row);
      row = [];
      fieldStart = i + 1;
    }
  }
  if (fieldStart < text.length || row.length) { finishField(text.length); rows.push(row); }
  const headers = rows.shift();
  headers[0] = headers[0].replace(/^\uFEFF/, "");
  return rows.filter(r => r.some(v => v !== "")).map(r => Object.fromEntries(headers.map((h, i) => [h, r[i] ?? ""])));
}

function csvCell(value) {
  const s = String(value ?? "");
  return /[",\r\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
}

function toCsv(headers, rows) {
  return [headers.join(","), ...rows.map(r => headers.map(h => csvCell(r[h])).join(","))].join("\r\n") + "\r\n";
}

const replacements = new Map([
  ["STREET", "ST"], ["AVENUE", "AVE"], ["ROAD", "RD"], ["BOULEVARD", "BLVD"],
  ["PLACE", "PL"], ["DRIVE", "DR"], ["LANE", "LN"], ["COURT", "CT"],
  ["PARKWAY", "PKWY"], ["HIGHWAY", "HWY"], ["TERRACE", "TER"],
  ["SUITE", "STE"], ["FLOOR", "FL"], ["APARTMENT", "APT"],
  ["NORTH", "N"], ["SOUTH", "S"], ["EAST", "E"], ["WEST", "W"],
]);

function normalizeAddress(value) {
  let s = String(value ?? "").toUpperCase().replace(/\bUNITED STATES(?: OF AMERICA)?\b/g, " ");
  s = s.replace(/(?:,?\s+)(?:USA|US)\s*$/g, " ").replace(/[^A-Z0-9]+/g, " ").trim();
  const tokens = s.split(/\s+/).map(t => replacements.get(t) ?? t);
  return tokens.join(" ");
}

function normalizeName(value) {
  return String(value ?? "").toUpperCase().replace(/[^A-Z0-9]+/g, " ").trim();
}

const professionalPatterns = [
  ["LEGAL_OR_LAWYER", /\b(ATTORNEY|ATTORNEYS|LAW|LAWYER|LAWYERS|LEGAL|COUNSEL|ESQUIRE|ESQ|LAW\s+OFFICE|LAW\s+FIRM)\b/i],
  ["CPA_OR_ACCOUNTING", /\b(CPA|CERTIFIED\s+PUBLIC\s+ACCOUNTANT|ACCOUNTANT|ACCOUNTANTS|ACCOUNTING|BOOKKEEP(?:ER|ING)?|TAX\s+(?:SERVICE|SERVICES|PREPARATION))\b/i],
  ["AGENT_OR_FILING_SERVICE", /\b(REGISTERED\s+AGENT|REGISTERED\s+AGENTS|PARACORP|CT\s+CORPORATION|C\s+T\s+CORPORATION|CORPORATION\s+SERVICE\s+COMPANY|NATIONAL\s+REGISTERED\s+AGENTS|UNITED\s+CORPORATE\s+SERVICES|CAPITOL\s+SERVICES|INCORP\s+SERVICES|NORTHWEST\s+REGISTERED\s+AGENT|COGENCY|LEGALINC|PROCESS\s+AGENT|FILING\s+SERVICE)\b/i],
  ["CARE_OF_OR_AGENT", /\b(CARE\s+OF|C\s+O|AGENT)\b/i],
];

function prohibitedLabels(value) {
  const canonical = normalizeName(value);
  return professionalPatterns.filter(([, re]) => re.test(canonical)).map(([label]) => label);
}

function splitPipe(value) {
  return String(value ?? "").split("|").map(x => x.trim()).filter(Boolean);
}

function parsePostalAddress(full) {
  const parts = String(full ?? "").split(",").map(x => x.trim()).filter(Boolean);
  if (["US", "USA", "UNITED STATES"].includes((parts.at(-1) ?? "").toUpperCase())) parts.pop();
  const zipIndex = parts.findLastIndex(x => /^\d{5}(?:-?\d{4})?$/.test(x));
  if (zipIndex < 2) return { street_and_unit: parts.slice(0, -2).join(", "), city: parts.at(-2) ?? "", state: parts.at(-1) ?? "", zip_code: "" };
  return {
    street_and_unit: parts.slice(0, zipIndex - 2).join(", "),
    city: parts[zipIndex - 2] ?? "",
    state: parts[zipIndex - 1] ?? "",
    zip_code: parts[zipIndex] ?? "",
  };
}

const candidates = parseCsv(await fs.readFile(candidatePath, "utf8"));
console.log(`stage: parsed ${candidates.length} candidates`);
const evidence = parseCsv(await fs.readFile(evidencePath, "utf8"));
console.log(`stage: parsed ${evidence.length} evidence rows`);

const evidenceByCluster = new Map();
for (const e of evidence) {
  if (!evidenceByCluster.has(e.cluster_id)) evidenceByCluster.set(e.cluster_id, []);
  evidenceByCluster.get(e.cluster_id).push({
    registeredAgentAddressKey: normalizeAddress(e.registered_agent_address),
    registeredAgentName: e.registered_agent_name,
    processAddressKey: normalizeAddress(e.dos_process_address),
    processName: e.dos_process_name,
    processLabels: prohibitedLabels(e.dos_process_name),
    locationAddressKey: normalizeAddress(e.location_address),
    locationName: e.location_name,
    locationLabels: prohibitedLabels(e.location_name),
  });
}
console.log(`stage: indexed ${evidenceByCluster.size} evidence clusters; largest bucket ${Math.max(...[...evidenceByCluster.values()].map(x => x.length))}`);

const excluded = [];
const survivors = [];
for (const c of candidates) {
  const reasons = new Set();
  const details = new Set();
  const targetKey = normalizeAddress(c.mailing_address);
  if (!targetKey) reasons.add("MISSING_MAILING_ADDRESS");
  if (c.agent_address_marker === "1") reasons.add("SOURCE_AGENT_ADDRESS_MARKER");
  if (c.situs_address_marker === "1") reasons.add("PROPERTY_ADDRESS_USED_AS_MAILING_ADDRESS");
  if (c.dos_corroboration === "Needs manual review") reasons.add("SOURCE_REQUIRES_MANUAL_REVIEW");
  if ((c.original_confidence || "").toUpperCase() === "LOW") reasons.add("LOW_SOURCE_CONFIDENCE");
  for (const field of ["mailing_address", "recommended_addressee", "possible_named_addressee"]) {
    for (const label of prohibitedLabels(c[field])) { reasons.add(label); details.add(`${field}:${c[field]}`); }
  }
  for (const e of evidenceByCluster.get(c.cluster_id) ?? []) {
    if (targetKey && e.registeredAgentAddressKey && targetKey === e.registeredAgentAddressKey && e.registeredAgentName) {
      reasons.add("REGISTERED_AGENT_ADDRESS_MATCH"); details.add(`registered_agent:${e.registeredAgentName}`);
    }
    if (targetKey && e.processAddressKey && targetKey === e.processAddressKey) {
      for (const label of e.processLabels) {
        reasons.add(label); details.add(`dos_process_name:${e.processName}`);
      }
    }
    if (targetKey && e.locationAddressKey && targetKey === e.locationAddressKey) {
      for (const label of e.locationLabels) {
        reasons.add(label); details.add(`location_name:${e.locationName}`);
      }
    }
  }
  if (reasons.size) excluded.push({
    cluster_id: c.cluster_id,
    mailing_address: c.mailing_address,
    recommended_addressee: c.recommended_addressee,
    distinct_llcs: c.distinct_llcs,
    distinct_properties: c.distinct_properties,
    original_confidence: c.original_confidence,
    dos_corroboration: c.dos_corroboration,
    exclusion_reasons: [...reasons].sort().join(" | "),
    exclusion_details: [...details].sort().join(" | "),
  });
  else survivors.push({ ...c, normalized_mailing_address: targetKey });
}
console.log(`stage: screened ${survivors.length} survivors and ${excluded.length} exclusions`);

const grouped = new Map();
for (const c of survivors) {
  if (!grouped.has(c.normalized_mailing_address)) grouped.set(c.normalized_mailing_address, []);
  grouped.get(c.normalized_mailing_address).push(c);
}

const confidenceRank = { High: 3, Medium: 2, Low: 1 };
const mailingRows = [];
let mailingNumber = 0;
for (const group of grouped.values()) {
  mailingNumber += 1;
  const addresses = [...new Set(group.map(x => x.mailing_address))];
  const fullAddress = addresses.sort((a, b) => b.length - a.length)[0];
  const parsed = parsePostalAddress(fullAddress);
  const named = [...new Set(group.map(x => x.recommended_addressee).filter(x => x && x !== "PROPERTY OWNER" && !prohibitedLabels(x).length))];
  const addressee = named.length === 1 ? named[0] : "PROPERTY OWNER";
  const llcs = [...new Set(group.flatMap(x => splitPipe(x.llc_names)))].sort();
  const properties = [...new Set(group.flatMap(x => splitPipe(x.property_addresses)))].sort();
  const confidence = group.map(x => x.original_confidence).sort((a, b) => (confidenceRank[a] ?? 0) - (confidenceRank[b] ?? 0))[0];
  const corroboration = [...new Set(group.map(x => x.dos_corroboration))].join(" | ");
  mailingRows.push({
    mailing_id: `NYC-MAIL-${String(mailingNumber).padStart(5, "0")}`,
    addressee,
    mailing_address_full: fullAddress,
    street_and_unit: parsed.street_and_unit,
    city: parsed.city,
    state: parsed.state,
    zip_code: parsed.zip_code,
    source_cluster_ids: group.map(x => x.cluster_id).sort().join(" | "),
    distinct_llcs: llcs.length,
    distinct_properties: properties.length,
    llc_names: llcs.join(" | "),
    property_addresses: properties.join(" | "),
    source_confidence: confidence,
    dos_corroboration: corroboration,
    exclusion_screen: "PASS",
    duplicate_address_count_consolidated: group.length,
    postal_validation_status: "NOT_CASS_OR_DPV_VALIDATED",
    source_url: [...new Set(group.map(x => x.source_url).filter(Boolean))].join(" | "),
  });
}
mailingRows.sort((a, b) => a.zip_code.localeCompare(b.zip_code) || a.mailing_address_full.localeCompare(b.mailing_address_full));
mailingRows.forEach((r, i) => { r.mailing_id = `NYC-MAIL-${String(i + 1).padStart(5, "0")}`; });

const mailingHeaders = Object.keys(mailingRows[0] ?? {});
const exclusionHeaders = Object.keys(excluded[0] ?? {});
await fs.writeFile(path.join(outputDir, "NYC_MAILING_READY_DEDUPED_FILTERED.csv"), toCsv(mailingHeaders, mailingRows));
await fs.writeFile(path.join(outputDir, "NYC_MAILING_EXCLUSIONS_AUDIT.csv"), toCsv(exclusionHeaders, excluded));
console.log(`stage: wrote CSV outputs with ${mailingRows.length} unique addresses`);

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
const ready = workbook.worksheets.add("Mailing Ready");
const excludedSheet = workbook.worksheets.add("Excluded");
const rules = workbook.worksheets.add("Rules");

const ink = "#000000", white = "#FFFFFF", light = "#F2F2F2", mid = "#D9D9D9";
function addTable(sheet, headers, rows, name) {
  const matrix = [headers, ...rows.map(r => headers.map(h => r[h] ?? ""))];
  const range = sheet.getRangeByIndexes(0, 0, matrix.length, headers.length);
  range.values = matrix;
  const table = sheet.tables.add(range, true, name);
  table.style = "TableStyleMedium2";
  table.showBandedRows = true;
  table.showFilterButton = true;
  sheet.freezePanes.freezeRows(1);
  sheet.showGridLines = false;
  sheet.getRangeByIndexes(0, 0, 1, headers.length).format = { fill: ink, font: { bold: true, color: white }, wrapText: true, rowHeight: 34 };
  return range;
}

addTable(ready, mailingHeaders, mailingRows, "MailingReadyTable");
ready.getRange(`A1:A${mailingRows.length + 1}`).format.columnWidth = 17;
ready.getRange(`B1:B${mailingRows.length + 1}`).format.columnWidth = 30;
ready.getRange(`C1:C${mailingRows.length + 1}`).format.columnWidth = 55;
ready.getRange(`D1:G${mailingRows.length + 1}`).format.columnWidth = 22;
ready.getRange(`H1:H${mailingRows.length + 1}`).format.columnWidth = 34;
ready.getRange(`I1:J${mailingRows.length + 1}`).format.columnWidth = 15;
ready.getRange(`K1:L${mailingRows.length + 1}`).format = { columnWidth: 70, wrapText: true };
ready.getRange(`M1:R${mailingRows.length + 1}`).format = { columnWidth: 24, wrapText: true };
ready.getRange(`I2:J${mailingRows.length + 1}`).format.numberFormat = "#,##0";

addTable(excludedSheet, exclusionHeaders, excluded, "ExclusionsTable");
excludedSheet.getRange(`A1:A${excluded.length + 1}`).format.columnWidth = 18;
excludedSheet.getRange(`B1:C${excluded.length + 1}`).format = { columnWidth: 42, wrapText: true };
excludedSheet.getRange(`D1:G${excluded.length + 1}`).format.columnWidth = 20;
excludedSheet.getRange(`H1:I${excluded.length + 1}`).format = { columnWidth: 55, wrapText: true };

summary.showGridLines = false;
summary.mergeCells("A1:F2");
summary.getRange("A1:F2").values = [["NYC Mailing Campaign Release Workbook"]];
summary.getRange("A1:F2").format = { fill: ink, font: { bold: true, color: white, size: 20 }, verticalAlignment: "center" };
summary.mergeCells("A3:F3");
summary.getRange("A3:F3").values = [["One row per normalized owner mailing address; lawyers, agents, CPAs, manual-review records, and low-confidence records excluded."]];
summary.getRange("A3:F3").format = { font: { italic: true, color: ink }, wrapText: true, rowHeight: 34 };
summary.getRange("A5:B10").values = [
  ["Control", "Result"],
  ["Input candidate rows", candidates.length],
  ["Rows excluded before deduplication", excluded.length],
  ["Rows surviving before deduplication", survivors.length],
  ["Final unique mailing addresses", ""],
  ["Duplicate candidate rows consolidated", ""],
];
summary.getRange("B9").formulas = [["=ROWS(MailingReadyTable[mailing_id])"]];
summary.getRange("B10").formulas = [["=SUM(MailingReadyTable[duplicate_address_count_consolidated])-ROWS(MailingReadyTable[mailing_id])"]];
summary.getRange("A5:B5").format = { fill: ink, font: { bold: true, color: white } };
summary.getRange("A6:A10").format = { fill: light, font: { bold: true } };
summary.getRange("A5:B10").format.borders = { preset: "inside", style: "thin", color: mid };
summary.getRange("A1:A10").format.columnWidth = 42;
summary.getRange("B1:B10").format.columnWidth = 22;
summary.getRange("B6:B10").format.numberFormat = "#,##0";
summary.getRange("A12:F15").values = [
  ["Release note", "", "", "", "", ""],
  ["This list is rule-screened and duplicate-free, but it has not been validated by USPS CASS/DPV/NCOA. Run postal validation and a final suppression review before printing.", "", "", "", "", ""],
  ["Authoritative destination field", "mailing_address_full", "", "", "", ""],
  ["Campaign unit", "One postcard per normalized mailing address", "", "", "", ""],
];
summary.mergeCells("A12:F12"); summary.mergeCells("A13:F13"); summary.mergeCells("B14:F14"); summary.mergeCells("B15:F15");
summary.getRange("A12:F12").format = { fill: ink, font: { bold: true, color: white } };
summary.getRange("A13:F13").format = { fill: light, wrapText: true, rowHeight: 48 };
summary.getRange("A14:A15").format = { fill: light, font: { bold: true } };

const ruleRows = [
  ["Campaign unit", "One output row and one postcard per normalized owner mailing address."],
  ["Deduplication", "Normalize case, punctuation, country suffix, street types, directions, and unit labels; preserve suite/unit identifiers; consolidate all source clusters sharing the resulting key."],
  ["Source agent flag", "Exclude candidate when agent_address_marker = 1."],
  ["Registered agent match", "Exclude only when the target mailing address matches a populated registered-agent address; merely having an agent elsewhere is not disqualifying."],
  ["Legal / lawyer", "Exclude target-address evidence or addressee text containing attorney, law, lawyer, legal, counsel, Esq., or equivalent law-office terms."],
  ["CPA / accounting", "Exclude target-address evidence or addressee text containing CPA, certified public accountant, accountant/accounting, bookkeeping, or tax-service terms."],
  ["Filing / service agent", "Exclude registered-agent, process-agent, filing-service, corporation-service, Paracorp, CT Corporation, Cogency, Legalinc, and similar service-provider destinations."],
  ["Care of", "Exclude C/O or care-of destinations from the automated campaign list."],
  ["Property address", "Exclude when the candidate is flagged as using a property/situs address instead of an owner mailing address."],
  ["Confidence gate", "Exclude source records marked Needs manual review or Low confidence; retain them in the audit log."],
  ["Postal validation", "Required before print release: USPS CASS/DPV and, when appropriate, NCOA plus campaign suppression checks."],
  ["Evidence retention", "Retain original cluster IDs, LLC names, property addresses, exclusion reasons, and source URL for auditability."],
];
addTable(rules, ["Rule", "Requirement"], ruleRows.map(x => ({ Rule: x[0], Requirement: x[1] })), "RulesTable");
rules.getRange("A1:A13").format = { columnWidth: 30, wrapText: true };
rules.getRange("B1:B13").format = { columnWidth: 110, wrapText: true };
rules.getRange("A2:B13").format.autofitRows();

for (const [sheetName, range] of [
  ["Summary", "A1:F15"],
  ["Mailing Ready", `A1:R${Math.min(26, mailingRows.length + 1)}`],
  ["Excluded", `A1:I${Math.min(26, excluded.length + 1)}`],
  ["Rules", "A1:B13"],
]) {
  const blob = await workbook.render({ sheetName, range, scale: 1.2, format: "png" });
  const safe = sheetName.toLowerCase().replace(/[^a-z0-9]+/g, "-");
  await fs.writeFile(path.join(qaDir, `${safe}.png`), new Uint8Array(await blob.arrayBuffer()));
}

console.log((await workbook.inspect({ kind: "table", range: "Summary!A1:F15", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 6 })).ndjson);
console.log((await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 100 }, summary: "formula error scan" })).ndjson);
const workbookFile = await SpreadsheetFile.exportXlsx(workbook);
await workbookFile.save(path.join(outputDir, "NYC_MAILING_READY_DEDUPED_FILTERED.xlsx"));

const reasonCounts = {};
for (const row of excluded) for (const reason of row.exclusion_reasons.split(" | ")) reasonCounts[reason] = (reasonCounts[reason] ?? 0) + 1;
const stats = { inputCandidates: candidates.length, excludedRows: excluded.length, survivorsBeforeDeduplication: survivors.length, finalUniqueMailingAddresses: mailingRows.length, duplicateRowsConsolidated: survivors.length - mailingRows.length, exclusionReasonCounts: Object.fromEntries(Object.entries(reasonCounts).sort((a, b) => b[1] - a[1])) };
await fs.writeFile(path.join(outputDir, "NYC_MAILING_READY_STATS.json"), JSON.stringify(stats, null, 2) + "\n");
console.log(JSON.stringify(stats, null, 2));
