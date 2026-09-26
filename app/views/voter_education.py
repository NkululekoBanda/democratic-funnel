"""🗳️ Voter Education - how to take part. Information only; no political persuasion."""
import streamlit as st

from lib import ui

st.title("🗳️ Voter Education")
st.markdown("### How do I take part in the local government elections?")
st.markdown("South Africa's next local government elections are on **4 November 2026**. Here is how to make sure "
            "you can vote. Always check the **Electoral Commission (IEC)** for the latest official information.")

IEC = "https://www.elections.org.za"
PORTAL = "https://registertovote.elections.org.za"
FINDER = "https://maps.elections.org.za/vsfinder/"

c = st.columns(2)
ui.card(c[0], "✅", "Am I registered?",
        f"<p>SMS your ID number to <b>32810</b> (costs R1), or check online on the "
        f"<a href='{PORTAL}' target='_blank'>IEC voter portal</a>. You will see whether you are registered and "
        "where your voting station is.</p>")
ui.card(c[1], "📍", "Where do I vote?",
        f"<p>You vote at the voting station where you are registered. Find it with the "
        f"<a href='{FINDER}' target='_blank'>IEC voting station finder</a>, the official IEC app, or by SMS to "
        "<b>32810</b>.</p>")
st.write("")
c = st.columns(2)
ui.card(c[0], "📝", "How do I register?",
        f"<ol><li>You must be a <b>South African citizen</b> aged <b>16 or older</b> (you can vote from 18).</li>"
        f"<li>Register <b>online</b> at <a href='{PORTAL}' target='_blank'>registertovote.elections.org.za</a>, "
        "at your <b>local IEC office</b>, at your voting station during a <b>registration weekend</b>, or at an IEC "
        "registration event.</li><li>Nobody can register for you — you must do it yourself.</li>"
        "<li>Registration closes when the election is proclaimed, so do not wait.</li></ol>")
ui.card(c[1], "🪪", "What do I need?",
        "<p>One of these original documents from Home Affairs:</p><ul><li>green, barcoded ID book</li>"
        "<li>smart ID card</li><li>valid Temporary Identity Certificate</li></ul>"
        "<p>No other identification is accepted. Bring the same document when you vote.</p>")
st.write("")
c = st.columns(2)
ui.card(c[0], "🏠", "What if I have moved?",
        f"<p>You must <b>update your registration</b> when you move to a new address, so that you vote in the ward "
        f"where you now live. You can do this <a href='{PORTAL}' target='_blank'>online</a> or at your local IEC "
        "office before registration closes.</p>")
ui.card(c[1], "♿", "What are special votes?",
        f"<p>If you cannot vote at your voting station on election day, you can <b>apply for a special vote</b>. "
        "Voters who are physically infirm, disabled or pregnant can ask for a <b>home visit</b>; others vote at "
        f"their voting station before election day. You must apply within the period set by the IEC — see "
        f"<a href='{IEC}' target='_blank'>elections.org.za</a>.</p>")
st.write("")

st.markdown("### Why do local elections matter?")
st.markdown("""
Your **municipal council** makes decisions that affect daily life. Municipalities are responsible for services such as:

- **water** and **sanitation**
- **electricity** distribution in many areas
- **refuse removal**
- **local roads**, streetlights and storm-water drains
- local **planning**, building approvals, parks and community facilities

In local government elections you vote for a **ward councillor** (the person who represents your ward) and for a
**party** on the proportional ballot; outside the metros there is also a party ballot for the district council.
These votes decide who sits on the council and who governs your municipality for the next five years.
""")
ui.panel("This page gives voter information only. It does not recommend any party or candidate. For official "
         f"information, visit <a href='{IEC}' target='_blank'>elections.org.za</a>.")
