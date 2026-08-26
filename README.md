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
make explain      # one symbol, walked through every stage
make progress     # what is done, what is next
```

Read [`docs/walkthrough.md`](docs/walkthrough.md) alongside `make explain` — the
same symbol and the same numbers, one live and one explained. Unfamiliar terms
are in [`docs/glossary.md`](docs/glossary.md), each pointing at the file where it
turns up.

`make inspect` works before any model exists and prints what the project is
currently committed to, including which class definitions are still missing.

## Where the work is

Five stages, in order. Each is a failing test file that opens with what you are
building and why it is done that way; the assertions are the specification.

| stage | what you build | module |
|---|---|---|
| 1 | split identifiers into words | `features/lexical.py` |
| 2 | label each word with where it came from | `features/lexical.py` |
| 3 | lay the numeric facts out in contract order | `features/numeric.py` |
| 4 | join the two blocks and scale one | `features/build.py` |
| 5 | fit the classifier | `model/train.py` |

Stage 5 is three lines, and that is the point: everything before it is
deterministic feature engineering, and only the last stage learns anything.

```bash
make progress                                    # the ordered to-do list
uv run pytest tests/spec/test_stage1_split.py    # start here
```

Everything downstream is already built and tested — contracts, loaders,
cross-validation, metrics, reporting, the ablation runner and the CLI. They are
waiting on these five stages.

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
make explain     # one symbol through every stage
make progress    # stage-by-stage status
make inspect     # what the contracts declare
make evaluate    # stratified 5-fold, full report into reports/
make ablate      # A / B-local / B-global / C comparison
make train       # fit on everything, write models/model.v1.json
make lint typecheck test
```

`explain` takes `--symbol`, matching an id or part of a name:

```bash
uv run code-ast-symbol-classifier explain --symbol isEligible
```

## Reading order

1. [`docs/walkthrough.md`](docs/walkthrough.md) — one symbol from source to prediction, with the real numbers, and which part of this is actually machine learning
2. [`docs/glossary.md`](docs/glossary.md) — the terms, each pointing at the file where it appears
3. [`docs/taxonomy.md`](docs/taxonomy.md) — the ten classes, the pairs that get argued about, and what is still undefined
4. [`docs/data-contract.md`](docs/data-contract.md) — the input format, and why parse-time and graph-time features are versioned separately
5. [`docs/reporting-checklist.md`](docs/reporting-checklist.md) — what has to be in a result before it is shareable

## Two open items that block work downstream

- **The class definitions do not exist.** The taxonomy lists ten classes and
  summarises them; nobody has written what they mean. Labelling before that is
  labelling against a guess.
- **The existing labels target the old 14-class taxonomy** and cannot be carried
  over. The loader refuses the mismatch rather than training on classes that no
  longer exist.
