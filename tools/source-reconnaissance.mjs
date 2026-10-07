#!/usr/bin/env node

import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const SOURCES = [
  { language: "da", file: "data/raw/smk_all_da.json" },
  { language: "en", file: "data/raw/smk_all_en.json" },
];

const VISUAL_FIELDS = ["brightness", "contrast", "saturation", "colortemp", "entropy"];
const COMPARE_FIELDS = [
  "id", "created", "modified", "acquisition_date", "acquisition_date_precision",
  "object_number", "object_url", "frontend_url", "iiif_manifest", "enrichment_url",
  "similar_images_url", "public_domain", "rights", "on_display", "image_mime_type",
  "image_iiif_id", "image_iiif_info", "image_width", "image_height", "image_size",
  "image_thumbnail", "image_native", "image_cropped", "image_orientation", "image_hq",
  "has_3d_file", "has_image", "colors", "suggested_bg_color", ...VISUAL_FIELDS,
];
const RELEVANT_KEYS = new Set([
  "object_number", "public_domain", "titles", "title", "object_names", "name",
  "classification", "classifications", "dimensions", "part", "type", "unit", "value",
  "image_width", "image_height", "has_image", "colors", "colors_palette",
  "colors_palette_weighted", "colors_palette_weighted_s", "suggested_bg_color",
  ...VISUAL_FIELDS,
]);

