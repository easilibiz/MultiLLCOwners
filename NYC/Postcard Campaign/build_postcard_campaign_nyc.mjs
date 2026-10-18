import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

const sourcePath = path.resolve(
  '..',
  '01_FINAL_OUTPUTS',
  'mailing_ready',
  'NYC_MAILING_READY_DEDUPED_FILTERED.csv',
);
const outputPath = path.resolve('Postcard Campaign - New York City.csv');

function parseCsv(input) {
  const rows = [];
  let row = [];
  let field = '';
  let quoted = false;
  for (let index = 0; index < input.length; index += 1) {
    const character = input[index];
    if (quoted) {
      if (character === '"' && input[index + 1] === '"') {
        field += '"';
        index += 1;
      } else if (character === '"') quoted = false;
      else field += character;
    } else if (character === '"') quoted = true;
    else if (character === ',') {
      row.push(field);
      field = '';
    } else if (character === '\n') {
      row.push(field.replace(/\r$/, ''));
      rows.push(row);
      row = [];
      field = '';
    } else field += character;
  }
  if (field || row.length) {
    row.push(field.replace(/\r$/, ''));
    rows.push(row);
  }
  const headers = (rows.shift() || []).map((header, index) =>
    index === 0 ? header.replace(/^\uFEFF/, '') : header,
  );
  return {
    headers,
    rows: rows
      .filter((values) => values.some(Boolean))
      .map((values) =>
        Object.fromEntries(headers.map((header, index) => [header, values[index] || ''])),
      ),
  };
}

