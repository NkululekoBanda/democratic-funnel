"""The Democratic Funnel - dashboard.

Reads only app/artifacts/dashboard.csv and app/artifacts/municipalities.geojson
(both written by notebooks/09_dashboard_prep.ipynb). No cleaning or modelling happens here.

Run locally:  streamlit run app/app.py
"""
import base64
import json
from textwrap import dedent
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ART = Path(__file__).resolve().parent / "artifacts"
st.set_page_config(page_title="The Democratic Funnel", page_icon=":material/how_to_vote:", layout="wide",
                   initial_sidebar_state="collapsed")

# ------------------------------------------------------------------ house style (same as 07_eda)
BLUE, AMBER, CRIMSON, GREEN, NAVY = "#2a78d6", "#eda100", "#a3143a", "#7bc586", "#1b2f5b"
LIGHT_BLUE, LIGHT_AMBER = "#9ec5f0", "#f6d58a"          # tints for older elections (no grey: team rule)
YEAR_COLOURS = {2011: LIGHT_BLUE, 2016: LIGHT_AMBER, 2021: AMBER}
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
  /* Colours come from variables: light by default, dark when the page is in dark mode (html[data-theme=dark],
     set by the script in the header). */
  :root {{ --ink: {INK}; --ink2: {INK2}; --grid: {GRID}; --surface: #ffffff; --panel: #f3f5fa; --warn: #fbf1f3;
           --accent: {NAVY}; --blue-text: {BLUE}; --amber-text: #b27800; --shadow: 0 1px 3px rgba(16, 24, 40, .06); }}
  html[data-theme="dark"] {{ --ink: #e9ecf2; --ink2: #aab2c0; --grid: #2b3446; --surface: #161c28; --panel: #1b2435;
           --warn: #2b1a21; --accent: #a9bdf0; --blue-text: #6ea8ff; --amber-text: #f2b53a;
           --shadow: 0 1px 3px rgba(0, 0, 0, .35); }}
  html, body, [class*="css"] {{ font-size: 17px; }}
  .block-container {{ padding-top: 3.2rem; max-width: 1200px; }}
  .msr {{ font-family: "Material Symbols Rounded"; font-weight: normal; font-style: normal; line-height: 1;
          letter-spacing: normal; text-transform: none; white-space: nowrap; direction: ltr;
          font-feature-settings: "liga"; -webkit-font-smoothing: antialiased; }}
  .card {{ border: 1px solid var(--grid); border-radius: 10px; padding: 16px 18px; height: 100%; background: var(--surface);
           box-shadow: var(--shadow); }}
  .card .big {{ font-size: 2.3rem; font-weight: 700; line-height: 1.1; color: var(--ink); }}
  .card .small {{ font-size: 0.98rem; color: var(--ink2); margin-top: 6px; line-height: 1.35; }}
  .pill {{ display: inline-block; padding: 4px 12px; border-radius: 999px; font-weight: 700; font-size: 0.95rem; }}
  .box {{ border-left: 5px solid var(--accent); background: var(--panel); padding: 12px 16px; border-radius: 6px;
          margin: 8px 0 14px; line-height: 1.5; }}
  [data-testid="stExpandSidebarButton"] svg, [data-testid="stExpandSidebarButton"] span,
  [data-testid="stSidebarCollapsedControl"] button svg,
  [data-testid="stSidebarCollapsedControl"] button span {{ display: none !important; }}
  [data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] button {{
    width: auto !important; min-width: 90px; padding: 4px 10px !important; border-radius: 8px; gap: 6px;
    border: 1px solid var(--grid) !important; background: var(--surface) !important; }}
  [data-testid="stExpandSidebarButton"]::before, [data-testid="stSidebarCollapsedControl"] button::before {{
    content: "menu"; font-family: "Material Symbols Rounded"; font-feature-settings: "liga"; font-size: 1.35rem;
    color: var(--accent); }}
  [data-testid="stExpandSidebarButton"]::after, [data-testid="stSidebarCollapsedControl"] button::after {{
    content: "Menu"; font-size: 1.05rem; font-weight: 700; color: var(--accent); }}
  .topbar {{ display: flex; align-items: center; gap: 18px; background: #fff; border: 1px solid var(--grid);
             border-bottom: 4px solid {DIRISA_ORANGE}; border-radius: 12px; padding: 12px 20px; margin-bottom: 18px;
             box-shadow: var(--shadow); }}
  .topbar img.dirisa {{ height: 54px; }}
  .topbar img.ul {{ height: 62px; margin-left: auto; }}
  .topbar .name {{ border-left: 1px solid {GRID}; padding-left: 18px; }}
  .topbar .name .t {{ font-size: 1.55rem; font-weight: 800; color: {NAVY}; line-height: 1.15; }}
  .topbar .name .s {{ font-size: .95rem; color: {INK2}; }}
  .modebar {{ display: flex; justify-content: flex-end; margin: -8px 0 10px; }}
  .modebtn {{ display: inline-flex; align-items: center; gap: 6px; cursor: pointer; font: inherit; font-size: .92rem;
              font-weight: 600; color: var(--accent); background: var(--surface); border: 1px solid var(--grid);
              border-radius: 999px; padding: 5px 14px 5px 10px; }}
  .modebtn:hover {{ border-color: var(--accent); }}
  .modebtn .msr {{ font-size: 1.2rem; }}
  .modebtn .to-light {{ display: none; }}
  html[data-theme="dark"] .modebtn .to-dark {{ display: none; }}
  html[data-theme="dark"] .modebtn .to-light {{ display: inline-flex; align-items: center; gap: 6px; }}
  .modebtn .to-dark {{ display: inline-flex; align-items: center; gap: 6px; }}
  .pagehead {{ margin: 2px 0 14px; }}
  .pagehead h2 {{ color: var(--accent); font-size: 1.7rem; font-weight: 800; margin: 0; padding: 0; }}
  .pagehead p {{ color: var(--ink2); margin: 4px 0 0; font-size: 1.02rem; }}
  .kpi {{ border: 1px solid var(--grid); border-radius: 12px; padding: 14px 16px; height: 100%; background: var(--surface);
          box-shadow: var(--shadow); }}
  .kpi .label {{ font-size: .92rem; font-weight: 700; color: var(--ink); }}
  .kpi .value {{ font-size: 2rem; font-weight: 800; line-height: 1.15; margin: 4px 0; }}
  .kpi .note {{ font-size: .88rem; color: var(--ink2); line-height: 1.35; }}
  .panel {{ border-left: 5px solid var(--accent); background: var(--panel); padding: 12px 16px;
            margin: 6px 0 14px; line-height: 1.5; }}
  .panel.warn {{ border-left-color: {CRIMSON}; background: var(--warn); }}
  .rec {{ border: 1px solid var(--grid); border-radius: 12px; padding: 4px 18px 10px; margin-bottom: 16px;
          background: var(--surface); box-shadow: var(--shadow); }}
  .rec h3 {{ margin-bottom: 4px; color: var(--accent); }}
  .rec .row {{ display: flex; gap: 12px; padding: 8px 0; border-top: 1px solid var(--grid); }}
  .rec .k {{ min-width: 190px; font-weight: 700; color: var(--accent); }}
  .info {{ border: 1px solid var(--grid); border-radius: 12px; padding: 16px 18px; height: 100%; background: var(--surface);
           box-shadow: var(--shadow); }}
  .info .icon {{ font-size: 1.9rem; color: var(--accent); }}
  .info h4 {{ margin: 6px 0; color: var(--accent); }}
  .hl-blue {{ color: var(--blue-text); }} .hl-amber {{ color: var(--amber-text); }}
  .footer {{ margin-top: 42px; border-top: 4px solid {DIRISA_ORANGE}; background: #fff; padding: 18px 8px 8px;
             border-radius: 0 0 12px 12px; }}
  .footer img {{ width: 100%; max-width: 900px; display: block; margin: 0 auto 12px; }}
  .footer .txt {{ text-align: center; color: {INK2}; font-size: .86rem; line-height: 1.55; }}
  /* Charts in dark mode: navy and dark grey marks are lifted so they stay visible on the dark background.
     (Plotly writes colours inline, so they are matched by their rgb() value.) */
  html[data-theme="dark"] .js-plotly-plot [style*="stroke: rgb(27, 47, 91)"] {{ stroke: #7f9ad6 !important; }}
  html[data-theme="dark"] .js-plotly-plot [style*="fill: rgb(27, 47, 91)"] {{ fill: #5d78b8 !important; }}
  html[data-theme="dark"] .js-plotly-plot [style*="stroke: rgb(74, 74, 71)"] {{ stroke: #aab2c0 !important; }}
  html[data-theme="dark"] .js-plotly-plot [style*="fill: rgb(74, 74, 71)"] {{ fill: #aab2c0 !important; }}
  html[data-theme="dark"] .js-plotly-plot [style*="stroke: rgb(183, 195, 220)"] {{ stroke: #4c5874 !important; }}
  html[data-theme="dark"] .js-plotly-plot [style*="fill: rgb(183, 195, 220)"] {{ fill: #4c5874 !important; }}
  @media (max-width: 640px) {{
    .card .big {{ font-size: 1.8rem; }}
    .topbar {{ flex-wrap: wrap; gap: 10px; }} .topbar img.dirisa {{ height: 40px; }} .topbar img.ul {{ height: 46px; }}
    .topbar .name {{ border-left: none; padding-left: 0; order: 3; width: 100%; }}
    .rec .row {{ flex-direction: column; gap: 2px; }} .rec .k {{ min-width: 0; }}
  }}
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


def img64(name):
    path = Path(__file__).resolve().parent / "static" / name
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode() if path.exists() else ""


def page_header(title, subtitle):
    st.markdown(f"<div class='pagehead'><h2>{title}</h2><p>{subtitle}</p></div>", unsafe_allow_html=True)


def kpi(col, label, value, note, colour="var(--ink)"):
    col.markdown(f"<div class='kpi'><div class='label'>{label}</div><div class='value' style='color:{colour}'>"
                 f"{value}</div><div class='note'>{note}</div></div>", unsafe_allow_html=True)


def panel(html, warn=False):
    st.markdown(f"<div class='panel{' warn' if warn else ''}'>{html}</div>", unsafe_allow_html=True)


def info_card(col, icon, title, body):
    col.markdown(f"<div class='info'><div class='icon msr'>{icon}</div><h4>{title}</h4>{body}</div>",
                 unsafe_allow_html=True)


def recommendation(title, finding, evidence, response, further):
    rows = [("What the data shows", finding), ("Evidence", evidence), ("Possible response", response),
            ("Further evidence needed", further)]
    body = "".join(f"<div class='row'><div class='k'>{k}</div><div>{v}</div></div>" for k, v in rows)
    st.markdown(f"<div class='rec'><h3>{title}</h3>{body}</div>", unsafe_allow_html=True)


def national(df):
    """National totals and rates, each tied to its year."""
    adults = df["Adults who may vote"].sum()
    n = {"adults": adults}
    for y in (2011, 2016, 2021):
        n[f"registered_{y}"], n[f"votes_{y}"] = df[f"Registered {y}"].sum(), df[f"Votes cast {y}"].sum()
        n[f"turnout_{y}"] = n[f"votes_{y}"] / n[f"registered_{y}"]
    n["registered_2026"] = df["Registered 2026"].sum()
    n["reg_rate_2026"] = n["registered_2026"] / adults
    n["youth_adults"], n["youth_registered"] = df["Young adults who may vote"].sum(), df["Young adults registered"].sum()
    n["youth_not_registered"] = df["Young adults not registered"].sum()
    n["youth_reg_rate"] = n["youth_registered"] / n["youth_adults"]
    n["older_reg_rate"] = (n["registered_2026"] - n["youth_registered"]) / (adults - n["youth_adults"])
    n["youth_share_of_missing"] = n["youth_not_registered"] / (adults - n["registered_2026"])
    return n


def by_province(df):
    rows = []
    for p, g in df.groupby("Province"):
        r = {"Province": p}
        for y in (2011, 2016, 2021):
            r[f"Turnout {y}"] = g[f"Votes cast {y}"].sum() / g[f"Registered {y}"].sum()
        r["Participation 2021"] = g["Votes cast 2021"].sum() / g["Adults who may vote"].sum()
        rows.append(r)
    return pd.DataFrame(rows)


def chart(fig, height=360):
    # Text and grid colours come from Streamlit's chart theme, so they follow light / dark mode.
    fig.update_layout(height=height, margin=dict(l=8, r=8, t=36, b=8), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)", font=dict(size=15),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
                      hoverlabel=dict(font_size=15))
    fig.update_xaxes(zeroline=False)
    fig.update_yaxes(zeroline=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ------------------------------------------------------------------ header: logos and name
st.markdown(f"""
<div class="topbar">
  <img class="dirisa" src="{img64('dirisa_logo.png')}" alt="NICIS DIRISA">
  <div class="name"><div class="t">The Democratic Funnel</div>
    <div class="s">Where local democracy leaks before the local government elections on 4 November 2026</div></div>
  <img class="ul" src="{img64('ul_logo.png')}" alt="University of Limpopo">
</div>""", unsafe_allow_html=True)

# ------------------------------------------------------------------ light / dark mode
# Streamlit follows the viewer's system setting (both themes are in .streamlit/config.toml). The button saves the
# other theme in the browser the same way Streamlit's own Settings menu does, and reloads. The script also marks the
# page html[data-theme] so the custom cards and charts above follow Streamlit's theme.
PAGE_SLUGS = ["overview", "map", "profile", "priority", "recommendations", "participation", "voter-education", "about"]
st.html(r"""
<div class="modebar"><button class="modebtn" id="df-mode" type="button" title="Switch between light and dark mode">
  <span class="to-dark"><span class="msr">dark_mode</span>Dark mode</span>
  <span class="to-light"><span class="msr">light_mode</span>Light mode</span>
</button></div>
<script>
(() => {
  const slugs = %s;
  const isDark = () => {
    const app = document.querySelector(".stApp");
    const rgb = app ? getComputedStyle(app).backgroundColor.match(/\d+/g) : null;
    return !!rgb && (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) < 128;
  };
  const sync = () => { document.documentElement.dataset.theme = isDark() ? "dark" : "light"; };
  sync();
  if (window.__dfMode) return;
  window.__dfMode = true;
  setInterval(sync, 400);
  document.addEventListener("click", (e) => {
    if (!e.target.closest("#df-mode")) return;
    const next = isDark() ? "Light" : "Dark";
    const parts = window.location.pathname.replace(/\/+$/, "").split("/");
    if (slugs.includes(parts[parts.length - 1])) parts.pop();
    const base = parts.join("/");
    for (const path of [base, base + "/", ...slugs.map((s) => base + "/" + s)]) {
      localStorage.setItem("stActiveTheme-" + (path || "/") + "-v2", JSON.stringify(next));
    }
    window.location.reload();
  });
})();
</script>""" % json.dumps(PAGE_SLUGS), unsafe_allow_javascript=True)


# ================================================================== 1. overview
def overview():
    page_header("Overview", "The national picture: where people are lost between being eligible, registering and voting.")
    st.markdown(f"<div style='font-size:1.35rem;font-weight:600;margin:4px 0 14px'>People are lost at two points: "
                "<span class='hl-blue'>before registering</span>, and <span class='hl-amber'>after</span>."
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
    page_header("Map", "Every municipality by its problem group. Filter by province or group; hover or tap for details.")
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
        fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
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
    page_header("Municipality profile", "Look up any municipality: its funnel, its problem, what to send, and its 2026 outlook.")
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
                st.markdown(f"**Predicted turnout 2026: {pct(p, 1)}** (likely range {pct(lo)} – {pct(hi)}): its 2021 "
                            f"turnout plus the national change of {(p - row['Turnout 2021']) * 100:+.1f} points that the "
                            "2024 national election points to — the same change for every municipality.")
            else:
                st.markdown("The 2026 prediction will appear here once 08_model has run.")
            covid = row.get("After COVID (2024)")
            if isinstance(covid, str):
                how = ("did relatively better in the 2024 national election than in 2021, so 2021 probably "
                       "understated it" if covid.startswith("recovered") else
                       "fell further behind the rest of the country in the 2024 national election "
                       "than it usually does")
                st.markdown(f"**After COVID: {covid}.** This municipality {how}. If that carries into 2026, "
                            f"turnout would be about **{pct(row['Predicted turnout 2026 (COVID recovery)'], 1)}** "
                            "(COVID recovery scenario).")
            if str(row["Worse than expected in 2021"]) == "True":
                st.info("**Fell much more than the country in 2021:** one of the 15 municipalities whose turnout fell "
                        "furthest below the national change. Something local happened that our data cannot see.",
                        icon=":material/search:")
            st.caption(NOT_A_CAUSE + " Youth figures are about registration only: the IEC does not publish "
                       "turnout by age.")

        if caution:
            st.warning("*More people are registered here than the Census 2022 counted adults. The Census sample is "
                       "small in this municipality, so its registration rate is not reliable.", icon=":material/warning:")

# ================================================================== 4. priority list
def priority_list():
    page_header("Priority list", "Municipalities ranked by how far they are below a typical municipality, with the gap split into its two parts.")
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
    page_header("About", "The problem, how we measured it, how the prediction works, our data sources and the limitations.")
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
2026 turnout = 2021 turnout + a **national change**, taken from turnout in the 2024 national election. Every
municipality gets the same change.

We also built a statistical model (a hierarchical regression, with municipalities grouped inside provinces) to
predict which municipalities would do better or worse than the national change. We tested it honestly: trained on
2011 → 2016 and predicting 2016 → 2021, it was **not more accurate** than giving every municipality the same
national change, and it did not rank municipalities correctly. Most of the change between elections is national,
and differences between municipalities were hard to predict — so the dashboard uses the national change alone.

Every prediction comes with a **range**, not a single number: the spread of this approach's errors when it was
tested on 2021 (8 in 10 municipalities fell inside it).

### Data sources
| Source | Used for |
|---|---|
| IEC municipal election results 2011, 2016, 2021 | registered voters, votes cast, turnout |
| IEC national election results 2024 | the national change in turnout expected for 2026 |
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


# ================================================================== Recommendations
def recommendations_page():
    page_header("Recommendations", "Evidence-linked responses to each type of gap: what the data shows, the evidence, a possible response, and what further evidence is needed.")
    n = national(d)

    st.markdown("Each recommendation is tied to a finding in the data. For every one we separate **what the data shows**, "
                "**the evidence**, **a possible response**, and **what further evidence is needed**. Municipalities are "
                "not ranked or scored: the data shows where a gap exists, not why it exists or what matters most locally.")

    low_reg = d["Problem group"].isin(["Low registration", "Both low"])
    low_turn = d["Problem group"].isin(["Low turnout", "Both low"])
    youth_below = int((d["Youth registration rate"] < d["Registration rate 2026"]).sum())

    recommendation(
        "1 · Registration",
        f"{millions(n['adults'] - n['registered_2026'])} eligible adults ({pct(1 - n['reg_rate_2026'])}) are not on the "
        f"2026 voters' roll. In <b>{int(low_reg.sum())}</b> municipalities registration is below a typical municipality.",
        f"2026 registration figures (IEC, September 2026) compared with citizens aged 18+ (Census 2022). Typical "
        f"(median) registration rate: {pct(d['Typical registration rate'].iloc[0])}.",
        "Make registration information easier to find and understand; publicise the ways to register (online, at IEC "
        "offices, at registration events); explain the documents needed; focus voter education where registration "
        "gaps are documented.",
        "Why people are not registered in each place — for example address changes, missing identity documents, "
        "information gaps or mobility. That needs local or survey research; this data cannot show it.")

    recommendation(
        "2 · Turnout",
        f"In 2021, {pct(1 - n['turnout_2021'], 1)} of registered voters did not vote "
        f"({millions(n['registered_2021'] - n['votes_2021'])} people). In <b>{int(low_turn.sum())}</b> municipalities "
        "turnout is expected to be below a typical municipality.",
        f"IEC results: turnout was {pct(n['turnout_2011'], 1)} (2011), {pct(n['turnout_2016'], 1)} (2016) and "
        f"{pct(n['turnout_2021'], 1)} (2021, held under COVID-19 restrictions). Every province fell in 2021.",
        "Improve public information about voting: dates, voting-station locations, procedures and special votes; "
        "make that information simple and available in local languages; support voters to confirm their details "
        "before election day.",
        "Local barriers to voting (distance, transport, work, queues, trust) are possible explanations, not findings. "
        "Research with communities is needed before choosing between them.")

    recommendation(
        "3 · Youth participation",
        f"{millions(n['youth_not_registered'])} adults aged 18–29 are not registered — {pct(n['youth_share_of_missing'])} "
        f"of everyone missing from the roll. Young adults are registered at a lower rate than adults overall in "
        f"<b>{youth_below} of {len(d)}</b> municipalities.",
        f"Youth registration rate {pct(n['youth_reg_rate'])} against {pct(n['older_reg_rate'])} for adults aged 30+ "
        "(IEC registration by age, Census 2022).",
        "Expand youth-focused voter education; communicate through channels young people use; explain what "
        "municipalities are responsible for; make registration and voting information easy to access on a phone.",
        "Turnout by age is not published, so we cannot say how young people vote once registered. Youth-specific "
        "research is needed on why registration is lower.")

    recommendation(
        "4 · Data and research",
        f"Some questions cannot be answered with the available data. In <b>{int(d['Census caution'].sum())}</b> small "
        "municipalities more people are registered than the Census counted adults.",
        "Population figures come only from Census 2022; youth turnout is not published; 2011 results had to be moved "
        "onto today's boundaries; past elections could not predict which municipalities would do better or worse than "
        "the national change, so the 2026 forecast is the same national change for everyone, give or take about 5 points.",
        "Publish turnout by age group at municipal level; publish registration by age for past elections; update "
        "population estimates between censuses; combine these numbers with community-level research.",
        "Better data would show whether the gaps found here persist, and why they occur.")

    panel("<b>What this page does not claim.</b> " + NOT_A_CAUSE + " The responses above are options to consider, "
             "not conclusions of the model.")

    # ------------------------------------------------------------------ where each gap is documented
    st.markdown("### Where is each gap documented?")
    st.caption("Listed alphabetically, not ranked. Use it to find the municipalities where a particular gap exists.")
    area = st.radio("Gap", ["Registration gap", "Turnout gap", "Youth registration gap"], horizontal=True)
    prov = st.selectbox("Province", ["All provinces"] + sorted(d["Province"].unique()), key="rec_prov")
    t = d if prov == "All provinces" else d[d["Province"] == prov]
    if area == "Registration gap":
        t = t[t["Problem group"].isin(["Low registration", "Both low"])]
        cols = {"Registration rate 2026": "Registration rate 2026",
                "Registrations needed to reach typical": "Registrations to reach typical"}
    elif area == "Turnout gap":
        t = t[t["Problem group"].isin(["Low turnout", "Both low"])]
        cols = {"Turnout 2021": "Turnout 2021", "Turnout used": "Turnout outlook 2026",
                "Extra voters needed to reach typical": "Extra voters to reach typical"}
    else:
        t = t[t["Youth registration rate"] < t["Typical youth registration rate"]]
        cols = {"Youth registration rate": "Youth registration rate", "Young adults not registered": "Young adults not registered"}
    out = t[["Municipality", "Province", *cols]].rename(columns=cols).sort_values("Municipality").copy()
    fmt = {}
    for c in out.columns[2:]:
        if "rate" in c.lower() or "Turnout" in c:
            out[c] = (out[c].clip(upper=1) * 100).round(1)
            fmt[c] = st.column_config.NumberColumn(format="%.0f%%")
        else:
            fmt[c] = st.column_config.NumberColumn(format="%d")
    st.dataframe(out, hide_index=True, use_container_width=True, height=380, column_config=fmt)
    st.download_button("Download this list (CSV)", out.to_csv(index=False).encode("utf-8"),
                       f"democratic_funnel_{area.lower().replace(' ', '_')}.csv", "text/csv", type="primary")
    st.caption(f"{len(out)} municipalities. 'Typical' = the median municipality. Rates above 100% (Census caution) are "
               "shown as 100%.")


# ================================================================== Electoral participation
def participation_page():
    page_header("Electoral participation", "Turnout trends 2011 → 2016 → 2021 by province and municipality, the 2021 context, and what the data cannot tell you.")
    n = national(d)
    bp = by_province(d)

    st.markdown("Trends in municipal election participation, **2011 → 2016 → 2021**, nationally, by province and by "
                "municipality.")

    # ------------------------------------------------------------------ national + provinces
    st.markdown("### Turnout by province")
    province_chart(bp)
    st.caption(f"Nationally, turnout was {pct(n['turnout_2011'], 1)} (2011), {pct(n['turnout_2016'], 1)} (2016) and "
               f"{pct(n['turnout_2021'], 1)} (2021). Provinces are sorted by 2021 turnout, highest at the top.")

    t = bp[["Province", "Turnout 2011", "Turnout 2016", "Turnout 2021", "Participation 2021"]].copy()
    t["Change 2016 → 2021"] = t["Turnout 2021"] - t["Turnout 2016"]
    t = t.sort_values("Change 2016 → 2021")
    for c in t.columns[1:]:
        t[c] = (t[c] * 100).round(1)
    st.dataframe(t, hide_index=True, use_container_width=True, column_config={
        **{c: st.column_config.NumberColumn(format="%.1f%%") for c in
           ["Turnout 2011", "Turnout 2016", "Turnout 2021", "Participation 2021"]},
        "Change 2016 → 2021": st.column_config.NumberColumn(format="%+.1f points"),
        "Participation 2021": st.column_config.NumberColumn("Participation 2021 (% of all adults)", format="%.1f%%")})

    # ------------------------------------------------------------------ 2021 context
    st.markdown("### The 2021 election in context")
    drop = (n["turnout_2021"] - n["turnout_2016"]) * 100
    panel(f"<b>What the data shows.</b> National turnout fell from {pct(n['turnout_2016'], 1)} (2016) to "
             f"{pct(n['turnout_2021'], 1)} (2021), a change of {drop:+.1f} points. <b>Every province fell</b>, from "
             f"{t['Change 2016 → 2021'].max():+.1f} to {t['Change 2016 → 2021'].min():+.1f} points. "
             f"Registered voters: {millions(n['registered_2016'])} (2016) and {millions(n['registered_2021'])} (2021).<br>"
             "<b>Context.</b> The 2021 election was held under COVID-19 restrictions on gatherings and campaigning. "
             "A drop across every province is consistent with a national cause, but this data cannot separate the "
             "effect of the pandemic from other reasons turnout may have changed.")

    st.markdown("### How much municipalities differ")
    fig = go.Figure()
    for y, colour in [(2016, "#b7c3dc"), (2021, AMBER)]:
        fig.add_trace(go.Histogram(x=d[f"Turnout {y}"], name=str(y), marker_color=colour, opacity=0.85, nbinsx=30,
                                   hovertemplate=f"{y}: " + "%{x:.0%}: %{y} municipalities<extra></extra>"))
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(tickformat=".0%", title="Turnout")
    fig.update_yaxes(title="Municipalities")
    chart(fig, 320)
    st.caption(f"In 2021, municipal turnout ranged from {pct(d['Turnout 2021'].min())} to {pct(d['Turnout 2021'].max())}. "
               "The whole distribution moved lower than in 2016.")

    st.markdown("### Not included")
    panel("<b>2006 results, the 2024 national election and municipal by-elections are not part of this analysis.</b> "
             "Our comparisons use the three most recent municipal elections on today's boundaries. National and "
             "municipal elections are not directly comparable, and single by-elections are not a reliable measure of "
             "municipal or national engagement.")

    # ------------------------------------------------------------------ limits
    st.markdown("### What the data can't tell you")
    panel("Election data shows <b>where</b> and <b>how much</b> participation differs. It cannot show <b>why</b>. "
             "Explanations such as transport barriers, documentation problems, lack of information, residential "
             "mobility, political attitudes, dissatisfaction or administrative barriers are <b>possible explanations "
             "that need further evidence</b> — they are not conclusions of this analysis or of the model.", warn=True)


# ================================================================== Voter education
def voter_education_page():
    page_header("Voter education", "How to take part in the local government elections on 4 November 2026. Information only — no political persuasion.")
    st.markdown("### How do I take part in the local government elections?")
    st.markdown("South Africa's next local government elections are on **4 November 2026**. Here is how to make sure "
                "you can vote. Always check the **Electoral Commission (IEC)** for the latest official information.")

    IEC = "https://www.elections.org.za"
    PORTAL = "https://registertovote.elections.org.za"
    FINDER = "https://maps.elections.org.za/vsfinder/"

    c = st.columns(2)
    info_card(c[0], "how_to_reg", "Am I registered?",
            f"<p>SMS your ID number to <b>32810</b> (costs R1), or check online on the "
            f"<a href='{PORTAL}' target='_blank'>IEC voter portal</a>. You will see whether you are registered and "
            "where your voting station is.</p>")
    info_card(c[1], "location_on", "Where do I vote?",
            f"<p>You vote at the voting station where you are registered. Find it with the "
            f"<a href='{FINDER}' target='_blank'>IEC voting station finder</a>, the official IEC app, or by SMS to "
            "<b>32810</b>.</p>")
    st.write("")
    c = st.columns(2)
    info_card(c[0], "edit_note", "How do I register?",
            f"<ol><li>You must be a <b>South African citizen</b> aged <b>16 or older</b> (you can vote from 18).</li>"
            f"<li>Register <b>online</b> at <a href='{PORTAL}' target='_blank'>registertovote.elections.org.za</a>, "
            "at your <b>local IEC office</b>, at your voting station during a <b>registration weekend</b>, or at an IEC "
            "registration event.</li><li>Nobody can register for you — you must do it yourself.</li>"
            "<li>Registration closes when the election is proclaimed, so do not wait.</li></ol>")
    info_card(c[1], "badge", "What do I need?",
            "<p>One of these original documents from Home Affairs:</p><ul><li>green, barcoded ID book</li>"
            "<li>smart ID card</li><li>valid Temporary Identity Certificate</li></ul>"
            "<p>No other identification is accepted. Bring the same document when you vote.</p>")
    st.write("")
    c = st.columns(2)
    info_card(c[0], "home_work", "What if I have moved?",
            f"<p>You must <b>update your registration</b> when you move to a new address, so that you vote in the ward "
            f"where you now live. You can do this <a href='{PORTAL}' target='_blank'>online</a> or at your local IEC "
            "office before registration closes.</p>")
    info_card(c[1], "accessible", "What are special votes?",
            f"<p>If you cannot vote at your voting station on election day, you can <b>apply for a special vote</b>. "
            "Voters who are physically infirm, disabled or pregnant can ask for a <b>home visit</b>; others vote at "
            f"their voting station before election day. You must apply within the period set by the IEC — see "
            f"<a href='{IEC}' target='_blank'>elections.org.za</a>.</p>")
    st.write("")

    st.markdown("### Why do local elections matter?")
    st.markdown(dedent("""
    Your **municipal council** makes decisions that affect daily life. Municipalities are responsible for services such as:

    - **water** and **sanitation**
    - **electricity** distribution in many areas
    - **refuse removal**
    - **local roads**, streetlights and storm-water drains
    - local **planning**, building approvals, parks and community facilities

    In local government elections you vote for a **ward councillor** (the person who represents your ward) and for a
    **party** on the proportional ballot; outside the metros there is also a party ballot for the district council.
    These votes decide who sits on the council and who governs your municipality for the next five years.
    """))
    panel("This page gives voter information only. It does not recommend any party or candidate. For official "
             f"information, visit <a href='{IEC}' target='_blank'>elections.org.za</a>.")


# ================================================================== Key findings: the charts of 07_eda
def province_chart(bp):
    """07_eda Q2: one bar per election, provinces sorted by 2021 turnout (highest at the top)."""
    order = bp.sort_values("Turnout 2021")
    fig = go.Figure()
    for y in (2021, 2016, 2011):                     # drawn bottom-up, so 2011 sits on top within each province
        fig.add_trace(go.Bar(y=order["Province"], x=order[f"Turnout {y}"], orientation="h", name=str(y),
                             marker_color=YEAR_COLOURS[y], text=[pct(v, 1) for v in order[f"Turnout {y}"]],
                             textposition="outside", cliponaxis=False, textfont=dict(size=13),
                             hovertemplate="%{y} " + str(y) + ": %{x:.1%}<extra></extra>"))
    fig.update_layout(barmode="group", bargap=0.22, bargroupgap=0.05, legend_traceorder="reversed")
    fig.update_xaxes(tickformat=".0%", range=[0, 0.8], title="Turnout rate")
    fig.update_yaxes(title="Province")
    chart(fig, 640)


def findings_page():
    page_header("Key findings", "The charts from our exploratory analysis (07_eda): registration and turnout, who, "
                                "what goes with low turnout, and where.")
    n, bp = national(d), by_province(d)
    adults = d["Adults who may vote"].sum()

    # ------------------------------------------------------------------ A. turnout and registration
    st.markdown("## A. Turnout and registration")
    st.markdown("### Q1. Registration vs Turnout (2011-2026)")
    yrs = [2011, 2016, 2021, 2026]
    reg = [d[f"Registered {y}"].sum() / adults for y in yrs]
    tur = [n[f"turnout_{y}"] for y in yrs[:3]]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=yrs, y=reg, name="Registration rate (% of adults who may vote)", mode="lines+markers+text",
                             line=dict(color=BLUE, width=3), marker=dict(size=10), text=[pct(v, 1) for v in reg],
                             textposition="top center", textfont=dict(color=BLUE, size=14),
                             hovertemplate="Registration %{x}: %{y:.1%}<extra></extra>"))
    fig.add_trace(go.Scatter(x=yrs[:3], y=tur, name="Turnout (% of registered voters)", mode="lines+markers+text",
                             line=dict(color=AMBER, width=3), marker=dict(size=10, symbol="square"),
                             text=[pct(v, 1) for v in tur], textposition="bottom center",
                             textfont=dict(color=AMBER, size=14), hovertemplate="Turnout %{x}: %{y:.1%}<extra></extra>"))
    fig.add_annotation(x=2026, y=0.30, text="4 Nov 2026:<br>not held yet", showarrow=False, bordercolor=AMBER,
                       borderpad=6, font=dict(color=AMBER, size=13))
    fig.update_yaxes(tickformat=".0%", range=[0, 1], title="Percentage")
    fig.update_xaxes(tickvals=yrs, title="Local government election year")
    chart(fig, 400)
    st.caption("All registration rates use the 2022 Census, so earlier years are understated.")
    st.markdown(f"More adults are on the roll than ever: the registration rate rose from **{pct(reg[0])}** (2011) to "
                f"**{pct(reg[-1])}** (2026). But turnout **fell from {pct(tur[1])} to {pct(tur[2])} in 2021**, the "
                "COVID election. The problem is less getting people registered and more getting registered voters "
                "to the polls.")

    st.markdown("### Q2. Turnout by province")
    province_chart(bp)
    fall = (bp["Turnout 2021"] - bp["Turnout 2016"]) * 100
    st.markdown(f"Turnout fell in **every province** in 2021, by about **{-fall.max():.0f} to {-fall.min():.0f} points**. "
                f"**{bp.loc[bp['Turnout 2021'].idxmax(), 'Province']}** had the highest turnout in 2021 "
                f"({pct(bp['Turnout 2021'].max())}); the lowest was **{bp.loc[bp['Turnout 2021'].idxmin(), 'Province']}** "
                f"({pct(bp['Turnout 2021'].min(), 1)}).")

    st.markdown("### Q3. The 10 municipalities with the lowest average turnout (2011–2021)")
    tw = d.set_index("Municipality")[["Province", "Turnout 2011", "Turnout 2016", "Turnout 2021"]].copy()
    tw["Average"] = tw[["Turnout 2011", "Turnout 2016", "Turnout 2021"]].mean(axis=1)
    low = tw.nsmallest(10, "Average").iloc[::-1]
    labels = [f"{m} ({p})" for m, p in zip(low.index, low["Province"])]
    fig = go.Figure()
    for y in (2021, 2016, 2011):
        fig.add_trace(go.Bar(y=labels, x=low[f"Turnout {y}"], orientation="h", name=str(y),
                             marker_color=YEAR_COLOURS[y], text=[pct(v, 1) for v in low[f"Turnout {y}"]],
                             textposition="outside", cliponaxis=False, textfont=dict(size=13),
                             hovertemplate="%{y} " + str(y) + ": %{x:.1%}<extra></extra>"))
    fig.update_layout(barmode="group", bargap=0.22, bargroupgap=0.05, legend_traceorder="reversed")
    fig.update_xaxes(tickformat=".0%", range=[0, 0.62], title="Turnout rate")
    fig.update_yaxes(title="Municipality")
    chart(fig, 700)
    st.caption("Ranked by average turnout over the 2011, 2016 and 2021 elections. 2011 turnout for municipalities "
               "created or re-drawn in 2016 is an estimate (results moved onto today's boundaries).")
    rose = low[low["Turnout 2021"] > low["Turnout 2016"]].index.tolist()
    note = ""
    if rose:
        note = f" Turnout **rose** in 2021 in {', '.join(rose)}"
        if rose == ["Collins Chabane"]:
            note += (": it was created in 2016, so its 2011 figure is an estimate, and it is in this list because of "
                     "its low 2016 turnout")
        note += "."
    st.markdown(f"**{low.index[-1]} ({low['Province'].iloc[-1]})** has the lowest average turnout "
                f"({pct(low['Average'].iloc[-1], 1)})." + note +
                " Low turnout is a share of *registered* voters: a municipality with low turnout may still have a "
                "full roll, and the other way round.")

    # ------------------------------------------------------------------ B. who
    st.markdown("## B. Who")
    st.markdown("### Q4. Young adults are far less likely to be registered (2026)")
    ages = pd.DataFrame({"registered": [n["youth_registered"], n["registered_2026"] - n["youth_registered"]],
                         "eligible": [n["youth_adults"], adults - n["youth_adults"]]}, index=["18–29", "30+"])
    ages["rate"] = ages["registered"] / ages["eligible"]
    fig = go.Figure(go.Bar(y=ages.index, x=ages["rate"], orientation="h", marker_color=[BLUE, NAVY],
                           text=[f"{r:.1%}  ({a / 1e6:.1f}m of {b / 1e6:.1f}m)" for r, a, b in
                                 zip(ages["rate"], ages["registered"], ages["eligible"])],
                           textposition="outside", cliponaxis=False, textfont=dict(size=14),
                           hovertemplate="%{y}: %{x:.1%}<extra></extra>"))
    fig.update_yaxes(autorange="reversed", title="Age")
    fig.update_xaxes(tickformat=".0%", range=[0, 1.15], title="Registration rate, 2026")
    chart(fig, 250)
    youth_below = int((d["Youth registration rate"] < d["Registration rate 2026"]).sum())
    st.markdown(f"**Young adults (18–29)** have by far the lowest participation: **{pct(ages['rate'].iloc[0])}** are "
                f"registered, against **{pct(ages['rate'].iloc[1])}** of adults aged 30 and older, and they are "
                f"registered at a lower rate than adults overall in {youth_below} of {len(d)} municipalities. "
                "This is registration only: the IEC does not publish turnout by age.")

    # ------------------------------------------------------------------ C. what goes with low turnout
    st.markdown("## C. What goes with low turnout")
    panel("<b>A link is not proof of a cause.</b> A pattern across municipalities cannot show why individuals do or "
          "do not vote. The honest version of \"what causes low turnout\" is \"what is <b>associated</b> with it\".")
    st.markdown("### Q5. What goes with low registration and low turnout, 2021")
    x = d.assign(**{"Population density": np.log(d["Population density"])})
    chars = ["Adults with higher education", "Households with piped water", "Households with electricity",
             "Households with refuse removal", "Population density", "Neighbours' turnout 2021"]
    corr = x[["Registration vs typical 2021", "Turnout vs typical 2021"] + chars].corr().loc[
        chars, ["Registration vs typical 2021", "Turnout vs typical 2021"]]
    fig = go.Figure(go.Heatmap(z=corr.values, x=["Registration vs typical", "Turnout vs typical"],
                               y=[c.replace(" 2021", "") for c in chars], zmin=-1, zmax=1,
                               colorscale=[[0, "#2166ac"], [0.5, "#f7f7f7"], [1, "#b2182b"]],
                               texttemplate="%{z:.2f}", textfont=dict(size=16, color="#0b0b0b"),
                               colorbar=dict(title="correlation"),
                               hovertemplate="%{y} and %{x}: %{z:.2f}<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(side="top")
    chart(fig, 430)
    st.markdown(
        f"- **Registration and turnout are only loosely related** (correlation "
        f"**{d['Registration vs typical 2021'].corr(d['Turnout vs typical 2021']):.2f}**): the two leaks are largely "
        "different problems.\n"
        f"- **Density matters most:** denser municipalities had lower turnout in 2021 "
        f"(**{corr.loc['Population density', 'Turnout vs typical 2021']:.2f}**).\n"
        "- **Services and education:** their simple links with turnout in 2021 are weak. Tested properly (08_model), "
        "better-serviced municipalities fell more in 2021 only, not before. It points to COVID hitting urban-type "
        "places, not to services driving turnout.\n"
        f"- **Neighbours matter:** turnout is strongly related to neighbours' turnout "
        f"(**{corr.loc[chars[-1], 'Turnout vs typical 2021']:.2f}**, see Q6).")

    st.markdown("### Q6. Turnout clusters geographically")
    sp = d.dropna(subset=["Neighbours' turnout 2021", "Turnout 2021"])
    rho = sp["Turnout 2021"].corr(sp["Neighbours' turnout 2021"])
    rho_prev = sp["Turnout 2021"].corr(sp["Neighbours' turnout 2016"])
    b, a = np.polyfit(sp["Neighbours' turnout 2021"], sp["Turnout 2021"], 1)
    xs = np.linspace(sp["Neighbours' turnout 2021"].min(), sp["Neighbours' turnout 2021"].max(), 50)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sp["Neighbours' turnout 2021"], y=sp["Turnout 2021"], mode="markers",
                             marker=dict(color=AMBER, size=9, line=dict(color="white", width=0.8)),
                             customdata=sp[["Municipality"]],
                             hovertemplate="%{customdata[0]}<br>own %{y:.1%}, neighbours %{x:.1%}<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=a + b * xs, mode="lines", line=dict(color=NAVY, width=3), hoverinfo="skip"))
    fig.add_annotation(x=0.02, y=0.98, xref="paper", yref="paper", showarrow=False, xanchor="left",
                       text=f"<b>correlation = {rho:.2f}</b>", font=dict(size=15, color=NAVY))
    fig.update_layout(showlegend=False)
    fig.update_xaxes(tickformat=".0%", title="Neighbours' average turnout, 2021")
    fig.update_yaxes(tickformat=".0%", title="Own turnout, 2021")
    chart(fig, 430)
    st.markdown(f"**Yes.** A municipality's turnout is strongly related to its neighbours' turnout in the same election "
                f"(correlation **{rho:.2f}**), and still clearly related to their turnout at the previous election "
                f"(**{rho_prev:.2f}**). Low turnout is regional. **Was 2021 just COVID?** In cities the 2021 drop was "
                "COVID; in rural municipalities turnout is really falling: in 2024 the densest municipalities returned "
                "to their normal pattern, while the least dense are still below theirs.")

    st.markdown("### Q7. Denser municipalities have lower turnout")
    dd = d.dropna(subset=["Population density", "Turnout vs typical 2021"])
    lx, yv = np.log10(dd["Population density"].to_numpy()), dd["Turnout vs typical 2021"].to_numpy()
    b, a = np.polyfit(lx, yv, 1)
    grid = np.linspace(lx.min(), lx.max(), 60)
    resid = yv - (a + b * lx)
    se = np.sqrt((resid ** 2).sum() / (len(lx) - 2)
                 * (1 / len(lx) + (grid - lx.mean()) ** 2 / ((lx - lx.mean()) ** 2).sum()))
    fit = a + b * grid
    r7 = np.corrcoef(lx, yv)[0, 1]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=np.r_[10 ** grid, 10 ** grid[::-1]], y=np.r_[fit + 1.96 * se, (fit - 1.96 * se)[::-1]],
                             fill="toself", fillcolor="rgba(42, 120, 214, 0.18)", line=dict(width=0), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=dd["Population density"], y=yv, mode="markers",
                             marker=dict(color=AMBER, size=9, opacity=0.8, line=dict(color="white", width=0.6)),
                             customdata=dd[["Municipality"]],
                             hovertemplate="%{customdata[0]}<br>%{x:,.0f} people per km²: %{y:+.0%}<extra></extra>"))
    fig.add_trace(go.Scatter(x=10 ** grid, y=fit, mode="lines", line=dict(color=BLUE, width=3), hoverinfo="skip"))
    fig.add_annotation(x=0.02, y=0.98, xref="paper", yref="paper", showarrow=False, xanchor="left",
                       text=f"<b>correlation = {r7:.2f}</b>", font=dict(size=15, color=NAVY))
    fig.update_layout(showlegend=False)
    fig.update_xaxes(type="log", tickvals=[1, 10, 100, 1000], ticktext=["1", "10", "100", "1,000"],
                     title="People per km² (log scale)")
    fig.update_yaxes(tickformat=".0%", title="Turnout vs typical municipality, 2021")
    chart(fig, 430)
    st.markdown(f"Denser municipalities had lower turnout than a typical municipality in 2021 (correlation "
                f"**{r7:.2f}**): metros and large urban municipalities lost more voters between registration and the "
                "ballot box. Density stands in for many things at once (urban living, migration, COVID restrictions "
                "in 2021), so this is a link, not a cause.")

    # ------------------------------------------------------------------ D. what to do
    st.markdown("## D. What to do")
    st.markdown("### Q8. Where should effort go before 4 November 2026?")
    counts = d["Problem group"].value_counts()
    st.markdown(f"**{counts.get('Both low', 0)} municipalities are below typical on both registration and turnout**: "
                "they are the first priority, and need registration drives, ID and address help, and voter "
                "education and mobilisation together. The full ranked list, with the number of registrations and "
                "extra voters each one needs, is on the **Priority list** page (Menu).")


# ================================================================== navigation: Menu (top left)
nav = st.navigation([
    st.Page(overview, title="Overview", icon=":material/home:", url_path="overview", default=True),
    st.Page(findings_page, title="Key findings", icon=":material/insights:", url_path="findings"),
    st.Page(map_page, title="Map", icon=":material/map:", url_path="map"),
    st.Page(profile, title="Municipality profile", icon=":material/account_balance:", url_path="profile"),
    st.Page(priority_list, title="Priority list", icon=":material/format_list_numbered:", url_path="priority"),
    st.Page(recommendations_page, title="Recommendations", icon=":material/lightbulb:", url_path="recommendations"),
    st.Page(participation_page, title="Electoral participation", icon=":material/bar_chart:", url_path="participation"),
    st.Page(voter_education_page, title="Voter education", icon=":material/how_to_vote:", url_path="voter-education"),
    st.Page(about, title="About", icon=":material/info:", url_path="about"),
], position="sidebar")
st.sidebar.caption("The Democratic Funnel · Team UL · DIRISA Student Datathon Challenge 2026")
nav.run()

# ------------------------------------------------------------------ footer (every page)
st.markdown(f"""
<div class="footer">
  <img src="{img64('partners_footer.png')}" alt="Department of Science, Technology and Innovation · CSIR · NICIS DIRISA">
  <div class="txt">
    <b>The Democratic Funnel</b> · Team UL, University of Limpopo · DIRISA Student Datathon Challenge 2026<br>
    A student project. Not an official publication of DIRISA, NICIS, the CSIR, the Department of Science, Technology
    and Innovation or the Electoral Commission.<br>
    Data: Electoral Commission of South Africa (IEC) · Statistics South Africa, Census 2022 · Municipal Demarcation Board
  </div>
</div>""", unsafe_allow_html=True)
