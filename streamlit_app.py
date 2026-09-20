"""Banking Campaigns Comparator — Streamlit dashboard.

Covers the whole repo: analysis, profiles, rubric, collection, data,
limitations, and trends. Built for share.streamlit.io deployment.

Dependencies: streamlit, pandas, pyyaml, requests (see requirements-streamlit.txt)

Usage:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
import yaml

REPO = Path(__file__).resolve().parent
DATA = REPO / "data" / "processed"
OUTPUTS = REPO / "outputs"
RUBRIC = REPO / "data" / "rubric"
CONFIG = REPO / "config"
KBCH = REPO / "kbc-ing-benchmark"

st.set_page_config(page_title="Banking Campaigns Comparator", layout="wide")


# ── helpers ──────────────────────────────────────────────────────────────

@st.cache_data
def load_campaigns() -> pd.DataFrame | None:
    p = DATA / "campaigns.csv"
    if p.is_file():
        return pd.read_csv(p)
    return None


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
    # sieg 20/09: these sheets get hand-edited in Excel between sessions, and
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


# ── page 1: Home ──────────────────────────────────────────────────────

def page_accueil(df: pd.DataFrame | None, profiles: dict) -> None:
    st.title("🏦 Banking Campaigns Comparator")
    st.caption(
        "How Belgian banks communicate about the same products, "
        "and what ING can learn from them. ING DACI / Customer AI POC."
    )

    scope = profiles.get("_scope", {})
    profs = profiles.get("profiles", {})

    # sieg 20/09, FIXED: this used to replace a missing df with an empty
    # DataFrame() and then call df["bank"] on it below - an empty frame has no
    # "bank" column, so that raised KeyError and took the whole page down.
    # Every metric/loop below now degrades to "N/A" instead of crashing.
    if df is None:
        st.warning("No campaign data available (`data/processed/campaigns.csv` is gitignored - "
                    "run `python3 scripts/run_analysis.py` locally to regenerate it).")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Banks with captures", df["bank"].nunique() if df is not None else "N/A")
    col2.metric("Pages collected", len(df) if df is not None else "N/A")
    col3.metric("Features measured", len(df.columns) if df is not None else "N/A")
    col4.metric("Banks in scope", len(scope.get("banks_included", [])))

    st.divider()

    st.subheader("Project status")
    st.info(
        "Day 5/10 — weekend before Day 6 gate (Mon 21 Sep). "
        "The analysis pipeline works end-to-end on real captures. "
        "The 13 rubric features are being scored."
    )

    if df is not None:
        st.subheader("Banks — collection status")
        banks = df.drop_duplicates("bank").sort_values("bank")
        for _, b in banks.iterrows():
            bank = b["bank"]
            in_scope = bank in scope.get("banks_included", [])
            excluded = bank in scope.get("banks_excluded_no_page_in_family", [])
            status = "✅ In scope" if in_scope else ("⛔ Out of scope (no page in family)" if excluded else "⚠️ Captured, currently out of scope")
            st.markdown(f"- **{bank}** ({b.get('bank_category', 'N/A')}) — {status}")

    if scope.get("banks_excluded_no_page_in_family"):
        st.markdown(
            "\n**Banks with usable captures but no page in the compared family:** "
            f"{', '.join(scope['banks_excluded_no_page_in_family'])} "
            "(DR-04: comparing across product families would confound every difference)"
        )

    st.divider()
    st.subheader("Available deliverables")
    for f in sorted(OUTPUTS.iterdir()):
        if f.is_file() and f.suffix in (".png", ".csv", ".json", ".md"):
            st.download_button(
                label=f"📄 {f.name}",
                data=f.read_bytes(),
                file_name=f.name,
                key=f"dl_{f.name}",
            )


# ── page 2: Analysis ──────────────────────────────────────────────────────

def _csv_or_missing(name: str, note: str, **kwargs) -> pd.DataFrame | None:
    """Load a real outputs/*.csv, or say plainly it hasn't been generated yet.

    sieg 20/09: every tab in this page used to show hand-typed numbers that
    looked like a real run but were not read from anywhere - the exact
    "results from this dataset are NOT findings" problem the rest of this repo
    goes out of its way to avoid. Missing is now an honest empty state, never
    invented numbers.
    """
    frame = load_output_csv(name, **kwargs)
    if frame is None:
        st.info(f"`outputs/{name}` not found. Run `python3 scripts/run_analysis.py` to generate it. {note}")
    return frame


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
            st.image(str(png), use_column_width=True)  # sieg 20/09: st.image() on the pinned streamlit==1.38.0 doesn't have use_container_width yet
        else:
            st.info("`outputs/01_positioning.png` not found. Run `python3 scripts/run_analysis.py`.")

    with tab2:
        st.subheader("ING vs peers — largest differences")
        st.caption("Gap in peer standard deviations. Positive = above the peer mean.")
        gaps = _csv_or_missing("ing_vs_peers.csv", "")
        if gaps is not None:
            cols = [c for c in ("feature", "dimension", "ing_value", "peer_mean", "peer_n", "gap_sd", "direction") if c in gaps.columns]
            st.dataframe(gaps[cols].set_index("feature"), use_container_width=True, height=350)

    with tab3:
        st.subheader("Traditional vs challenger — which separates the most?")
        st.caption("Cohen's d. Positive = higher at challengers, negative = higher at traditional.")
        sep = _csv_or_missing("category_comparison.csv", "")
        if sep is not None:
            cols = [c for c in ("feature", "traditional_mean", "challenger_mean", "effect_size_d") if c in sep.columns]
            st.dataframe(sep[cols].set_index("feature"), use_container_width=True, height=350)

    with tab4:
        st.subheader("Similarity between banks")
        st.caption("Euclidean distance in standardised feature space. Lower = more similar.")
        dist = _csv_or_missing("similarity_matrix.csv", "", index_col=0)
        if dist is not None:
            st.dataframe(dist.style.background_gradient(cmap="Blues_r", axis=None), use_container_width=True)

    with tab5:
        st.subheader("AI Score — six independently-measured signals")
        st.caption("0-10 per axis, deterministic from features already in the dataset. Blank = no data, never a zero.")
        scores = _csv_or_missing("ai_score.csv", "")
        if scores is not None:
            st.dataframe(scores.set_index("bank"), use_container_width=True)

    with tab6:
        st.subheader("Cross-sell")
        st.caption("Share of possible other products cross-sold, and which product pairs actually appear together.")
        cs_score = load_output_csv("cross_sell_score.csv")
        cs_matrix = load_output_csv("cross_sell_matrix.csv", index_col=0)
        if cs_score is not None:
            st.markdown("**Cross-sell score per bank**")
            st.bar_chart(cs_score.set_index("bank")["cross_sell_score"])
        if cs_matrix is not None:
            st.markdown("**Product co-occurrence matrix** (row = a page's own product, column = what else it cross-sells)")
            st.dataframe(cs_matrix, use_container_width=True)
        if cs_score is None and cs_matrix is None:
            st.info("`outputs/cross_sell_*.csv` not found. Run `python3 scripts/run_analysis.py`.")

    st.divider()
    st.subheader("📌 Deck claims (FR-14)")
    st.caption("Five observations from ING's own kickoff deck, tested against the measured pages.")
    claims = _csv_or_missing("deck_claims.csv", "")
    if claims is not None:
        cols = [c for c in ("id", "bank", "claim", "verdict", "evidence") if c in claims.columns]
        st.dataframe(claims[cols].set_index("id"), use_container_width=True)


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

    # sieg 20/09: tabs instead of five stacked st.json() blobs - same content,
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
            st.image(str(pngs[0]), caption=f"{pngs[0].name}", use_column_width=True)  # sieg 20/09: see note above


# ── page 4: Rubric ───────────────────────────────────────────────────────

def page_rubric(df: pd.DataFrame | None, profiles: dict) -> None:  # noqa: ARG001 - uniform page signature, see main()
    st.title("📝 Rubric scoring")

    st.info(
        "13 features scored by 2 independent human raters. "
        "Run `scripts/rubric_sheet.py emit` to create sheets, "
        "`merge` to fold them into the dataset, `agreement` for inter-rater agreement."
    )

    raters = ["dan", "siegried", "stephane", "model"]
    for rater in raters:
        df = load_rubric_sheet(f"{rater}_scores.csv")
        label = f"{rater}" + (" (model)" if rater == "model" else "")
        with st.expander(f"{label} — {df.shape[0] if df is not None else 0} pages", expanded=False):
            if df is None:
                st.warning(f"No sheet for {rater}")
                continue
            st.dataframe(df, use_container_width=True, height=300)

    st.divider()
    st.subheader("Inter-rater agreement")
    st.caption(
        "Run `scripts/rubric_sheet.py agreement --sheets data/rubric/*_scores.csv` "
        "for computed Cohen's kappa and percentage agreement."
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

        # sieg 20/09, FIXED: these two filters were built and shown but never
        # applied - picking a bank/family did nothing to the table below it.
        filtered = df[df["bank"].isin(picked_banks) & df["product_family"].isin(picked_families)]
        st.caption(f"Showing {len(filtered)} of {len(df)} pages.")
        st.dataframe(filtered, use_container_width=True, height=400)

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
            st.dataframe(fd_df, use_container_width=True, height=500)
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
    st.dataframe(df[available], use_container_width=True)

    st.divider()
    st.subheader("Collection pipeline")
    st.markdown("""
    **Commands:**
    - `python3 scripts/run_collection.py --config scripts/collection_targets.yaml --method headless`
    - `python3 scripts/import_captures.py --dir <folder> --merge-with data/processed/campaigns.csv`
    """)
    st.caption("Compliance: assert_can_fetch() checks robots.txt before each fetch (fail closed).")


# ── page 8: Trends ───────────────────────────────────────────────────────

def page_trends(df: pd.DataFrame | None, profiles: dict) -> None:  # noqa: ARG001 - uniform page signature, see main()
    st.title("📈 Trends (Google)")
    st.caption(
        "Google Trends Belgium — ING vs competitors. "
        "Separate pipeline in `kbc-ing-benchmark/` (Streamlit + pytrends)."
    )

    st.subheader("Dedicated dashboard")
    st.markdown("""
    The Trends pipeline has its own Streamlit app:
    `cd kbc-ing-benchmark && streamlit run app.py`
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
        st.info("No kbc-ing-benchmark/export found in this repo checkout.")


# ── main ─────────────────────────────────────────────────────────────────

def main() -> None:
    # sieg 20/09, simplified: every page function now takes the same (df,
    # profiles) signature, whether it uses both, one or neither - the old
    # needs_df/needs_profiles branching was one fragile hand-maintained rule
    # away from calling a page with the wrong number of arguments the next
    # time a page's data needs changed. Pages that already guard `df is None`
    # (Data, Collection) keep doing so themselves; this dispatch does not
    # need to know which pages care.
    st.sidebar.title("Navigation")
    pages = {
        "🏠 Home": page_accueil,
        "📊 Analysis": page_analyse,
        "🏷️ Bank profiles": page_profils,
        "📝 Rubric": page_rubric,
        "🗄️ Data": page_data,
        "⚠️ Limitations": page_limitations,
        "🕷️ Collection": page_collection,
        "📈 Trends": page_trends,
    }
    choice = st.sidebar.radio("Pages", list(pages.keys()))

    st.sidebar.divider()
    st.sidebar.caption("Banking Campaigns Comparator\nING DACI / Customer AI\nPOC — 2 weeks, Sep 2026")

    df = load_campaigns()
    profiles = load_profiles()
    pages[choice](df, profiles)


if __name__ == "__main__":
    main()
