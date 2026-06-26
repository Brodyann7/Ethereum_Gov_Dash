"""EIP Explorer page for browsing and filtering EIPs."""

import pandas as pd
import streamlit as st

from src.models.eip import EIP_STATUSES, EIP_TYPES, EIP_CATEGORIES, STATUS_COLORS
from src.services.eip_service import get_eip_service


def show_explorer():
    """Render the EIP Explorer page."""
    st.title("EIP Explorer")
    st.markdown("Browse, search, and filter Ethereum Improvement Proposals.")
    
    # Load data
    service = get_eip_service()
    
    with st.spinner("Loading EIP data..."):
        all_eips = service.get_all_eips()
    
    # Sidebar filters
    with st.sidebar:
        st.header("Filters")
        
        search_query = st.text_input("Search", placeholder="Title, description, or author")
        
        status_filter = st.multiselect(
            "Status",
            options=EIP_STATUSES,
            default=[],
        )
        
        type_filter = st.multiselect(
            "Type",
            options=EIP_TYPES,
            default=[],
        )
        
        category_filter = st.multiselect(
            "Category",
            options=EIP_CATEGORIES,
            default=[],
        )
        
        min_created = st.date_input("Created after", value=None)
        max_created = st.date_input("Created before", value=None)
        
        sort_by = st.selectbox(
            "Sort by",
            options=["Number", "Title", "Created", "Status"],
            index=0,
        )
        
        sort_ascending = st.checkbox("Ascending", value=True)
    
    # Apply filters
    filtered_eips = all_eips
    
    if search_query:
        filtered_eips = service.search_eips(search_query)
    
    if status_filter:
        filtered_eips = [eip for eip in filtered_eips if eip.status in status_filter]
    
    if type_filter:
        filtered_eips = [eip for eip in filtered_eips if eip.type in type_filter]
    
    if category_filter:
        filtered_eips = [eip for eip in filtered_eips if eip.category in category_filter]
    
    if min_created:
        filtered_eips = [
            eip for eip in filtered_eips
            if eip.created and eip.created >= min_created
        ]
    
    if max_created:
        filtered_eips = [
            eip for eip in filtered_eips
            if eip.created and eip.created <= max_created
        ]
    
    # Sort
    sort_map = {
        "Number": lambda e: e.number,
        "Title": lambda e: e.title.lower(),
        "Created": lambda e: e.created or pd.Timestamp.min.to_pydatetime().date(),
        "Status": lambda e: e.status_order,
    }
    filtered_eips = sorted(filtered_eips, key=sort_map[sort_by], reverse=not sort_ascending)
    
    # Results summary
    st.markdown(f"**{len(filtered_eips)}** EIPs found")
    
    # Display as table
    if filtered_eips:
        df = service.to_dataframe(filtered_eips)
        
        # Select and format columns
        display_df = pd.DataFrame({
            "EIP": df["number"],
            "Title": df.apply(
                lambda row: f"<a href='?nav=detail&eip={row['number']}' target='_self'>{row['title']}</a>",
                axis=1,
            ),
            "Status": df["status"],
            "Type": df["type"],
            "Category": df["category"].fillna("-"),
            "Created": df["created"].apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else "-"),
            "Authors": df["authors"].apply(lambda x: ", ".join(x[:3]) + ("..." if len(x) > 3 else ""))
        })
        
        st.markdown(
            display_df.to_html(
                index=False,
                escape=False,
                classes=["eip-table"],
                table_id="eip-table",
            ),
            unsafe_allow_html=True,
        )
        
        st.caption("Click a title to open the EIP Detail page.")
        
        # Detail expanders for selected status
        st.subheader("Quick View")
        selected = st.selectbox(
            "Select an EIP to view details",
            options=[f"EIP-{eip.number}: {eip.title}" for eip in filtered_eips[:50]],
            index=0,
        )
        
        if selected:
            eip_number = int(selected.split(":")[0].replace("EIP-", ""))
            eip = service.get_eip(eip_number)
            if eip:
                _show_eip_card(eip)
    else:
        st.info("No EIPs match the selected filters.")


def _show_eip_card(eip):
    """Display a compact EIP detail card."""
    status_color = STATUS_COLORS.get(eip.status, "#6b7280")
    
    st.markdown(
        f"<h3><a href='{eip.url}'>EIP-{eip.number}: {eip.title}</a></h3>",
        unsafe_allow_html=True,
    )
    
    cols = st.columns(3)
    with cols[0]:
        st.markdown(f"**Status:** <span style='color:{status_color}'>{eip.status}</span>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown(f"**Type:** {eip.type}")
    with cols[2]:
        st.markdown(f"**Category:** {eip.category or 'N/A'}")
    
    st.markdown(f"**Authors:** {eip.short_authors}")
    st.markdown(f"**Created:** {eip.created.strftime('%Y-%m-%d') if eip.created else 'N/A'}")
    
    if eip.description:
        st.markdown(f"**Description:** {eip.description}")
    
    if eip.discussions_to:
        st.markdown(f"[Discuss on Ethereum Magicians]({eip.discussions_to})")