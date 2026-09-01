/**
 * The fixed-order numeric block.
 *
 * Mirrors src/code_ast_symbol_classifier/features/numeric.py exactly,
 * including the entrypointDistance = -1 ("unreachable") sentinel — every
 * other field's absence reads as 0.0.
 */

import type { NumericField, SymbolRecord } from "./types";

const ABSENCE_DEFAULTS: Record<string, number> = {
  entrypointDistance: -1.0,
};

export function numericVector(record: SymbolRecord, fields: NumericField[]): number[] {
  return fields.map(
    (field) => record.numeric[field.name] ?? ABSENCE_DEFAULTS[field.name] ?? 0.0
  );
}
