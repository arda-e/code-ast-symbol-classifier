# Data contract

This repository trains and evaluates. It does not parse TypeScript. The boundary
between the two is a JSONL file, and this page defines it.

## Input: one symbol per line

```json
{
  "id": "src/orders/order.service.ts#OrderService.placeOrder",
  "name": "placeOrder",
  "owner": "OrderService",
  "filePath": "src/orders/order.service.ts",
  "kind": "method",
  "callees": ["this.orderFactory.create", "this.inventory.reserve"],
  "paramTypes": ["CreateOrderDto"],
  "returnType": "Promise<Order>",
  "numeric": { "outDegree": 4, "inDegree": 3, "awaitCount": 4 },
  "extractorVersion": "v1"
}
```

`id`, `name`, `filePath` and `kind` are required. Everything else defaults to
empty, and a numeric field that is absent is zero.

Note what is **not** here: the function body. No statements, no comments, no
variable names. Callee names are the only thing taken from inside the body, and
they arrive already reduced to names.

`numeric` keys come from [`contracts/feature-spec.v1.json`](../contracts/feature-spec.v1.json).
Keys the current spec does not know about are ignored rather than rejected —
that is a version skew to notice, not a parse error.

## Labels: a separate, separately versioned file

```json
{
  "labelsetId": "labelset-v1",
  "taxonomyVersion": "v1",
  "labels": { "src/orders/order.service.ts#OrderService.placeOrder": "orchestrator" }
}
```

`taxonomyVersion` is not decoration. A label set produced against a different
class list joins perfectly well against these symbols and would train a model on
classes that no longer exist, so the loader refuses the mismatch outright.

## Two stages, two versions

The numeric fields are not all available at the same moment, and each field in
the spec carries a `stage` saying which:

```
PARSE                          AFTER THE GRAPH IS BUILT
─────                          ────────────────────────
lexical names                  outDegree (finalised)
AST counters                   inDegree
flags, sizes                   distinctCallers
side effects, mutations        entrypointDistance
```

Classification cannot happen during parsing, because `inDegree` is unknowable
there — you would need every other file already parsed — and even `outDegree` is
not final until call resolution has run. It cannot happen entirely after the
graph either, because counters like `comparisonCount` need the AST, which the
graph no longer holds.

So parse-time features ride along on the symbol, and the graph-global block is
appended once the graph exists. Two producers, two version numbers:

- **`extractorVersion`** — the parse-time extractor
- **`featureVersion`** — the vector layout as a whole

They move independently, and both are separate from the model version. Model
versions change several times a day during experimentation; parse output does
not. Folding classification into the parse step would tie the parse cache to the
model version and re-parse thousands of unchanged files on every retrain.

## One consequence worth knowing

Graph-global features make classification non-incremental. A file changes, a new
call appears, and some symbol nobody edited now has `inDegree` 4 instead of 3 —
its classification can change without its code changing.

That is why the ablation splits `B-local` from `B-global`. If the graph-global
block contributes little, the whole complication can be dropped and
classification can stay file-incremental.

## Fixtures

`data/fixtures/` holds a small synthetic set used by the tests and by a smoke
run. It is not training data and no score from it means anything — see the note
inside `labels.sample.json`.

Real label sets belong in `data/labels/`, one file per version. Machine-local
corpora (clones, extractions, external repositories) stay in `data/raw/`,
`data/processed/` and `data/external/`, all of which are ignored by git: if a
file cannot be reproduced on another machine, it cannot be an input to a run that
CI is expected to repeat.
