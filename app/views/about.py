"""ℹ️ About / Methodology - how everything was calculated, and what it cannot show."""
import streamlit as st

from lib import ui
from lib.data import AMBER, BLUE, CRIMSON, MODEL_ACCURACY, NAVY, NOT_A_CAUSE, YOUTH_NOTE, load

d, geo = load()
a = MODEL_ACCURACY

st.title("ℹ️ About / Methodology")

st.markdown("### The Democratic Funnel")
ui.funnel_steps([("Eligible population", "E", NAVY), ("Registered voters", "R", BLUE),
                 ("Voters who turn out", "V", AMBER), ("Participation", "V ÷ E", CRIMSON)])
st.markdown("""
- **Registration rate** = R ÷ E — how full the voters' roll is. **Registration gap** = 1 − registration rate.
- **Turnout rate** = V ÷ R — of those registered, how many voted. **Turnout gap** = 1 − turnout rate.
- **Participation** = V ÷ E = registration rate × turnout rate. **Participation shortfall** = 1 − participation.
- **Youth registration rate** = registered voters aged 18–29 ÷ citizens aged 18–29.
- **Typical municipality** = the median of all 213 municipalities.
""")

st.markdown("### How municipalities are compared")
st.markdown("""
In plain words: each municipality is compared with the typical municipality on registration and on turnout, and
placed in one of four groups — **low registration**, **low turnout**, **both low**, or **healthy** (at or above
typical on both).

Technically: registration gap to typical = ln(r ÷ median r), turnout gap to typical = ln(t ÷ median t). The two
add up exactly to the municipality's participation gap to typical, ln(p ÷ median p). Registration uses the 2026
roll; turnout uses the model's 2026 outlook. "Registrations needed" and "extra voters needed" turn the gaps into
people: how many more would bring the municipality up to the typical level.
""")

st.markdown("### The 2026 turnout outlook (the model)")
st.markdown(f"""
In plain words: **2026 turnout = 2021 turnout + a national recovery from the 2021 drop + an adjustment for each
municipality.** The central scenario assumes half of the 2016 → 2021 drop is recovered. The adjustment comes from
a **hierarchical (mixed-effects) regression** — municipalities grouped within provinces — using past turnout,
registration, neighbours' turnout, population density, household services and education.

**How accurate is it?** The model was trained on the 2011 → 2016 change and tested on 2016 → 2021, for all 213
municipalities:
- average error **{a['mae']:.2f} turnout points** (95% confidence interval {a['mae_ci'][0]:.2f}–{a['mae_ci'][1]:.2f});
- **{a['within5']:.0%}** of predictions within 5 points, **{a['within3']:.0%}** within 3 points;
- it explains about half the variation in turnout between municipalities (R² = {a['r2']:.2f}); rank correlation
  {a['rank_corr']:.2f};
- a simple baseline — last turnout plus the national change — did slightly better
  ({a['baseline_mae']:.2f} points, CI {a['baseline_ci'][0]:.2f}–{a['baseline_ci'][1]:.2f}), because COVID changed which
  municipalities fell most. Predicting "no change" was far worse ({a['no_change_mae']:.2f} points).

These errors assume the national change is known. For 2026 it is not, so every outlook is shown with a range.
""")

st.markdown("### Data sources")
st.markdown("""
| Source | Year | Level | Used for | Limitations |
|---|---|---|---|---|
| IEC municipal election results | 2011, 2016, 2021 | voting district → municipality | registered voters, votes cast, turnout (ward ballot) | 2011 moved onto today's boundaries |
| IEC voter registration statistics | September 2026 | municipality, by age | the 2026 roll, ages 18–29 | a snapshot; changes until the roll closes |
| Stats SA Census 2022 | 2022 | municipality | citizens 18+ (eligible population), services, education | undercount; small samples in small municipalities |
| Municipal Demarcation Board | 2026 boundaries | municipality | map, area, neighbours | — |
| IEC municipal atlas | 2011, 2016 | municipality | moving 2011 results onto today's boundaries | area shares approximate population shares |
""")

st.markdown("### Important limitations")
ui.panel(f"""
<ul style='margin:0;padding-left:1.1rem'>
<li><b>{NOT_A_CAUSE}</b></li>
<li><b>Population estimates</b> come from Census 2022 only, so registration <i>rates</i> are compared for 2021 and
2026, not earlier years. The 2026 rate is slightly overstated because the population has grown since 2022.</li>
<li>In <b>{int(d['Census caution'].sum())}</b> small municipalities more people are registered than the Census
counted adults. Their rates are flagged and counted as 100%.</li>
<li><b>{YOUTH_NOTE}</b></li>
<li><b>Boundaries changed in 2016</b>; 2011 results were apportioned by area.</li>
<li><b>Turnout does not explain motivation.</b> National and municipal elections are not directly comparable.</li>
<li><b>Small sample:</b> 213 municipalities and two past changes in turnout.</li>
</ul>""", warn=True)

st.caption("Team UL, University of Limpopo · DIRISA Student Datathon Challenge 2026 · Code and notebooks: GitHub "
           "repository democratic-funnel.")
