# Label sets

One file per version, each carrying the `taxonomyVersion` it was produced
against. The loader refuses a set whose version does not match the current
taxonomy — a label set built for the old 14-class list joins cleanly against
these symbols and would train a model on classes that no longer exist.

Nothing is here yet, and nothing should be until the class definitions in
`contracts/taxonomy.v1.yaml` are filled in. Labelling against undefined classes
produces disagreement that reads as labeller error but is a missing definition.
