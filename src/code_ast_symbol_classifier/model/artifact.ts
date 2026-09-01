/**
 * Reading the deployable model file and scoring one vector with it.
 *
 * Mirrors contracts/model-artifact.md and the read side of
 * src/code_ast_symbol_classifier/model/artifact.py. Nothing here trains
 * anything — multiply, add, softmax, per the artifact's own coef/intercept.
 */

import { hashBucket } from "../features/hashing";
import { lexicalFeatures } from "../features/lexical";
import { numericVector } from "../features/numeric";
import type { FeatureSpec, HashConfig, NumericField, SymbolRecord } from "../features/types";

export interface ScalerParams {
  mean: number[];
  scale: number[];
}

export interface ModelArtifact {
  artifactVersion: string;
  featureVersion: string;
  taxonomyVersion: string;
  labelsetId: string;
  createdAt: string;
  buckets: number;
  numericFields: string[];
  classes: string[];
  coef: number[][]; // [n_classes][n_features]
  intercept: number[]; // [n_classes]
  scaler: ScalerParams | null;
  thresholds: Record<string, number>;
  training: Record<string, unknown>;
}

export class ArtifactError extends Error {}

/**
 * Load an artifact, refusing a feature-version mismatch.
 *
 * Refusing is correct rather than strict: a vector built by a different
 * extractor version lines up column-for-column with the trained weights and
 * produces confident nonsense (model-artifact.md: "refusal conditions, not
 * metadata").
 */
export function readArtifact(raw: unknown, expectedFeatureVersion?: string): ModelArtifact {
  const data = raw as Record<string, any>;

  if (expectedFeatureVersion !== undefined && data.featureVersion !== expectedFeatureVersion) {
    throw new ArtifactError(
      `artifact was trained on featureVersion "${data.featureVersion}" but the current ` +
        `feature spec is "${expectedFeatureVersion}"; retrain rather than predict`
    );
  }

  const scaler = data.scaler;
  return {
    artifactVersion: data.artifactVersion,
    featureVersion: data.featureVersion,
    taxonomyVersion: data.taxonomyVersion,
    labelsetId: data.labelsetId ?? "unknown",
    createdAt: data.createdAt ?? "",
    buckets: Number(data.buckets),
    numericFields: data.numericFields,
    classes: data.classes,
    coef: data.coef,
    intercept: data.intercept,
    scaler: scaler ? { mean: scaler.mean, scale: scaler.scale } : null,
    thresholds: data.thresholds ?? {},
    training: data.training ?? {},
  };
}

function vectorSize(artifact: ModelArtifact): number {
  return artifact.buckets + artifact.numericFields.length;
}

/**
 * Build the full feature vector for one symbol.
 *
 * Uses `spec.hash` for hashing (algorithm/seed/signed/encoding), because the
 * artifact itself does NOT carry those — only `buckets` (a count, not a
 * config). The featureVersion refusal check in readArtifact() is what
 * guarantees spec.hash still matches what trained this artifact: those
 * settings only change with a featureVersion bump, which forces a retrain.
 */
export function buildInferenceVector(
  record: SymbolRecord,
  spec: FeatureSpec,
  artifact: ModelArtifact
): number[] {
  const size = vectorSize(artifact);
  const vector = new Array<number>(size).fill(0);

  for (const featureString of lexicalFeatures(record, spec)) {
    const bucket = hashBucket(featureString, spec.hash);
    vector[bucket] = 1;
  }

  const fields: NumericField[] = artifact.numericFields.map((name) => ({
    name,
    group: "",
    stage: "",
  }));
  const raw = numericVector(record, fields);
  const scaled = artifact.scaler
    ? raw.map((v, i) => (v - artifact.scaler!.mean[i]) / artifact.scaler!.scale[i])
    : raw;

  scaled.forEach((v, i) => {
    vector[artifact.buckets + i] = v;
  });

  return vector;
}

/**
 * Score one already-built feature vector. Multiply, add, softmax.
 */
export function predictProba(artifact: ModelArtifact, vector: number[]): number[] {
  const expected = vectorSize(artifact);
  if (vector.length !== expected) {
    throw new ArtifactError(`vector has ${vector.length} features, artifact expects ${expected}`);
  }

  const logits = artifact.coef.map((row, classIndex) => {
    let sum = artifact.intercept[classIndex];
    for (let i = 0; i < row.length; i++) {
      sum += row[i] * vector[i];
    }
    return sum;
  });

  const maxLogit = Math.max(...logits);
  const shifted = logits.map((l) => Math.exp(l - maxLogit));
  const total = shifted.reduce((a, b) => a + b, 0);
  return shifted.map((v) => v / total);
}
