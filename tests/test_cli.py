from __future__ import annotations

import pytest

from code_ast_symbol_classifier.cli import main


def test_inspect_runs_without_a_model(capsys):
    assert main(["inspect"]) == 0

    out = capsys.readouterr().out
    assert "feature spec" in out
    assert "10 classes" in out


def test_inspect_names_the_classes_still_missing_a_definition(capsys):
    main(["inspect"])
    assert "have no definition" in capsys.readouterr().out


def test_unimplemented_slot_reports_itself_instead_of_a_traceback(capsys):
    """A fresh clone hits this on the first `evaluate`."""
    assert main(["evaluate"]) == 2

    err = capsys.readouterr().err
    assert "not written yet" in err
    assert "make spec" in err


def test_ablate_still_produces_a_table_with_slots_empty(capsys):
    assert main(["ablate"]) == 0
    assert "| variant |" in capsys.readouterr().out


def test_unknown_command_is_rejected():
    with pytest.raises(SystemExit):
        main(["nope"])
