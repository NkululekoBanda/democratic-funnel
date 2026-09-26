"""Loading the dashboard data, and the house style shared by every page.

The app only reads what notebooks/09_dashboard_prep.ipynb wrote to app/artifacts/.
"""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

ART = Path(__file__).resolve().parents[1] / "artifacts"

# ------------------------------------------------------------------ colours (same meanings as 07_eda)
BLUE, AMBER, CRIMSON, GREEN, NAVY = "#2a78d6", "#eda100", "#a3143a", "#7bc586", "#1b2f5b"
BLUE_LIGHT = "#8db8ec"
AMBER_TEXT = "#8a5d00"            # amber is too light for text on white; this darker step is used for words
DIRISA_ORANGE = "#ee7900"
INK, INK2, GRID = "#0b0b0b", "#4a4a47", "#e4e3de"

GROUPS = ["Low registration", "Low turnout", "Both low", "Healthy"]
GROUP_COLOURS = {"Low registration": BLUE, "Low turnout": AMBER, "Both low": CRIMSON, "Healthy": GREEN}

# one-hue ramps, light (small gap) -> dark (large gap)
RAMPS = {
    "blue": ["#e3eefb", "#b7d3f6", "#86b6ef", "#3987e5", "#1c5cab", "#0d366b"],
    "amber": ["#fdf1d6", "#f9dc97", "#f2c14f", "#eda100", "#b27800", "#6e4a00"],
    "crimson": ["#f8e1e6", "#eaa7b5", "#d4637c", "#a3143a", "#7a0f2b", "#4d0a1b"],
}

# the measures a user can put on a map - each clearly defined
MAP_MEASURES = {
    "Registration gap (2026)": dict(col="Registration gap 2026", ramp="blue",
                                    help="Share of adults who may vote who are NOT on the 2026 voters' roll."),
    "Turnout gap (2021)": dict(col="Turnout gap 2021", ramp="amber",
                               help="Share of registered voters who did NOT vote in the 2021 municipal election."),
    "Participation shortfall (2021)": dict(col="Participation shortfall 2021", ramp="crimson",
                                           help="Share of ALL adults who may vote who did NOT vote in 2021 "
                                                "(both leaks together)."),
    "Youth registration gap (2026)": dict(col="Youth registration gap 2026", ramp="blue",
                                          help="Share of adults aged 18–29 who are NOT on the 2026 voters' roll."),
    "Youth turnout gap": dict(col=None, ramp="amber",
                              help="Not available: the IEC does not publish turnout by age for municipalities."),
}

NOT_A_CAUSE = "A pattern is not proof of a cause: differences between municipalities cannot show why individuals act."
YOUTH_NOTE = "Youth figures are about registration only. The IEC does not publish turnout by age for municipalities."

# Measured accuracy of the prediction model (08_model, trained 2011->2016, tested on 2016->2021, 213 municipalities)
MODEL_ACCURACY = {
    "mae": 3.53, "mae_ci": (3.14, 3.91), "within5": 0.76, "within3": 0.54, "r2": 0.53, "rank_corr": 0.70,
    "baseline_mae": 3.25, "baseline_ci": (2.93, 3.60), "no_change_mae": 9.13,
}


@st.cache_data
def load():
    d = pd.read_csv(ART / "dashboard.csv")
    geo_path = ART / "municipalities.geojson"
    geo = json.loads(geo_path.read_text(encoding="utf-8")) if geo_path.exists() else None
    return d, geo


def has_data():
    return (ART / "dashboard.csv").exists()


def national(d):
    """National totals and rates, each labelled with its year."""
    adults = d["Adults who may vote"].sum()
    out = {"adults": adults, "municipalities": len(d)}
    for y in (2011, 2016, 2021):
        out[f"registered_{y}"] = d[f"Registered {y}"].sum()
        out[f"votes_{y}"] = d[f"Votes cast {y}"].sum()
        out[f"turnout_{y}"] = out[f"votes_{y}"] / out[f"registered_{y}"]
    out["registered_2026"] = d["Registered 2026"].sum()
    out["reg_rate_2026"] = out["registered_2026"] / adults
    out["reg_rate_2021"] = out["registered_2021"] / adults
    out["participation_2021"] = out["votes_2021"] / adults
    out["youth_adults"] = d["Young adults who may vote"].sum()
    out["youth_registered"] = d["Young adults registered"].sum()
    out["youth_not_registered"] = d["Young adults not registered"].sum()
    out["youth_reg_rate"] = out["youth_registered"] / out["youth_adults"]
    older_adults = adults - out["youth_adults"]
    out["older_reg_rate"] = (out["registered_2026"] - out["youth_registered"]) / older_adults
    out["youth_share_of_missing"] = out["youth_not_registered"] / (adults - out["registered_2026"])
    pred = d["Predicted turnout 2026"]
    if pred.notna().all():
        w = d["Registered 2026"]
        out["pred_2026"] = (pred * w).sum() / w.sum()
        out["pred_2026_low"] = (d["Predicted turnout 2026 (low)"] * w).sum() / w.sum()
        out["pred_2026_high"] = (d["Predicted turnout 2026 (high)"] * w).sum() / w.sum()
    return out


def by_province(d):
    rows = []
    for p, g in d.groupby("Province"):
        r = {"Province": p}
        for y in (2011, 2016, 2021):
            r[f"Turnout {y}"] = g[f"Votes cast {y}"].sum() / g[f"Registered {y}"].sum()
        r["Registration rate 2026"] = g["Registered 2026"].sum() / g["Adults who may vote"].sum()
        r["Youth registration rate 2026"] = g["Young adults registered"].sum() / g["Young adults who may vote"].sum()
        r["Participation 2021"] = g["Votes cast 2021"].sum() / g["Adults who may vote"].sum()
        rows.append(r)
    return pd.DataFrame(rows)


def pct(x, digits=0):
    return "–" if pd.isna(x) else f"{x * 100:.{digits}f}%"


def num(x):
    return "–" if pd.isna(x) else f"{x:,.0f}".replace(",", " ")


def millions(x):
    return f"{x / 1e6:.1f} million"
