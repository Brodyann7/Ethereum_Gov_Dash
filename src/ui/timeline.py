"""Activity timeline page showing EIP creation over time."""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.models.eip import STATUS_COLORS, EIP_STATUSES, EIP_CATEGORIES
from src.services.eip_service import get_eip_service


def show_timeline():
    """Render the activity timeline page."""
    st.title("Activity Timeline")
    st.markdown("Visualize EIP creation and activity over time.")
    
    service = get_eip_service()
    
    with st.spinner("Loading timeline data..."):
        eips = service.get_all_eips()
        timeline_df = service.get_timeline_data()
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            options=EIP_STATUSES,
            default=[],
        )
    with col2:
        category_filter = st.multiselect(
            "Filter by Category",
            options=EIP_CATEGORIES,
            default=[],
        )
    
    # Apply filters
    filtered_eips = eips
    if status_filter:
        filtered_eips = [eip for eip in filtered_eips if eip.status in status_filter]
    if category_filter:
        filtered_eips = [eip for eip in filtered_eips if eip.category in category_filter]
    
    # Recalculate timeline with filters
    timeline_data = {}
    for eip in filtered_eips:
        if eip.created:
            date_key = eip.created
            timeline_data[date_key] = timeline_data.get(date_key, 0) + 1
    
    filtered_timeline_df = pd.DataFrame([
        {"date": date, "count": count}
        for date, count in sorted(timeline_data.items())
    ])
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total EIPs", len(filtered_eips))
    with col2:
        earliest = min((eip.created for eip in filtered_eips if eip.created), default=None)
        st.metric("Earliest", earliest.strftime("%Y-%m-%d") if earliest else "N/A")
    with col3:
        latest = max((eip.created for eip in filtered_eips if eip.created), default=None)
        st.metric("Latest", latest.strftime("%Y-%m-%d") if latest else "N/A")
    
    st.divider()
    
    # Timeline chart
    st.subheader("EIP Creation Over Time")
    
    if not filtered_timeline_df.empty:
        # Cumulative
        filtered_timeline_df["cumulative"] = filtered_timeline_df["count"].cumsum()
        
        fig = px.area(
            filtered_timeline_df,
            x="date",
            y="cumulative",
            title="Cumulative EIP Creations",
            labels={"date": "Date", "cumulative": "Total EIPs"},
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Cumulative EIPs",
            showlegend=False,
        )
        st.plotly_chart(fig, width="stretch")
        
        # Monthly bar chart
        filtered_timeline_df["month"] = pd.to_datetime(filtered_timeline_df["date"]).dt.to_period("M")
        monthly = filtered_timeline_df.groupby("month")["count"].sum().reset_index()
        monthly["month_str"] = monthly["month"].astype(str)
        
        fig2 = px.bar(
            monthly,
            x="month_str",
            y="count",
            title="EIPs Created Per Month",
            labels={"month_str": "Month", "count": "New EIPs"},
        )
        fig2.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig2, width="stretch")
    else:
        st.info("No timeline data available for the selected filters.")
    
    st.divider()
    
    # Recent activity table
    st.subheader("Activity Feed")
    
    def _activity_key(e):
        if e.last_updated:
            return e.last_updated.date()
        return e.created or pd.Timestamp.min.to_pydatetime().date()
    
    activity_eips = sorted(filtered_eips, key=_activity_key, reverse=True)[:20]
    
    for eip in activity_eips:
        status_color = STATUS_COLORS.get(eip.status, "#6b7280")
        date_str = (
            eip.last_updated.strftime("%Y-%m-%d") if eip.last_updated
            else (eip.created.strftime("%Y-%m-%d") if eip.created else "N/A")
        )
        
        st.markdown(
            f"**[{eip.title}]({eip.url})** — "
            f"<span style='color:{status_color};font-weight:600'>{eip.status}</span> — "
            f"{date_str}",
            unsafe_allow_html=True,
        )
        st.caption(f"EIP-{eip.number} · {eip.type} · {eip.category or 'No category'}")
        st.markdown("---")