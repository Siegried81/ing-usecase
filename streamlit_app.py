"""Banking Campaigns Comparator — Streamlit dashboard.

Covers the whole repo: analysis, profiles, rubric, collection, data,
limitations, trends, and research. Built for share.streamlit.io deployment.

Dependencies: streamlit, pandas, pyyaml, requests (see requirements-streamlit.txt)

Usage:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml
from dotenv import load_dotenv

REPO = Path(__file__).resolve().parent

# This file lives at the repo root (for share.streamlit.io, which
# needs a top-level entry point), so `comparator` isn't importable without
# putting src/ on the path first - same technique as scripts/_bootstrap.py.
sys.path.insert(0, str(REPO / "src"))
from comparator import analysis, research, schema  # noqa: E402
from comparator.dictionary import load_dictionary as load_feature_dictionary  # noqa: E402

# The Research page reads SEMANTIC_SCHOLAR_API_KEY via os.getenv()
# inside research.search_papers() - without this, a real local .env key was
# silently never read when running `streamlit run streamlit_app.py` directly
# (every other entry point loads .env via scripts/_bootstrap.py; this file has
# no equivalent). No-ops harmlessly if .env doesn't exist (e.g. on Streamlit
# Community Cloud, which uses its own secrets mechanism instead).
load_dotenv(REPO / ".env")
DATA = REPO / "data" / "processed"
OUTPUTS = REPO / "outputs"
RUBRIC = REPO / "data" / "rubric"
CONFIG = REPO / "config"
KBCH = REPO / "search_interest"

st.set_page_config(page_title="Banking Campaigns Comparator", page_icon="🏦", layout="wide")


# ── helpers ──────────────────────────────────────────────────────────────

@st.cache_data
def load_campaigns() -> pd.DataFrame | None:
    """The rubric-merged dataset, falling back to the unscored one.

    campaigns_scored.csv is what run_analysis.py and export_web_report.py read:
    it carries the 13 judged features that campaigns.csv does not. Reading the
    unscored file here meant every rubric-derived figure was silently absent
    from this dashboard while the React UI showed it - the same two-derived-
    files hazard decisions.md records for the web export on 20/09.
    """
    for name in ("campaigns_scored.csv", "campaigns.csv"):
        p = DATA / name
        if p.is_file():
            return pd.read_csv(p)
    return None


def features_compared(df: pd.DataFrame | None, family: str | None) -> tuple[int, int] | None:
    """(declared, actually compared), read from analysis.feature_accounting().

    Deliberately not recomputed here. feature_accounting() is where this project
    decides which features survive into a comparison - provenance, withdrawn,
    bands redundant with their raw value, language- and capture-window-excluded,
    missing for some bank - and outputs/charts.md prints the same two numbers
    from the same call. A second definition living in the dashboard is exactly
    how two surfaces start quoting different figures for the same run.

    Scoped to one product family, like the comparison itself (DR-04). Pooled
    across all six families the count is 36; every other artefact quotes the
    scoped 33, so the dashboard quotes it too.

    This replaced len(df.columns), which read 89: the width of the unscored CSV,
    provenance columns included, and no relation to what was compared.
    """
    if df is None:
        return None
    fd = load_feature_dictionary()
    typed = schema.coerce_types(df, fd)
    if family:
        typed, _scope = analysis.scope_to_family(typed, family)
    accounting = analysis.feature_accounting(typed, fd)
    return accounting["dictionary_total"], accounting["n_used"]


@st.cache_data
def load_profiles() -> dict:
    p = OUTPUTS / "bank_profiles.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"_scope": {}, "profiles": {}}


@st.cache_data
def load_dictionary() -> dict:
    p = CONFIG / "feature_dictionary.yaml"
    if p.is_file():
        with open(p, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


@st.cache_data
def load_rubric_sheet(name: str) -> pd.DataFrame | None:
    # These sheets get hand-edited in Excel between sessions, and
    # Excel's CSV export defaults to ";" under a French/Belgian locale - this
    # file has already flipped between "," and ";" more than once. Sniffing
    # the header line rather than assuming either survives the next re-save.
    p = RUBRIC / name
    if not p.is_file():
        return None
    try:
        header = p.read_text(encoding="utf-8").splitlines()[0]
        sep = ";" if header.count(";") > header.count(",") else ","
        return pd.read_csv(p, sep=sep)
    except Exception:
        return None


def fit_height(n_rows: int) -> int:
    """Pixel height that shows every row of an st.dataframe, header included.

    st.dataframe caps itself at about ten rows and scrolls the rest, so a
    fourteen-bank table hid four banks behind a scrollbar. 35 px is Streamlit's
    row height; the extra 3 px is the border.
    """
    return 35 * (n_rows + 1) + 3


# The bank sits in the index of every per-bank table. Left unsized, the index
# column is as narrow as its header and cuts "bnp_paribas_fortis" in half.
BANK_INDEX = {"_index": st.column_config.TextColumn("Bank", width=150)}


def _dict_table(d: dict) -> None:
    """A flat dict as a clean two-column table, instead of a raw st.json() blob."""
    if not d:
        st.caption("No data.")
        return
    st.table(pd.DataFrame({"Field": list(d.keys()), "Value": [str(v) for v in d.values()]}).set_index("Field"))


@st.cache_data
def load_output_csv(name: str, **kwargs) -> pd.DataFrame | None:
    p = OUTPUTS / name
    if not p.is_file():
        return None
    try:
        return pd.read_csv(p, **kwargs)
    except Exception:
        return None


@st.cache_data
def load_json_output(name: str) -> dict | None:
    p = OUTPUTS / name
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


# ── page 1: Home ──────────────────────────────────────────────────────

def bank_status_table(df: pd.DataFrame, scope: dict) -> pd.DataFrame:
    """One row per captured bank: category, pages captured, scope status.

    A table rather than one bullet per bank, so fourteen banks fit on one
    screen. The status reads profiles["_scope"], the same scope run_analysis.py
    compared, so this page cannot claim a bank is in a comparison it was left
    out of.
    """
    included = set(scope.get("banks_included", []))
    no_page = set(scope.get("banks_excluded_no_page_in_family", []))
    rows = []
    for bank, pages in df.groupby("bank"):
        if bank in included:
            status = "✅ In scope"
        elif bank in no_page:
            status = "⛔ Out of scope (no page in family)"
        else:
            status = "⚠️ Captured, currently out of scope"
        category = pages["bank_category"].iat[0] if "bank_category" in pages else "N/A"
        rows.append({"Bank": bank, "Category": category, "Pages": len(pages), "Status": status})
    return pd.DataFrame(rows, columns=["Bank", "Category", "Pages", "Status"]).set_index("Bank")


def page_accueil(df: pd.DataFrame | None, profiles: dict) -> None:
    st.title("🏦 Banking Campaigns Comparator")
    st.caption(
        "How Belgian banks communicate about the same products, "
        "and what ING can learn from them. ING DACI / Customer AI POC."
    )

    scope = profiles.get("_scope", {})

    # A missing dataset stays None rather than becoming an empty DataFrame():
    # an empty frame has no "bank" column, so df["bank"] below would raise
    # KeyError and take the whole page down. Every metric degrades to "N/A".
    if df is None:
        st.warning("No campaign data available - expected `data/processed/campaigns_scored.csv` "
                   "(or `campaigns.csv`). Both are tracked, so this usually means the working "
                   "tree is incomplete; see docs/pipeline.md to regenerate them.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Banks with captures", df["bank"].nunique() if df is not None else "N/A")
    col2.metric("Pages collected", len(df) if df is not None else "N/A")
    counts = features_compared(df, scope.get("product_family"))
    col3.metric(
        "Features compared",
        counts[1] if counts else "N/A",
        help=(
            f"of {counts[0]} declared in the dictionary. The rest are provenance, "
            "withdrawn, redundant with a band, excluded for mixing languages or "
            "capture dates, or missing for at least one bank - see Limitations."
        ) if counts else None,
    )
    col4.metric("Banks in scope", len(scope.get("banks_included", [])))

    st.divider()

    st.subheader("Project status")
    # Counted, not written in: a literal page or bank count is a claim that
    # goes stale the next time anything is collected.
    if df is not None:
        declared = len(load_dictionary().get("features", []))
        st.info(
            f"The pipeline runs end to end on real captures: {len(df)} pages across "
            f"{df['bank'].nunique()} banks and {df['product_family'].nunique()} product "
            f"families, {declared} features, one judged rubric sheet. "
            "Comparisons run within one product family at a time."
        )

    if df is not None:
        st.subheader("Banks — collection status")
        status = bank_status_table(df, scope)
        st.dataframe(status, width="stretch", height=fit_height(len(status)),
                     column_config={**BANK_INDEX, "Pages": st.column_config.NumberColumn(format="%d")})

    if scope.get("banks_excluded_no_page_in_family"):
        st.markdown(
            "\n**Banks with usable captures but no page in the compared family:** "
            f"{', '.join(scope['banks_excluded_no_page_in_family'])} "
            "(DR-04: comparing across product families would confound every difference)"
        )

    st.divider()
    deliverables = [f for f in sorted(OUTPUTS.iterdir())
                    if f.is_file() and f.suffix in (".png", ".csv", ".json", ".md")]
    with st.expander(f"📦 Available deliverables ({len(deliverables)} files)"):
        grid = st.columns(3)
        for i, f in enumerate(deliverables):
            grid[i % 3].download_button(
                label=f"📄 {f.name}",
                data=f.read_bytes(),
                file_name=f.name,
                key=f"dl_{f.name}",
                width="stretch",
            )


# ── page 2: Analysis ──────────────────────────────────────────────────────

def _csv_or_missing(name: str, note: str, **kwargs) -> pd.DataFrame | None:
    """Load a real outputs/*.csv, or say plainly it hasn't been generated yet.

    Every tab in this page used to show hand-typed numbers that
    looked like a real run but were not read from anywhere - the exact
    "results from this dataset are NOT findings" problem the rest of this repo
    goes out of its way to avoid. Missing is now an honest empty state, never
    invented numbers.
    """
    frame = load_output_csv(name, **kwargs)
    if frame is None:
        st.info(f"`outputs/{name}` not found. Run `python3 scripts/run_analysis.py` to generate it. {note}")
    return frame


VERDICT_COLOURS = {"supported": "green", "not supported": "red", "not testable": "gray"}


def verdict_badge(verdict: str) -> str:
    """A deck-claim verdict as a coloured Streamlit markdown badge.

    The three colours map to the three verdicts analysis.check_deck_claims()
    writes. An unknown verdict falls back to grey rather than raising, so a
    new verdict label shows up as plain text instead of taking the page down.
    """
    return f":{VERDICT_COLOURS.get(verdict, 'gray')}-badge[{verdict}]"


def page_analyse(df: pd.DataFrame | None, profiles: dict) -> None:  # noqa: ARG001 - uniform page signature, see main()
    st.title("📊 Analysis")
    st.caption("Every number below is read live from `outputs/`, generated by `scripts/run_analysis.py` - "
               "nothing on this page is typed in by hand.")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["Positioning", "ING vs peers", "Separation", "Similarity", "AI Score", "Cross-sell"]
    )

    with tab1:
        st.subheader("Positioning — traditional ↔ challenger axis")
        st.caption("0 = traditional centroid, 1 = challenger centroid. Computed from real captures.")
        png = OUTPUTS / "01_positioning.png"
        if png.is_file():
            # The PNG is drawn for a slide, about 9.5 inches wide. Stretched across
            # a wide layout it blows up and blurs, so it is shown at a fixed
            # width in a centred middle column instead.
            _left, middle, _right = st.columns([1, 4, 1])
            middle.image(str(png), width=820)
        else:
            st.info("`outputs/01_positioning.png` not found. Run `python3 scripts/run_analysis.py`.")

    with tab2:
        st.subheader("ING vs peers — largest differences")
        st.caption("Gap in peer standard deviations. Positive = above the peer mean.")
        gaps = _csv_or_missing("ing_vs_peers.csv", "")
        if gaps is not None:
            cols = [c for c in ("feature", "dimension", "ing_value", "peer_mean", "peer_n", "gap_sd", "direction") if c in gaps.columns]
            st.dataframe(
                gaps[cols].set_index("feature"), width="stretch", height=420,
                column_config={
                    "dimension": st.column_config.TextColumn("Dimension"),
                    "ing_value": st.column_config.NumberColumn("ING", format="%.2f"),
                    "peer_mean": st.column_config.NumberColumn("Peer mean", format="%.2f"),
                    "peer_n": st.column_config.NumberColumn("Peers", format="%d"),
                    "gap_sd": st.column_config.NumberColumn("Gap (SD)", format="%+.1f"),
                    "direction": st.column_config.TextColumn("Direction"),
                },
            )

    with tab3:
        st.subheader("Traditional vs challenger — which separates the most?")
        st.caption("Cohen's d. Positive = higher at challengers, negative = higher at traditional.")
        sep = _csv_or_missing("category_comparison.csv", "")
        if sep is not None:
            cols = [c for c in ("feature", "traditional_mean", "challenger_mean", "effect_size_d") if c in sep.columns]
            st.dataframe(
                sep[cols].set_index("feature"), width="stretch", height=420,
                column_config={
                    "traditional_mean": st.column_config.NumberColumn("Traditional mean", format="%.2f"),
                    "challenger_mean": st.column_config.NumberColumn("Challenger mean", format="%.2f"),
                    "effect_size_d": st.column_config.NumberColumn("Cohen's d", format="%+.2f"),
                },
            )

    with tab4:
        st.subheader("Similarity between banks")
        st.caption("Euclidean distance in standardised feature space. Lower = more similar.")
        dist = _csv_or_missing("similarity_matrix.csv", "", index_col=0)
        if dist is not None:
            st.dataframe(
                dist.style.background_gradient(cmap="Blues_r", axis=None).format("{:.2f}"),
                width="stretch", height=fit_height(len(dist)), column_config=BANK_INDEX,
            )

    with tab5:
        st.subheader("AI Score — six independently-measured signals")
        st.caption("0-10 per axis, deterministic from features already in the dataset. Blank = no data, never a zero.")
        scores = _csv_or_missing("ai_score.csv", "")
        if scores is not None:
            # Bars on a fixed 0-10 scale, so every axis reads against the same
            # ruler. A blank cell stays blank: the bar is only drawn for a number.
            st.dataframe(
                scores.set_index("bank"), width="stretch", height=fit_height(len(scores)),
                column_config={**BANK_INDEX, **{
                    axis: st.column_config.ProgressColumn(
                        axis.replace("_", " ").capitalize(), format="%.1f", min_value=0, max_value=10,
                    )
                    for axis in scores.columns if axis != "bank"
                }},
            )

    with tab6:
        st.subheader("Cross-sell")
        st.caption("Share of possible other products cross-sold, and which product pairs actually appear together.")
        cs_score = load_output_csv("cross_sell_score.csv")
        cs_matrix = load_output_csv("cross_sell_matrix.csv", index_col=0)
        if cs_score is not None:
            st.markdown("**Cross-sell score per bank**")
            st.dataframe(
                cs_score.set_index("bank"), width="stretch", height=fit_height(len(cs_score)),
                column_config={**BANK_INDEX, "cross_sell_score": st.column_config.ProgressColumn(
                    "Share of other products cross-sold", format="percent", min_value=0, max_value=1,
                )},
            )
        if cs_matrix is not None:
            st.markdown("**Product co-occurrence matrix** (row = a page's own product, column = what else it cross-sells)")
            st.dataframe(cs_matrix, width="stretch")
        if cs_score is None and cs_matrix is None:
            st.info("`outputs/cross_sell_*.csv` not found. Run `python3 scripts/run_analysis.py`.")

    st.divider()
    st.subheader("📌 Deck claims (FR-14)")
    st.caption("Five observations from ING's own kickoff deck, tested against the measured pages.")
    claims = _csv_or_missing("deck_claims.csv", "")
    if claims is not None:
        # One card per claim rather than a table: the evidence is a full
        # sentence, and a dataframe cell cut it off mid-word.
        for c in claims.to_dict("records"):
            with st.container(border=True):
                st.markdown(
                    f"{verdict_badge(c.get('verdict', ''))} &nbsp; **{c.get('id', '')}** · "
                    f"{c.get('claim', '')} &nbsp; `{c.get('bank', '')}`"
                )
                st.caption(c.get("evidence", ""))


# ── page 3: Bank profiles ──────────────────────────────────────────────────────

def page_profils(df: pd.DataFrame | None, profiles: dict) -> None:
    st.title("🏷️ Bank profiles")
    profs = profiles.get("profiles", {})
    if not profs:
        st.warning("No profiles found. Run `scripts/run_analysis.py` first.")
        return

    selected = st.selectbox("Choose a bank", sorted(profs.keys()))
    p = profs[selected]
    ident = p.get("identity", {})

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"{selected} — {ident.get('category', 'N/A')}")
        _dict_table(ident)

    with col2:
        st.subheader("Palette & design")
        palette = p.get("palette", {})
        if palette.get("dominant_colour"):
            st.markdown(
                f'<div style="background:{palette["dominant_colour"]};height:40px;'
                f'border-radius:8px;border:1px solid #ccc;margin-bottom:8px"></div>',
                unsafe_allow_html=True,
            )
        _dict_table(palette)

    # Tabs instead of five stacked st.json() blobs - same content,
    # far less scrolling, and a table reads faster than a raw JSON dump.
    tabs = st.tabs(["Imagery", "Layout", "Tone", "Value proposition", "Marketing principles"])
    for tab, key in zip(tabs, ("imagery", "layout", "tone", "value_proposition", "marketing_principles")):
        with tab:
            _dict_table(p.get(key, {}))

    st.subheader("Signature (SD from mean)")
    sig = p.get("signature", [])
    if sig:
        sig_df = pd.DataFrame(sig, columns=["Feature", "Z-score"]).set_index("Feature")
        st.bar_chart(sig_df["Z-score"])

    # Screenshot if available
    bank_dir = DATA.parent / "raw" / selected
    if bank_dir.is_dir():
        pngs = list(bank_dir.glob("*.png"))
        if pngs:
            st.subheader("Capture")
            st.image(str(pngs[0]), caption=f"{pngs[0].name}", width="stretch")


# ── page 4: Rubric ───────────────────────────────────────────────────────

def page_rubric(df: pd.DataFrame | None, profiles: dict) -> None:  # noqa: ARG001 - uniform page signature, see main()
    st.title("📝 Rubric scoring")

    st.info(
        "13 features are judgements rather than measurements. They come from ONE "
        "judged sheet by one named person - `scripts/rubric_sheet.py emit` creates "
        "it, `merge` folds it into the dataset."
    )

    df_sheet = load_rubric_sheet("siegried_scores.csv")
    with st.expander(f"siegried — {df_sheet.shape[0] if df_sheet is not None else 0} pages", expanded=False):
        if df_sheet is None:
            st.warning("No judged sheet found")
        else:
            st.dataframe(df_sheet, width="stretch", height=300)

    st.divider()
    st.subheader("Why there is no agreement figure")
    st.caption(
        "One judged sheet means no second rater, so there is no percentage "
        "agreement and no chance-corrected kappa to report - and single-judge bias "
        "is therefore present and un-measured. It is named as a limitation rather "
        "than left for a reader to notice. Model-written sheets are kept in "
        "`data/rubric/model_reference/` as reference only: the pinned text-only "
        "model can legitimately judge 1 of the 13 features, because the other 12 "
        "are declared in the dictionary as judged from the screenshot."
    )

    st.subheader("Scoring guide — features to score")
    fd = load_dictionary()
    features = fd.get("features", [])
    rubric_features = [f for f in features if f.get("extraction") == "rubric"]
    if rubric_features:
        for f in rubric_features:
            st.markdown(
                f"- **`{f['name']}`** — {f.get('definition', 'N/A')[:120]}…"
            )


# ── page 5: Data ──────────────────────────────────────────────────────

def page_data(df: pd.DataFrame | None, profiles: dict) -> None:  # noqa: ARG001 - uniform page signature, see main()
    st.title("🗄️ Data")

    if df is None:
        st.warning("No campaign data available. Run analysis first.")
        return

    tab1, tab2 = st.tabs(["Dataset", "Dictionary"])

    with tab1:
        st.subheader(f"campaigns.csv — {df.shape[0]} pages × {df.shape[1]} columns")
        st.caption("Each row = one campaign page. Gitignored, regenerated from raw captures.")
        col1, col2 = st.columns(2)
        with col1:
            banks = sorted(df["bank"].unique())
            picked_banks = st.multiselect("Filter by bank", banks, default=banks)
        with col2:
            families = sorted(df["product_family"].dropna().unique())
            picked_families = st.multiselect("Filter by family", families, default=families)

        # The filters must be applied to the table below them, not just shown.
        filtered = df[df["bank"].isin(picked_banks) & df["product_family"].isin(picked_families)]
        st.caption(f"Showing {len(filtered)} of {len(df)} pages.")
        st.dataframe(filtered, width="stretch", height=400)

        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button("Download filtered CSV", data=csv, file_name="campaigns.csv")

    with tab2:
        features = load_dictionary().get("features", [])
        st.subheader(f"Feature dictionary — {len(features)} features")
        st.caption("config/feature_dictionary.yaml — single source of truth. Frozen after Day 2.")
        if features:
            fd_df = pd.DataFrame([
                {
                    "Feature": f["name"],
                    "Dimension": f.get("dimension", "N/A"),
                    "Type": f.get("type", "N/A"),
                    "Extraction": f.get("extraction", "N/A"),
                    "Comparability": f.get("comparability", "N/A"),
                    "Tier": f.get("tier", "N/A"),
                    "Required": "Yes" if f.get("required") else "No",
                    "Definition": f.get("definition", "")[:100],
                }
                for f in features
            ])
            st.dataframe(fd_df, width="stretch", height=500)
        else:
            st.warning("No features found in dictionary YAML")


# ── page 6: Limitations ──────────────────────────────────────────────────

def page_limitations(df: pd.DataFrame | None, profiles: dict) -> None:  # noqa: ARG001 - uniform page signature, see main()
    st.title("⚠️ Limitations (D-09)")
    p = OUTPUTS / "limitations.md"
    if p.is_file():
        st.markdown(p.read_text(encoding="utf-8"))
    else:
        st.warning("No limitations file found. Run `scripts/run_analysis.py` first.")


# ── page 7: Collection ───────────────────────────────────────────────────

def page_collection(df: pd.DataFrame | None, profiles: dict) -> None:  # noqa: ARG001 - uniform page signature, see main()
    st.title("🕷️ Collection")

    if df is None:
        st.warning("No campaign data available. Run analysis first.")
        return

    st.subheader("Status per bank")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Banks", df["bank"].nunique())
    col2.metric("Pages", len(df))
    col3.metric("Robots allowed", int(df["robots_allowed"].sum()) if "robots_allowed" in df.columns else "N/A")
    col4.metric("Quality ok", int((df["capture_quality"] == "ok").sum()) if "capture_quality" in df.columns else "N/A")
    col5.metric("Manual captures", int((df["collection_method"] == "manual_capture").sum()) if "collection_method" in df.columns else "N/A")
    col6.metric("Languages", ", ".join(sorted(df["language"].unique())))

    st.divider()
    st.subheader("Detailed pages")
    cols = ["page_id", "bank", "product_family", "language", "collection_method", "capture_quality", "data_source"]
    available = [c for c in cols if c in df.columns]
    st.dataframe(df[available], width="stretch")

    st.divider()
    st.subheader("Collection pipeline")
    st.markdown("""
    **Commands:**
    - `python3 scripts/run_collection.py --config scripts/collection_targets.yaml --method headless`
    - `python3 scripts/import_captures.py --dir <folder> --merge-with data/processed/campaigns.csv`
    """)
    st.caption("Compliance: assert_can_fetch() checks robots.txt before each fetch (fail closed).")


# ── page: Reputation ─────────────────────────────────────────────────────

def reputation_table(banks: dict) -> pd.DataFrame:
    """One row per bank: headline count, then one count per news theme.

    A bank can be null in reputation.json - bank_snapshot() returns None when
    nothing could be fetched or classified. That row stays empty, never zero:
    0 means the query ran and matched nothing, an empty cell means there is no
    result to read, and the two must not look the same.
    """
    themes = sorted({t for b in banks.values() if b for t in (b.get("themes") or {})})
    labels = {t: t.replace("_", " ").capitalize() for t in themes}
    rows = []
    for name, b in sorted(banks.items()):
        if b is None:
            rows.append({"Bank": name})
            continue
        counts = b.get("themes") or {}
        rows.append({"Bank": name, "Headlines": b.get("headline_count", 0),
                     **{labels[t]: counts.get(t, 0) for t in themes}})
    columns = ["Bank", "Headlines", *labels.values()]
    return pd.DataFrame(rows, columns=columns).set_index("Bank").astype("Int64")


def page_reputation(df: pd.DataFrame | None, profiles: dict) -> None:  # noqa: ARG001 - uniform page signature, see main()
    st.title("📰 Reputation")
    st.caption(
        "What each bank is in the news ABOUT, over the last 90 days of Belgian "
        "coverage. Themes, never sentiment: how positively a bank is covered is "
        "a different and harder claim this project does not make."
    )

    data = load_json_output("reputation.json")
    if data is None:
        st.warning("`outputs/reputation.json` not found - run `python3 scripts/run_analysis.py`.")
        return
    if not data.get("available"):
        st.info("No news API key configured, so no headlines were fetched.")
        return

    banks = data.get("banks") or {}
    if not banks:
        st.info("A key is configured but no headlines came back.")
        return

    # available: true means a key is configured, not that articles were
    # returned (docs/pipeline.md) - a bank at 0 may be quiet or may be a failed
    # request, and the two must not read the same.
    st.caption(
        "A headline count of 0 means nothing matched in the window - it is not "
        "evidence that a bank is absent from the news."
    )

    table = reputation_table(banks)
    no_snapshot = [name for name, b in sorted(banks.items()) if b is None]
    # A null bank's theme cells read "—" rather than "None". Display-only copy:
    # Streamlit ignores a Styler's na_rep on nullable integers, so the theme
    # columns become text here, while reputation_table() keeps the numbers.
    themes = [c for c in table.columns if c != "Headlines"]
    shown = table.astype({c: "object" for c in themes})
    shown[themes] = shown[themes].where(table[themes].notna(), "—")
    st.dataframe(
        shown,
        width="stretch",
        height=fit_height(len(table)),
        column_config={**BANK_INDEX, "Headlines": st.column_config.ProgressColumn(
            "Headlines", format="%d", min_value=0,
            max_value=max(int(table["Headlines"].fillna(0).max()), 1),
        )},
    )
    if no_snapshot:
        st.caption(
            f"No snapshot for {', '.join(no_snapshot)}: nothing could be fetched or "
            "classified for them, so their row is empty rather than zero."
        )

    chosen = st.selectbox("Headlines for", [name for name, b in sorted(banks.items()) if b is not None])
    if chosen is None:
        return
    for theme, items in (banks[chosen].get("theme_headlines") or {}).items():
        if items:
            st.markdown(f"**{theme.replace('_', ' ').capitalize()}**")
            for h in items:
                title = h.get("title", "")
                url = h.get("url")
                st.markdown(f"- [{title}]({url})" if url else f"- {title}")


# ── page: Recommendations ────────────────────────────────────────────────

def page_recommendations(df: pd.DataFrame | None, profiles: dict) -> None:  # noqa: ARG001 - uniform page signature, see main()
    st.title("💡 Recommendations")
    st.caption(
        "Changes ING could test, each argued from a measured feature. Read-only "
        "here: generating them is the React UI's job, this page shows the last run."
    )

    data = load_json_output("web_recommendations.json")
    if data is None:
        st.warning(
            "`outputs/web_recommendations.json` not found - it is written by "
            "`scripts/serve_web.py` when recommendations are generated."
        )
        return

    st.caption(
        f"Generated {data.get('generated_at', 'unknown')} by {data.get('model', 'unknown')}. "
        "No performance data exists in this project, so every item is a hypothesis "
        "to test, never a demonstrated improvement."
    )
    if data.get("summary"):
        st.info(data["summary"])

    for r in data.get("recommendations", []):
        with st.expander(f"{r.get('id', '?')} — {r.get('title', '')}  ·  {r.get('priority', '')}"):
            if r.get("finding"):
                st.markdown(f"**Finding.** {r['finding']}")
            if r.get("recommendation"):
                st.markdown(f"**Recommendation.** {r['recommendation']}")
            feats = r.get("features") or []
            # A reputation-basis item carries no features by design: news themes
            # are context, and citing a page feature as their evidence would be
            # the causal claim this project refuses.
            st.caption(
                "Measured features: " + ", ".join(feats) if feats
                else f"No page feature cited (basis: {r.get('basis', 'unknown')})."
            )


# ── page 8: Trends ───────────────────────────────────────────────────────

def page_trends(df: pd.DataFrame | None, profiles: dict) -> None:  # noqa: ARG001 - uniform page signature, see main()
    st.title("📈 Trends (Google)")
    st.caption(
        "Google Trends Belgium — ING vs competitors. "
        "Separate pipeline in `search_interest/` (Streamlit + pytrends)."
    )

    st.subheader("Dedicated dashboard")
    st.markdown("""
    The Trends pipeline has its own Streamlit app:
    `cd search_interest && streamlit run app.py`
    """)

    st.subheader("What's in the repo")
    if (KBCH / "export").is_dir():
        for f in sorted((KBCH / "export").glob("*.md")):
            st.download_button(
                f"📄 {f.name}",
                data=f.read_bytes(),
                file_name=f.name,
                key=f"trends_dl_{f.name}",
            )
    else:
        st.info("No search_interest/export found in this repo checkout.")


# ── page 9: Research ─────────────────────────────────────────────────────

def page_research(df: pd.DataFrame | None, profiles: dict) -> None:  # noqa: ARG001 - uniform page signature, see main()
    # Wires comparator/research.py into the dashboard. Deliberately
    # not a per-bank metric or an automatic per-insight citation - the module's
    # own docstring explains why (no defined metric, would be inventing scope).
    # This stays what the module was built for: an on-demand search box for
    # whoever is writing the business narrative.
    st.title("📚 Research")
    st.caption(
        "Semantic Scholar paper search, for sourcing claims in the business narrative. "
        "Works without an API key at low volume; a key in `SEMANTIC_SCHOLAR_API_KEY` "
        "only raises the rate limit, it does not unlock the feature."
    )

    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input("Search query", placeholder="e.g. cross-selling retail banking")
    with col2:
        limit = st.number_input("Max results", min_value=1, max_value=20, value=5)

    if st.button("Search", disabled=not query.strip()):
        with st.spinner("Searching Semantic Scholar…"):
            papers = research.search_papers(query.strip(), limit=int(limit))
        if not papers:
            st.info(
                "No papers returned. Either nothing matched, or the request was "
                "rate-limited (Semantic Scholar's public access without an API key "
                "has a low limit) - try again in a moment."
            )
        for p in papers:
            title = p.get("title") or "(untitled)"
            year = f" ({p['year']})" if p.get("year") else ""
            st.markdown(f"**[{title}]({p['url']}){year}**" if p.get("url") else f"**{title}{year}**")
            if p.get("abstract"):
                abstract = p["abstract"]
                st.caption(abstract[:400] + ("…" if len(abstract) > 400 else ""))
            st.divider()


# ── main ─────────────────────────────────────────────────────────────────

def main() -> None:
    # Every page function takes the same (df, profiles) signature, whether it
    # uses both, one or neither. Per-page argument rules would be one
    # hand-maintained mistake away from calling a page with the wrong number
    # of arguments the next time its data needs change. Pages that need
    # `df` guard `df is None` themselves; this dispatch does not need to know
    # which pages care.
    pages = {
        # Same order as the React UI's TABS (web/src/App.tsx), so the two
        # surfaces read as one product. Limitations has no React tab of its own
        # - it is a section of the Analysis tab there - and is kept last here
        # rather than dropped, because it is deliverable D-09.
        "🏠 Home": page_accueil,
        "📊 Analysis": page_analyse,
        "🏷️ Bank profiles": page_profils,
        "🗄️ Data": page_data,
        "📝 Rubric": page_rubric,
        "🕷️ Collection": page_collection,
        "📈 Trends": page_trends,
        "📰 Reputation": page_reputation,
        "💡 Recommendations": page_recommendations,
        "📚 Research": page_research,
        "⚠️ Limitations": page_limitations,
    }
    df = load_campaigns()
    profiles = load_profiles()

    # st.navigation instead of a sidebar radio: each page gets its own URL
    # (/analysis, /reputation...), so a link can point straight at one page.
    # The label's leading emoji becomes the icon, the rest the title, and the
    # URL is the title in kebab case - one dict above stays the only list.
    nav = st.navigation([
        st.Page(
            lambda page=page: page(df, profiles),
            title=label.split(" ", 1)[1],
            icon=label.split(" ", 1)[0],
            url_path=label.split(" ", 1)[1].lower().replace(" ", "-"),
            default=i == 0,
        )
        for i, (label, page) in enumerate(pages.items())
    ])
    st.sidebar.caption("Banking Campaigns Comparator\nING DACI / Customer AI\nPOC — 2 weeks, Sep 2026")
    nav.run()


if __name__ == "__main__":
    main()
