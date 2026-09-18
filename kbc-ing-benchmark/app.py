"""Streamlit app: ING against eight competitor banks on Google Trends,
one comparison per sidebar entry and one tab per product sheet.

Reads trends_data, anomalies and term_validation from SQLite. All three
tables are populated by separate pipeline steps
(collectors/trends_collector.py, analysis/anomaly_detection.py,
collectors/term_resolver.py) and are only read here, so the UI stays fast.
Ad/campaign verification against the flagged anomalies is handled by a
separate downstream pipeline, out of scope here.
"""

import sqlite3

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from config import (
    ANOMALY_TYPE_LABELS, BANK_DISPLAY_LABELS, DB_PATH, KNOWN_EVENTS, PRODUCTS,
    TERM_DISPLAY_LABELS,
)

PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#c98500", "#e87ba4"]
ANOMALY_SYMBOLS = {"isolated_spike": "diamond", "sustained_trend": "star"}

# Line style per bank. Styles are reused on purpose: two banks sharing a
# style never appear in the same product sheet, so they can never be
# confused inside one chart.
BANK_DASH = {
    "ING": "dash",
    "KBC": "solid",
    "CBC": "dashdot",
    "BNPPF": "dot",
    "ARGENTA": "longdash",
    "CRELAN": "longdashdot",
    "REVOLUT": "dot",
    "N26": "longdash",
    "BUNQ": "longdashdot",
}

# Sheets grouped under the "Marques & contexte" view rather than under the
# view of a single competitor: they carry the ING/KBC anchor terms and are
# meant to be read across banks.
BRAND_CONTEXT_FICHES = [
    "marque_generique",
    "marque_generique_traditionnelles",
    "marque_generique_neobanques",
    "contexte_integration_bnppf_bpost",
    "contexte_fusion_crelan_axa",
]

BRAND_CONTEXT_VIEW = "Marques & contexte"

# Sidebar comparison selector: label -> bank code filtered on, or None for
# the brand/context group. ING is the common anchor of every sheet and so
# has no view of its own.
COMPARISON_VIEWS = {
    "KBC": "KBC",
    "CBC": "CBC",
    "BNP Paribas Fortis": "BNPPF",
    "Argenta": "ARGENTA",
    "Crelan": "CRELAN",
    "Revolut": "REVOLUT",
    "N26": "N26",
    "bunq": "BUNQ",
    BRAND_CONTEXT_VIEW: None,
}

FLAG_LABELS = {
    "selected_low_coverage": "couverture faible (série peu dense, anomalies plus bruitées)",
    "broad_fallback": "terme large (capte un périmètre plus étendu que le terme ING)",
    "asymmetric": "asymétrique (n'est pas la transposition exacte du terme ING)",
    "ambiguous_string": "chaîne brute ambiguë (aucun topic Knowledge Graph valide)",
}

st.set_page_config(page_title="Benchmark ING vs concurrents", layout="wide")


def display_term(term):
    return TERM_DISPLAY_LABELS.get(term, term)


def display_bank(bank):
    return BANK_DISPLAY_LABELS.get(bank, bank)


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    try:
        trends = pd.read_sql_query("SELECT * FROM trends_data", conn, parse_dates=["date"])
        anomalies = pd.read_sql_query("SELECT * FROM anomalies", conn, parse_dates=["date"])
    finally:
        conn.close()
    return trends, anomalies


