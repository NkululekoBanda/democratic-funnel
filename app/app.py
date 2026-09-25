"""The Democratic Funnel - interactive dashboard.

Run locally:   streamlit run app/app.py
Data:          app/artifacts/ (made by app/prepare_artifacts.py after 08_model)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ARTIFACTS = Path(__file__).resolve().parent / "artifacts"

st.set_page_config(page_title="Democratic Funnel", page_icon="🗳️", layout="wide")

# ------------------------------------------------------------------ colours
# Leak types: the first three categorical slots (validated colour-blind safe as a set) plus a
# light neutral for "no leak", which should recede rather than compete.
LEAK_COLOURS = {
    "Registration leak": "#2a78d6",
    "Turnout leak": "#eb6834",
    "Both leaks": "#1baf7a",
    "No leak": "#dcdbd5",
}
LEAK_ORDER = list(LEAK_COLOURS)
# DIRISA brand (dirisa.ac.za): orange accent and charcoal. The orange is used for marks and accents,
# never for small text (2.85:1 on white); text stays charcoal.
BRAND = "#ee7900"
CHARCOAL = "#313131"
ORANGE_RAMP = ["#fdebd9", "#fbd0a6", "#f7ad6b", "#ee7900", "#c96500", "#9a4d00", "#6b3500"]
FUNNEL_STEPS = ["#f5a35a", "#ee7900", "#a95400"]          # ordinal: eligible -> registered -> voters
MUTED = "#898781"
GRID = "#e1e0d9"

SCENARIOS = {
    "Half recovery (central)": "t_2026_half_recovery",
    "No recovery": "t_2026_no_recovery",
    "Full recovery": "t_2026_full_recovery",
}
FACTOR_NOTE = "Factors are associations across municipalities, not proven causes."


# ------------------------------------------------------------------ data
@st.cache_data
def load():
    master = pd.read_csv(ARTIFACTS / "master.csv")
    pred = pd.read_csv(ARTIFACTS / "predictions_2026.csv")
    geo_path = ARTIFACTS / "municipalities.geojson"
    geo = json.loads(geo_path.read_text(encoding="utf-8")) if geo_path.exists() else None
    # Some IEC names are in capitals (e.g. "KAREEBERG"): title-case those only, keep "eThekwini" as is
    fix = lambda s: s.where(~s.str.isupper(), s.str.title())
    master["muni_name"] = fix(master.groupby("muni_code")["muni_name"].transform("last"))
    pred["muni_name"] = fix(pred["muni_name"])
    return master, pred, geo


def leak_type(reg_leak, turn_leak):
    """Below-median registration and/or turnout -> leak type."""
    return np.select(
        [(reg_leak < 0) & (turn_leak < 0), reg_leak < 0, turn_leak < 0],
        ["Both leaks", "Registration leak", "Turnout leak"],
        "No leak",
    )


def style(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=40, b=10),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", size=13),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
                      hoverlabel=dict(font_size=13))
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    return fig


def pct(x, digits=1):
    return "–" if pd.isna(x) else f"{x * 100:.{digits}f}%"


def num(x):
    return "–" if pd.isna(x) else f"{x:,.0f}".replace(",", " ")


def tile(col, label, value, note=None):
    """A headline number with an optional plain note underneath (not a +/- change)."""
    col.metric(label, value)
    if note:
        col.caption(note)


if not (ARTIFACTS / "master.csv").exists():
    st.error("No data found in app/artifacts/. Run `python app/prepare_artifacts.py` after 08_model.")
    st.stop()

master, pred, geo = load()

# 2026 forecast under the chosen scenario, with the model's range shifted to match
st.sidebar.markdown(f"<h2 style='color:{CHARCOAL};margin-bottom:0'>🗳️ Democratic Funnel</h2>"
                    f"<div style='height:4px;width:56px;background:{BRAND};margin:6px 0 14px'></div>",
                    unsafe_allow_html=True)
scenario = st.sidebar.radio(
    "2026 turnout scenario", list(SCENARIOS),
    help="2021 was the COVID election. The scenario sets how much national turnout recovers by 2026; "
         "the model then adjusts each municipality up or down from that.")
t_col = SCENARIOS[scenario]
shift = pred[t_col] - pred["t_2026"]
pred["t_fc"] = pred[t_col]
pred["t_fc_low"] = (pred["t_2026_low"] + shift).clip(0.05, 0.95)
pred["t_fc_high"] = (pred["t_2026_high"] + shift).clip(0.05, 0.95)
pred["p_fc"] = pred["r_2026"] * pred["t_fc"]

provinces = ["All provinces"] + sorted(pred["province"].unique())
province = st.sidebar.selectbox("Province", provinces)
st.sidebar.caption("Data: IEC election results 2011–2021, IEC registration (Sept 2026), "
                   "Stats SA Census 2022, Municipal Demarcation Board boundaries.")


def in_province(df):
    return df if province == "All provinces" else df[df["province"] == province]


# ------------------------------------------------------------------ header
st.markdown(f"""
<div style="background:{CHARCOAL};border-bottom:5px solid {BRAND};border-radius:6px;padding:20px 24px;margin-bottom:18px">
  <div style="color:{BRAND};font-size:0.8rem;letter-spacing:0.12em;font-weight:600">
    DIRISA STUDENT DATATHON CHALLENGE 2026 · TEAM UL</div>
  <div style="color:#ffffff;font-size:2.1rem;font-weight:700;line-height:1.2;margin-top:4px">The Democratic Funnel</div>
  <div style="color:#d9d6d0;font-size:1rem;margin-top:4px">
    Where local democracy leaks before the local government elections on 4 November 2026</div>
