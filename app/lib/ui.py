"""Reusable dashboard components: styling, KPI cards, boxes, funnel, map and trend charts."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib.data import (AMBER, BLUE, CRIMSON, DIRISA_ORANGE, GRID, GROUP_COLOURS, INK, INK2, MAP_MEASURES, NAVY,
                      RAMPS, pct)


def css():
    st.markdown(f"""
<style>
  html, body, [class*="css"] {{ font-size: 17px; }}
  .block-container {{ padding-top: 3rem; max-width: 1200px; }}
  .hero {{ background: {NAVY}; border-bottom: 5px solid {DIRISA_ORANGE}; border-radius: 12px; padding: 22px 26px;
           margin-bottom: 18px; color: #fff; }}
  .hero .kicker {{ color: {DIRISA_ORANGE}; font-size: .8rem; letter-spacing: .12em; font-weight: 700; }}
  .hero h1 {{ color: #fff; font-size: 2.1rem; font-weight: 800; margin: 4px 0 6px; padding: 0; line-height: 1.2; }}
  .hero p {{ color: #dfe5f2; font-size: 1.05rem; margin: 0; }}
  .kpi {{ border: 1px solid {GRID}; border-radius: 12px; padding: 14px 16px; height: 100%; background: #fff; }}
  .kpi .label {{ font-size: .92rem; font-weight: 700; color: {INK}; }}
  .kpi .value {{ font-size: 2.1rem; font-weight: 800; line-height: 1.15; margin: 4px 0; }}
  .kpi .note {{ font-size: .88rem; color: {INK2}; line-height: 1.35; }}
  .kpi .tag {{ display: inline-block; font-size: .72rem; font-weight: 700; border-radius: 6px; padding: 1px 7px;
               background: #eef1f7; color: {NAVY}; margin-top: 6px; }}
  .pill {{ display: inline-block; padding: 3px 11px; border-radius: 999px; font-weight: 700; font-size: .9rem; }}
  .panel {{ border-left: 5px solid {NAVY}; background: #f3f5fa; padding: 12px 16px; border-radius: 8px;
            margin: 6px 0 14px; line-height: 1.5; }}
  .panel.warn {{ border-left-color: {CRIMSON}; background: #fbf1f3; }}
  .rec {{ border: 1px solid {GRID}; border-radius: 12px; padding: 4px 18px 10px; margin-bottom: 16px; background: #fff; }}
  .rec h3 {{ margin-bottom: 4px; }}
  .rec .row {{ display: flex; gap: 12px; padding: 8px 0; border-top: 1px solid {GRID}; }}
  .rec .row:first-of-type {{ border-top: none; }}
  .rec .k {{ min-width: 190px; font-weight: 700; color: {NAVY}; }}
  .card {{ border: 1px solid {GRID}; border-radius: 12px; padding: 16px 18px; height: 100%; background: #fff; }}
  .card .icon {{ font-size: 1.9rem; }}
  .card h4 {{ margin: 6px 0; }}
  .step {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin: 8px 0 4px; }}
  .step .s {{ border-radius: 10px; padding: 10px 14px; color: #fff; font-weight: 700; text-align: center; }}
  .step .arrow {{ font-size: 1.4rem; color: {INK2}; }}
  /* menu button: show a ☰ hamburger instead of Streamlit's chevron */
  [data-testid="stExpandSidebarButton"] svg, [data-testid="stExpandSidebarButton"] span,
  [data-testid="stSidebarCollapsedControl"] button svg, [data-testid="stSidebarCollapsedControl"] button span {{ display: none !important; }}
  [data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"] button {{
    width: auto !important; min-width: 90px; padding: 4px 10px !important; border-radius: 8px;
    border: 1px solid {GRID} !important; background: #fff !important; }}
  [data-testid="stExpandSidebarButton"]::after, [data-testid="stSidebarCollapsedControl"] button::after {{
    content: "☰  Menu"; font-size: 1.05rem; font-weight: 700; color: {NAVY}; white-space: pre; }}
  @media (max-width: 640px) {{
    .hero h1 {{ font-size: 1.6rem; }} .kpi .value {{ font-size: 1.7rem; }}
    .rec .row {{ flex-direction: column; gap: 2px; }} .rec .k {{ min-width: 0; }}
  }}
</style>""", unsafe_allow_html=True)


def hero(title, subtitle, kicker="DIRISA STUDENT DATATHON CHALLENGE 2026 · TEAM UL"):
    st.markdown(f"<div class='hero'><div class='kicker'>{kicker}</div><h1>{title}</h1><p>{subtitle}</p></div>",
                unsafe_allow_html=True)


def kpi(col, label, value, note, tag, colour=INK):
    """A KPI card: what it is (label), the number, what it means (note), and the year/unit (tag)."""
    col.markdown(f"<div class='kpi'><div class='label'>{label}</div>"
                 f"<div class='value' style='color:{colour}'>{value}</div>"
                 f"<div class='note'>{note}</div><div class='tag'>{tag}</div></div>", unsafe_allow_html=True)


def pill(group):
    text = "#ffffff" if group in ("Low registration", "Both low") else INK
    return f"<span class='pill' style='background:{GROUP_COLOURS[group]};color:{text}'>{group}</span>"


def panel(html, warn=False):
    st.markdown(f"<div class='panel{' warn' if warn else ''}'>{html}</div>", unsafe_allow_html=True)


def card(col, icon, title, body):
    col.markdown(f"<div class='card'><div class='icon'>{icon}</div><h4>{title}</h4>{body}</div>",
                 unsafe_allow_html=True)


def recommendation(title, finding, evidence, response, further):
    rows = [("What the data shows", finding), ("Evidence", evidence), ("Possible response", response),
            ("Further evidence needed", further)]
    body = "".join(f"<div class='row'><div class='k'>{k}</div><div>{v}</div></div>" for k, v in rows)
    st.markdown(f"<div class='rec'><h3>{title}</h3>{body}</div>", unsafe_allow_html=True)


def funnel_steps(steps):
    """Simple visual funnel: [(label, value_text, colour), ...] with arrows between."""
    parts = []
    for i, (label, value, colour) in enumerate(steps):
        text_colour = INK if colour in (AMBER,) else "#fff"
        parts.append(f"<div class='s' style='background:{colour};color:{text_colour}'>{label}<br>"
                     f"<span style='font-size:1.3rem'>{value}</span></div>")
        if i < len(steps) - 1:
            parts.append("<div class='arrow'>→</div>")
    st.markdown(f"<div class='step'>{''.join(parts)}</div>", unsafe_allow_html=True)


def show(fig, height=360, key=None, on_select=None):
    fig.update_layout(height=height, margin=dict(l=8, r=8, t=36, b=8), plot_bgcolor="rgba(0,0,0,0)",
                      paper_bgcolor="rgba(0,0,0,0)", font=dict(size=15, color=INK),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None),
                      hoverlabel=dict(font_size=15))
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID)
    kwargs = dict(use_container_width=True, config={"displayModeBar": False})
    if on_select:
        return st.plotly_chart(fig, key=key, on_select=on_select, selection_mode="points", **kwargs)
    return st.plotly_chart(fig, key=key, **kwargs)


def funnel_bars(values, labels, colours, typical=None, height=260):
    """Horizontal 'out of 100' funnel bars, optionally with navy markers for a typical municipality."""
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=colours,
                           text=[f"{v:.0f}" for v in values], textposition="inside", insidetextanchor="start",
                           textfont=dict(size=18, color=["#fff" if c not in (AMBER,) else INK for c in colours]),
                           name="This place", hovertemplate="%{y}: %{x:.0f} of 100<extra></extra>"))
    if typical:
        fig.add_trace(go.Scatter(x=[v for _, v in typical], y=[l for l, _ in typical], mode="markers",
                                 name="Typical municipality",
                                 marker=dict(symbol="line-ns", size=34, line=dict(width=4, color=NAVY)),
                                 hovertemplate="Typical municipality: %{x:.0f} of 100<extra></extra>"))
    fig.update_yaxes(autorange="reversed", title=None)
    fig.update_xaxes(range=[0, 105], showticklabels=False, showgrid=False)
    return fig


def gap_map(d, geo, measure, key=None, selectable=False):
    """Choropleth of one gap measure. Returns the selection event when selectable."""
    spec = MAP_MEASURES[measure]
    col = spec["col"]
    dd = d.copy()
    dd["_value_txt"] = [pct(v, 1) for v in dd[col]]
    dd["_reg_txt"] = [("over 100% (Census caution)" if c else pct(v, 1))
                      for v, c in zip(dd["Registration rate 2026"], dd["Census caution"])]
    fig = go.Figure(go.Choropleth(
        geojson=geo, featureidkey="properties.muni_code", locations=dd["Code"], z=dd[col],
        colorscale=[[i / (len(RAMPS[spec["ramp"]]) - 1), c] for i, c in enumerate(RAMPS[spec["ramp"]])],
        marker_line_color="white", marker_line_width=0.5,
        colorbar=dict(tickformat=".0%", title=None, thickness=14, len=0.7),
        customdata=dd[["Municipality", "Province", "_value_txt", "_reg_txt", "Turnout 2021",
                       "Youth registration gap 2026", "Problem group"]],
        hovertemplate=(f"<b>%{{customdata[0]}}</b><br>%{{customdata[1]}}<br>{measure}: %{{customdata[2]}}<br>"
                       "Registration rate 2026: %{customdata[3]}<br>Turnout 2021: %{customdata[4]:.1%}<br>"
                       "Youth registration gap 2026: %{customdata[5]:.1%}<br>Group: %{customdata[6]}"
                       "<extra></extra>")))
    fig.update_geos(fitbounds="locations", visible=False)
    return show(fig, 560, key=key, on_select="rerun" if selectable else None)


def selected_code(event):
    """Municipality code clicked on a map (or None)."""
    try:
        pts = event.selection.points if hasattr(event, "selection") else event["selection"]["points"]
        return pts[0].get("location") if pts else None
    except Exception:
        return None


def trend(years, series, height=320, pct_axis=True, predicted=None):
    """Line chart over elections. series: [(name, values, colour, dash)]. predicted: (value, low, high, colour)."""
    fig = go.Figure()
    for name, vals, colour, dash in series:
        fig.add_trace(go.Scatter(x=years, y=vals, name=name, mode="lines+markers",
                                 line=dict(color=colour, width=3 if dash == "solid" else 2, dash=dash),
                                 marker=dict(size=10, line=dict(width=2, color="white")),
                                 hovertemplate=f"{name} %{{x}}: " + ("%{y:.1%}" if pct_axis else "%{y:,.0f}")
                                               + "<extra></extra>"))
    if predicted:
        p, lo, hi, colour = predicted
        fig.add_trace(go.Scatter(x=[years[-1], 2026], y=[series[-1][1][-1], p], name="Model outlook 2026",
                                 mode="lines+markers", line=dict(color=colour, width=2, dash="dash"),
                                 marker=dict(size=[0, 13], symbol="diamond"),
                                 error_y=dict(type="data", symmetric=False, array=[0, hi - p], arrayminus=[0, p - lo],
                                              color=NAVY, thickness=2, width=8),
                                 hovertemplate="Model outlook 2026: %{y:.1%}<extra></extra>"))
    if pct_axis:
        fig.update_yaxes(tickformat=".0%")
    fig.update_xaxes(tickvals=list(years) + ([2026] if predicted else []), title=None)
    return fig
