"""Tests for the report.json export (sieg 19/09).

No test covered scripts/export_web_report.py before this - this only adds
targeted coverage for the two new additions (personas, AI Score), following
tests/test_import_captures.py's pattern for loading a scripts/*.py module
directly since it isn't part of the installed package.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

spec = importlib.util.spec_from_file_location("export_web_report", ROOT / "scripts" / "export_web_report.py")
export_web_report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(export_web_report)

from comparator import ai_score  # noqa: E402
from comparator.dictionary import load_dictionary  # noqa: E402
from comparator.fixtures import build_fixture  # noqa: E402
from comparator.rubric import rubric_features  # noqa: E402
from comparator.schema import write_dataset  # noqa: E402


@pytest.fixture(scope="module")
def report(tmp_path_factory):
    # sieg 19/09, FIXED: a function-scoped `monkeypatch.delenv` autouse fixture
    # cannot reliably run before this module-scoped fixture's one-time setup -
    # pytest sets up broader-scoped fixtures first regardless of autouse, so
    # the deletion happened too late and this test made a REAL NewsAPI call
    # once NEWSAPI_KEY was actually set in .env (caught by CI-style full-suite
    # run taking 117s instead of ~12s). Popping the var directly here, at the
    # start of the fixture that actually needs it gone, has no such ordering
    # ambiguity.
    import os
    os.environ.pop("NEWSAPI_KEY", None)
    # steve 21/09: second key slot (newsapi.ai) - both must go, or this test
    # makes real network calls and asserts the wrong availability state.
    os.environ.pop("NEWSAPI_AI_KEY", None)
    fd = load_dictionary()
    df = build_fixture(fd)
    path = write_dataset(df, tmp_path_factory.mktemp("data") / "campaigns.csv", fd)
    report, _trends = export_web_report.build_report(
        path, family="term_account", focus="ing", top_n=10, trends_dir=None,
    )
    return report


def test_ai_score_axes_are_listed_at_the_top_level(report):
    keys = {axis["key"] for axis in report["aiScoreAxes"]}
    assert keys == set(ai_score.AXES)


def test_every_bank_carries_personas_and_an_ai_score(report):
    assert report["banks"], "fixture should produce at least one bank"
    for bank in report["banks"]:
        assert "personas" in bank
        assert "aiScore" in bank
        assert "crossSellScore" in bank
        assert set(bank["aiScore"]) == set(ai_score.AXES)
        for persona in bank["personas"]:
            assert 0 <= persona["share"] <= 1


def test_reputation_is_an_honest_not_configured_state_without_a_key(report):
    assert report["reputation"] == {"available": False, "banks": {}}


# sieg 20/09: geo_trends.py's output file is optional and rate-limited to
# generate, so this checks the SHAPE is well-formed rather than a specific
# availability value - whether outputs/geo_trends.json happens to exist on
# the machine running the test is not something this test should depend on.
def test_geo_trends_payload_is_well_formed_whether_or_not_it_was_generated(report):
    geo = report["geoTrends"]
    assert isinstance(geo["available"], bool)
    for bank in geo["banks"].values():
        assert "name" in bank
        assert isinstance(bank["regions"], dict)


def test_cross_sell_matrix_is_square_over_the_product_taxonomy(report):
    matrix = report["crossSellMatrix"]
    n = len(matrix["products"])
    assert n > 0
    assert all(len(row) == n for row in matrix["matrix"])


def test_ing_personas_match_the_fixture_archetype(report):
    ing = next(b for b in report["banks"] if b["key"] == "ing")
    assert {p["persona"] for p in ing["personas"]} == {"family", "expat", "mass_market"}


# steve 21/09: the operator surface (dictionary, dataset, collection, rubric)
# moved out of Streamlit and into operations.json. These check its shape, not
# the repo's own rubric sheets - a machine with no data/rubric must still build
# an honest empty payload.
@pytest.fixture(scope="module")
def operations(tmp_path_factory):
    import os
    os.environ.pop("NEWSAPI_KEY", None)
    os.environ.pop("NEWSAPI_AI_KEY", None)
    fd = load_dictionary()
    df = build_fixture(fd)
    path = write_dataset(df, tmp_path_factory.mktemp("ops") / "campaigns.csv", fd)
    return export_web_report.build_operations(path, family="term_account")


def test_operations_dictionary_mirrors_the_feature_dictionary(operations):
    fd = load_dictionary()
    assert len(operations["dictionary"]) == len(fd)
    names = {f["name"] for f in operations["dictionary"]}
    assert names == set(fd.names)
    first = operations["dictionary"][0]
    for key in ("name", "dimension", "type", "extraction", "tier", "required", "definition"):
        assert key in first


def test_operations_dataset_table_is_the_analysed_rows(operations):
    table = operations["dataset_table"]
    assert table["page_count"] == len(table["rows"])
    assert table["page_count"] > 0
    assert table["bank_count"] > 0
    assert "bank" in table["columns"] and "page_id" in table["columns"]


def test_operations_collection_status_covers_every_bank(operations):
    metrics = operations["collection"]["metrics"]
    assert metrics["banks"] == len(operations["collection"]["banks"])
    assert metrics["pages"] == operations["dataset_table"]["page_count"]
    for bank in operations["collection"]["banks"]:
        assert isinstance(bank["in_scope"], bool)
    if operations["collection"]["pages"]:
        assert "bank" in operations["collection"]["pages"][0]
        assert "language" in operations["collection"]["pages"][0]


def test_operations_rubric_payload_always_has_its_four_parts(operations):
    rubric = operations["rubric"]
    for key in ("raters", "agreement", "kappa", "features"):
        assert isinstance(rubric[key], list)
    # 13 rubric-scored features in the frozen dictionary.
    assert len(rubric["features"]) == len(rubric_features())
    assert all("definition" in f for f in rubric["features"])
