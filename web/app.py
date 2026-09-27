"""The Democratic Funnel - dashboard (Flask).

Reads only app/artifacts/dashboard.csv and app/artifacts/municipalities.geojson (both written by
notebooks/09_dashboard_prep.ipynb). Every number the pages show is worked out here, once, and sent to the browser
as one JSON bundle; the browser draws the pages (Chart.js for charts, Leaflet for the map).

Run locally:  python web/app.py            (then open http://localhost:5000)
On Render:    gunicorn --chdir web app:app
"""
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, Response, jsonify, render_template, send_file

ROOT = Path(__file__).resolve().parent
ART = ROOT.parent / "app" / "artifacts"

app = Flask(__name__)
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 60 * 60 * 24          # static files and the map are cached for a day

GROUPS = ["Low registration", "Low turnout", "Both low", "Healthy"]
YEARS = (2011, 2016, 2021)


def clean(x):
    """JSON-safe value: NaN becomes None, numpy numbers become plain numbers."""
    if isinstance(x, (np.floating, float)):
        return None if np.isnan(x) else round(float(x), 6)
    if isinstance(x, np.integer):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def wavg(df, col, weight="Registered 2026"):
    return float((df[col] * df[weight]).sum() / df[weight].sum())


def national(d):
    adults = d["Adults who may vote"].sum()
    n = {"adults": adults}
    for y in YEARS:
        n[f"registered_{y}"], n[f"votes_{y}"] = d[f"Registered {y}"].sum(), d[f"Votes cast {y}"].sum()
        n[f"turnout_{y}"] = n[f"votes_{y}"] / n[f"registered_{y}"]
        n[f"reg_rate_{y}"] = n[f"registered_{y}"] / adults
    n["registered_2026"] = d["Registered 2026"].sum()
    n["reg_rate_2026"] = n["registered_2026"] / adults
    n["youth_adults"], n["youth_registered"] = d["Young adults who may vote"].sum(), d["Young adults registered"].sum()
    n["youth_not_registered"] = d["Young adults not registered"].sum()
    n["youth_reg_rate"] = n["youth_registered"] / n["youth_adults"]
    n["older_reg_rate"] = (n["registered_2026"] - n["youth_registered"]) / (adults - n["youth_adults"])
    n["youth_share_of_missing"] = n["youth_not_registered"] / (adults - n["registered_2026"])
    n["youth_below"] = int((d["Youth registration rate"] < d["Registration rate 2026"]).sum())
    n["census_caution"] = int(d["Census caution"].sum())
    n["has_pred"] = bool(d["Predicted turnout 2026"].notna().all())
    if n["has_pred"]:
        n["pred_2026"] = wavg(d, "Predicted turnout 2026")
        n["pred_2026_low"] = wavg(d, "Predicted turnout 2026 (low)")
        n["pred_2026_high"] = wavg(d, "Predicted turnout 2026 (high)")
    n["typical_reg"] = float(d["Typical registration rate"].iloc[0])
    n["groups"] = {g: int((d["Problem group"] == g).sum()) for g in GROUPS}
    n["covid"] = d["After COVID (2024)"].value_counts().to_dict() if "After COVID (2024)" in d else {}
    return {k: clean(v) if not isinstance(v, dict) else v for k, v in n.items()}


def by_province(d):
    rows = []
    for p, g in d.groupby("Province"):
        r = {"province": p}
        for y in YEARS:
            r[f"t{y}"] = g[f"Votes cast {y}"].sum() / g[f"Registered {y}"].sum()
        r["p2021"] = g["Votes cast 2021"].sum() / g["Adults who may vote"].sum()
        rows.append({k: clean(v) for k, v in r.items()})
    return sorted(rows, key=lambda r: r["t2021"], reverse=True)


def fit_line(x, y):
    """Straight-line fit with a 95% band for the mean, on the given x values."""
    b, a = np.polyfit(x, y, 1)
    resid = y - (a + b * x)
    s2 = (resid ** 2).sum() / (len(x) - 2)
    grid = np.linspace(x.min(), x.max(), 40)
    se = np.sqrt(s2 * (1 / len(x) + (grid - x.mean()) ** 2 / ((x - x.mean()) ** 2).sum()))
    fit = a + b * grid
    return {"x": grid.tolist(), "y": fit.tolist(), "lo": (fit - 1.96 * se).tolist(), "hi": (fit + 1.96 * se).tolist(),
            "r": float(np.corrcoef(x, y)[0, 1])}


