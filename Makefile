.PHONY: setup lint format typecheck test spec inspect evaluate ablate train golden all

setup:
	uv sync --all-groups
	uv run pre-commit install

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy src/

# The blocking suite. Slot specifications are excluded — they fail by design
# until the module they describe is written.
test:
	uv run pytest -m "not spec"

# The work that is still open. Every failure here is a module waiting to be
# implemented, and the assertion is the specification for it.
spec:
	uv run pytest -m spec

inspect:
	uv run code-ast-symbol-classifier inspect

evaluate:
	uv run code-ast-symbol-classifier evaluate

ablate:
	uv run code-ast-symbol-classifier ablate

train:
	uv run code-ast-symbol-classifier train

# Regenerate the parity fixtures. Only after a deliberate change to the feature
# spec, and always alongside a new featureVersion.
golden:
	uv run python scripts/generate_golden.py

all: lint typecheck test