function csvCell(value) {
  const text = String(value ?? '');
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function boroughForZip(zip) {
  const number = Number(zip);
  if (number >= 10001 && number <= 10292) return 'Manhattan';
  if (number >= 10301 && number <= 10314) return 'Staten Island';
  if (number >= 10451 && number <= 10475) return 'Bronx';
  if (number >= 11201 && number <= 11256) return 'Brooklyn';
  if (
    [11004, 11005].includes(number) ||
    (number >= 11101 && number <= 11109) ||
    (number >= 11351 && number <= 11697)
  ) return 'Queens';
  return '';
}

function llcBand(count) {
  if (count <= 3) return '2-3 LLCs';
  if (count <= 6) return '4-6 LLCs';
  if (count <= 10) return '7-10 LLCs';
  return '11+ LLCs';
}

function propertyBand(count) {
  if (count <= 3) return '2-3 properties';
  if (count <= 9) return '4-9 properties';
  if (count <= 24) return '10-24 properties';
  return '25+ properties';
}

function geography(propertyAddresses) {
  const counts = new Map();
  for (const match of propertyAddresses.matchAll(/\b(?:NY\s+)?((?:10|11)\d{3})\b/g)) {
    const borough = boroughForZip(match[1]);
    if (borough) counts.set(borough, (counts.get(borough) || 0) + 1);
  }
  const ranked = [...counts.entries()].sort((left, right) => right[1] - left[1]);
  const mapped = ranked.reduce((total, [, count]) => total + count, 0);
  const [dominant = '', dominantCount = 0] = ranked[0] || [];
  const share = mapped ? dominantCount / mapped : 0;
  const scope = dominant && share >= 0.6 ? 'BOROUGH_CONCENTRATED' : mapped ? 'MULTI_BOROUGH' : 'GEOGRAPHY_UNMAPPED';
  const label = scope === 'BOROUGH_CONCENTRATED' ? dominant : 'New York City';
  const confidence = share >= 0.8 ? 'STRONG' : share >= 0.6 ? 'MODERATE' : mapped ? 'DISTRIBUTED' : 'UNMAPPED';
  return {
    dominant,
    dominantCount,
    mapped,
    share,
    scope,
    label,
    confidence,
    counts: ranked.map(([name, count]) => `${name}: ${count}`).join(' | '),
  };
}

function messageFields(llcCount, propertyCount, geo) {
  const location = geo.label;
  let segment;
  let headline;
  if (llcCount <= 3) {
    segment = 'GROWING_PORTFOLIO';
    headline = `${llcCount} LLCs in ${location}. A clean foundation for what comes next.`;
  } else if (llcCount <= 6) {
    segment = 'ESTABLISHED_PORTFOLIO';
    headline = `${llcCount} LLCs in ${location}. One clear financial picture.`;
  } else if (llcCount <= 10) {
    segment = 'PORTFOLIO_SCALE';
    headline = `${llcCount} LLCs in ${location}. Portfolio-scale books without the friction.`;
  } else {
    segment = 'COMPLEX_PORTFOLIO';
    headline = `A ${llcCount}-LLC portfolio in ${location} needs a system built for complexity.`;
  }
  const propertyWord = propertyCount === 1 ? 'property' : 'properties';
  return {
    segment,
    postcardLine: `Bookkeeping built for ${llcCount} LLCs connected with ${propertyCount} ${propertyWord} in ${location}.`,
    headline,
    body: `BooksRez keeps each entity separate, reconciled, and ready for your CPA while giving you one practical view of the portfolio.`,
    cta: 'Request a confidential portfolio evaluation',
  };
}

const source = parseCsv(readFileSync(sourcePath, 'utf8'));
const addedHeaders = [
  'campaign_market',
  'campaign_id',
  'campaign_recipient_id',
  'llc_count_band',
  'property_count_band',
  'holdings_geography_scope',
  'holdings_geography_label',
  'dominant_holdings_borough',
  'dominant_borough_property_count',
  'mapped_property_count',
  'borough_concentration_pct',
  'borough_concentration_confidence',
  'borough_property_counts',
  'personalization_segment',
  'postcard_personalized_line',
  'landing_page_headline',
  'landing_page_body',
  'landing_page_cta',
  'tracking_token',
  'personalized_url',
  'qr_value',
  'qr_status',
  'campaign_release_status',
  'personalization_review_status',
];
const headers = [...source.headers, ...addedHeaders];
const outputRows = source.rows.map((row) => {
  const llcCount = Number(row.distinct_llcs);
  const propertyCount = Number(row.distinct_properties);
  const geo = geography(row.property_addresses);
  const message = messageFields(llcCount, propertyCount, geo);
  return {
    ...row,
    campaign_market: 'New York City',
    campaign_id: 'NYC-POSTCARD-2026-01',
    campaign_recipient_id: row.mailing_id,
    llc_count_band: llcBand(llcCount),
    property_count_band: propertyBand(propertyCount),
    holdings_geography_scope: geo.scope,
    holdings_geography_label: geo.label,
    dominant_holdings_borough: geo.dominant,
    dominant_borough_property_count: geo.dominantCount,
    mapped_property_count: geo.mapped,
    borough_concentration_pct: geo.mapped ? (geo.share * 100).toFixed(1) : '',
    borough_concentration_confidence: geo.confidence,
    borough_property_counts: geo.counts,
    personalization_segment: message.segment,
    postcard_personalized_line: message.postcardLine,
    landing_page_headline: message.headline,
    landing_page_body: message.body,
    landing_page_cta: message.cta,
    tracking_token: '',
    personalized_url: '',
    qr_value: '',
    qr_status: 'NOT GENERATED - AWAITING WEBSITE',
    campaign_release_status: 'HOLD - POSTAL VALIDATION REQUIRED',
    personalization_review_status: 'READY FOR MESSAGE REVIEW',
  };
});

const output = [
  headers.map(csvCell).join(','),
  ...outputRows.map((row) => headers.map((header) => csvCell(row[header])).join(',')),
].join('\n');
writeFileSync(outputPath, `${output}\n`, 'utf8');

const summary = {
  rows: outputRows.length,
  columns: headers.length,
  addedColumns: addedHeaders.length,
  geographyScopes: Object.fromEntries(
    [...new Set(outputRows.map((row) => row.holdings_geography_scope))].map((value) => [
      value,
      outputRows.filter((row) => row.holdings_geography_scope === value).length,
    ]),
  ),
  outputPath,
};
console.log(JSON.stringify(summary, null, 2));
