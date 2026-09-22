"""Guards against campaigns_scored.csv silently drifting behind campaigns.csv.

sieg 22/09, audit item #6 (decisions.md:277-300). merge_scores() joins on
page_id (rubric.py:154), not URL - re-running `rubric_sheet.py merge` is the
only thing that copies a campaigns.csv change into campaigns_scored.csv, and
nothing enforced that this happens before today. A silent skip has already
cost real scope once (see decisions.md's "sieg 21/09, scope restored..."
entry). This test checks the one thing decisions.md asked for: every page_id
in campaigns.csv must have a row in campaigns_scored.csv.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

CAMPAIGNS = Path("data/processed/campaigns.csv")
SCORED = Path("data/processed/campaigns_scored.csv")


@pytest.mark.skipif(
    not CAMPAIGNS.exists() or not SCORED.exists(),
    reason="real collected dataset not present in this environment",
)
def test_campaigns_scored_has_every_campaigns_page_id():
    """Catches the exact failure mode from decisions.md:277-300: campaigns.csv
    gains or changes rows (a re-collection, a scope restoration) and
    campaigns_scored.csv is not re-merged, so the web report and analysis
    silently run on a stale dataset.
    """
    campaigns = pd.read_csv(CAMPAIGNS)
    scored = pd.read_csv(SCORED)
    missing = set(campaigns["page_id"]) - set(scored["page_id"])
    assert not missing, (
        f"{len(missing)} page_id(s) in campaigns.csv are missing from "
        f"campaigns_scored.csv - re-run "
        f"'python3 scripts/rubric_sheet.py merge --sheets data/rubric/*_scores.csv': "
        f"{sorted(missing)}"
    )
