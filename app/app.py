"""The Democratic Participation Dashboard - entry point and navigation.

Overview is the landing page; every other section is in the menu (☰, top left).
Data: app/artifacts/ (written by notebooks/09_dashboard_prep.ipynb). Run: streamlit run app/app.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st  # noqa: E402

st.set_page_config(page_title="The Democratic Participation Dashboard", page_icon="🗳️", layout="wide",
                   initial_sidebar_state="collapsed")

from lib import data, ui  # noqa: E402

ui.css()
if not data.has_data():
    st.error("app/artifacts/dashboard.csv is missing. Run notebooks/09_dashboard_prep.ipynb first.")
    st.stop()

pages = [
    st.Page("views/overview.py", title="Overview", icon="🏠", default=True),
    st.Page("views/deep_dive.py", title="Municipal Deep Dive", icon="🏛️"),
    st.Page("views/youth.py", title="Youth Lens", icon="👥"),
    st.Page("views/recommendations.py", title="Recommendations", icon="💡"),
    st.Page("views/voter_education.py", title="Voter Education", icon="🗳️"),
    st.Page("views/participation.py", title="Electoral Participation", icon="📊"),
    st.Page("views/about.py", title="About / Methodology", icon="ℹ️"),
]
nav = st.navigation(pages, position="sidebar")
st.sidebar.caption("The Democratic Participation Dashboard · Team UL · DIRISA Student Datathon Challenge 2026")
nav.run()
