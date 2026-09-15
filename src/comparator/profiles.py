"""Bank profile cards - the presentable form of the dataset.

Project Plan, Appendix A. One card per bank, identical fields for every bank,
GENERATED from the rows rather than written by hand so the cards stay reproducible
and comparable (NFR-01, NFR-02).
"""

from __future__ import annotations

from collections import Counter

import pandas as pd

from comparator.analysis import bank_vectors, comparable_features, standardise
from comparator.dictionary import FeatureDictionary, load_dictionary
from comparator.schema import parse_list

# How many features the auto-written signature line is allowed to cite.
SIGNATURE_FEATURES = 3

# Card fields whose value is the mean of a boolean feature. A mean of 0.5 means
# "half the pages", not "0.5" - the renderer says so rather than printing a float.
BOOLEAN_FIELDS = {
    "people_present", "animated", "hero_image",
    "cta_above_fold", "rate_shown",
}


def _mode(series: pd.Series) -> str | None:
    values = series.dropna()
    return None if values.empty else str(values.mode().iat[0])


def _flatten_lists(series: pd.Series) -> list[str]:
    counter: Counter[str] = Counter()
    for cell in series.dropna():
        counter.update(parse_list(cell))
    return [item for item, _ in counter.most_common()]


def _distinctive(bank: str, df: pd.DataFrame, fd: FeatureDictionary, n: int = SIGNATURE_FEATURES, *, tier: str | None = None) -> list[tuple[str, float]]:
    """The features on which this bank departs most from the market average."""
    # sieg 14/09: see the dropna(axis=1, how="any") note in analysis.positioning_axis().
    z = standardise(bank_vectors(df, fd, tier=tier).dropna(axis=1, how="any"))
    if bank not in z.index:
        return []
    row = z.loc[bank].dropna()
    return [(name, float(row[name])) for name in row.abs().sort_values(ascending=False).head(n).index]


def build_profile(df: pd.DataFrame, bank: str, fd: FeatureDictionary | None = None, *, tier: str | None = None) -> dict:
    """Build one bank's profile card from its rows."""
    fd = fd or load_dictionary()
    rows = df[df["bank"] == bank]
    if rows.empty:
        raise ValueError(f"no rows for bank {bank!r}")

    def mean(col: str) -> float | None:
        if col not in rows.columns:
            return None
        values = pd.to_numeric(rows[col].astype("float64"), errors="coerce").dropna()
        return None if values.empty else float(values.mean())

    return {
        "identity": {
            "bank": bank,
            "category": _mode(rows["bank_category"]),
            "pages_analysed": len(rows),
            "product_family": _mode(rows["product_family"]),
            "language": _mode(rows["language"]),
            "captured": _mode(rows["captured_at"].astype("string")),
            "data_source": _mode(rows["data_source"]),
        },
        "palette": {
            "dominant_colour": _mode(rows.get("dominant_colour_hex", pd.Series(dtype="object"))),
            "brand_colour_share": mean("brand_colour_share"),
            "accent_colour_count": mean("accent_colour_count"),
            "accent_locations": _flatten_lists(rows.get("accent_locations", pd.Series(dtype="object"))),
            "background_luminance": mean("background_luminance"),
        },
        "imagery": {
            "image_count": mean("image_count"),
            "dominant_image_type": _mode(rows.get("dominant_image_type", pd.Series(dtype="object"))),
            "people_present": mean("people_present"),
            "animated": mean("has_animation"),
            "image_area_share": mean("total_image_area_ratio"),
        },
        "layout": {
            "archetype": _mode(rows.get("layout_archetype", pd.Series(dtype="object"))),
            "hero_image": mean("hero_image_present"),
            "text_image_layout": _mode(rows.get("text_image_layout", pd.Series(dtype="object"))),
            "page_height_px": mean("page_height_px"),
            "cta_count": mean("cta_count"),
            "cta_above_fold": mean("cta_above_fold"),
        },
        "tone": {
            "word_count": mean("word_count"),
            "readability_band": _mode(rows.get("readability_band", pd.Series(dtype="object"))),
            "formality_score": mean("formality_score"),
            "second_person_ratio": mean("second_person_ratio"),
            "urgency_markers": mean("urgency_marker_count"),
        },
        "value_proposition": {
            "primary_product": _mode(rows.get("primary_product", pd.Series(dtype="object"))),
            "rate_shown": mean("rate_shown"),
            "rate_prominence": _mode(rows.get("rate_prominence", pd.Series(dtype="object"))),
            "benefit_framing": _mode(rows.get("benefit_framing", pd.Series(dtype="object"))),
            "fab_level": _mode(rows.get("fab_level", pd.Series(dtype="object"))),
        },
        "marketing_principles": {
            "aida_coverage": mean("aida_coverage_score"),
            "persuasion_levers": _flatten_lists(rows.get("persuasion_levers", pd.Series(dtype="object"))),
            "lever_count": mean("persuasion_lever_count"),
        },
        "signature": _distinctive(bank, df, fd, tier=tier),
    }


