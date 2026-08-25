# Taxonomy

Ten classes, one axis: what a symbol was written **for**. The list lives in
[`contracts/taxonomy.v1.yaml`](../contracts/taxonomy.v1.yaml); this page explains
it and tracks what is still missing.

## The rule behind the list

No class restates a mechanical fact. "Touches the database", "publishes to Kafka",
"is async" are all absent, because the code graph already knows them. Training a
model to predict a known fact reproduces it at lower accuracy.

What the graph structurally cannot see is intent. Consider a function that calls
nothing, mutates nothing, writes nowhere, and returns a boolean. Its graph
signature is identical whether it is a general-purpose helper, an input check, a
permission decision, or a business rule — four different classes, one signature.
That gap is the model's entire job.

## The classes

| class | what it means | discriminating question |
|---|---|---|
| `orchestrator` | Sequences other units to complete a workflow | Delete its calls — does a rule remain? If not, orchestrator |
| `domain_logic` | Carries a business rule, invariant or calculation | Does the result depend on a domain rule? |
| `transformer` | Reshapes data without deciding anything | Shape change (`User` → `UserDTO`), or a rule? |
| `validator` | Checks input against constraints | "Is this well-formed?" |
| `policy` | Decides permission or eligibility | "Is this allowed?" |
| `adapter` | Translates one external boundary into local terms | Does it wrap exactly one boundary? |
| `factory` | Constructs and wires objects, closures or behaviour | Is the output a value, or a thing? |
| `configuration` | Assembles settings and connection values | Is the output configuration? |
| `utility` | Domain-independent general helper | Could it move to another project unchanged? |
| `unknown` | The labeller could not decide | — |

## The pairs that will be argued about

Labelling is easy in the middle and hard at the edges. These collide most:

```
orchestrator ↔ domain_logic    delete the calls; if a rule remains, domain_logic
transformer  ↔ domain_logic    if the output depends on a business rule, domain_logic
validator    ↔ policy          "well-formed?" ↔ "allowed?"
validator    ↔ domain_logic    judgement about the INPUT ↔ about the RESULT
utility      ↔ transformer     if it knows domain types, transformer
adapter      ↔ orchestrator    one boundary ↔ several units
factory      ↔ configuration   produces objects/behaviour ↔ produces values/settings
```

Worked example — `isEligibleForDiscount(customer, order)` returning
`customer.loyaltyYears >= 3 && order.total > 1000`. It is arguably `policy`: it
decides eligibility. It is arguably `domain_logic`: it computes a domain outcome
from a business rule, with no authorization or quota involved. Both readings are
defensible, which is exactly the problem the next section is about.

## Open: the definitions do not exist

Every `definition` field in the contract is empty, and
`code-ast-symbol-classifier inspect` says so on every run.

The table above is a set of one-line summaries, not definitions. Two people
labelling from it will disagree at the edges, and the disagreement will look like
labeller error when it is really an underspecified class. **Labelling should not
start before these are written**, and writing them needs someone who knows the
production architecture — it is not a task the person doing the modelling can
pick up.

When the definitions land, `tests/test_taxonomy.py::test_class_definitions_are_still_missing`
flips to assert the opposite. That flip is the signal that labelling can begin.

## Open: `unknown` means two different things

It is both a label a person can assign ("I could not decide") and an output
bucket the model falls into when its confidence is below the tentative threshold.
Those are different facts — one is about the input, the other about the
prediction — and sharing a name will eventually confuse a metric. It needs a
decision before the first real label set is built.

## Open: existing labels target the old taxonomy

The earlier spike labelled against a 14-class list (`http_handler`,
`pipeline_stage`, `pure_utility`, …) which measured mechanics as much as intent.
Those labels cannot be carried over. `data/loader.py` refuses a label set whose
`taxonomyVersion` does not match, so the mismatch fails loudly rather than
training a model on classes that no longer exist.
