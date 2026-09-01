/**
 * The feature contract, loaded and enforced.
 *
 * Mirrors src/code_ast_symbol_classifier/features/spec.py. The hash
 * primitive itself lives in hashing.ts; this module is about the shape of
 * the vector — namespaces, numeric fields, ablation variants.
 */

import type { FeatureSpec, HashConfig, NumericField, VariantConfig } from "./types";

const SUPPORTED_HASH_ALGORITHM = "murmur3_x86_32";

export class FeatureSpecError extends Error {}

export function loadFeatureSpec(raw: unknown): FeatureSpec {
  const data = raw as Record<string, any>;

  return {
    version: data.featureVersion,
    hash: readHashConfig(data.hash),
    namespaces: data.lexical.namespaces.map((n: any) => n.prefix as string),
    numericFields: readNumericFields(data.numeric.fields),
    variants: readVariants(data.ablationVariants),
  };
}

function readHashConfig(raw: Record<string, any>): HashConfig {
  if (raw.algorithm !== SUPPORTED_HASH_ALGORITHM) {
    throw new FeatureSpecError(
      `unsupported hash algorithm "${raw.algorithm}"; changing it requires a new ` +
        "featureVersion and a regenerated golden fixture"
    );
  }
  return {
    algorithm: raw.algorithm,
    seed: Number(raw.seed),
    buckets: Number(raw.buckets),
    signed: Boolean(raw.signed),
    encoding: raw.encoding,
    occurrence: raw.occurrence,
  };
}

function readNumericFields(raw: any[]): NumericField[] {
  const fields = raw.map((field) => ({
    name: field.name as string,
    group: field.group as string,
    stage: field.stage as string,
    description: field.description ?? "",
  }));

  const names = fields.map((f) => f.name);
  const duplicates = names.filter((name, i) => names.indexOf(name) !== i);
  if (duplicates.length > 0) {
    throw new FeatureSpecError(`duplicate numeric fields: ${[...new Set(duplicates)].sort().join(", ")}`);
  }
  return fields;
}

function readVariants(raw: Record<string, any>): Record<string, VariantConfig> {
  const variants: Record<string, VariantConfig> = {};
  for (const [name, value] of Object.entries(raw)) {
    // Skips non-variant entries such as the spec's own "rationale" note —
    // those are strings, not objects.
    if (value && typeof value === "object" && !Array.isArray(value)) {
      variants[name] = {
        name,
        useLexical: Boolean(value.lexical),
        numericGroups: (value.numericGroups ?? []).map(String),
      };
    }
  }
  return variants;
}