def build_all(df: pd.DataFrame, fd: FeatureDictionary | None = None, *, tier: str | None = None) -> dict[str, dict]:
    fd = fd or load_dictionary()
    return {bank: build_profile(df, bank, fd, tier=tier) for bank in sorted(df["bank"].unique())}


def _fmt_share(value: object) -> str:
    """Render a mean-of-boolean as something a reader can act on."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "-"
    share = float(value)
    if share >= 0.999:
        return "yes (all pages)"
    if share <= 0.001:
        return "no"
    return f"{share:.0%} of pages"


def _fmt(value: object, digits: int = 2) -> str:
    # sieg 14/09 - NOTE FOR LATER, not fixed now (never triggered today, every
    # call site uses the default digits=2): with digits=0 there is no decimal
    # point for rstrip("0") to stop at, so an integer like 200 would be
    # stripped down to "2". Safe today only because digits=0 is never passed.
    # If anyone parameterises this later, guard it, e.g.:
    #   text = f"{value:,.{digits}f}"
    #   return text.rstrip("0").rstrip(".") if "." in text else text
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "-"
    if isinstance(value, float):
        return f"{value:,.{digits}f}".rstrip("0").rstrip(".") if abs(value) < 1000 else f"{value:,.0f}"
    if isinstance(value, list):
        return ", ".join(value) if value else "-"
    return str(value)


def render_markdown(profile: dict, fd: FeatureDictionary | None = None) -> str:
    """Render one profile card as markdown, ready to drop into the deck."""
    fd = fd or load_dictionary()
    ident = profile["identity"]
    lines = [
        f"### {ident['bank']}  ({ident['category']})",
        "",
        f"*{ident['pages_analysed']} page(s) · {ident['product_family']} · "
        f"{ident['language']} · captured {ident['captured']} · source: {ident['data_source']}*",
        "",
        "| Field | Value |",
        "| --- | --- |",
    ]
    for section in ("palette", "imagery", "layout", "tone", "value_proposition", "marketing_principles"):
        for key, value in profile[section].items():
            rendered = _fmt_share(value) if key in BOOLEAN_FIELDS else _fmt(value)
            lines.append(f"| {key.replace('_', ' ')} | {rendered} |")

    if profile["signature"]:
        parts = []
        for name, z in profile["signature"]:
            direction = "well above" if z > 0 else "well below"
            parts.append(f"{name.replace('_', ' ')} {direction} the market average ({z:+.1f} SD)")
        lines += ["", f"**Signature:** {'; '.join(parts)}."]

    return "\n".join(lines)


def render_all_markdown(profiles: dict[str, dict], fd: FeatureDictionary | None = None) -> str:
    fd = fd or load_dictionary()
    return "\n\n".join(render_markdown(p, fd) for p in profiles.values())
