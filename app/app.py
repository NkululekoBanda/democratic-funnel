"""The Democratic Funnel - dashboard.

Reads only app/artifacts/dashboard.csv and app/artifacts/municipalities.geojson
(both written by notebooks/09_dashboard_prep.ipynb). No cleaning or modelling happens here.

Run locally:  streamlit run app/app.py
"""
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ART = Path(__file__).resolve().parent / "artifacts"
st.set_page_config(page_title="The Democratic Funnel", page_icon="🗳️", layout="wide",
                   initial_sidebar_state="collapsed")

# ------------------------------------------------------------------ house style (same as 07_eda)
BLUE, AMBER, CRIMSON, GREEN, NAVY = "#2a78d6", "#eda100", "#a3143a", "#7bc586", "#1b2f5b"
DIRISA_ORANGE = "#ee7900"
INK, INK2, GRID = "#0b0b0b", "#4a4a47", "#e4e3de"
GROUPS = ["Low registration", "Low turnout", "Both low", "Healthy"]
GROUP_COLOURS = {"Low registration": BLUE, "Low turnout": AMBER, "Both low": CRIMSON, "Healthy": GREEN}
GROUP_MEANING = {
    "Low registration": "below a typical municipality on registration — but those who are registered, vote",
    "Low turnout": "well registered — but fewer registered voters turn out than in a typical municipality",
    "Both low": "below a typical municipality at both stages: registering and voting",
    "Healthy": "at or above a typical municipality on both registration and turnout",
}
NOT_A_CAUSE = "A link is not proof of a cause: patterns across municipalities cannot show why individuals act."