function valueType(value) {
  if (value === null) return "null";
  if (Array.isArray(value)) return "array";
  return typeof value;
}

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stable(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function digestValue(value) {
  return createHash("sha256").update(stable(value)).digest("hex").slice(0, 16);
}

function increment(map, key) {
  map.set(key, (map.get(key) ?? 0) + 1);
}

function inspectRelevant(value, currentPath, stats) {
  if (Array.isArray(value)) {
    for (const item of value) inspectRelevant(item, `${currentPath}[]`, stats);
    return;
  }
  if (!value || typeof value !== "object") return;
  for (const [key, child] of Object.entries(value)) {
    const childPath = currentPath ? `${currentPath}.${key}` : key;
    if (RELEVANT_KEYS.has(key) || /palette|color|brightness|contrast|saturation|entropy|dimension/i.test(key)) {
      const statKey = `${childPath}\u0000${valueType(child)}`;
      increment(stats, statKey);
    }
    inspectRelevant(child, childPath, stats);
  }
}

function sampleRecord(record) {
  const keys = [
    "id", "object_number", "public_domain", "has_image", "image_width", "image_height",
    "dimensions", "titles", "object_names", "colors", "suggested_bg_color", ...VISUAL_FIELDS,
  ];
  return Object.fromEntries(keys.filter((key) => Object.hasOwn(record, key)).map((key) => [key, record[key]]));
}

async function inspectSource(source) {
  const hash = createHash("sha256");
  const ids = new Map();
  const comparison = new Map();
  const topLevelFields = new Map();
  const relevantPaths = new Map();
  const counts = {
    records: 0, missing_object_number: 0, blank_object_number: 0, public_domain_true: 0,
    has_image_true: 0, dimensions_present: 0, colors_present: 0,
    all_visual_fields_present: 0,
  };
  const visualFieldPresence = Object.fromEntries(VISUAL_FIELDS.map((key) => [key, 0]));
  const samples = { first: null, last: null, first_without_image: null, first_without_object_number: null };

  let bytes = 0;
  let rootStarted = false;
  let rootEnded = false;
  let collecting = false;
  let depth = 0;
  let inString = false;
  let escaped = false;
  let recordText = "";

  function accept(record) {
    counts.records += 1;
    const sampled = sampleRecord(record);
    samples.first ??= sampled;
    samples.last = sampled;
    if (record.has_image !== true) samples.first_without_image ??= sampled;

    const rawId = record.object_number;
    const validId = typeof rawId === "string" && rawId.trim() !== "";
    if (!Object.hasOwn(record, "object_number")) counts.missing_object_number += 1;
    else if (!validId) counts.blank_object_number += 1;
    if (!validId) samples.first_without_object_number ??= sampled;
    if (validId) {
      const id = rawId.trim();
      increment(ids, id);
      const fingerprints = {};
      for (const key of COMPARE_FIELDS) {
        fingerprints[key] = Object.hasOwn(record, key) ? digestValue(record[key]) : null;
      }
      if (!comparison.has(id)) comparison.set(id, fingerprints);
    }

    if (record.public_domain === true) counts.public_domain_true += 1;
    if (record.has_image === true) counts.has_image_true += 1;
    if (Array.isArray(record.dimensions) && record.dimensions.length > 0) counts.dimensions_present += 1;
    if (Array.isArray(record.colors) && record.colors.length > 0) counts.colors_present += 1;
    if (VISUAL_FIELDS.every((key) => record[key] !== null && record[key] !== undefined)) {
      counts.all_visual_fields_present += 1;
    }
    for (const key of VISUAL_FIELDS) {
      if (record[key] !== null && record[key] !== undefined) visualFieldPresence[key] += 1;
    }
    for (const [key, value] of Object.entries(record)) {
      increment(topLevelFields, `${key}\u0000${valueType(value)}`);
    }
    inspectRelevant(record, "", relevantPaths);
  }

  const stream = createReadStream(source.file, { highWaterMark: 1024 * 1024 });
  for await (const chunk of stream) {
    bytes += chunk.length;
    hash.update(chunk);
    const text = chunk.toString("utf8");
    for (const char of text) {
      if (!rootStarted) {
        if (/\s/.test(char)) continue;
        if (char !== "[") throw new Error(`${source.file}: expected top-level array`);
        rootStarted = true;
        continue;
      }
      if (!collecting) {
        if (/\s/.test(char) || char === ",") continue;
        if (char === "]") { rootEnded = true; continue; }
        if (char !== "{") throw new Error(`${source.file}: expected object array element`);
        collecting = true;
        depth = 1;
        inString = false;
        escaped = false;
        recordText = "{";
        continue;
      }

      recordText += char;
      if (inString) {
        if (escaped) escaped = false;
        else if (char === "\\") escaped = true;
        else if (char === "\"") inString = false;
        continue;
      }
      if (char === "\"") inString = true;
      else if (char === "{" || char === "[") depth += 1;
      else if (char === "}" || char === "]") depth -= 1;
      if (depth === 0) {
        accept(JSON.parse(recordText));
        collecting = false;
        recordText = "";
      }
    }
  }
  if (!rootStarted || !rootEnded || collecting) throw new Error(`${source.file}: incomplete JSON array`);

  const duplicates = [...ids.entries()].filter(([, count]) => count > 1).sort((a, b) => a[0].localeCompare(b[0]));
  return {
    language: source.language,
    path: source.file.replaceAll("\\", "/"),
    bytes,
    sha256: hash.digest("hex"),
    observed_structure: {
      top_level_type: "array",
      record_path: "$[]",
      element_type: "object",
      envelope: null,
    },
    counts: {
      ...counts,
      unique_object_numbers: ids.size,
      duplicate_object_numbers: duplicates.length,
      duplicate_rows_beyond_first: duplicates.reduce((sum, [, count]) => sum + count - 1, 0),
      visual_field_presence: visualFieldPresence,
    },
    duplicate_details: duplicates.map(([object_number, count]) => ({ object_number, count })),
    top_level_fields: [...topLevelFields.entries()].map(([key, count]) => {
      const [field, type] = key.split("\u0000");
      return { field, type, count };
    }).sort((a, b) => a.field.localeCompare(b.field) || a.type.localeCompare(b.type)),
    relevant_field_locations: [...relevantPaths.entries()].map(([key, count]) => {
      const [field_path, type] = key.split("\u0000");
      return { field_path, type, count };
    }).sort((a, b) => a.field_path.localeCompare(b.field_path) || a.type.localeCompare(b.type)),
    representative_records: samples,
    _ids: ids,
    _comparison: comparison,
  };
}

function compareSources(da, en) {
  const daIds = new Set(da._ids.keys());
  const enIds = new Set(en._ids.keys());
  const daOnly = [...daIds].filter((id) => !enIds.has(id)).sort();
  const enOnly = [...enIds].filter((id) => !daIds.has(id)).sort();
  const overlap = [...daIds].filter((id) => enIds.has(id));
  const fieldDifferences = Object.fromEntries(COMPARE_FIELDS.map((field) => [field, 0]));
  const differenceExamples = Object.fromEntries(COMPARE_FIELDS.map((field) => [field, []]));
  for (const id of overlap) {
    const left = da._comparison.get(id);
    const right = en._comparison.get(id);
    for (const field of COMPARE_FIELDS) {
      if (left[field] !== right[field]) {
        fieldDifferences[field] += 1;
        if (differenceExamples[field].length < 5) differenceExamples[field].push(id);
      }
    }
  }
  return {
    overlap_unique_object_numbers: overlap.length,
    da_only_count: daOnly.length,
    en_only_count: enOnly.length,
    da_only_object_numbers: daOnly,
    en_only_object_numbers: enOnly,
    selected_field_difference_counts_on_overlap: fieldDifferences,
    selected_field_difference_examples: Object.fromEntries(
      Object.entries(differenceExamples).filter(([, ids]) => ids.length > 0),
    ),
  };
}

const startedAt = new Date().toISOString();
const results = [];
for (const source of SOURCES) {
  process.stderr.write(`Inspecting ${source.file}...\n`);
  results.push(await inspectSource(source));
}
const comparison = compareSources(results[0], results[1]);
for (const result of results) {
  delete result._ids;
  delete result._comparison;
}

const output = {
  reconnaissance_version: "1.0.0",
  tool: { name: "tools/source-reconnaissance.mjs", version: "1.0.0", runtime: process.version },
  started_at_utc: startedAt,
  generated_at_utc: new Date().toISOString(),
  sources: results,
  identity_comparison: comparison,
};
await mkdir("data/reports", { recursive: true });
await writeFile("data/reports/source-reconnaissance.json", `${JSON.stringify(output, null, 2)}\n`);
process.stdout.write(`${JSON.stringify(output, null, 2)}\n`);