</div>""", unsafe_allow_html=True)

# ------------------------------------------------------------------ turnout for every election
p26 = in_province(pred)
past = in_province(master[master["election"] < 2026]).groupby("election")[["votes_cast", "registered"]].sum()
history = pd.DataFrame({
    "election": [2011, 2016, 2021, 2026],
    "registered": [*past["registered"], p26["registered_2026"].sum()],
    "turnout": [*(past["votes_cast"] / past["registered"]),
                (p26["t_fc"] * p26["registered_2026"]).sum() / p26["registered_2026"].sum()],
})
area = "South Africa" if province == "All provinces" else province

st.markdown(f"**Turnout in local government elections — {area}**")
k = st.columns(4)
for col, (_, h) in zip(k, history.iterrows()):
    label = "2026 (forecast)" if h["election"] == 2026 else str(int(h["election"]))
    note = scenario.split(" (")[0] if h["election"] == 2026 else f"{num(h['registered'])} registered"
    tile(col, label, pct(h["turnout"]), note)

tab_overview, tab_map, tab_profile, tab_gap, tab_about = st.tabs(
    ["Overview", "Funnel map", "Municipality profile", "Gap to target", "About"])

# ================================================================== 0. overview
with tab_overview:
    st.markdown(
        "**How to use this dashboard.** Start here for the big picture. **Funnel map** shows where people are "
        "lost, municipality by municipality. **Municipality profile** looks at one place in detail, including its "
        "2026 forecast. **Gap to target** shows how many registrations or voters each municipality is short. "
        "Use the sidebar to pick a province or a 2026 scenario — every page updates.")

    left, right = st.columns(2)
    with left:
        st.subheader("Turnout at every election")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=history["election"][:3], y=history["turnout"][:3], name="Actual",
                                 mode="lines+markers+text", text=[pct(v) for v in history["turnout"][:3]],
                                 textposition="top center", line=dict(color=BRAND, width=2),
                                 marker=dict(size=10, line=dict(width=2, color="white")),
                                 hovertemplate="%{x}: %{y:.1%}<extra></extra>"))
        scen = {name: (pd.Series(p26[col]) * p26["registered_2026"]).sum() / p26["registered_2026"].sum()
                for name, col in SCENARIOS.items()}
        fig.add_trace(go.Scatter(x=[2021, 2026], y=[history["turnout"][2], history["turnout"][3]],
                                 name=f"2026 forecast ({scenario.split(' (')[0].lower()})",
                                 mode="lines+markers+text", text=["", pct(history["turnout"][3])],
                                 textposition="top center", line=dict(color=BRAND, width=2, dash="dash"),
                                 marker=dict(size=[0, 11], symbol="diamond"),
                                 hovertemplate="%{x}: %{y:.1%}<extra></extra>"))
        lo, hi = min(scen.values()), max(scen.values())
        fig.add_trace(go.Scatter(x=[2026, 2026], y=[lo, hi], name="Range of scenarios", mode="lines",
                                 line=dict(color=MUTED, width=6), opacity=0.45,
                                 hovertemplate="Scenario range: %{y:.1%}<extra></extra>"))
        fig.update_yaxes(tickformat=".0%", title="Turnout (share of registered voters)",
                         range=[min(history["turnout"].min(), lo) - 0.06, max(history["turnout"].max(), hi) + 0.06])
        fig.update_xaxes(tickvals=[2011, 2016, 2021, 2026], title=None)
        st.plotly_chart(style(fig, 380), use_container_width=True)
        st.caption(f"Turnout was steady in 2011 and 2016, then fell sharply in 2021 (the COVID election). "
                   f"For 2026 the grey bar shows the scenarios: {pct(lo)} if turnout does not recover, "
                   f"{pct(hi)} if it fully returns to the 2016 level.")

    with right:
        st.subheader("Registered voters at every election")
        fig = go.Figure(go.Bar(x=history["election"].astype(str), y=history["registered"],
                               marker_color=[BRAND, BRAND, BRAND, "#f5a35a"],
                               text=[f"{v / 1e6:.1f} m" if area == "South Africa" else num(v)
                                     for v in history["registered"]],
                               textposition="outside", cliponaxis=False,
                               hovertemplate="%{x}: %{y:,.0f} registered<extra></extra>"))
        fig.update_yaxes(title="Registered voters", range=[0, history["registered"].max() * 1.18])
        fig.update_xaxes(title=None, type="category")
        st.plotly_chart(style(fig, 380), use_container_width=True)
        elig = p26["eligible_adults"].sum()
        st.caption(f"{num(p26['registered_2026'].sum())} people are registered for 2026, out of "
                   f"{num(elig)} eligible adults (Census 2022): {p26['registered_2026'].sum() / elig:.0%}. "
                   f"The other {num(elig - p26['registered_2026'].sum())} are the registration leak.")

    st.subheader("Turnout by province, every election")
    by_prov = master[master["election"] < 2026].groupby(["province", "election"])[["votes_cast", "registered"]].sum()
    by_prov = (by_prov["votes_cast"] / by_prov["registered"]).unstack("election")
    fc = pred.groupby("province").apply(lambda g: (g["t_fc"] * g["registered_2026"]).sum() / g["registered_2026"].sum())
    by_prov["2026 forecast"] = fc
    by_prov.columns = [str(c) for c in by_prov.columns]
    by_prov = by_prov * 100                                   # show as percentages with one decimal
    by_prov["Change 2016 → 2021"] = by_prov["2021"] - by_prov["2016"]
    by_prov = by_prov.sort_values("2021").reset_index()
    st.dataframe(by_prov, hide_index=True, use_container_width=True,
                 column_config={"province": "Province",
                                **{c: st.column_config.NumberColumn(c, format="%.1f%%")
                                   for c in ["2011", "2016", "2021", "2026 forecast"]},
                                "Change 2016 → 2021": st.column_config.NumberColumn(
                                    "Change 2016 → 2021", format="%+.1f points")})
    st.caption("Turnout = votes cast ÷ registered voters (ward ballot). 2011 figures are on today's municipal "
               "boundaries. The 2026 forecast follows the scenario chosen in the sidebar.")

# ================================================================== 1. funnel map
with tab_map:
    c1, c2 = st.columns([1, 1])
    year = c1.radio("Election", ["2011", "2016", "2021", "2026 forecast"], index=2, horizontal=True)
    measure = c2.radio("Colour by", ["Leak type", "Turnout", "Registration rate", "Real participation"],
                       horizontal=True)

    if year == "2026 forecast":
        d = pred[["muni_code", "muni_name", "province", "r_2026", "t_fc", "p_fc"]].rename(
            columns={"r_2026": "r", "t_fc": "t", "p_fc": "p"})
    else:
        d = master.loc[master["election"] == int(year), ["muni_code", "muni_name", "province", "r", "t", "p"]]
    d = d.copy()
    # Leaks compare each municipality with the median municipality in that election
    d["leak_reg"] = np.log(d["r"].clip(upper=1.0) / d["r"].median())   # capped: see Note below
    d["leak_turn"] = np.log(d["t"] / d["t"].median())
    d["Leak type"] = leak_type(d["leak_reg"], d["leak_turn"])
    d = in_province(d)
    # More registered than Census eligible adults = Census sample too small there: cap at 100% and say so
    d["Registration rate"] = d["r"].clip(upper=1.0)
    d["Turnout"] = d["t"]
    d["Real participation"] = d["p"].clip(upper=1.0)
    d["Note"] = np.where(d["r"] > 1.05, "Census too small here: rate capped at 100%", "")
    hover = {"muni_code": True, "province": True, "Registration rate": ":.1%", "Turnout": ":.1%",
             "Real participation": ":.1%", "Leak type": True, "Note": True}

    if geo is None:
        st.info("The map layer is not in app/artifacts yet (run prepare_artifacts.py with boundaries.gpkg). "
                "The leak chart below shows the same information.")
    else:
        common = dict(geojson=geo, locations="muni_code", featureidkey="properties.muni_code",
                      hover_name="muni_name", hover_data=hover)
        if measure == "Leak type":
            fig = px.choropleth(d, color="Leak type", color_discrete_map=LEAK_COLOURS,
                                category_orders={"Leak type": LEAK_ORDER}, **common)
        else:
            fig = px.choropleth(d, color=measure, color_continuous_scale=ORANGE_RAMP, **common)
            fig.update_coloraxes(colorbar=dict(tickformat=".0%", title=None, thickness=12))
        fig.update_traces(marker_line_color="white", marker_line_width=0.4)
        fig.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(style(fig, 560), use_container_width=True)

    st.subheader("Which leak does each municipality have?")
    st.caption("Right of the line: registration above the median municipality. Above the line: turnout above "
               "the median. A municipality can lose people at either stage, or both.")
    fig = px.scatter(d, x="leak_reg", y="leak_turn", color="Leak type", color_discrete_map=LEAK_COLOURS,
                     category_orders={"Leak type": LEAK_ORDER}, hover_name="muni_name", hover_data=hover)
    fig.add_hline(y=0, line_color=MUTED, line_width=1)
    fig.add_vline(x=0, line_color=MUTED, line_width=1)
    fig.update_traces(marker=dict(size=9, line=dict(width=1.5, color="white")))
    fig.update_xaxes(title="Registration leak (log ratio to median; below 0 = leaking)")
    fig.update_yaxes(title="Turnout leak (log ratio to median)")
    st.plotly_chart(style(fig, 460), use_container_width=True)

    counts = d["Leak type"].value_counts().reindex(LEAK_ORDER, fill_value=0)
    st.caption(" · ".join(f"**{k}:** {v}" for k, v in counts.items()) + f" municipalities ({year})")
    with st.expander("Show as a table"):
        st.dataframe(d[["muni_code", "muni_name", "province", "Registration rate", "Turnout",
                        "Real participation", "Leak type"]].sort_values("Real participation"),
                     hide_index=True, use_container_width=True,
                     column_config={"muni_code": "Code", "muni_name": "Municipality", "province": "Province",
                                    **{c: st.column_config.NumberColumn(format="percent")
                                       for c in ["Registration rate", "Turnout", "Real participation"]}})

# ================================================================== 2. municipality profile
with tab_profile:
    options = in_province(pred).sort_values("muni_name")
    labels = options["muni_name"] + " (" + options["muni_code"] + ")"
    pick = st.selectbox("Choose a municipality", labels.tolist())
    code = options.loc[labels == pick, "muni_code"].iloc[0]
    row = pred[pred["muni_code"] == code].iloc[0]
    hist = master[master["muni_code"] == code].sort_values("election")

    unreliable = row["r_above_1_05"] == 1
    k = st.columns(4)
    tile(k[0], "Registration rate 2026", "unreliable*" if unreliable else pct(row["r_2026"]),
                f"median {pct(pred['r_2026'].median())}")
    tile(k[1], "Turnout 2021", pct(row["t_2021"]))
    tile(k[2], "Forecast turnout 2026", pct(row["t_fc"]),
                f"range {pct(row['t_fc_low'], 0)} – {pct(row['t_fc_high'], 0)}")
    tile(k[3], "Real participation 2026", "unreliable*" if unreliable else pct(row["p_fc"]),
                "share of eligible adults expected to vote")

    left, right = st.columns(2)
    with left:
        st.subheader("The funnel in 2026")
        voters = row["registered_2026"] * row["t_fc"]
        stages = pd.DataFrame({
            "stage": ["Eligible adults", "Registered", "Expected to vote"],
            "people": [row["eligible_adults"], row["registered_2026"], voters],
        })
        stages["label"] = [num(v) for v in stages["people"]]
        fig = go.Figure(go.Bar(x=stages["people"], y=stages["stage"], orientation="h",
                               marker_color=FUNNEL_STEPS, text=stages["label"], textposition="outside",
                               cliponaxis=False,
                               hovertemplate="%{y}: %{x:,.0f}<extra></extra>"))
        fig.update_yaxes(autorange="reversed", title=None)
        fig.update_xaxes(title="People", range=[0, stages["people"].max() * 1.18])
        st.plotly_chart(style(fig, 280), use_container_width=True)
        lost_reg = max(row["eligible_adults"] - row["registered_2026"], 0)
        st.markdown(f"- **Registration leak:** about **{num(lost_reg)}** eligible adults are not registered.\n"
                    f"- **Turnout leak:** about **{num(row['registered_2026'] - voters)}** registered voters are "
                    f"expected not to vote ({scenario.lower()}).")
        if unreliable:
            st.warning("*More people are registered here than the Census counts as eligible adults. "
                       "The Census 2022 sample is small in this municipality, so treat its registration "
                       "rate with caution.", icon="⚠️")

    with right:
        st.subheader("Turnout history and 2026 forecast")
        nat = master[master["election"] < 2026].groupby("election")[["votes_cast", "registered"]].sum()
        nat = (nat["votes_cast"] / nat["registered"]).reset_index(name="t")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=nat["election"], y=nat["t"], name="National", mode="lines+markers",
                                 line=dict(color=MUTED, width=2, dash="dot"), marker=dict(size=8),
                                 hovertemplate="National %{x}: %{y:.1%}<extra></extra>"))
        past = hist[hist["election"] < 2026]
        fig.add_trace(go.Scatter(x=past["election"], y=past["t"], name=row["muni_name"], mode="lines+markers",
                                 line=dict(color=BRAND, width=2),
                                 marker=dict(size=9, line=dict(width=2, color="white")),
                                 hovertemplate="%{x}: %{y:.1%}<extra></extra>"))
        fig.add_trace(go.Scatter(
            x=[2021, 2026], y=[row["t_2021"], row["t_fc"]], name="2026 forecast", mode="lines+markers",
            line=dict(color=BRAND, width=2, dash="dash"),
            marker=dict(size=[0, 10], symbol="diamond"),
            error_y=dict(type="data", symmetric=False, array=[0, row["t_fc_high"] - row["t_fc"]],
                         arrayminus=[0, row["t_fc"] - row["t_fc_low"]], color=MUTED, thickness=2, width=6),
            hovertemplate="%{x}: %{y:.1%}<extra></extra>"))
        fig.update_yaxes(tickformat=".0%", title="Turnout")
        fig.update_xaxes(tickvals=[2011, 2016, 2021, 2026], title=None)
        st.plotly_chart(style(fig, 330), use_container_width=True)

        st.markdown("**What the model associates with this municipality's forecast**")
        bits = []
        if isinstance(row["main_factor_down"], str):
            bits.append(f"Pulling turnout down most: **{row['main_factor_down']}**")
        if isinstance(row["main_factor_up"], str):
            bits.append(f"Holding turnout up most: **{row['main_factor_up']}**")
        st.markdown("\n".join(f"- {b}" for b in bits) or "- No strong factor either way.")
        if row["worse_than_expected_2021"] == 1:
            st.info("**Worse than expected in 2021:** turnout here fell much more than the model predicted. "
                    "Something local happened that the data cannot see.", icon="🔎")
        st.caption(FACTOR_NOTE)

# ================================================================== 3. gap to target
with tab_gap:
    st.subheader("What would it take to reach the median municipality?")
    st.caption("Plain arithmetic, for campaign planning: how many more registrations would bring each "
               "municipality to the national median registration rate, and how many more voters would bring "
               "it to the median forecast turnout.")
    g = pred.merge(master.loc[master["election"] == 2026, ["muni_code", "eligible_youth", "registered_youth"]],
                   on="muni_code", how="left")
    r_med, t_med = pred["r_2026"].median(), pred["t_fc"].median()
    g["registrations_needed"] = np.ceil((r_med * g["eligible_adults"] - g["registered_2026"]).clip(lower=0))
    g["extra_voters_needed"] = np.ceil(((t_med - g["t_fc"]) * g["registered_2026"]).clip(lower=0))
    g["youth_not_registered"] = (g["eligible_youth"] - g["registered_youth"]).clip(lower=0)
    g = in_province(g)

    k = st.columns(3)
    tile(k[0], "Registrations needed (total)", num(g["registrations_needed"].sum()),
                f"to reach {pct(r_med)} registration")
    tile(k[1], "Extra voters needed (total)", num(g["extra_voters_needed"].sum()),
                f"to reach {pct(t_med)} turnout")
    tile(k[2], "Young citizens (18–29) not registered", num(g["youth_not_registered"].sum()))

    top = g.nlargest(15, "registrations_needed").sort_values("registrations_needed")
    fig = go.Figure(go.Bar(x=top["registrations_needed"], y=top["muni_name"], orientation="h",
                           marker_color=BRAND,
                           text=[num(v) for v in top["registrations_needed"]], textposition="outside",
                           cliponaxis=False, hovertemplate="%{y}: %{x:,.0f} registrations<extra></extra>"))
    fig.update_layout(title="Largest registration gaps")
    fig.update_xaxes(title="Registrations needed to reach the median rate",
                     range=[0, top["registrations_needed"].max() * 1.2])
    st.plotly_chart(style(fig, 460), use_container_width=True)

    table = g[["muni_code", "muni_name", "province", "r_2026", "t_fc", "registrations_needed",
               "extra_voters_needed", "youth_not_registered"]].sort_values("registrations_needed", ascending=False)
    st.dataframe(table, hide_index=True, use_container_width=True,
                 column_config={"muni_code": "Code", "muni_name": "Municipality", "province": "Province",
                                "r_2026": st.column_config.NumberColumn("Registration rate", format="percent"),
                                "t_fc": st.column_config.NumberColumn("Forecast turnout", format="percent"),
                                "registrations_needed": st.column_config.NumberColumn("Registrations needed",
                                                                                      format="%d"),
                                "extra_voters_needed": st.column_config.NumberColumn("Extra voters needed",
                                                                                     format="%d"),
                                "youth_not_registered": st.column_config.NumberColumn("Youth not registered",
                                                                                      format="%d")})
    st.download_button("Download this table (CSV)", table.to_csv(index=False).encode("utf-8"),
                       "democratic_funnel_gap_to_target.csv", "text/csv")

# ================================================================== 4. about
with tab_about:
    st.markdown("""