def eda(d, n):
    out = {}
    tw = d[["Municipality", "Province"] + [f"Turnout {y}" for y in YEARS]].copy()
    tw["avg"] = tw[[f"Turnout {y}" for y in YEARS]].mean(axis=1)
    low = tw.nsmallest(10, "avg")
    out["lowest10"] = [{"name": r["Municipality"], "province": r["Province"], "t2011": clean(r["Turnout 2011"]),
                        "t2016": clean(r["Turnout 2016"]), "t2021": clean(r["Turnout 2021"]), "avg": clean(r["avg"])}
                       for _, r in low.iterrows()]

    chars = ["Adults with higher education", "Households with piped water", "Households with electricity",
             "Households with refuse removal", "Population density", "Neighbours' turnout 2021"]
    x = d.assign(**{"Population density": np.log(d["Population density"])})
    corr = x[["Registration vs typical 2021", "Turnout vs typical 2021"] + chars].corr()
    out["corr"] = {"rows": [c.replace(" 2021", "") for c in chars],
                   "reg": [clean(corr.loc[c, "Registration vs typical 2021"]) for c in chars],
                   "turn": [clean(corr.loc[c, "Turnout vs typical 2021"]) for c in chars],
                   "reg_turn": clean(corr.loc["Registration vs typical 2021", "Turnout vs typical 2021"])}

    sp = d.dropna(subset=["Neighbours' turnout 2021", "Turnout 2021"])
    out["cluster"] = {"points": [[clean(a), clean(b), m] for a, b, m in
                                 zip(sp["Neighbours' turnout 2021"], sp["Turnout 2021"], sp["Municipality"])],
                      "fit": fit_line(sp["Neighbours' turnout 2021"].to_numpy(), sp["Turnout 2021"].to_numpy()),
                      "r_prev": clean(sp["Turnout 2021"].corr(sp["Neighbours' turnout 2016"]))}

    dd = d.dropna(subset=["Population density", "Turnout vs typical 2021"])
    f = fit_line(np.log10(dd["Population density"].to_numpy()), dd["Turnout vs typical 2021"].to_numpy())
    f["x"] = [10 ** v for v in f["x"]]
    out["density"] = {"points": [[clean(a), clean(b), m] for a, b, m in
                                 zip(dd["Population density"], dd["Turnout vs typical 2021"], dd["Municipality"])],
                      "fit": f}
    return out


# columns the browser needs, per municipality
COLS = ["Code", "Municipality", "Province", "Type", "Adults who may vote", "Registered 2026", "Registration rate 2026",
        "Census caution", "Young adults who may vote", "Young adults registered", "Youth registration rate",
        "Young adults not registered", "Turnout 2011", "Turnout 2016", "Turnout 2021", "Registered 2021",
        "Votes cast 2021", "Predicted turnout 2026", "Predicted turnout 2026 (low)", "Predicted turnout 2026 (high)",
        "Worse than expected in 2021", "After COVID (2024)", "Predicted turnout 2026 (COVID recovery)", "Turnout used",
        "Typical registration rate", "Typical turnout", "Typical youth registration rate", "Problem group",
        "What to send", "Registered per 100 adults", "Voters per 100 adults", "Registrations needed to reach typical",
        "Extra voters needed to reach typical", "Shortfall: registration part", "Shortfall: turnout part",
        "Priority rank"]


@lru_cache(maxsize=1)
def bundle():
    d = pd.read_csv(ART / "dashboard.csv")
    d["Worse than expected in 2021"] = d["Worse than expected in 2021"].astype(str) == "True"
    n = national(d)
    rows = [{k: clean(v) for k, v in r.items()} for r in d[COLS].sort_values("Priority rank").to_dict("records")]
    payload = {"national": n, "provinces": by_province(d), "eda": eda(d, n), "rows": rows}
    return json.dumps(payload, separators=(",", ":"), allow_nan=False)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/data")
def data():
    return Response(bundle(), mimetype="application/json", headers={"Cache-Control": "public, max-age=600"})


@app.route("/api/geo")
def geo():
    # sent once and kept by the browser (ETag + a day of caching); the page also keeps the map alive between pages
    return send_file(ART / "municipalities.geojson", mimetype="application/geo+json", conditional=True, max_age=86400)


@app.route("/healthz")
def healthz():
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
