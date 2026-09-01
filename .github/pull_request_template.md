## What changed

<!-- One or two sentences. -->

## How it was verified

<!-- `make lint test`, plus anything specific you ran. -->

## Metric impact

<!--
If this touches features, training or evaluation, paste the ablation table
before and after. "No metric impact" is a fine answer — say it explicitly rather
than leaving the section empty.

A single accuracy number is not a result: macro-F1, per-class with low-N marks,
coverage and precision@covered travel together. See docs/reporting-checklist.md.
-->

## Contract changes

<!--
Tick if this PR touches any of these, and say why:

- [ ] `contracts/feature-spec.v1.json` — needs a new featureVersion and regenerated goldens (`make golden`)
- [ ] `contracts/taxonomy.v1.yaml` — existing label sets may no longer apply
- [ ] `contracts/model-artifact.md` — a consumer has to be updated alongside
-->