### The problem
People drop out of local democracy at **two points**: eligible adults who never **register**, and registered
voters who do not **vote**. The usual turnout figure only measures the second, because it is calculated among
registered voters. Everyone who never registered is invisible in it. The two leaks need different responses:
registration drives and ID support for the first, voter education and mobilisation for the second.

### The funnel
For each municipality: **r** = registered ÷ eligible adults, **t** = votes cast ÷ registered, and real
participation **p = r × t**. Comparing each municipality with the median municipality splits its shortfall
exactly into a *registration leak* and a *turnout leak*.

### The forecast
2026 turnout = 2021 turnout + a national swing + an adjustment for each municipality from a
**hierarchical (mixed-effects) regression** (municipalities grouped within provinces). The model was tested
by training on the 2011 → 2016 change and predicting the 2016 → 2021 change. Most of the change between
elections is national, so the national swing is shown as scenarios (no, half or full recovery from the COVID
drop in 2021), and each forecast comes with a range.

### Data sources
| Source | Used for |
|---|---|
| IEC municipal election results 2011, 2016, 2021 | registered voters, votes cast, turnout |
| IEC voter registration statistics (September 2026) | registered voters for 2026 |
| Stats SA Census 2022 | eligible adults (citizens 18+), services, education |
| Municipal Demarcation Board | boundaries, area, neighbours |
| IEC municipal atlas | registration activity, 2011 → current boundary crosswalk |

### Limitations
- **Census undercount and small samples:** in a few small municipalities more people are registered than the
  Census counts as eligible, so their registration rate is flagged and should be read with caution.
- **2021 was a COVID election:** its low turnout is partly a one-off, which is why 2026 is given as scenarios.
- **Boundaries changed in 2016:** 2011 results were moved onto today's boundaries using area shares.
- **Registration is a snapshot** taken in September 2026; it changes until the roll closes.
- **Municipality-level data only:** patterns across municipalities cannot show how individuals behave. The
  factors shown are associations, never proven causes.
- **Youth turnout is not published** by the IEC, so youth findings are about registration only.
- **Small sample:** 213 municipalities and two past changes in turnout; forecasts come with a range.

*Team UL, University of Limpopo · DIRISA Student Datathon Challenge 2026*
""")
