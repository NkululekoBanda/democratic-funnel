"""👥 Youth Lens - where young adults face the largest registration gaps."""
import plotly.graph_objects as go
import streamlit as st

from lib import ui
from lib.data import BLUE, BLUE_LIGHT, INK2, YOUTH_NOTE, by_province, load, millions, national, num, pct

d, geo = load()
n = national(d)

st.title("👥 Youth Lens")
st.markdown("**Where do young people (aged 18–29) face the largest gaps in electoral participation?** "
            "The data covers **registration** for the 2026 roll.")

k = st.columns(4)
ui.kpi(k[0], "Youth registration rate", pct(n["youth_reg_rate"]),
       f"of adults aged 18–29 are registered, compared with {pct(n['older_reg_rate'])} of adults aged 30+.",
       "2026 roll · % of age group", BLUE)
ui.kpi(k[1], "Youth registration gap", millions(n["youth_not_registered"]),
       f"adults aged 18–29 are not registered ({pct(1 - n['youth_reg_rate'])} of the age group).",
       "2026 roll · people", BLUE)
ui.kpi(k[2], "Share of the registration gap", pct(n["youth_share_of_missing"]),
       f"of everyone missing from the roll is aged 18–29, although this age group is "
       f"{pct(n['youth_adults'] / n['adults'])} of eligible adults.", "2026 roll · % of unregistered adults", BLUE)
ui.kpi(k[3], "Youth turnout", "Not published", "The IEC does not publish turnout by age for municipalities.",
       "no data available", INK2)

below = int((d["Youth registration rate"] < d["Registration rate 2026"]).sum())
ui.panel(f"<b>What the data shows.</b> In <b>{below} of {len(d)}</b> municipalities, young adults are registered at a "
         "lower rate than adults overall. This is a registration difference; it does not tell us how young people "
         "vote once registered, or why fewer are registered.")

# ------------------------------------------------------------------ map
st.markdown("### Youth registration gap by municipality")
if geo is not None:
    ui.gap_map(d, geo, "Youth registration gap (2026)", key="youth_map")
    st.caption("Share of adults aged 18–29 not on the 2026 roll. Darker = larger gap. Hover or tap for details.")

# ------------------------------------------------------------------ provinces
st.markdown("### Provinces: young adults compared with all adults")
bp = by_province(d).sort_values("Youth registration rate 2026")
fig = go.Figure()
fig.add_trace(go.Bar(y=bp["Province"], x=bp["Registration rate 2026"], orientation="h", name="All adults",
                     marker_color=BLUE_LIGHT, text=[pct(v) for v in bp["Registration rate 2026"]],
                     textposition="outside", hovertemplate="%{y}, all adults: %{x:.1%}<extra></extra>"))
fig.add_trace(go.Bar(y=bp["Province"], x=bp["Youth registration rate 2026"], orientation="h", name="Aged 18–29",
                     marker_color=BLUE, text=[pct(v) for v in bp["Youth registration rate 2026"]],
                     textposition="outside", hovertemplate="%{y}, aged 18–29: %{x:.1%}<extra></extra>"))
fig.update_layout(barmode="group", bargap=0.25, legend_traceorder="reversed")
fig.update_xaxes(tickformat=".0%", range=[0, 1.1], title="Registration rate, 2026")
ui.show(fig, 520)
st.caption("In every province, young adults are registered at a lower rate than adults overall.")

# ------------------------------------------------------------------ metros vs local
st.markdown("### Metros compared with local municipalities")
m = d.groupby("Type")[["Youth registration rate", "Registration rate 2026"]].median()
c = st.columns(2)
for col, t in zip(c, ["Metro", "Local"]):
    ui.kpi(col, f"{t} municipalities (typical)", pct(m.loc[t, "Youth registration rate"]),
           f"youth registration rate, against {pct(m.loc[t, 'Registration rate 2026'])} for all adults",
           "2026 roll · median municipality", BLUE)
st.write("")

# ------------------------------------------------------------------ comparison table
st.markdown("### Compare municipalities")
prov = st.selectbox("Province", ["All provinces"] + sorted(d["Province"].unique()), key="youth_prov")
t = d if prov == "All provinces" else d[d["Province"] == prov]
t = t[["Municipality", "Province", "Youth registration rate", "Registration rate 2026", "Young adults not registered",
       "Young adults who may vote"]].sort_values("Municipality").copy()
for col in ["Youth registration rate", "Registration rate 2026"]:
    t[col] = (t[col].clip(upper=1) * 100).round(1)
st.dataframe(t, hide_index=True, use_container_width=True, height=380, column_config={
    "Youth registration rate": st.column_config.NumberColumn("Youth registration rate", format="%.0f%%"),
    "Registration rate 2026": st.column_config.NumberColumn("All adults", format="%.0f%%"),
    "Young adults not registered": st.column_config.NumberColumn(format="%d"),
    "Young adults who may vote": st.column_config.NumberColumn(format="%d")})
st.caption("Click a column heading to sort. Rates above 100% (Census caution) are shown as 100%.")

st.markdown("### Historical trends")
ui.panel("<b>Not available.</b> The IEC publishes registration by age for the current roll only, so youth "
         "registration cannot be compared with 2011, 2016 or 2021. " + YOUTH_NOTE)
