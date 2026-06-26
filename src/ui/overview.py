"""Overview page for the EIP Governance Dashboard."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.models.eip import STATUS_COLORS, EIP_STATUSES
from src.services.eip_service import get_eip_service


def show_overview():
    """Render the dashboard overview page."""
    st.title("Ethereum L1 Governance Dashboard")
    st.markdown("Track Ethereum Improvement Proposals (EIPs) through their lifecycle.")
    
    # Load data
    service = get_eip_service()
    
    with st.spinner("Loading EIP data..."):
        eips = service.get_all_eips()
        stats = service.get_statistics()
    
    # Header metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total EIPs", stats["total"])
    with col2:
        st.metric("Active EIPs", stats["active"])
    with col3:
        st.metric("Finalized", stats["finalized"])
    with col4:
        recent_count = len(service.get_recent_eips(days=30))
        st.metric("Recent (30 days)", recent_count)
    
    st.divider()
    
    # Charts row
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("EIPs by Status")
        status_data = {status: stats["by_status"].get(status, 0) for status in EIP_STATUSES}
        status_df = pd.DataFrame(
            [(k, v) for k, v in status_data.items() if v > 0],
            columns=["Status", "Count"],
        )
        
        if not status_df.empty:
            fig = px.pie(
                status_df,
                values="Count",
                names="Status",
                color="Status",
                color_discrete_map=STATUS_COLORS,
                hole=0.4,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No status data available.")
    
    with col_right:
        st.subheader("EIPs by Type")
        type_data = {k: v for k, v in stats["by_type"].items() if k}
        type_df = pd.DataFrame(
            [(k, v) for k, v in type_data.items()],
            columns=["Type", "Count"],
        )
        
        if not type_df.empty:
            fig = px.bar(
                type_df,
                x="Type",
                y="Count",
                color="Type",
                text="Count",
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No type data available.")
    
    # Category chart and recent EIPs
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Categories (Standards Track)")
        category_data = {k: v for k, v in stats["by_category"].items() if k}
        if category_data:
            category_df = pd.DataFrame(
                [(k, v) for k, v in category_data.items()],
                columns=["Category", "Count"],
            )
            fig = px.bar(
                category_df,
                x="Category",
                y="Count",
                color="Category",
                text="Count",
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No category data available.")
    
    with col2:
        st.subheader("Recent EIPs")
        recent_eips = eips[:5]  # Already sorted by number
        
        # Sort by last_updated if available
        def _recent_key(e):
            if e.last_updated:
                return e.last_updated.date()
            if e.created:
                return e.created.date() if hasattr(e.created, 'date') else e.created
            return pd.Timestamp.min.to_pydatetime().date()
        
        recent_sorted = sorted(eips, key=_recent_key, reverse=True)[:5]
        
        for eip in recent_sorted:
            with st.container():
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(
                        f"**[{eip.title}]({eip.url})**  \n"
                        f"`EIP-{eip.number}` · {eip.status} · {eip.type}"
                    )
                with col_b:
                    if eip.last_updated:
                        st.caption(f"Updated: {eip.last_updated.strftime('%Y-%m-%d')}")
                    elif eip.created:
                        st.caption(f"Created: {eip.created.strftime('%Y-%m-%d')}")
                st.markdown("---")