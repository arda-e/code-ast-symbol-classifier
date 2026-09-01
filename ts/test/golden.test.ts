import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { hashBucket } from "../src/features/hashing";
import { lexicalFeatures } from "../src/features/lexical";
import { numericVector } from "../src/features/numeric";
import { readArtifact, predictProba, ArtifactError } from "../src/model/artifact";
import type { FeatureSpec, HashConfig, NumericField, SymbolRecord } from "../src/features/types";

// NOTE: this path is computed relative to the COMPILED file's location
// (dist/test/golden.test.js), not the source file's location (test/golden.test.ts).
//
//   ts/dist/test/golden.test.js   <- __dirname points here (tsc compiles into outDir=dist)
//        ..  -> ts/dist
//        ..  -> ts
//        ..  -> repo root
//   repo root + "contracts"       <- target
//
// Three levels up are required, not two. Because tsconfig.json has
// "rootDir": ".", ts/test/golden.test.ts compiles to ts/dist/test/golden.test.js
// (an extra "dist" layer is inserted), so the compiled file's relative
// position differs by one level from the source file's.
const CONTRACTS_DIR = join(__dirname, "..", "..", "..", "contracts");

function loadJSON(relativePath: string): any {
  return JSON.parse(readFileSync(join(CONTRACTS_DIR, relativePath), "utf-8"));
}

test("hash-golden.json: every feature string lands in the expected bucket", () => {
  const golden = loadJSON("fixtures/hash-golden.json");
  const config: HashConfig = golden.hash;

  for (const { input, bucket } of golden.cases) {
    assert.equal(hashBucket(input, config), bucket, `mismatch for "${input}"`);
  }
});

test("vector-golden.json: lexicalFeatures + hashBucket + numericVector match exactly", () => {
  const golden = loadJSON("fixtures/vector-golden.json");
  const record: SymbolRecord = {
    id: golden.record.id,
    name: golden.record.name,
    owner: golden.record.owner ?? null,
    filePath: golden.record.filePath,
    kind: golden.record.kind,
    callees: golden.record.callees,
    paramTypes: golden.record.paramTypes,
    returnType: golden.record.returnType ?? null,
    numeric: golden.record.numeric,
  };

  const spec: FeatureSpec = {
    version: golden.featureVersion,
    hash: golden.hash ?? {
      algorithm: "murmur3_x86_32",
      seed: 0,
      buckets: 4096,
      signed: false,
      encoding: "utf-8",
      occurrence: "binary",
    },
    namespaces: ["name", "owner", "path", "callee", "accepts", "returns"],
    numericFields: [],
    variants: {},
  };

  const gotLexical = new Set(lexicalFeatures(record, spec));
  const expectedLexical = new Set(golden.expectedLexicalFeatures);
  assert.deepEqual(gotLexical, expectedLexical, "lexical feature strings differ");

  const gotBuckets = [...new Set([...gotLexical].map((f) => hashBucket(f, spec.hash)))].sort(
    (a, b) => a - b
  );
  assert.deepEqual(
    gotBuckets,
    [...golden.expectedBuckets].sort((a: number, b: number) => a - b)
  );

  const fields: NumericField[] = golden.numericFieldOrder.map((name: string) => ({
    name,
    group: "",
    stage: "",
  }));
  const gotNumeric = numericVector(record, fields);
  assert.deepEqual(gotNumeric, golden.expectedNumericValues);
});

test("artifact: predict_proba matches the tiny_artifact scenario from test_artifact.py", () => {
  const raw = {
    artifactVersion: "1",
    featureVersion: "v1",
    taxonomyVersion: "v1",
    labelsetId: "test",
    createdAt: "",
    buckets: 1,
    numericFields: ["outDegree"],
    classes: ["a", "b"],
    coef: [
      [1.0, 0.0],
      [0.0, 1.0],
    ],
    intercept: [0.0, 0.0],
    scaler: { mean: [0.0], scale: [1.0] },
    thresholds: { accept: 0.85, tentative: 0.65 },
    training: {},
  };

  const artifact = readArtifact(raw);
  const probabilities = predictProba(artifact, [1.0, 0.0]);

  const sum = probabilities.reduce((a, b) => a + b, 0);
  assert.ok(Math.abs(sum - 1.0) < 1e-9, "probabilities should sum to 1");
  assert.ok(
    Math.abs(probabilities[0] - Math.exp(1) / (Math.exp(1) + 1)) < 1e-9,
    "probabilities[0] should match e/(e+1), same as test_predict_proba_is_a_softmax_over_the_logits"
  );
});

test("artifact: predict_proba rejects a vector of the wrong size", () => {
  const artifact = readArtifact({
    artifactVersion: "1",
    featureVersion: "v1",
    taxonomyVersion: "v1",
    labelsetId: "test",
    createdAt: "",
    buckets: 1,
    numericFields: ["outDegree"],
    classes: ["a", "b"],
    coef: [
      [1, 0],
      [0, 1],
    ],
    intercept: [0, 0],
    scaler: null,
    thresholds: {},
    training: {},
  });

  assert.throws(
    () => predictProba(artifact, [1, 0, 3]),
    (err: unknown) => err instanceof ArtifactError && /expects 2/.test((err as Error).message)
  );
});

test("artifact: readArtifact rejects a featureVersion mismatch", () => {
  const raw = {
    artifactVersion: "1",
    featureVersion: "v1",
    taxonomyVersion: "v1",
    labelsetId: "test",
    createdAt: "",
    buckets: 1,
    numericFields: ["outDegree"],
    classes: ["a", "b"],
    coef: [
      [1, 0],
      [0, 1],
    ],
    intercept: [0, 0],
    scaler: null,
    thresholds: {},
    training: {},
  };

  assert.throws(
    () => readArtifact(raw, "v2"),
    (err: unknown) => err instanceof ArtifactError && /retrain rather than predict/.test((err as Error).message)
  );
});
