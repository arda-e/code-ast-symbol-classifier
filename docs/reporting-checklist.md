# Reporting checklist

A result is not reportable as one number. `evaluation/report.py` renders every
line below, and prints "not measured" for anything absent rather than omitting
it — a missing row reads as a number nobody needed rather than one nobody took.

## Required in every report

| item | why it is required |
|---|---|
| **macro-F1** | The headline. Weights every class equally, so getting the common one right and the rare ones wrong does not pass. |
| **per-class precision / recall / F1** | Where the model actually fails. An average hides a class scoring zero. |
| **low-N marks** | A class with two examples has an F1 that is noise. Unmarked, it sits in the table at full visual weight and pulls decisions. |
| **coverage** | How often the model answered at all. Without it, "92% accurate" might describe 5% of symbols. |
| **precision@covered** | Accuracy among the answers it did give. |
| **abstention rate** | The other half of coverage, stated plainly. |
| **calibration check** | Whether accept is really more precise than tentative. If not, the threshold separates nothing. |
| **p50 / p95 / p99 latency** | Cost has to be measured, not assumed. |
| **cold start** | The first symbol after a process starts pays it. |
| **model size** | Decides the deployment story as much as accuracy does. |

Accuracy may appear, but never on its own: with one class at half the data, a
model that learned nothing scores 50%.

## Comparisons need a floor and a ladder

A score means nothing in isolation. Report it next to:

- **rule baseline** — plain if/else over the graph facts. If that scores 0.85,
  the question for anything more complex is what the extra points cost.
- **the ablation table** — A (names only), B-local, B-global, C. If A alone
  scores nearly as well as C, the model is doing word matching, and word matching
  does not survive a codebase with different naming habits.

A more complex approach does not win by being better. It wins by being better
*by enough to pay for what it drags along* — a runtime dependency, a model file,
a conversion step, a tokenizer that has to be reimplemented identically in
another language. Two points does not buy that; eighteen might.

## Cross-repo is the real exam

In-repo cross-validation flatters any model that keys off names, because one
codebase names things consistently. Portability across repositories is the
product goal, so a held-out external repository is not an extra credit — it is
the test that decides.