st.markdown(f"""
<style>
  html, body, [class*="css"] {{ font-size: 17px; }}
  .block-container {{ padding-top: 3.2rem; max-width: 1200px; }}
  .card {{ border: 1px solid {GRID}; border-radius: 10px; padding: 16px 18px; height: 100%; background: #fff; }}
  .card .big {{ font-size: 2.3rem; font-weight: 700; line-height: 1.1; color: {INK}; }}
  .card .small {{ font-size: 0.98rem; color: {INK2}; margin-top: 6px; line-height: 1.35; }}
  .pill {{ display: inline-block; padding: 4px 12px; border-radius: 999px; font-weight: 700; font-size: 0.95rem; }}
  .box {{ border-left: 5px solid {NAVY}; background: #f3f5fa; padding: 12px 16px; border-radius: 6px;
          margin: 8px 0 14px; line-height: 1.5; }}
  [data-testid="stExpandSidebarButton"] svg, [data-testid="stExpandSidebarButton"] span,
  [data-testid="stSidebarCollapsedControl"] button svg,
  [data-testid="stSidebarCollapsedControl"] button span {{ display: none !important; }}
  [data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] button {{
    width: auto !important; min-width: 90px; padding: 4px 10px !important; border-radius: 8px;
    border: 1px solid {GRID} !important; background: #fff !important; }}
  [data-testid="stExpandSidebarButton"]::after, [data-testid="stSidebarCollapsedControl"] button::after {{
    content: "☰  Menu"; font-size: 1.05rem; font-weight: 700; color: {NAVY}; white-space: pre; }}
  @media (max-width: 640px) {{ .card .big {{ font-size: 1.8rem; }} }}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------ data
@st.cache_data
def load():
    d = pd.read_csv(ART / "dashboard.csv")
    geo_path = ART / "municipalities.geojson"
    geo = json.loads(geo_path.read_text(encoding="utf-8")) if geo_path.exists() else None
    return d, geo


if not (ART / "dashboard.csv").exists():
    st.error("app/artifacts/dashboard.csv is missing. Run notebooks/09_dashboard_prep.ipynb first.")
    st.stop()

d, geo = load()
HAS_PRED = d["Predicted turnout 2026"].notna().all()
TURNOUT_LABEL = "Predicted turnout 2026" if HAS_PRED else "Turnout 2021"


def pct(x, digits=0):
    return "–" if pd.isna(x) else f"{x * 100:.{digits}f}%"


def num(x):
    return "–" if pd.isna(x) else f"{x:,.0f}".replace(",", " ")


def millions(x):
    return f"{x / 1e6:.1f} m"


def wavg(df, col, weight="Registered 2026"):
    return (df[col] * df[weight]).sum() / df[weight].sum()


def card(col, big, small):
    col.markdown(f"<div class='card'><div class='big'>{big}</div><div class='small'>{small}</div></div>",
                 unsafe_allow_html=True)


def stat(col, label, value, note):
    col.metric(label, value)
    col.caption(note)


def pill(group):
    text = "#ffffff" if group in ("Low registration", "Both low") else INK
    return f"<span class='pill' style='background:{GROUP_COLOURS[group]};color:{text}'>{group}</span>"


def box(html):
    st.markdown(f"<div class='box'>{html}</div>", unsafe_allow_html=True)


def chart(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=8, r=8, t=36, b=8), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)", font=dict(size=15, color=INK),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
                      hoverlabel=dict(font_size=15))
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ------------------------------------------------------------------ header
st.markdown(f"""
<div style="background:{NAVY};border-bottom:5px solid {DIRISA_ORANGE};border-radius:10px;padding:18px 22px;margin-bottom:14px">
  <div style="color:{DIRISA_ORANGE};font-size:0.8rem;letter-spacing:0.12em;font-weight:700">
    DIRISA STUDENT DATATHON CHALLENGE 2026 · TEAM UL</div>
  <div style="color:#fff;font-size:2rem;font-weight:800;line-height:1.2;margin-top:4px">The Democratic Funnel</div>
  <div style="color:#dfe5f2;font-size:1.02rem;margin-top:4px">
    Where local democracy leaks before the local government elections on 4 November 2026</div>
</div>""", unsafe_allow_html=True)


# ================================================================== 1. overview
def overview():
    st.markdown(f"<div style='font-size:1.35rem;font-weight:600;margin:4px 0 14px'>People are lost at two points: "
                f"<span style='color:{BLUE}'>before registering</span>, and <span style='color:#b27800'>after</span>."
                "</div>", unsafe_allow_html=True)

    adults, reg26 = d["Adults who may vote"].sum(), d["Registered 2026"].sum()
    reg21, votes21 = d["Registered 2021"].sum(), d["Votes cast 2021"].sum()
    k = st.columns(4)
    card(k[0], f"{100 * reg26 / adults:.0f} of 100", "adults are registered to vote in 2026")
    card(k[1], f"{100 * votes21 / adults:.0f} of 100", "adults actually voted in 2021")
    card(k[2], millions(d["Young adults not registered"].sum()), "young adults (18–29) are not registered")
    if HAS_PRED:
        card(k[3], pct(wavg(d, "Predicted turnout 2026"), 1),
             f"predicted turnout in 2026 (range {pct(wavg(d, 'Predicted turnout 2026 (low)'))}–"
             f"{pct(wavg(d, 'Predicted turnout 2026 (high)'))})")
    else:
        card(k[3], pct(votes21 / reg21, 1), "turnout in 2021 (prediction not available yet)")

    st.write("")
    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("#### The funnel, 2021: out of every 100 adults")
        stages = ["May vote", "Registered", "Voted"]
        vals = [100, 100 * reg21 / adults, 100 * votes21 / adults]
        fig = go.Figure(go.Bar(x=vals, y=stages, orientation="h", marker_color=[NAVY, BLUE, AMBER],
                               text=[f"{v:.0f}" for v in vals], textposition="outside", cliponaxis=False,
                               textfont=dict(size=18), hovertemplate="%{y}: %{x:.0f} of 100<extra></extra>"))
        fig.update_yaxes(autorange="reversed", title=None)
        fig.update_xaxes(range=[0, 115], showticklabels=False, showgrid=False)
        chart(fig, 250)
        st.caption(f"About {vals[0] - vals[1]:.0f} of every 100 adults were lost before registering, and another "
                   f"{vals[1] - vals[2]:.0f} after registering. The official turnout figure only shows the second loss.")
    with right:
        st.markdown("#### Turnout at every election")
        yrs = [2011, 2016, 2021]
        ts = [d[f"Votes cast {y}"].sum() / d[f"Registered {y}"].sum() for y in yrs]
        fig = go.Figure(go.Scatter(x=yrs, y=ts, mode="lines+markers+text", name="Actual",
                                   text=[pct(v, 1) for v in ts], textposition="top center",
                                   line=dict(color=NAVY, width=3), marker=dict(size=11),
                                   hovertemplate="%{x}: %{y:.1%}<extra></extra>"))
        if HAS_PRED:
            p26 = wavg(d, "Predicted turnout 2026")
            fig.add_trace(go.Scatter(x=[2021, 2026], y=[ts[-1], p26], mode="lines+markers+text", name="Predicted",
                                     text=["", pct(p26, 1)], textposition="top center",
                                     line=dict(color=NAVY, width=3, dash="dash"),
                                     marker=dict(size=[0, 12], symbol="diamond"),
                                     hovertemplate="%{x} (predicted): %{y:.1%}<extra></extra>"))
        fig.add_annotation(x=2021, y=ts[-1], text="COVID election", showarrow=False, yshift=-26,
                           font=dict(color=INK2, size=13))
        fig.update_yaxes(tickformat=".0%", range=[0.35, 0.7], title=None)
        fig.update_xaxes(tickvals=[2011, 2016, 2021, 2026], title=None)
        chart(fig, 250)
        st.caption("Turnout = votes cast ÷ registered voters. It fell about 12 points in the 2021 COVID election.")

    counts = d["Problem group"].value_counts().reindex(GROUPS, fill_value=0)
    st.markdown("#### Every municipality has one of four problems")
    st.markdown(" &nbsp; ".join(f"{pill(g)} <b>{counts[g]}</b>" for g in GROUPS), unsafe_allow_html=True)
    st.caption(f"Compared with a typical municipality, using the 2026 roll and {TURNOUT_LABEL.lower()}. "
               "Open the Map to see where they are, or the Municipality profile to look up your own.")

# ================================================================== 2. map
def map_page():
    c1, c2 = st.columns([1, 2])
    prov = c1.selectbox("Province", ["All provinces"] + sorted(d["Province"].unique()), key="map_prov")
    groups = c2.multiselect("Problem group", GROUPS, default=GROUPS, key="map_groups")
    m = d if prov == "All provinces" else d[d["Province"] == prov]
    m = m[m["Problem group"].isin(groups)].copy()

    if geo is None:
        st.info("The map layer is missing (app/artifacts/municipalities.geojson). Run 09_dashboard_prep.")
    elif m.empty:
        st.info("No municipalities match these filters.")
    else:
        m["reg_txt"] = [("over 100% (Census caution)" if c else pct(v, 1))
                        for v, c in zip(m["Registration rate 2026"], m["Census caution"])]
        m["pred_txt"] = [pct(v, 1) for v in m["Predicted turnout 2026"]] if HAS_PRED else "not available yet"
        fig = go.Figure()
        for g in GROUPS:
            s = m[m["Problem group"] == g]
            if s.empty:
                continue
            fig.add_trace(go.Choropleth(
                geojson=geo, featureidkey="properties.muni_code", locations=s["Code"], z=[1] * len(s),
                colorscale=[[0, GROUP_COLOURS[g]], [1, GROUP_COLOURS[g]]], showscale=False, name=g,
                showlegend=False, marker_line_color="white", marker_line_width=0.5,
                customdata=s[["Municipality", "Province", "reg_txt", "Turnout 2021", "Problem group", "pred_txt"]],
                hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                              "Registration rate 2026: %{customdata[2]}<br>"
                              "Turnout 2021: %{customdata[3]:.1%}<br>"
                              "Problem group: %{customdata[4]}<br>"
                              "Predicted turnout 2026: %{customdata[5]}<extra></extra>"))
            fig.add_trace(go.Scattergeo(lon=[None], lat=[None], mode="markers", name=f"{g} ({len(s)})",
                                        marker=dict(size=14, color=GROUP_COLOURS[g], symbol="square")))
        fig.update_geos(fitbounds="locations", visible=False)
        chart(fig, 600)
        st.caption("Each municipality coloured by its problem group. Hover (or tap) for its numbers. "
                   "The groups cluster by region, which points to regional causes.")

    with st.expander("Show as a table"):
        st.dataframe(m[["Municipality", "Province", "Problem group", "Registration rate 2026", "Turnout 2021",
                        "Predicted turnout 2026"]].sort_values("Municipality"), hide_index=True,
                     use_container_width=True,
                     column_config={c: st.column_config.NumberColumn(format="percent")
                                    for c in ["Registration rate 2026", "Turnout 2021", "Predicted turnout 2026"]})

# ================================================================== 3. municipality profile
def profile():
    labels = (d["Municipality"] + " (" + d["Province"] + ")").tolist()
    choice = st.selectbox("Type a municipality's name", sorted(labels), index=None,
                          placeholder="e.g. Polokwane, eThekwini, Mbombela ...")
    if choice is None:
        st.info("Start typing a name above to see that municipality's funnel, problem and 2026 forecast.")
    else:
        row = d.iloc[labels.index(choice)]
        g, caution = row["Problem group"], bool(row["Census caution"])
        st.markdown(f"### {row['Municipality']}")
        st.caption(f"{row['Type']} municipality, {row['Province']}")
        st.markdown(f"{pill(g)} &nbsp; This municipality is <b>{GROUP_MEANING[g]}</b>.", unsafe_allow_html=True)

        gap_reg, gap_vote = row["Registrations needed to reach typical"], row["Extra voters needed to reach typical"]
        send = {"Low registration": f"<b>Send: a registration drive.</b> About <b>{num(gap_reg)}</b> more "
                                    f"registrations would bring {row['Municipality']} to the typical level "
                                    f"({pct(row['Typical registration rate'])} of adults).",
                "Low turnout": f"<b>Send: voter mobilisation.</b> About <b>{num(gap_vote)}</b> more voters would "
                               f"bring turnout to the typical level ({pct(row['Typical turnout'])}).",
                "Both low": f"<b>Send: a registration drive and voter mobilisation.</b> About "
                            f"<b>{num(gap_reg)}</b> more registrations and <b>{num(gap_vote)}</b> more voters would "
                            "bring it to the typical level.",
                "Healthy": "<b>Nothing urgent.</b> Registration and turnout are at or above a typical "
                           "municipality."}[g]
        if row["Young adults not registered"] > 0:
            send += (f" Young adults are the biggest group missing: <b>{num(row['Young adults not registered'])}"
                     "</b> people aged 18–29 are not registered.")
        box(send)

        left, right = st.columns(2)
        with left:
            st.markdown("#### Out of every 100 adults")
            reg100, vote100 = min(row["Registered per 100 adults"], 100), row["Voters per 100 adults"]
            typ_reg100 = 100 * row["Typical registration rate"]
            typ_vote100 = typ_reg100 * row["Typical turnout"]
            vote_label = "Expected to vote (2026)" if HAS_PRED else "Voted (at 2021 turnout)"
            fig = go.Figure()
            fig.add_trace(go.Bar(x=[100, reg100, vote100], y=["May vote", "Registered (2026)", vote_label],
                                 orientation="h", marker_color=[NAVY, BLUE, AMBER], name=row["Municipality"],
                                 text=[f"{v:.0f}" for v in (100, reg100, vote100)], textposition="inside",
                                 insidetextanchor="start", textfont=dict(size=18, color=["#fff", "#fff", INK]),
                                 hovertemplate="%{y}: %{x:.0f} of 100<extra></extra>"))
            fig.add_trace(go.Scatter(x=[typ_reg100, typ_vote100], y=["Registered (2026)", vote_label],
                                     mode="markers", name="Typical municipality",
                                     marker=dict(symbol="line-ns", size=34, line=dict(width=4, color=NAVY)),
                                     hovertemplate="Typical municipality: %{x:.0f} of 100<extra></extra>"))
            fig.update_yaxes(autorange="reversed", title=None)
            fig.update_xaxes(range=[0, 118], showticklabels=False, showgrid=False)
            chart(fig, 270)
            st.caption("Bars: this municipality. Navy lines: a typical municipality."
                       + (" Registration is capped at 100 here — see the Census note below." if caution else ""))

            st.markdown("#### Compared with a typical municipality")
            cc = st.columns(3)
            reg_txt = "over 100%*" if caution else pct(row["Registration rate 2026"])
            stat(cc[0], "Registration rate", reg_txt, f"typical: {pct(row['Typical registration rate'])}")
            stat(cc[1], "Predicted turnout" if HAS_PRED else "Turnout 2021", pct(row["Turnout used"]),
                 f"typical: {pct(row['Typical turnout'])}")
            stat(cc[2], "Youth (18–29)", pct(row["Youth registration rate"]),
                 f"all adults here: {reg_txt}")

        with right:
            st.markdown("#### Turnout, and the 2026 prediction")
            yrs = [2011, 2016, 2021]
            ts = [row[f"Turnout {y}"] for y in yrs]
            nat = [d[f"Votes cast {y}"].sum() / d[f"Registered {y}"].sum() for y in yrs]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=yrs, y=nat, name="National", mode="lines+markers",
                                     line=dict(color=NAVY, width=2, dash="dot"), marker=dict(size=8),
                                     hovertemplate="National %{x}: %{y:.1%}<extra></extra>"))
            fig.add_trace(go.Scatter(x=yrs, y=ts, name=row["Municipality"], mode="lines+markers",
                                     line=dict(color=AMBER, width=3),
                                     marker=dict(size=11, line=dict(width=2, color="white")),
                                     hovertemplate="%{x}: %{y:.1%}<extra></extra>"))
            if HAS_PRED:
                p, lo, hi = (row["Predicted turnout 2026"], row["Predicted turnout 2026 (low)"],
                             row["Predicted turnout 2026 (high)"])
                fig.add_trace(go.Scatter(
                    x=[2021, 2026], y=[ts[-1], p], name="Predicted 2026", mode="lines+markers",
                    line=dict(color=AMBER, width=3, dash="dash"), marker=dict(size=[0, 13], symbol="diamond"),
                    error_y=dict(type="data", symmetric=False, array=[0, hi - p], arrayminus=[0, p - lo],
                                 color=NAVY, thickness=2, width=8),
                    hovertemplate="%{x} predicted: %{y:.1%}<extra></extra>"))
            fig.update_yaxes(tickformat=".0%", title=None)
            fig.update_xaxes(tickvals=[2011, 2016, 2021, 2026], title=None)
            chart(fig, 300)
            if HAS_PRED:
                st.markdown(f"**Predicted turnout 2026: {pct(p, 1)}** (likely range {pct(lo)} – {pct(hi)}).")
            else:
                st.markdown("The 2026 prediction will appear here once the model has run.")

            factors = []
            if isinstance(row["Main factor pulling turnout down"], str):
                factors.append(f"pulling turnout down: **{row['Main factor pulling turnout down']}**")
            if isinstance(row["Main factor holding turnout up"], str):
                factors.append(f"holding turnout up: **{row['Main factor holding turnout up']}**")
            if factors:
                st.markdown("What the model links with this forecast — " + "; ".join(factors) + ".")
            if str(row["Worse than expected in 2021"]) == "True":
                st.info("**Worse than expected in 2021:** turnout here fell much more than the model predicted. "
                        "Something local happened that our data cannot see.", icon="🔎")
            st.caption(NOT_A_CAUSE + " Youth figures are about registration only: the IEC does not publish "
                       "turnout by age.")

        if caution:
            st.warning("*More people are registered here than the Census 2022 counted adults. The Census sample is "
                       "small in this municipality, so its registration rate is not reliable.", icon="⚠️")

# ================================================================== 4. priority list
def priority_list():
    st.markdown("#### Where to act before 4 November 2026")
    st.caption(f"Ranked by how far each municipality is below a typical one, using the 2026 roll and "
               f"{TURNOUT_LABEL.lower()}. The shortfall is split into its registration part and its turnout part.")
    c1, c2 = st.columns([1, 2])
    prov = c1.selectbox("Province", ["All provinces"] + sorted(d["Province"].unique()), key="prio_prov")
    groups = c2.multiselect("Problem group", GROUPS, default=["Both low", "Low registration", "Low turnout"],
                            key="prio_groups")
    p = d if prov == "All provinces" else d[d["Province"] == prov]
    p = p[p["Problem group"].isin(groups)].sort_values("Priority rank")

    top = p.head(15).iloc[::-1]
    if not top.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(y=top["Municipality"], x=top["Shortfall: registration part"], orientation="h",
                             name="Registration part", marker_color=BLUE,
                             hovertemplate="%{y}: registration part %{x:.2f}<extra></extra>"))
        fig.add_trace(go.Bar(y=top["Municipality"], x=top["Shortfall: turnout part"], orientation="h",
                             name="Turnout part", marker_color=AMBER,
                             hovertemplate="%{y}: turnout part %{x:.2f}<extra></extra>"))
        fig.update_layout(barmode="stack", bargap=0.25, legend_traceorder="normal")
        fig.update_xaxes(title="How far below a typical municipality")
        chart(fig, 520)
        st.caption("The top 15 on this list. Blue: the part of the shortfall from people not registering. "
                   "Amber: the part from registered voters not voting.")

    table = p[["Priority rank", "Municipality", "Province", "Problem group", "What to send",
               "Registration rate 2026", "Turnout used", "Registrations needed to reach typical",
               "Extra voters needed to reach typical", "Young adults not registered",
               "Shortfall: registration part", "Shortfall: turnout part"]].rename(
        columns={"Turnout used": TURNOUT_LABEL, "Priority rank": "Rank"})
    table[["Registration rate 2026", TURNOUT_LABEL]] = (table[["Registration rate 2026", TURNOUT_LABEL]] * 100).round(1)
    st.dataframe(table, hide_index=True, use_container_width=True, height=460, column_config={
        "Registration rate 2026": st.column_config.NumberColumn(format="%.0f%%"),
        TURNOUT_LABEL: st.column_config.NumberColumn(format="%.0f%%"),
        "Registrations needed to reach typical": st.column_config.NumberColumn(format="%d"),
        "Extra voters needed to reach typical": st.column_config.NumberColumn(format="%d"),
        "Young adults not registered": st.column_config.NumberColumn(format="%d"),
        "Shortfall: registration part": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1),
        "Shortfall: turnout part": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=1)})
    st.download_button("Download this list (CSV)", table.to_csv(index=False).encode("utf-8"),
                       "democratic_funnel_priority_list.csv", "text/csv", type="primary")
    st.caption(f"{len(p)} municipalities shown. Registration rates above 100% (Census caution) are counted as 100%.")

# ================================================================== 5. about
def about():
    st.markdown(f"""
### The problem
South Africa votes for its local councils on **4 November 2026**. People drop out of local democracy at two
points: adults who never **register**, and registered voters who do not **vote**. The turnout figure in the news
only measures the second, because it is calculated among registered voters. The two leaks need different
responses: registration drives for the first, voter education and mobilisation for the second.

### How we measure it
For each municipality: **registration rate** = registered ÷ adults who may vote; **turnout** = votes cast ÷
registered; **real participation** = registration rate × turnout. Each municipality is compared with the
**typical (median) municipality**, which places it in one of four problem groups.

### How the prediction works, in plain words
2026 turnout = 2021 turnout + a **national recovery** from the COVID drop + an **adjustment** for each municipality.
The adjustment comes from a statistical model (a hierarchical regression, with municipalities grouped inside
provinces) that learned how turnout changed between 2011, 2016 and 2021. We tested it by training on
2011 → 2016 and predicting 2016 → 2021. Most of the change between elections is national, so every prediction
comes with a **range**, not a single number.

### Data sources
| Source | Used for |
|---|---|
| IEC municipal election results 2011, 2016, 2021 | registered voters, votes cast, turnout |
| IEC voter registration statistics, September 2026 | the 2026 roll, including ages 18–29 |
| Stats SA Census 2022 | adults who may vote (citizens 18+), services, education |
| Municipal Demarcation Board | boundaries, area, neighbours |
| IEC municipal atlas | 2011 results moved onto today's boundaries |

### Limitations, stated honestly
- **{NOT_A_CAUSE}**
- **Youth figures are about registration only.** The IEC does not publish turnout by age at municipal level.
- **Census undercount and small samples.** In {int(d['Census caution'].sum())} small municipalities more people
  are registered than the Census counted adults; their registration rate is flagged and counted as 100%.
- **2021 was a COVID election.** Its low turnout is partly a one-off, which is why 2026 is given as a range.
- **Boundaries changed in 2016.** 2011 results were moved onto today's boundaries using area shares.
- **Registration is a snapshot** from September 2026; it changes until the roll closes.
- **Small sample.** 213 municipalities and two past changes in turnout.

*Team UL, University of Limpopo · DIRISA Student Datathon Challenge 2026*
""")


# ================================================================== navigation: ☰ Menu (top left)
nav = st.navigation([
    st.Page(overview, title="Overview", icon="🏠", url_path="overview", default=True),
    st.Page(map_page, title="Map", icon="🗺️", url_path="map"),
    st.Page(profile, title="Municipality profile", icon="🏛️", url_path="profile"),
    st.Page(priority_list, title="Priority list", icon="📋", url_path="priority"),
    st.Page(about, title="About", icon="ℹ️", url_path="about"),
], position="sidebar")
st.sidebar.caption("The Democratic Funnel · Team UL · DIRISA Student Datathon Challenge 2026")
nav.run()
