"""EIP Detail page showing full information for a single EIP."""

import streamlit as st

from src.models.eip import STATUS_COLORS
from src.services.eip_service import get_eip_service


def show_detail():
    """Render the EIP Detail page."""
    st.title("EIP Detail")
    
    # EIP number input (support navigation from query params)
    default_eip = int(st.session_state.get("nav_eip", 1))
    eip_number = st.number_input(
        "Enter EIP Number",
        min_value=1,
        value=default_eip,
        step=1,
    )
    
    service = get_eip_service()
    
    with st.spinner("Loading EIP details..."):
        eip = service.get_eip(int(eip_number))
    
    if not eip:
        st.error(f"EIP-{eip_number} not found.")
        return
    
    # Fetch discussion metrics in background
    with st.spinner("Loading discussion metrics..."):
        discussion = service.get_discussion_metrics(eip)
    
    # Header
    status_color = STATUS_COLORS.get(eip.status, "#6b7280")
    
    st.markdown(
        f"<h1><a href='{eip.url}'>EIP-{eip.number}: {eip.title}</a></h1>",
        unsafe_allow_html=True,
    )
    
    st.markdown(
        f"**Status:** <span style='color:{status_color};font-size:1.2em;font-weight:600'>{eip.status}</span>  ·  "
        f"**Type:** {eip.type}  ·  "
        f"**Category:** {eip.category or 'N/A'}",
        unsafe_allow_html=True,
    )
    
    st.divider()
    
    # Metadata
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Metadata")
        st.markdown(f"**Authors:** {', '.join(eip.authors)}")
        st.markdown(f"**Created:** {eip.created.strftime('%Y-%m-%d') if eip.created else 'N/A'}")
        st.markdown(f"**Last Updated:** {eip.last_updated.strftime('%Y-%m-%d') if eip.last_updated else 'N/A'}")
        
        if eip.last_call_deadline:
            st.markdown(f"**Last Call Deadline:** {eip.last_call_deadline.strftime('%Y-%m-%d')}")
        
        if eip.requires:
            st.markdown("**Requires:** " + ", ".join(f"[EIP-{n}](#)" for n in eip.requires))
    
    with col2:
        st.subheader("Links")
        st.markdown(f"[View on GitHub]({eip.url})")
        if eip.discussions_to:
            st.markdown(f"[Discuss on Ethereum Magicians]({eip.discussions_to})")
    
    st.divider()
    
    # Description
    st.subheader("Description")
    st.markdown(eip.description or "No description available.")
    
    st.divider()
    
    # Discussion Metrics
    st.subheader("Community Discussion")
    
    if discussion:
        cols = st.columns(4)
        with cols[0]:
            st.metric("Posts", discussion.posts_count)
        with cols[1]:
            st.metric("Views", discussion.views)
        with cols[2]:
            st.metric("Likes", discussion.like_count)
        with cols[3]:
            st.metric("Participants", len(discussion.participants))
        
        if discussion.last_posted_at:
            st.caption(f"Last activity: {discussion.last_posted_at.strftime('%Y-%m-%d %H:%M')}")
        
        if discussion.participants:
            st.markdown(f"**Top participants:** {', '.join(discussion.participants[:10])}")
    else:
        st.info("No discussion metrics available for this EIP.")
    
    # Status progression
    st.divider()
    st.subheader("Lifecycle")
    
    status_order = ["Draft", "Review", "Last Call", "Final"]
    if eip.status in ["Living", "Stagnant", "Withdrawn"]:
        status_order = [eip.status]
    
    current_step = status_order.index(eip.status) if eip.status in status_order else -1
    
    progress_html = "<div style='display:flex;align-items:center;gap:8px;margin:20px 0;'>"
    for i, status in enumerate(status_order):
        if i <= current_step:
            color = STATUS_COLORS.get(status, "#10b981")
            progress_html += (
                f"<div style='background:{color};color:white;padding:8px 16px;"
                f"border-radius:20px;font-weight:600;'>{status}</div>"
            )
        else:
            progress_html += (
                f"<div style='background:#e5e7eb;color:#6b7280;padding:8px 16px;"
                f"border-radius:20px;'>{status}</div>"
            )
        if i < len(status_order) - 1:
            progress_html += "<div style='color:#9ca3af;'>→</div>"
    
    progress_html += "</div>"
    st.markdown(progress_html, unsafe_allow_html=True)