"""Main Streamlit application for Ethereum L1 Governance Dashboard."""

import streamlit as st

from src.ui.overview import show_overview
from src.ui.explorer import show_explorer
from src.ui.detail import show_detail
from src.ui.timeline import show_timeline

# Page configuration
st.set_page_config(
    page_title="Ethereum L1 Governance Dashboard",
    page_icon="⛓️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main():
    """Main application entry point."""
    # Read query params for cross-page links
    query_params = st.query_params
    
    if query_params.get("nav") == "detail":
        try:
            eip_num = int(query_params.get("eip", 1))
            st.session_state.nav_eip = eip_num
            st.session_state.nav_page = "EIP Detail"
        except (ValueError, TypeError):
            st.session_state.nav_page = "EIP Detail"
            st.session_state.nav_eip = 1
    elif "nav_page" not in st.session_state:
        st.session_state.nav_page = "Overview"
        st.session_state.nav_eip = 1

    pages = ["Overview", "EIP Explorer", "EIP Detail", "Timeline"]
    
    with st.sidebar:
        st.title("⛓️ EIP Dashboard")
        st.markdown("Ethereum L1 Governance Tracker")
        st.divider()
        
        page = st.radio(
            "Navigation",
            options=pages,
            index=pages.index(st.session_state.nav_page),
            key="nav_radio",
        )
        
        st.divider()
        st.markdown("### Data Sources")
        st.markdown("- [ethereum/EIPs](https://github.com/ethereum/EIPs)")
        st.markdown("- [Ethereum Magicians](https://ethereum-magicians.org)")
        
        st.markdown("### About")
        st.markdown(
            "This dashboard tracks Ethereum Improvement Proposals (EIPs) "
            "through their lifecycle stages and surfaces community discussion activity."
        )
    
    # Route to the selected page
    if page == "Overview":
        show_overview()
    elif page == "EIP Explorer":
        show_explorer()
    elif page == "EIP Detail":
        show_detail()
    elif page == "Timeline":
        show_timeline()


if __name__ == "__main__":
    main()