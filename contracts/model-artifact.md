# Model artifact contract

Training ends in a file. Inference reads that file and does multiply, add, softmax —
nothing is learned at prediction time. This document defines the file, because it is
the entire deployment story: a few hundred KB of JSON, no runtime, no native
dependency, no model download.

## Shape

```json
{
  "artifactVersion": "1",
  "featureVersion": "v1",
  "taxonomyVersion": "v1",
  "labelsetId": "labelset-v1",
  "createdAt": "2026-08-25T12:00:00Z",

  "hash": { "algorithm": "murmur3_x86_32", "seed": 0, "buckets": 4096, "signed": false, "occurrence": "binary" },
  "numericFields": ["outDegree", "inDegree", "..."],

  "classes": ["adapter", "configuration", "domain_logic", "..."],
  "coef": [[0.13, -0.02, "..."], "..."],
  "intercept": [0.01, -0.44, "..."],

  "scaler": {
    "mean": [3.1, 2.4, "..."],
    "scale": [1.8, 2.2, "..."]
  },

  "thresholds": { "accept": 0.85, "tentative": 0.65 },
  "training": { "variant": "C", "C": 0.5, "classWeight": "balanced", "maxIter": 1000, "seed": 42, "sampleCount": 0 }
}
```

## Rules

- **`coef` is `[n_classes][n_features]`**, and `n_features` equals
  `hash.buckets + len(numericFields)`. The hashed block comes first; the numeric
  block follows in exactly the `numericFields` order. That order is copied from the
  feature spec into the artifact on purpose — a consumer must be able to validate
  its own layout without also resolving the right version of the spec file.
- **`classes` order matches `coef` rows.** Row *i* scores class *i*.
- **The scaler applies to the numeric block only.** The hashed block is 0/1 and is
  not scaled. Skipping the scaler at inference does not raise; it just scores worse.
- **`featureVersion` and `taxonomyVersion` are refusal conditions, not metadata.**
  A consumer reading an artifact whose `featureVersion` differs from its own
  extractor's version must refuse to run rather than predict with a shifted vector.
- **`numericFields` may not be reordered in place.** Adding, removing or moving a
  field means a new `featureVersion` and a regenerated golden fixture.

## Why versions are separate

`featureVersion` tracks the extractor and the vector layout. `taxonomyVersion`
tracks the label set. They move independently: a taxonomy change retrains the model
but leaves the vector alone, while a new counter changes the vector but not the
classes. Collapsing them into one number forces needless invalidation on both sides.

The same reasoning applies upstream: the parse-time feature extractor carries its
own version, separate from the parser's. Model versions change several times a day
during experimentation; parse output does not.
