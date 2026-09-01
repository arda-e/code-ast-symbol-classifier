/**
 * Identifier tokens, namespaced and hashed.
 *
 * Mirrors src/code_ast_symbol_classifier/features/lexical.py exactly,
 * including three rules that are NOT spelled out as general rules in the
 * Python module's own docstring but are required to reproduce
 * contracts/fixtures/vector-golden.json:
 *
 *   1. A leading "this" receiver is dropped from callee tokens.
 *   2. A generic wrapper on returnType (Promise<Order>) is unwrapped to its
 *      inner type (Order) before splitting.
 *   3. The file path's extension is dropped before splitting.
 *
 * All three were reverse-engineered from vector-golden.json on the Python
 * side and verified against it there before this port was written.
 */

import type { FeatureSpec, SymbolRecord } from "./types";

const DELIMITER_RE = /[_\-./]/;
const CASE_BOUNDARY_RE = /[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z0-9]+|[A-Z0-9]+/g;
const STOPWORDS = new Set(["this"]);
const GENERIC_WRAPPER_RE = /^\w+<(.+)>$/;

export function splitIdentifier(identifier: string): string[] {
  if (!identifier) return [];

  const tokens: string[] = [];
  for (const part of identifier.split(DELIMITER_RE)) {
    if (!part) continue;
    const matches = part.match(CASE_BOUNDARY_RE);
    if (!matches) continue;
    for (const sub of matches) {
      if (sub) tokens.push(sub.toLowerCase());
    }
  }
  return tokens.filter((token) => !STOPWORDS.has(token));
}

function stripGenericWrapper(typeString: string): string {
  const match = typeString.match(GENERIC_WRAPPER_RE);
  return match ? match[1] : typeString;
}

function stripExtension(filePath: string): string {
  const lastDot = filePath.lastIndexOf(".");
  return lastDot === -1 ? filePath : filePath.slice(0, lastDot);
}

export function lexicalFeatures(record: SymbolRecord, spec: FeatureSpec): string[] {
  const features: string[] = [];

  for (const prefix of spec.namespaces) {
    let source: string[];
    switch (prefix) {
      case "name":
        source = [record.name];
        break;
      case "owner":
        source = record.owner ? [record.owner] : [];
        break;
      case "path":
        source = [stripExtension(record.filePath)];
        break;
      case "callee":
        source = record.callees;
        break;
      case "accepts":
        source = record.paramTypes;
        break;
      case "returns":
        source = record.returnType ? [stripGenericWrapper(record.returnType)] : [];
        break;
      default:
        source = [];
    }

    for (const value of source) {
      for (const token of splitIdentifier(value)) {
        features.push(`${prefix}:${token}`);
      }
    }
  }

  return features;
}
