/**
 * Mirrors src/code_ast_symbol_classifier/data/records.py (SymbolRecord) and
 * features/spec.py (HashConfig, NumericField, FeatureSpec).
 *
 * JSON/contract keys stay camelCase here (filePath, paramTypes, returnType,
 * numericFields) to match contracts/fixtures/vector-golden.json and
 * contracts/feature-spec.v1.json directly — Python renames these to
 * snake_case on its own side (file_path, param_types, return_type) when it
 * parses the same JSON, so the two are equivalent, not identical spellings.
 */

export interface SymbolRecord {
  id: string;
  name: string;
  filePath: string;
  kind: string;
  owner?: string | null;
  callees: string[];
  paramTypes: string[];
  returnType?: string | null;
  numeric: Record<string, number>;
  extractorVersion?: string;
}

export interface HashConfig {
  algorithm: string;
  seed: number;
  buckets: number;
  signed: boolean;
  encoding: string;
  occurrence: string;
}

export interface NumericField {
  name: string;
  group: string;
  stage: string;
  description?: string;
}

/** field.stage === "post-graph" — mirrors NumericField.is_graph_global in spec.py. */
export function isGraphGlobal(field: NumericField): boolean {
  return field.stage === "post-graph";
}

/** Which blocks one ablation variant switches on. Mirrors VariantConfig in spec.py. */
export interface VariantConfig {
  name: string;
  useLexical: boolean;
  numericGroups: string[];
}

export interface FeatureSpec {
  version: string;
  hash: HashConfig;
  namespaces: string[];
  numericFields: NumericField[];
  variants: Record<string, VariantConfig>;
}

/** Mirrors FeatureSpec.fields_in_groups in spec.py. */
export function fieldsInGroups(spec: FeatureSpec, groups: string[]): NumericField[] {
  const wanted = new Set(groups);
  return spec.numericFields.filter((field) => wanted.has(field.group));
}

/** Mirrors FeatureSpec.variant(name) in spec.py — throws on an unknown variant. */
export function getVariant(spec: FeatureSpec, name: string): VariantConfig {
  const variant = spec.variants[name];
  if (!variant) {
    const known = Object.keys(spec.variants).sort().join(", ");
    throw new Error(`unknown ablation variant "${name}"; known variants: ${known}`);
  }
  return variant;
}

/** Mirrors FeatureSpec.vector_size in spec.py. */
export function vectorSize(spec: FeatureSpec): number {
  return spec.hash.buckets + spec.numericFields.length;
}
