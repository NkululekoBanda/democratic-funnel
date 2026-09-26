"""📊 Electoral Participation - trends and context for researchers, journalists and civil society."""
import plotly.graph_objects as go
import streamlit as st

from lib import ui
from lib.data import AMBER, NAVY, by_province, load, millions, national, pct

d, geo = load()
n = national(d)
bp = by_province(d)

st.title("📊 Electoral Participation")
st.markdown("Trends in municipal election participation, **2011 → 2016 → 2021**, nationally, by province and by "
            "municipality.")

# ------------------------------------------------------------------ national + provinces
st.markdown("### Turnout by province")
fig = go.Figure()
for _, row in bp.iterrows():
    fig.add_trace(go.Scatter(x=[2011, 2016, 2021], y=[row[f"Turnout {y}"] for y in (2011, 2016, 2021)],
                             name=row["Province"], mode="lines+markers", line=dict(color="#b7c3dc", width=1.6),
                             marker=dict(size=6), showlegend=False,
                             hovertemplate=row["Province"] + " %{x}: %{y:.1%}<extra></extra>"))
fig.add_trace(go.Scatter(x=[2011, 2016, 2021], y=[n[f"turnout_{y}"] for y in (2011, 2016, 2021)], name="National",
                         mode="lines+markers+text", text=[pct(n[f"turnout_{y}"], 1) for y in (2011, 2016, 2021)],
                         textposition="top center", line=dict(color=NAVY, width=4), marker=dict(size=11),
                         hovertemplate="National %{x}: %{y:.1%}<extra></extra>"))
fig.update_yaxes(tickformat=".0%", title="Turnout (votes ÷ registered)")
fig.update_xaxes(tickvals=[2011, 2016, 2021])
ui.show(fig, 420)
st.caption("Navy: national. Light lines: the nine provinces (hover for names).")

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
ui.panel(f"<b>What the data shows.</b> National turnout fell from {pct(n['turnout_2016'], 1)} (2016) to "
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
ui.show(fig, 320)
st.caption(f"In 2021, municipal turnout ranged from {pct(d['Turnout 2021'].min())} to {pct(d['Turnout 2021'].max())}. "
           "The whole distribution moved lower than in 2016.")

st.markdown("### Not included")
ui.panel("<b>2006 results, the 2024 national election and municipal by-elections are not part of this analysis.</b> "
         "Our comparisons use the three most recent municipal elections on today's boundaries. National and "
         "municipal elections are not directly comparable, and single by-elections are not a reliable measure of "
         "municipal or national engagement.")

# ------------------------------------------------------------------ limits
st.markdown("### What the data can't tell you")
ui.panel("Election data shows <b>where</b> and <b>how much</b> participation differs. It cannot show <b>why</b>. "
         "Explanations such as transport barriers, documentation problems, lack of information, residential "
         "mobility, political attitudes, dissatisfaction or administrative barriers are <b>possible explanations "
         "that need further evidence</b> — they are not conclusions of this analysis or of the model.", warn=True)
