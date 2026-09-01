"""Training the classifier, and freezing it into a file.

Learning stops when training does. Inference reads back a weight matrix and a
bias vector and does multiply, add, softmax — which is why the production side of
this project is a JSON file and no runtime at all.
"""
