"""`explain` has to stay useful while the stages are still empty.

It is the first command an intern runs, so a missing stage must read as "not
written yet, here is its specification" rather than as a broken repository.
"""

from __future__ import annotations

import pytest

from code_ast_symbol_classifier import explain as explain_module
from code_ast_symbol_classifier.cli import main
from code_ast_symbol_classifier.explain import Attempt, find_record


def test_shows_the_symbol_and_what_the_model_does_not_see(capsys):
    assert main(["explain"]) == 0

    out = capsys.readouterr().out
    assert "placeOrder" in out
    assert "does NOT get: the function body" in out


def test_names_every_stage_even_when_none_are_written(capsys):
    main(["explain"])
    out = capsys.readouterr().out

    for stage in ("STAGES 1-2", "STAGE 3", "STAGE 4", "STAGE 5"):
        assert stage in out


def test_an_empty_stage_points_at_its_specification(capsys):
    main(["explain"])
    out = capsys.readouterr().out

    assert "Not written yet" in out
    assert "tests/spec/test_stage1_split.py" in out


def test_missing_model_is_reported_rather_than_crashing(taxonomy, tmp_path, capsys):
    """Exercised directly, so it holds whether or not the stages are written."""
    explain_module._stage_prediction(Attempt(value=object()), taxonomy, tmp_path / "absent.json")

    out = capsys.readouterr().out
    assert "No trained model" in out
    assert "make train" in out


def test_symbol_can_be_chosen_by_part_of_its_name(capsys):
    assert main(["explain", "--symbol", "isEligible"]) == 0
    assert "isEligibleForDiscount" in capsys.readouterr().out


def test_symbol_can_be_chosen_by_id(sample_dataset, capsys):
    wanted = sample_dataset.records[3].id
    assert main(["explain", "--symbol", wanted]) == 0
    assert wanted in capsys.readouterr().out


def test_unknown_symbol_fails_with_a_readable_message(sample_dataset):
    with pytest.raises(SystemExit, match="no symbol matching"):
        find_record(list(sample_dataset.records), "definitely-not-here")
