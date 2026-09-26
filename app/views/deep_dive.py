"""🏛️ Municipal Deep Dive - one municipality in detail."""
import pandas as pd
import streamlit as st

from lib import ui
from lib.data import (AMBER, BLUE, MODEL_ACCURACY, NAVY, NOT_A_CAUSE, YOUTH_NOTE, load, national, num, pct)

d, geo = load()
n = national(d)
names = dict(zip(d["Code"], d["Municipality"] + " (" + d["Province"] + ")"))
code_of = {v: k for k, v in names.items()}
labels = sorted(code_of)

st.title("🏛️ Municipal Deep Dive")
chosen = names.get(st.session_state.get("muni_code"))
label = st.selectbox("Search for a municipality", labels, index=labels.index(chosen) if chosen else None,
                     placeholder="Type a name, e.g. Polokwane, eThekwini, Mbombela ...")
if label is None:
    st.info("Start typing a municipality's name above, or click a municipality on the Overview map.")
    st.stop()
code = code_of[label]
st.session_state["muni_code"] = code
r = d[d["Code"] == code].iloc[0]
caution = bool(r["Census caution"])
typ_reg21 = d["Registration rate 2021"].clip(upper=1).median()
typ_part21 = d["Participation 2021"].clip(upper=1).median()

# ------------------------------------------------------------------ profile
st.markdown(f"## {r['Municipality']}")
st.caption(f"{r['Type']} municipality · {r['Province']} · code {r['Code']}")
k = st.columns(4)
ui.kpi(k[0], "Eligible adults", num(r["Adults who may vote"]), "citizens aged 18+", "Census 2022 · people")
ui.kpi(k[1], "Registered voters", num(r["Registered 2026"]),
       "over 100% of the Census count — see note below" if caution
       else f"registration rate {pct(r['Registration rate 2026'])} (typical {pct(r['Typical registration rate'])})",
       "2026 roll · people", BLUE)
ui.kpi(k[2], "Turnout rate", pct(r["Turnout 2021"], 1),
       f"of registered voters voted (national {pct(n['turnout_2021'], 1)})", "2021 election · % of registered",
       "#8a5d00")
ui.kpi(k[3], "Participation", "unreliable*" if caution else f"{r['Participation 2021'] * 100:.0f} of 100",
       "eligible adults who voted", "2021 · per 100 adults", NAVY)
st.markdown(f"Group: {ui.pill(r['Problem group'])} &nbsp; compared with a typical (median) municipality, using the "
            "2026 roll and the model's 2026 turnout outlook.", unsafe_allow_html=True)

# ------------------------------------------------------------------ funnel
left, right = st.columns(2)
with left:
    st.markdown("#### The Democratic Funnel, 2021")
    reg100 = min(100 * r["Registration rate 2021"], 100)
    vote100 = min(100 * r["Participation 2021"], 100)
    fig = ui.funnel_bars([100, reg100, vote100], ["Eligible adults", "Registered", "Turned out"],
                         [NAVY, BLUE, AMBER],
                         typical=[("Registered", 100 * typ_reg21), ("Turned out", 100 * typ_part21)])
    ui.show(fig, 270)
    lost_reg, lost_turn = 100 - reg100, reg100 - vote100
    bigger = "before registering" if lost_reg > lost_turn else "after registering (at the ballot box)"
    st.markdown(f"Out of every 100 adults, about **{lost_reg:.0f}** were lost before registering and **{lost_turn:.0f}** "
                f"after registering. **The largest loss here is {bigger}.**")
    st.caption("Bars: this municipality. Navy lines: a typical municipality.")

with right:
    st.markdown("#### Turnout over time")
    years = [2011, 2016, 2021]
    pred = None
    if pd.notna(r["Predicted turnout 2026"]):
        pred = (r["Predicted turnout 2026"], r["Predicted turnout 2026 (low)"], r["Predicted turnout 2026 (high)"],
                AMBER)
    fig = ui.trend(years, [("National", [n[f"turnout_{y}"] for y in years], NAVY, "dot"),
                           (r["Municipality"], [r[f"Turnout {y}"] for y in years], AMBER, "solid")],
                   predicted=pred)
    ui.show(fig, 300)
    reg = " → ".join(f"{y}: {num(r[f'Registered {y}'])}" for y in years) + f" → 2026: {num(r['Registered 2026'])}"
    st.caption(f"Registered voters — {reg}. 2011 figures are on today's boundaries.")

# ------------------------------------------------------------------ youth + outlook
left, right = st.columns(2)
with left:
    st.markdown("#### Youth indicators (ages 18–29)")
    yk = st.columns(2)
    ui.kpi(yk[0], "Youth registration rate", pct(r["Youth registration rate"]),
           f"all adults here: {'over 100%*' if caution else pct(r['Registration rate 2026'])}", "2026 roll", BLUE)
    ui.kpi(yk[1], "Young adults not registered", num(r["Young adults not registered"]),
           f"of {num(r['Young adults who may vote'])} aged 18–29", "2026 roll · people", BLUE)
    st.write("")
    ui.panel("<b>Youth turnout: not available.</b> " + YOUTH_NOTE)

with right:
    st.markdown("#### Model outlook for 2026")
    if pred:
        st.markdown(f"Predicted turnout: **{pct(pred[0], 1)}**, likely range **{pct(pred[1])} – {pct(pred[2])}** "
                    "(central scenario: turnout recovers half of the 2021 drop).")
        bits = []
        if isinstance(r["Main factor pulling turnout down"], str):
            bits.append(f"pulling it down: **{r['Main factor pulling turnout down']}**")
        if isinstance(r["Main factor holding turnout up"], str):
            bits.append(f"holding it up: **{r['Main factor holding turnout up']}**")
        if bits:
            st.markdown("Linked in the model with " + "; ".join(bits) + ".")
        if str(r["Worse than expected in 2021"]) == "True":
            ui.panel("<b>Fell more than expected in 2021.</b> Turnout here dropped much further than the model "
                     "predicted — something local that the data cannot see.")
        st.caption(f"Accuracy: tested on 2021, predictions were off by {MODEL_ACCURACY['mae']:.1f} points on average "
                   f"and within 5 points for {MODEL_ACCURACY['within5']:.0%} of municipalities. {NOT_A_CAUSE}")
    else:
        st.markdown("The model's 2026 outlook is not available yet.")

if caution:
    ui.panel("*<b>Census caution.</b> More people are registered here than the Census 2022 counted adults. The "
             "Census sample is small in this municipality, so its registration rate and participation are not "
             "reliable.", warn=True)
