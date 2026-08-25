# code-ast-symbol-classifier

Predicts what a code symbol was written **for** — its architectural intent —
from its names and a block of facts the code graph already knows.

The graph can already answer "does this touch the database", "what does it call",
"how many things call it". What it structurally cannot see is why a symbol
exists. A function that calls nothing, mutates nothing and returns a boolean has
the same graph signature whether it is a helper, an input check, a permission
decision, or a business rule. That gap is what this model is for.

## How it works

```
placeOrder
     │
 ┌───┴────┐
 ▼        ▼
names   graph / AST facts
 │        │
 │ split  │
 │ prefix │
 │ hash   │
 │        ▼
 │   fixed-order numeric block, scaled
 └───┬────┘
     ▼
 concatenate  →  logistic regression  →  10 class probabilities
```

Everything before the classifier is deterministic feature engineering — the same
symbol always produces the same vector, and none of it learns. The classifier is
the only part that learns, and what it learns is a weight matrix and a bias
vector. Inference is multiply, add, softmax, which is why the deployable artifact
is a few hundred KB of JSON with no runtime attached.

## Getting started

```bash
make setup
make test
make inspect
```

`inspect` works before any model exists and prints what the project is currently
committed to — including which class definitions are still missing.

## Where the work is

Four modules ship as signatures and docstrings with `NotImplementedError` bodies.
Their tests are already written and currently fail; each assertion is the
specification for the thing it tests.

| module | what it has to do |
|---|---|
| [`features/lexical.py`](src/code_ast_symbol_classifier/features/lexical.py) | split identifiers, prefix them by source, produce feature strings |
| [`features/numeric.py`](src/code_ast_symbol_classifier/features/numeric.py) | read the numeric facts out in contract order |
| [`features/build.py`](src/code_ast_symbol_classifier/features/build.py) | concatenate the two blocks, scale the numeric one, honour the variant |
| [`model/train.py`](src/code_ast_symbol_classifier/model/train.py) | fit the logistic regression |

```bash
make spec     # the failing specifications — this is the to-do list
```

Everything else is in place: contracts, loaders, cross-validation, metrics,
reporting, the ablation runner and the CLI.

## Contracts

These files are the point of the repository. A future TypeScript inference port
reads them, and two of them can break silently — a mismatch raises nothing, it
only makes the model quietly worse.

| file | what it pins |
|---|---|
| [`contracts/feature-spec.v1.json`](contracts/feature-spec.v1.json) | hash algorithm, seed, buckets, namespaces, and the exact order of the 67 numeric fields |
| [`contracts/taxonomy.v1.yaml`](contracts/taxonomy.v1.yaml) | the ten classes and the confidence thresholds |
| [`contracts/model-artifact.md`](contracts/model-artifact.md) | the deployable JSON: weights, bias, scaler, versions |
| `contracts/fixtures/*.json` | golden cases both languages must reproduce |

Changing the feature spec means a new `featureVersion` and `make golden` to
regenerate the fixtures.

## Commands

```bash
make inspect     # what the contracts declare
make evaluate    # stratified 5-fold, full report into reports/
make ablate      # A / B-local / B-global / C comparison
make train       # fit on everything, write models/model.v1.json
make lint typecheck test
```

## Reading order

1. [`docs/taxonomy.md`](docs/taxonomy.md) — the ten classes, the pairs that get argued about, and what is still undefined
2. [`docs/data-contract.md`](docs/data-contract.md) — the input format, and why parse-time and graph-time features are versioned separately
3. [`docs/reporting-checklist.md`](docs/reporting-checklist.md) — what has to be in a result before it is shareable

## Two open items that block work downstream

- **The class definitions do not exist.** The taxonomy lists ten classes and
  summarises them; nobody has written what they mean. Labelling before that is
  labelling against a guess.
- **The existing labels target the old 14-class taxonomy** and cannot be carried
  over. The loader refuses the mismatch rather than training on classes that no
  longer exist.