@st.cache_data
def load_term_flags():
    """(product_id, term) -> list of flags recorded during term resolution.

    Empty for the historical sheets, which predate term_validation.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT product_id, term, verdict, flags FROM term_validation "
            "WHERE call_index = 0 AND slot_language != '__done__' AND verdict != 'dropped'"
        ).fetchall()
        brand_rows = conn.execute(
            "SELECT term, flags FROM term_validation WHERE scope = 'brand' "
            "AND call_index = 0 AND slot_language != '__done__'"
        ).fetchall()
    except sqlite3.OperationalError:
        # term_validation has not been created yet (fresh database).
        return {}
    finally:
        conn.close()

    brand_flags = {r[0]: [f for f in (r[1] or "").split(",") if f] for r in brand_rows}

    flags = {}
    for product_id, term, verdict, raw_flags in rows:
        parts = [f for f in (raw_flags or "").split(",") if f]
        if verdict == "selected_low_coverage":
            parts.insert(0, verdict)
        if parts:
            flags[(product_id, term)] = parts

    # Brand terms keep their flags wherever they are reused (brand sheets,
    # context sheets), since the ambiguity is a property of the term itself.
    for product in PRODUCTS:
        for t in product["terms"]:
            own = brand_flags.get(t["term"])
            if own:
                key = (product["product_id"], t["term"])
                flags[key] = sorted(set(flags.get(key, []) + own))
    return flags


def fiches_for_view(view_label):
    if COMPARISON_VIEWS[view_label] is None:
        return [p for p in PRODUCTS if p["product_id"] in BRAND_CONTEXT_FICHES]
    bank = COMPARISON_VIEWS[view_label]
    return [
        p for p in PRODUCTS
        if p["product_id"] not in BRAND_CONTEXT_FICHES
        and any(t["bank"] == bank for t in p["terms"])
    ]


def events_for_product(product):
    banks = {t["bank"] for t in product["terms"]}
    return [e for e in KNOWN_EVENTS if e["bank"] in banks]


def build_chart(product, trends_df, anomalies_df):
    fig = go.Figure()
    pid = product["product_id"]

    for i, t in enumerate(product["terms"]):
        term, bank, lang = t["term"], t["bank"], t["language"]
        label = display_term(term)
        bank_label = display_bank(bank)
        color = PALETTE[i % len(PALETTE)]
        dash = BANK_DASH.get(bank, "solid")

        series = trends_df[(trends_df["product_id"] == pid) & (trends_df["term"] == term)].sort_values("date")
        fig.add_trace(go.Scatter(
            x=series["date"], y=series["value"], mode="lines",
            name=f"{label} ({bank_label} · {lang.upper()})",
            line=dict(color=color, width=2, dash=dash),
            hovertemplate=f"<b>{label}</b><br>{bank_label} · {lang.upper()}<br>%{{x|%b %Y}}: %{{y}}<extra></extra>",
        ))

        term_anomalies = anomalies_df[(anomalies_df["product_id"] == pid) & (anomalies_df["term"] == term)]
        for atype, symbol in ANOMALY_SYMBOLS.items():
            sub = term_anomalies[term_anomalies["anomaly_type"] == atype]
            if sub.empty:
                continue
            fig.add_trace(go.Scatter(
                x=sub["date"], y=sub["value"], mode="markers",
                marker=dict(symbol=symbol, size=12, color=color, line=dict(color="#1a1a1a", width=1.2)),
                showlegend=False,
                hovertemplate=(
                    f"<b>{label}</b><br>{ANOMALY_TYPE_LABELS[atype]}"
                    "<br>%{x|%b %Y}: %{y}<extra></extra>"
                ),
            ))

    # Legend proxies explaining the anomaly marker symbols.
    for atype, symbol in ANOMALY_SYMBOLS.items():
        fig.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(symbol=symbol, size=12, color="#8c8d8a", line=dict(color="#1a1a1a", width=1.2)),
            name=ANOMALY_TYPE_LABELS[atype],
        ))

    # Known structural events of the banks present in this sheet. Display
    # only: these dates never take part in anomaly detection.
    for event in events_for_product(product):
        fig.add_vline(
            x=event["date"], line_width=1, line_dash="dot", line_color="#8c8d8a",
        )
        fig.add_trace(go.Scatter(
            x=[event["date"]], y=[100], mode="markers",
            marker=dict(symbol="triangle-down", size=10, color="#8c8d8a"),
            showlegend=False,
            hovertemplate=(
                f"<b>{display_bank(event['bank'])} · {event['date']}</b><br>"
                f"{event['label']}<extra></extra>"
            ),
        ))

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Intérêt de recherche (0-100)",
        legend=dict(orientation="h", yanchor="top", y=-0.18),
        height=440,
        margin=dict(t=20, b=10, l=10, r=10),
    )
    return fig


def render_flag_notes(product, term_flags):
    pid = product["product_id"]
    notes = []
    for t in product["terms"]:
        flags = term_flags.get((pid, t["term"]))
        if not flags:
            continue
        readable = ", ".join(FLAG_LABELS.get(f, f) for f in flags)
        notes.append(f"**{display_term(t['term'])}** ({display_bank(t['bank'])}) — {readable}")
    if notes:
        st.caption(
            "Termes signalés lors de la résolution (voir `data/term_validation_report.md`) : "
            + " · ".join(notes)
        )

    events = events_for_product(product)
    if events:
        st.caption(
            "Événements structurels marqués sur le graphique : "
            + " · ".join(f"{e['date']} — {display_bank(e['bank'])} : {e['label']}" for e in events)
        )


def render_anomalies_table(product, anomalies_df):
    pid = product["product_id"]
    subset = anomalies_df[anomalies_df["product_id"] == pid].sort_values("date").copy()
    if subset.empty:
        st.caption("Aucune anomalie détectée pour cette fiche.")
        return

    subset["date"] = subset["date"].dt.strftime("%Y-%m-%d")
    subset["anomaly_type"] = subset["anomaly_type"].map(ANOMALY_TYPE_LABELS)
    subset["term"] = subset["term"].map(display_term)
    subset["bank"] = subset["bank"].map(display_bank)
    subset = subset.rename(columns={
        "term": "Terme", "bank": "Banque", "date": "Date",
        "value": "Valeur", "anomaly_type": "Type d'anomalie",
        "deviation_score": "Score de déviation",
    })
    st.dataframe(
        subset[["Terme", "Banque", "Date", "Valeur", "Type d'anomalie", "Score de déviation"]],
        width="stretch", hide_index=True,
    )


def render_raw_data(product, trends_df):
    pid = product["product_id"]
    subset = trends_df[trends_df["product_id"] == pid].sort_values("date")
    if subset.empty:
        st.caption("Aucune donnée disponible pour cette fiche.")
        return

    term_options = [t["term"] for t in product["terms"]]
    selected_terms = st.multiselect(
        "Termes", term_options, default=term_options, format_func=display_term, key=f"terms_{pid}",
    )
    min_date, max_date = subset["date"].min().date(), subset["date"].max().date()
    date_range = st.date_input(
        "Période", value=(min_date, max_date), min_value=min_date, max_value=max_date, key=f"dates_{pid}",
    )

    filtered = subset[subset["term"].isin(selected_terms)]
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        filtered = filtered[(filtered["date"].dt.date >= start) & (filtered["date"].dt.date <= end)]

    display = filtered.copy()
    display["term"] = display["term"].map(display_term)
    display["bank"] = display["bank"].map(display_bank)
    display = display.rename(columns={
        "term": "Terme", "bank": "Banque", "language": "Langue",
        "date": "Date", "value": "Valeur",
    })
    display["Date"] = display["Date"].dt.strftime("%Y-%m-%d")
    st.dataframe(
        display[["Terme", "Banque", "Langue", "Date", "Valeur"]],
        width="stretch", hide_index=True,
    )


def render_product_tab(product, trends_df, anomalies_df, term_flags):
    st.plotly_chart(build_chart(product, trends_df, anomalies_df), width="stretch")
    render_flag_notes(product, term_flags)
    st.subheader("Anomalies détectées")
    render_anomalies_table(product, anomalies_df)
    st.subheader("Données brutes")
    render_raw_data(product, trends_df)


def main():
    st.title("Benchmark marketing ING vs concurrents")
    st.caption(
        "Intérêt de recherche Google Trends (Belgique, 5 dernières années) par fiche produit — "
        "les anomalies marquées ici sont les périodes où l'intérêt de recherche d'un produit a été "
        "anormalement élevé. La vérification de leur origine (publicité, campagne) se fait dans un "
        "autre pipeline, alimenté par les exports de ce projet."
    )

    trends_df, anomalies_df = load_data()
    if trends_df.empty:
        st.error(
            "Aucune donnée trouvée. Lancez d'abord `python collectors/trends_collector.py` "
            "puis `python analysis/anomaly_detection.py`."
        )
        st.stop()

    term_flags = load_term_flags()

    view_labels = list(COMPARISON_VIEWS)
    view = st.sidebar.selectbox("Comparaison", view_labels, index=view_labels.index("KBC"))
    st.sidebar.caption(
        "ING est l'ancre commune de toutes les fiches : chaque comparaison oppose ING à la "
        "banque sélectionnée. « Marques & contexte » regroupe les fiches de marque et les "
        "fiches expliquant les ruptures structurelles du marché."
    )

    products = fiches_for_view(view)
    if not products:
        st.info("Aucune fiche disponible pour cette comparaison.")
        st.stop()

    st.subheader(f"Comparaison ING vs {view}" if COMPARISON_VIEWS[view] else view)

    tabs = st.tabs([p["product_label"] for p in products])
    for tab, product in zip(tabs, products):
        with tab:
            render_product_tab(product, trends_df, anomalies_df, term_flags)


if __name__ == "__main__":
    main()
