"""The two figures the dashboard got wrong, pinned.

streamlit is an optional dependency (requirements-streamlit.txt, not
requirements.txt), so these skip cleanly in CI the same way test_geo_trends.py
does for pytrends.
"""
from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

import pandas as pd
import pytest

pytest.importorskip("streamlit")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import streamlit_app  # noqa: E402

FAMILY = "current_account_pack"


@pytest.fixture(scope="module")
def dataset():
    df = streamlit_app.load_campaigns()
    if df is None:
        pytest.skip("no dataset in the working tree")
    return df


def test_no_data_reports_nothing_rather_than_zero():
    """A missing dataset is not a dataset with no features in it."""
    assert streamlit_app.features_compared(None, FAMILY) is None


def test_the_headline_figure_is_the_one_every_other_artefact_quotes(dataset):
    """Regression: this read 89 - the width of the unscored CSV.

    outputs/charts.md prints "104 features in the dictionary" and
    "= 33 features used in this comparison" from the same feature_accounting()
    call. The dashboard must not invent a third number for the same run.
    """
    declared, used = streamlit_app.features_compared(dataset, FAMILY)
    assert declared == 104
    assert used == 33
    assert used != len(dataset.columns), "the metric is counting CSV columns again"


def test_the_count_is_scoped_to_one_product_family(dataset):
    """DR-04: a comparison is only valid inside one family, and the count
    follows it. Pooled across all six the figure is different, and quoting the
    pooled one beside a scoped chart is how two numbers start disagreeing."""
    _, scoped = streamlit_app.features_compared(dataset, FAMILY)
    _, pooled = streamlit_app.features_compared(dataset, None)
    assert scoped != pooled
    assert scoped == 33


def test_it_never_reports_more_features_than_the_dictionary_declares(dataset):
    declared, used = streamlit_app.features_compared(dataset, FAMILY)
    assert used <= declared


def test_load_campaigns_prefers_the_rubric_merged_dataset(tmp_path, monkeypatch):
    """campaigns.csv lacks the 13 judged features; campaigns_scored.csv has them.

    Reading the unscored file is what hid every rubric-derived figure from this
    dashboard while the React UI showed it.
    """
    pd.DataFrame({"page_id": ["scored"]}).to_csv(tmp_path / "campaigns_scored.csv", index=False)
    pd.DataFrame({"page_id": ["unscored"]}).to_csv(tmp_path / "campaigns.csv", index=False)
    monkeypatch.setattr(streamlit_app, "DATA", tmp_path)
    streamlit_app.load_campaigns.clear()

    assert streamlit_app.load_campaigns()["page_id"].iat[0] == "scored"


def test_load_campaigns_falls_back_when_only_the_unscored_file_exists(tmp_path, monkeypatch):
    """A tree part-way through the pipeline still shows what it has."""
    pd.DataFrame({"page_id": ["unscored"]}).to_csv(tmp_path / "campaigns.csv", index=False)
    monkeypatch.setattr(streamlit_app, "DATA", tmp_path)
    streamlit_app.load_campaigns.clear()

    assert streamlit_app.load_campaigns()["page_id"].iat[0] == "unscored"


def test_load_campaigns_returns_none_when_there_is_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(streamlit_app, "DATA", tmp_path)
    streamlit_app.load_campaigns.clear()

    assert streamlit_app.load_campaigns() is None


def _react_tabs() -> list[str]:
    """The React tab labels, read from web/src/App.tsx's TABS literal."""
    src = (ROOT / "web" / "src" / "App.tsx").read_text(encoding="utf-8")
    block = src.split("const TABS", 1)[1].split("];", 1)[0]
    return re.findall(r'\[\s*"[a-z]+"\s*,\s*"([^"]+)"\s*\]', block)


def _streamlit_pages() -> list[str]:
    """The sidebar labels, read from main()'s pages dict."""
    src = inspect.getsource(streamlit_app.main)
    return [re.sub(r"^[^\w]+", "", label) for label in re.findall(r'"([^"]+)": page_', src)]


def test_every_react_tab_has_a_streamlit_page():
    """The two surfaces are one product and must not drift apart.

    Reputation and Recommendations existed only in React, so the dashboard
    silently showed a smaller project than the web UI did.
    """
    missing = [t for t in _react_tabs() if t not in _streamlit_pages()]
    assert not missing, f"React tabs with no Streamlit page: {missing}"


def test_the_shared_tabs_are_in_the_same_order():
    """Same labels in a different order still reads as two different products."""
    react = _react_tabs()
    shared = [p for p in _streamlit_pages() if p in react]
    assert shared == [t for t in react if t in shared]


def test_a_null_reputation_bank_does_not_take_the_page_down():
    """Regression: bank_snapshot() writes null for a bank it could not fetch or
    classify, and b.get("themes") on that null raised AttributeError - the
    deployed Reputation page crashed on bunq, cbc, keytrade and n26."""
    banks = {
        "ing": {"headline_count": 2, "themes": {"regulatory": 1, "other": 1}},
        "n26": None,
    }
    table = streamlit_app.reputation_table(banks)
    assert list(table.index) == ["ing", "n26"]
    assert table.loc["ing", "Headlines"] == 2
    assert table.loc["ing", "Regulatory"] == 1


def test_a_null_reputation_bank_reads_empty_not_zero():
    """0 means the query ran and matched nothing; a null means there is no
    result. Filling the null row with zeros would make the two look the same."""
    table = streamlit_app.reputation_table({"ing": {"headline_count": 0, "themes": {"other": 0}}, "n26": None})
    assert table.loc["ing"].tolist() == [0, 0]
    assert table.loc["n26"].isna().all()


def test_every_reputation_bank_null_still_builds_a_table():
    table = streamlit_app.reputation_table({"bunq": None, "n26": None})
    assert table["Headlines"].isna().all()


def test_the_real_reputation_snapshot_builds_a_table():
    """The committed outputs/reputation.json is what the deployed app reads."""
    data = streamlit_app.load_json_output("reputation.json")
    if not data or not data.get("banks"):
        pytest.skip("no reputation snapshot in the working tree")
    table = streamlit_app.reputation_table(data["banks"])
    assert len(table) == len(data["banks"])


@pytest.mark.parametrize("verdict, colour", [
    ("supported", "green"), ("not supported", "red"), ("not testable", "gray"),
])
def test_each_deck_claim_verdict_gets_its_own_badge_colour(verdict, colour):
    assert streamlit_app.verdict_badge(verdict) == f":{colour}-badge[{verdict}]"


def test_an_unknown_verdict_falls_back_to_grey_instead_of_raising():
    assert streamlit_app.verdict_badge("new label") == ":gray-badge[new label]"


def test_bank_status_follows_the_analysed_scope():
    df = pd.DataFrame({
        "bank": ["ing", "ing", "kbc", "bunq"],
        "bank_category": ["traditional", "traditional", "traditional", "challenger"],
    })
    scope = {"banks_included": ["ing"], "banks_excluded_no_page_in_family": ["kbc"]}
    table = streamlit_app.bank_status_table(df, scope)
    assert table.loc["ing", "Pages"] == 2
    assert table.loc["ing", "Status"] == "✅ In scope"
    assert table.loc["kbc", "Status"].startswith("⛔")
    assert table.loc["bunq", "Status"].startswith("⚠️")
    assert table.loc["bunq", "Category"] == "challenger"


def test_fit_height_grows_with_the_row_count():
    """Fourteen banks must all fit: the default height scrolled four away."""
    assert streamlit_app.fit_height(14) > streamlit_app.fit_height(10)
    assert streamlit_app.fit_height(14) == 35 * 15 + 3
