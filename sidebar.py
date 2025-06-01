"""
sidebar.py
Sidebar component – navigation via button-style links.
The active page button is highlighted with the AMAS teal accent colour.
"""

import streamlit as st
from supplier.supplier_handler import get_missing_fields
from purchase_order.po_handler import get_purchase_orders_for_supplier

ACCENT = "#1ABC9C"  # AMAS accent teal
STATE_KEY = "nav_page"  # session_state key


# ───────────────────────────────────────────────────────────────
# Internal helpers
# ───────────────────────────────────────────────────────────────
def _inject_sidebar_css() -> None:
    """Highlight disabled nav buttons so the active page stands out."""
    st.markdown(
        f"""
        <style>
        button[data-testid="baseButton-secondary"][disabled] {{
            background-color: {ACCENT} !important;
            color: white !important;
            opacity: 1 !important;   /* remove grey overlay */
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _supplier_card(supplier: dict) -> None:
    """Small profile snippet at the top of the sidebar."""
    st.markdown(
        f"**{supplier.get('suppliername') or 'New Supplier'}**\n\n"
        f"ID&nbsp;`{supplier['supplierid']}`  \n"
        f"✉️ {supplier['contactemail']}",
        unsafe_allow_html=True,
    )
    if get_missing_fields(supplier):
        st.warning("Profile incomplete", icon="⚠️")


def _po_badge(supplier_id: int) -> tuple[str, str]:
    """
    Return (base_label, label_with_badge).  Adds pending-count badge if >0.
    """
    base = "📦 Purchase Orders"
    try:
        active = get_purchase_orders_for_supplier(supplier_id)
        pending = sum(1 for po in active if po["status"] == "Pending")
        if pending:
            return base, f"{base} ({pending})"
    except Exception:
        pass
    return base, base


# ───────────────────────────────────────────────────────────────
# Public API
# ───────────────────────────────────────────────────────────────
def render_sidebar(supplier: dict) -> str:
    """
    Renders the sidebar and returns the current navigation label.
    Uses button-style navigation; the active page button is disabled & teal.
    """
    _inject_sidebar_css()  # CSS must be injected AFTER page_config is set

    # Initialise nav state the first time
    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = "🏠 Home"
    current = st.session_state[STATE_KEY]

    # Build sidebar UI
    with st.sidebar:
        st.title("📌 Navigation")
        _supplier_card(supplier)
        st.divider()

        # ───────── Home ─────────
        if st.button("🏠 Home", use_container_width=True,
                     disabled=current == "🏠 Home", key="nav_home"):
            st.session_state[STATE_KEY] = "🏠 Home"
            st.rerun()

        # ───────── Purchase Orders ─────────
        base_po, po_label = _po_badge(supplier["supplierid"])
        if st.button(po_label, use_container_width=True,
                     disabled=current.startswith("📦"), key="nav_po"):
            st.session_state[STATE_KEY] = base_po
            st.rerun()

        # ───────── Supplier Dashboard ─────────
        dash = "📊 Supplier Dashboard"
        if st.button(dash, use_container_width=True,
                     disabled=current == dash, key="nav_dash"):
            st.session_state[STATE_KEY] = dash
            st.rerun()

        st.divider()
        if st.button("Log out", use_container_width=True, key="sidebar_logout"):
            st.logout()
            st.rerun()

    return st.session_state[STATE_KEY]
