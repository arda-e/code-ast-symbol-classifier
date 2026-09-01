# Glossary

Each term says where in the repository you will meet it. The order roughly
follows the pipeline rather than the alphabet, because the terms build on one
another.

## The problem

**architectural intent** — What a symbol was written *for*. The thing we are
trying to predict. "Does it write to the database" is a mechanical fact and the
graph's job; "is this a business rule or is it just reshaping data" is a
judgement and the model's job.
→ `contracts/taxonomy.v1.yaml`, `docs/taxonomy.md`

**outDegree / inDegree** — How many distinct things a symbol calls / how many
places call it. The asymmetry between them shapes the architecture: you can find
outDegree by looking at one file, but not inDegree — for that you need the whole
codebase.
→ `contracts/feature-spec.v1.json` (the `degree` group)

**graph-global / file-local** — Whether a feature needs the entire graph or just
one file. The moment you use a graph-global feature, classification can no longer
be file-incremental: a symbol nobody touched can change class because a different
file started calling it.
→ `features/spec.py` → `NumericField.is_graph_global`

## Feature engineering

**feature engineering** — Turning raw data into numbers a model can take.
Deterministic: same input, same output. It contains no learning, and it is most
of this pipeline.
→ the whole `features/` package

**token** — An identifier after splitting. `placeOrder` → `place`, `order`.
→ stage 1, `features/lexical.py`

**namespace** — The source tag at the front of a feature string: `name:`,
`callee:`, `path:`. It keeps the same word distinguishable by origin, so
`name:validate` and `callee:validate` stay different signals.
→ stage 2, `contracts/feature-spec.v1.json` → `lexical.namespaces`

**feature hashing** — Reducing a feature string to a position in a fixed-size
vector. The goal is not to produce meaning but to make a vocabulary unnecessary.
The chosen function is MurmurHash3 x86_32 with a fixed seed.
→ `features/hashing.py`

**collision** — Two different feature strings landing in the same bucket. The
unavoidable price of a fixed-size space; rare in practice because a symbol only
uses about 20 of 4096 buckets.
→ visible in `make explain` output

**binary presence** — Recording whether a feature occurred, not how many times
(`1` or `0`). Repetition is already represented in the numeric block, and giving
the model the same information twice does not help it.
→ `contracts/feature-spec.v1.json` → `hash.occurrence`

**sparse** — A vector where most entries are zero. About 35 of 4163 positions are
filled, so only the non-zero ones are stored.
→ `features/build.py` (`csr_matrix`)

**StandardScaler / scaling** — Bringing the numeric block onto a common scale
(subtract the mean, divide by the spread). Without it a single value like
`inDegree = 47` drowns out the other four thousand positions.
→ stage 4

**data leakage** — Test data influencing training. The typical form here: fitting
the scaler on all the data. It raises nothing and simply makes every score look
better than it is.
→ `pipeline.py` → `_run_fold`

## The model

**logistic regression** — Despite "regression" in the name, it is used for
classification. Everything it learns is a weight matrix and a bias vector. It can
also be read as a single-layer neural network.
→ stage 5, `model/train.py`

**logit** — The raw score before softmax. Its range is unbounded; on its own it
means nothing, and only comparisons between logits are meaningful.
→ `model/artifact.py` → `predict_proba`

**softmax** — Turns scores into probabilities that sum to 1. Exponentiating does
two jobs at once: it makes negatives positive, and it sharpens the gap between
them.
→ `model/artifact.py`

**cross-entropy** — The loss function. It penalises giving the correct class a low
probability, and penalises being confidently wrong especially hard. That is what
teaches the model to be cautious.
→ inside sklearn; you do not write it

**regularization / `C`** — The setting that stops memorisation by penalising large
weights. Critical with ~200 examples against 4163 features: an unconstrained model
finds a private feature for every example, scores 100% in training, and collapses
on an unseen symbol. Smaller `C` = tighter constraint = simpler model.
→ `config.py` → `TrainingConfig.regularisation`

**class_weight="balanced"** — Makes a mistake on a rare class expensive. Without
it the model discovers the strategy "always answer with the biggest class" —
genuinely good for accuracy, useless for us.
→ `config.py`

**inference** — Applying a trained model to a new input. The model **learns
nothing** while doing it; it computes with frozen `W` and `b`.
→ `model/artifact.py` → `predict_proba`

## Measurement

**accuracy** — The fraction predicted correctly. Misleading alone: with unbalanced
classes it rewards the biggest one. It appears in the report but never by itself.
→ `evaluation/metrics.py`

**macro-F1** — Compute each class's F1 separately and average them with **equal
weight**. Getting the common class right and the other nine wrong does not
produce a good score. This is the number to report.
→ `evaluation/metrics.py`

**precision / recall** — Precision: "of the things I called this class, how many
were". Recall: "of the things that were this class, how many did I catch". F1
balances the two.
→ `evaluation/results.py` → `ClassMetrics`

**support** — How many real examples of a class are in the test data.

**low-N** — A class with fewer examples than there are folds, so its result is
noise. Unmarked, it sits in the table at the same visual weight as everything
else and pulls decisions the wrong way.
→ `evaluation/folds.py` → `low_n_classes`

**stratified k-fold** — Cross-validation that preserves class proportions in every
fold. Each example is tested exactly once and used for training the rest of the
time — the point being not to waste labels that were expensive to produce.
→ `evaluation/folds.py`

**coverage** — The fraction of symbols the model was confident enough to answer
for. "92% accurate" says nothing without it; you might be answering on 5% of
symbols.
→ `evaluation/metrics.py`

**precision@covered** — Accuracy among the answers actually given. It trades
against coverage: raise the threshold and precision goes up while coverage goes
down.

**abstention** — How often the model says "I don't know". The other side of
coverage.

**calibration** — Whether the probability the model reports matches how often it
is actually right. A softmax output of `0.94` *looks* like a probability but is
not guaranteed to behave like one. The check is blunt and mandatory: is the accept
bucket really more precise than the tentative bucket?
→ `evaluation/results.py` → `Calibration.separates`

**confusion matrix** — Which class gets mistaken for which. The taxonomy already
predicts where that will happen: validator ↔ policy, orchestrator ↔ domain_logic.
→ `evaluation/confusion.py`

**ablation** — Removing a component and measuring how far the result falls, to
find out what it contributed. The four variants here: A (names only), B-local,
B-global, C (everything). If A alone scores nearly as well as C, the model is
doing word matching — and word matching collapses in a codebase with different
naming habits.
→ `experiments/ablation.py`

## Contracts

**featureVersion / taxonomyVersion** — The vector layout and the label list carry
separate version numbers because they change independently: a taxonomy change
leaves the vector alone, and a new counter leaves the classes alone.
→ `contracts/model-artifact.md`

**golden fixture** — A reference file both languages must read and reproduce
identically. The only mechanism that catches parity breaking silently.
→ `contracts/fixtures/`

**parity** — Python (training) and TypeScript (inference) producing byte-identical
numbers. When it breaks, **nothing raises** — the results just get worse.
→ `features/hashing.py`, `tests/test_hashing.py`

**artifact** — The trained model as a file: weights, bias, class names, scaler
parameters and versions. The whole of what ships to production.
→ `contracts/model-artifact.md`, `model/artifact.py`
