"""💡 Recommendations - evidence-linked responses, organised by the type of gap (no ranking)."""
import streamlit as st

from lib import ui
from lib.data import NOT_A_CAUSE, load, millions, national, num, pct

d, geo = load()
n = national(d)

st.title("💡 Recommendations")
st.markdown("Each recommendation is tied to a finding in the data. For every one we separate **what the data shows**, "
            "**the evidence**, **a possible response**, and **what further evidence is needed**. Municipalities are "
            "not ranked or scored: the data shows where a gap exists, not why it exists or what matters most locally.")

low_reg = d["Problem group"].isin(["Low registration", "Both low"])
low_turn = d["Problem group"].isin(["Low turnout", "Both low"])
youth_below = int((d["Youth registration rate"] < d["Registration rate 2026"]).sum())

ui.recommendation(
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

ui.recommendation(
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

ui.recommendation(
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

ui.recommendation(
    "4 · Data and research",
    f"Some questions cannot be answered with the available data. In <b>{int(d['Census caution'].sum())}</b> small "
    "municipalities more people are registered than the Census counted adults.",
    "Population figures come only from Census 2022; youth turnout is not published; 2011 results had to be moved "
    "onto today's boundaries; the model can predict turnout only within about ±5 points for three in four "
    "municipalities.",
    "Publish turnout by age group at municipal level; publish registration by age for past elections; update "
    "population estimates between censuses; combine these numbers with community-level research.",
    "Better data would show whether the gaps found here persist, and why they occur.")

ui.panel("<b>What this page does not claim.</b> " + NOT_A_CAUSE + " The responses above are options to consider, "
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
