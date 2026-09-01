/**
 * The hash contract, alone in its own module.
 *
 * Mirrors src/code_ast_symbol_classifier/features/hashing.py exactly. This is
 * the single most fragile file in the whole port: a TS implementation that
 * gets any one knob wrong (variant, seed, signed/unsigned, encoding) produces
 * a model that still runs, still returns confident answers, and is quietly
 * worse. See contracts/feature-spec.v1.json -> hash.traps.
 *
 * No external murmurhash package is used on purpose — a dependency update
 * could silently change behaviour. This is a direct, from-scratch port of
 * MurmurHash3 x86_32 (the variant contracts/feature-spec.v1.json pins),
 * verified against contracts/fixtures/hash-golden.json (see
 * ts/test/golden.test.ts).
 */

import type { HashConfig } from "./types";

function murmur3X86_32(bytes: Uint8Array, seed: number): number {
  const c1 = 0xcc9e2d51;
  const c2 = 0x1b873593;
  let h1 = seed | 0;
  const length = bytes.length;
  const blockCount = Math.floor(length / 4);

  for (let i = 0; i < blockCount; i++) {
    let k1 =
      (bytes[i * 4] |
        (bytes[i * 4 + 1] << 8) |
        (bytes[i * 4 + 2] << 16) |
        (bytes[i * 4 + 3] << 24)) |
      0;

    k1 = Math.imul(k1, c1);
    k1 = (k1 << 15) | (k1 >>> 17);
    k1 = Math.imul(k1, c2);

    h1 ^= k1;
    h1 = (h1 << 13) | (h1 >>> 19);
    h1 = (Math.imul(h1, 5) + 0xe6546b64) | 0;
  }

  let k1 = 0;
  const tailStart = blockCount * 4;
  const tailLength = length & 3;
  if (tailLength === 3) k1 ^= bytes[tailStart + 2] << 16;
  if (tailLength >= 2) k1 ^= bytes[tailStart + 1] << 8;
  if (tailLength >= 1) {
    k1 ^= bytes[tailStart];
    k1 = Math.imul(k1, c1);
    k1 = (k1 << 15) | (k1 >>> 17);
    k1 = Math.imul(k1, c2);
    h1 ^= k1;
  }

  h1 ^= length;

  // fmix32
  h1 ^= h1 >>> 16;
  h1 = Math.imul(h1, 0x85ebca6b);
  h1 ^= h1 >>> 13;
  h1 = Math.imul(h1, 0xc2b2ae35);
  h1 ^= h1 >>> 16;

  return h1 >>> 0; // force unsigned — see hash.traps.signed in the spec
}

/**
 * Map a feature string onto a fixed-size bucket index.
 *
 * `TextEncoder` produces UTF-8 bytes, matching Python's
 * `feature_string.encode("utf-8")` exactly. Do not swap this for
 * `Buffer.from(s)` without checking — the intent is the same, but keeping
 * TextEncoder makes this file portable outside Node too.
 */
export function hashBucket(featureString: string, config: HashConfig): number {
  const bytes = new TextEncoder().encode(featureString);
  const hash = murmur3X86_32(bytes, config.seed);
  return hash % config.buckets;
}
