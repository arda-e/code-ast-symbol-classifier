# How a symbol becomes numbers, and numbers become a prediction

This document follows one function from beginning to end. None of the numbers
below are invented — they live in `contracts/fixtures/vector-golden.json` and the
tests assert exactly these values.

To watch the same thing happen live:

```bash
make explain
```

It works even with the stages still empty; each one either prints its output or
says it has not been written yet and points at the test that specifies it.

---

## 0. The question

The function:

```ts
async placeOrder(input: CreateOrderDto) {
  const order = await this.orderFactory.create(input);
  await this.inventory.reserve(order.items);
  await this.payment.charge(order);
  await this.repository.save(order);
  return order;
}
```

The question is not "what does this do" but **"why was it written"**. What it
does, the graph already knows: it writes to a database, calls four things, is
async. What the graph cannot see is that this function makes no decision of its
own — its entire value is putting four units in the right order. That is
`orchestrator`.

The test is simple: **delete its calls; does a rule remain?** If not, it is an
orchestrator.

---

## 1. What reaches the model, and what does not

Intuition usually gets this wrong, so it is worth settling first.

The function **body does not reach the model.** Not the `if` blocks, not the
variable names, not the comments. The model sees this:

```
from names                          not from names
──────────                          ──────────────
the symbol's name  placeOrder       outDegree, inDegree
its owner          OrderService     async, exported, paramCount
its file path      src/orders/...   comparison / branch / await counters
callee names       create, reserve  side effects, mutations
                   charge, save
parameter type     CreateOrderDto
return type        Promise<Order>
```

Everything on the right is a countable fact the parser extracted; the left is
names. Note the fourth row: **callee names come from inside the body** — the
parser looks in and finds `this.payment.charge(order)`. So the information does
come from the body, but it reaches the model as a name.

---

## 2. Split names into words  *(stage 1)*

```
placeOrder              →  place, order
CreateOrderDto          →  create, order, dto
isEligibleForDiscount   →  is, eligible, for, discount
```

**Why split?** Left whole, `placeOrder` becomes its own isolated feature, sharing
nothing with `placeBid`, `cancelOrder` or `orderTotal`. The model could never
generalise — it would only recognise names it had already seen. Split, the word
`order` becomes a signal shared across all of them.

---

## 3. Record where each word came from  *(stage 2)*

The 21 strings produced for `placeOrder`:

```
name:place       name:order
owner:order      owner:service
path:src         path:orders        path:order       path:service
callee:order     callee:factory     callee:create
callee:inventory callee:reserve
callee:payment   callee:charge
callee:repository callee:save
accepts:create   accepts:order      accepts:dto
returns:order
```

**Why prefix them?** Because the same word means something entirely different
depending on where it came from:

```
name:validate      this function's own name contains "validate"
                   → probably a validator

callee:validate    this function calls something that validates
                   → it does not validate; perhaps an orchestrator
```

Without the prefix both land in the same bucket and the model can **never** learn
the difference.

Two smaller decisions, both written into the contract:

- **The receiver is kept in a call.** `save` appears everywhere; `repository.save`
  does not. The receiver is often a stronger signal than the method name.
- **`this` is dropped.** It sits on nearly every method call, separates nothing,
  and would waste a bucket.

---

## 4. Reduce strings to buckets  *(hashing)*

Getting the idea right here matters. Hashing is not used to **turn a word into a
number**; it is used to place an unbounded set of strings into **a bucket in a
fixed-size space**.

The alternative would be keeping a vocabulary — but a real codebase has hundreds
of thousands of identifiers, every new repository brings more, and that
vocabulary would have to be built, stored, versioned and **carried across two
languages**. Hashing removes all of it.

The real numbers, from `hash-golden.json`:

```
"name:place"        →  murmur3 →  % 4096  →   669
"owner:service"     →  murmur3 →  % 4096  →   677
"path:src"          →  murmur3 →  % 4096  →   200
"path:service"      →  murmur3 →  % 4096  →  3791
"name:order"        →  murmur3 →  % 4096  →  2966
```

The result is a 4096-long vector with 21 positions set to 1 and the rest 0.

> **This is the most fragile part of the repository.** The same hash has to
> produce identical results in TypeScript later. If it does not, **nothing
> raises** — predictions just get quietly worse. That is why the hash function
> sits in its own module (`features/hashing.py`), its configuration in the
> contract, and `hash-golden.json` as a fixture both languages read.
>
> Four details break parity, all of them silently: the variant (x86_32 vs
> x64_128), the seed, signedness (`signed=False` is required — `%` on a negative
> behaves differently in Python and JavaScript) and the encoding.

**Collisions.** Squeezing unbounded strings into a fixed space means two features
will sometimes land in the same bucket. It is tolerable because a symbol only
lights up about 20 of the 4096 positions.

---

## 5. Do not hash what is already a number  *(stage 3)*

Some facts are already numbers and form a **closed set** — there are exactly as
many side-effect kinds as the parser defines. Closed sets get reserved positions.
For `placeOrder`:

```
[ 0] outDegree                   4        [12] paramCount                1
[ 1] inDegree                    3        [13] statementCount            5
[ 2] distinctCallees             4        [14] lineCount                 7
[ 3] distinctCallers             3        [20] awaitCount                4
[ 4] entrypointDistance          1        [21] returnCount               1
[ 5] isAsync                     1        [48] sideEffect_database_write 1
[ 6] isExported                  1
[11] isMethod                    1        → 14 of 67 positions filled
```

**Why not embed these in the text?** Suppose the model were handed
`calls: create, reserve, charge, save` as text. To reach `outDegree = 4` it would
have to work out that the comma is a separator, count the pieces, and connect
that count to the idea of a degree. None of those are guaranteed, and while
learning them its only feedback is the class label. Given `outDegree = 4`, the
counting is already done.

**The order is a contract.** Swap two positions and `comparisonCount` gets
multiplied by `paramCount`'s weight. Nothing raises. The score simply drops, and
finding out why afterwards is close to impossible.

---

## 6. Concatenate the two blocks and scale one  *(stage 4)*

```
[0,0,...,1,...,1,...,0]  +  [4, 3, 4, 3, 1, ...]
└── 4096 buckets, 0/1 ──┘    └── 67 numbers, scaled ──┘
                  4163 numbers
```

Nothing is summed and nothing is mixed — the blocks are glued end to end. The
model learns a separate weight per position and does not care where a position
came from.

**Why scale?** The hashed half is only ever 0 or 1. The numeric half is not: a
value like `inDegree = 47` sits next to four thousand zeros and ones and, during
training, can drown out everything else on its own. Standardising — subtract the
mean, divide by the spread — puts them on comparable footing.

**Why are `fit` and `transform` separate?** The scaler must learn its mean from
the **training rows only**. Fit it on everything and the test rows have quietly
influenced the numbers used to score them; every result comes out better than the
model really is, and **you get no warning at all**. This split is the only thing
preventing that.

---

## 7. From vector to probabilities  *(stage 5)*

Everything that gets learned is a weight table and a bias vector:

```
weight matrix:   10 classes × 4163 features
bias:            10 numbers
```

Prediction:

```
scores = W × x + b           → 10 raw numbers (logits)
softmax(scores)              → 10 probabilities summing to 1
```

Output of `make explain --symbol isEligible`, from a real run:

```
domain_logic     0.799  ████████████████████████
policy           0.085  ███
unknown          0.056  ██
utility          0.018  █

tentative — domain_logic, worth a human glance
```

**Why is a single label not enough?** These two look identical once you take the
top answer:

```
orchestrator 0.94        orchestrator 0.45
domain_logic 0.04        domain_logic 0.40
   model is sure            coin flip
```

Both say "orchestrator". The shape of the distribution carries more information
than the label does.

**Three buckets:**

```
confidence ≥ 0.85   →  accept       take it
confidence ≥ 0.65   →  tentative    flag it for a human
below               →  unknown      throw the prediction away
```

Leaving a symbol unlabelled is cheaper than labelling it wrongly — a wrong
architectural role propagates into every query that trusts the graph.

> Those three thresholds are currently an **assumption, not a measurement**. The
> calibration check in `evaluation/metrics.py` tests exactly this: are predictions
> in the accept bucket really more often right than those in the tentative
> bucket? If not, the threshold separates nothing.

---

## 8. Which part of this is machine learning?

Worth asking early, because the answer is narrower than most people expect.

```
     placeOrder
          ↓
       split                 ┐
          ↓                  │
      prefix                 ├─  feature engineering
          ↓                  │   (NOT machine learning)
       hash                  │
          ↓                  │
   add the numeric block     │
          ↓                  │
   4163-dimensional vector   ┘
          ↓
   ┌──────────────┐
   │    model     │  ←────  this, exactly, is the ML
   └──────────────┘
          ↓
    10 class scores
```

Nothing in stages 1 through 4 learns. The same input always produces the same
output, and you wrote the rules. That is most of the work.

So what makes `model/train.py` machine learning? Compare it to writing the rules
by hand:

```python
if "validate" in name:
    return "validator"
if outDegree > 4 and awaitCount > 2:
    return "orchestrator"
```

That could work — but it is not machine learning, because **you decided which
feature matters and how much.** You picked the `> 4` threshold.

With logistic regression you supply only the examples, and this table falls out
of the data:

```
name:validate       for validator       +2.8
callee:save         for orchestrator    +0.7
comparisonCount     for domain_logic    +0.9
```

Nobody wrote that table. That is the whole of what machine learning means here.

And the practical consequence: **learning ends when training ends.** At inference
the model learns nothing; it multiplies and adds with frozen `W` and `b`. That is
why what ships to production is a few hundred KB of JSON — no runtime, no model
download, no native dependency.

---

## Next

```bash
make progress
```

It prints the five stages and which one is next. Each stage's test file opens
with what it does and **why** it is done that way.

For unfamiliar terms: [`glossary.md`](glossary.md).
