import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st


st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.title("Nifty 100 Analytics")

st.sidebar.title("Navigation")

st.sidebar.info(
    "Use the pages in the sidebar to explore "
    "Nifty 100 financial analytics."
)


st.header("Welcome")

st.write(
    """
    Welcome to the Nifty 100 Analytics dashboard.

    Use the sidebar to navigate between company profiles,
    screening, peer comparisons, trends, sector analysis,
    capital allocation, and annual reports.
    """
)
