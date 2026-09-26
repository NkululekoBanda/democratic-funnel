"""🏠 Overview - the landing page: the national picture in a few seconds."""
import plotly.graph_objects as go
import streamlit as st

from lib import ui
from lib.data import (AMBER, AMBER_TEXT, BLUE, CRIMSON, INK2, MAP_MEASURES, NAVY, load, millions, national, num,
                      pct)

d, geo = load()
n = national(d)

ui.hero("The Democratic Participation Dashboard",
        "Understanding where participation is lost across the electoral journey — from registration to turnout.")

st.markdown("People can drop out of local democracy at **two points**: adults who may vote but are **not "
            "registered**, and registered voters who **do not turn out**. The official turnout figure only counts "
            "the second. This is the **Democratic Funnel** for the last municipal election (2021):")
ui.funnel_steps([
    ("Eligible adults", millions(n["adults"]).replace(" million", " m"), NAVY),
    ("Registered voters", millions(n["registered_2021"]).replace(" million", " m"), BLUE),
    ("Voters who turned out", millions(n["votes_2021"]).replace(" million", " m"), AMBER),
    ("Participation", f"{n['participation_2021'] * 100:.0f} of 100 adults", CRIMSON),
])
st.caption(f"Eligible adults = South African citizens aged 18+ (Census 2022). For 2026, "
           f"{millions(n['registered_2026'])} people are registered so far. Open the menu (☰, top left) to explore.")

# ------------------------------------------------------------------ KPI cards
st.markdown("### Where participation is lost")
row1, row2 = st.columns(3), st.columns(3)
ui.kpi(row1[0], "Registration gap", millions(n["adults"] - n["registered_2026"]),
       f"adults who may vote are <b>not</b> on the voters' roll — {pct(1 - n['reg_rate_2026'])} of all "
       f"eligible adults (registration rate {pct(n['reg_rate_2026'])}).", "2026 roll · number of people", BLUE)
ui.kpi(row1[1], "Turnout gap", pct(1 - n["turnout_2021"], 1),
       f"of registered voters did <b>not</b> vote — {millions(n['registered_2021'] - n['votes_2021'])} people "
       f"(turnout rate {pct(n['turnout_2021'], 1)}).", "2021 municipal election · % of registered voters",
       AMBER_TEXT)
ui.kpi(row1[2], "Participation shortfall", f"{(1 - n['participation_2021']) * 100:.0f} of 100",
       f"eligible adults did <b>not</b> vote, counting both gaps together (participation "
       f"{pct(n['participation_2021'])}).", "2021 · per 100 eligible adults", CRIMSON)
ui.kpi(row2[0], "Youth registration gap", millions(n["youth_not_registered"]),
       f"adults aged 18–29 are <b>not</b> registered — {pct(1 - n['youth_reg_rate'])} of that age group, and "
       f"{pct(n['youth_share_of_missing'])} of everyone missing from the roll.", "2026 roll · ages 18–29", BLUE)
ui.kpi(row2[1], "Youth turnout gap", "Not published",
       "The IEC does not publish turnout by age for municipalities, so this cannot be measured.",
       "no data available", INK2)
ui.kpi(row2[2], "Municipalities analysed", str(n["municipalities"]),
       "every local and metropolitan municipality (district councils are not separate voting areas).",
       "today's boundaries · count")

# ------------------------------------------------------------------ national map
st.markdown("### Across the country")
choices = list(MAP_MEASURES)
measure = st.radio("Show on the map", choices, horizontal=True, key="ov_measure")
st.caption(MAP_MEASURES[measure]["help"])
if MAP_MEASURES[measure]["col"] is None:
    ui.panel("<b>No data.</b> The IEC does not publish turnout by age for municipalities, so a youth turnout gap "
             "cannot be mapped. The Youth Lens shows what <i>can</i> be measured: youth registration.", warn=True)
elif geo is None:
    st.info("Map layer missing: run notebooks/09_dashboard_prep.ipynb.")
else:
    event = ui.gap_map(d, geo, measure, key="ov_map", selectable=True)
    st.caption("Darker = larger gap. Hover or tap a municipality for its numbers; click it to open its profile.")
    code = ui.selected_code(event)
    if code:
        name = d.loc[d["Code"] == code, "Municipality"].iloc[0]
        if st.button(f"Open {name} in the Municipal Deep Dive →", type="primary"):
            st.session_state["muni_code"] = code
            st.switch_page("views/deep_dive.py")

# ------------------------------------------------------------------ history
st.markdown("### Over time")
left, right = st.columns(2)
with left:
    years = [2011, 2016, 2021]
    pred = (n["pred_2026"], n["pred_2026_low"], n["pred_2026_high"], AMBER) if "pred_2026" in n else None
    fig = ui.trend(years, [("Turnout rate", [n[f"turnout_{y}"] for y in years], AMBER, "solid")], predicted=pred)
    fig.add_annotation(x=2021, y=n["turnout_2021"], text="2021: held under COVID-19 restrictions",
                       showarrow=False, yshift=-24, font=dict(color=INK2, size=12))
    fig.update_yaxes(range=[0.35, 0.7])
    st.markdown("**Turnout rate** (votes ÷ registered voters)")
    ui.show(fig, 330)
    st.caption(f"Turnout was about {pct(n['turnout_2016'])} in 2011 and 2016 and {pct(n['turnout_2021'], 1)} in "
               "2021. The dashed line is the model's outlook for 2026, with its likely range.")
with right:
    yrs = ["2011", "2016", "2021", "2026"]
    vals = [n["registered_2011"], n["registered_2016"], n["registered_2021"], n["registered_2026"]]
    fig = go.Figure(go.Bar(x=yrs, y=vals, marker_color=[BLUE, BLUE, BLUE, "#8db8ec"],
                           text=[f"{v / 1e6:.1f} m" for v in vals], textposition="outside", cliponaxis=False,
                           hovertemplate="%{x}: %{y:,.0f} registered<extra></extra>"))
    fig.add_hline(y=n["adults"], line_color=NAVY, line_dash="dash",
                  annotation_text=f"Eligible adults (Census 2022): {n['adults'] / 1e6:.1f} m",
                  annotation_position="top left", annotation_font_color=NAVY)
    fig.update_yaxes(range=[0, n["adults"] * 1.18], title=None)
    fig.update_xaxes(type="category")
    st.markdown("**Registered voters**")
    ui.show(fig, 330)
    st.caption("The roll grew to a record size for 2026, but the gap to the dashed line is still the registration "
               "gap. We compare numbers, not rates, across years: the only population count is from 2022.")

# ------------------------------------------------------------------ explore
st.markdown("### Explore further")
c = st.columns(3)
with c[0]:
    st.page_link("views/voter_education.py", label="How do I register and vote?", icon="🗳️")
    st.page_link("views/deep_dive.py", label="Look up a municipality", icon="🏛️")
with c[1]:
    st.page_link("views/youth.py", label="Young voters", icon="👥")
    st.page_link("views/recommendations.py", label="Evidence-based recommendations", icon="💡")
with c[2]:
    st.page_link("views/participation.py", label="Trends and context", icon="📊")
    st.page_link("views/about.py", label="How this was calculated", icon="ℹ️")
