"""
sidebar.py
Sidebar component – button navigation with a modern blue highlight on
the active page.
"""

import streamlit as st
from supplier.supplier_handler import get_missing_fields
from purchase_order.po_handler import get_purchase_orders_for_supplier

ACCENT_BLUE = "#0d6efd"          # Bootstrap-like primary blue
ACCENT_BLUE_2 = "#1a74ff"        # lighter blue for gradient
STATE_KEY = "nav_page"           # session_state key


# ───────────────────────────────────────────────────────────────
# Internal helpers
# ───────────────────────────────────────────────────────────────
def _inject_sidebar_css() -> None:
    """Inject CSS that re-skins disabled nav buttons as a blue highlight."""
    st.markdown(
        f"""
        <style>
        button[data-testid="baseButton-secondary"][disabled] {{
            background: linear-gradient(90deg, {ACCENT_BLUE} 0%, {ACCENT_BLUE_2} 100%) !important;
            color: white !important;
            opacity: 1 !important;          /* remove grey overlay       */
            box-shadow: inset 0 0 0 2px rgba(255,255,255,0.15); /* subtle inner border */
            cursor: default !important;     /* pointer stays arrow       */
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _supplier_card(supplier: dict) -> None:
    st.markdown(
        f"**{supplier.get('suppliername') or 'New Supplier'}**<br>"
        f"ID&nbsp;`{supplier['supplierid']}`<br>"
        f"✉️ {supplier['contactemail']}",
        unsafe_allow_html=True,
    )
    if get_missing_fields(supplier):
        st.warning("Profile incomplete", icon="⚠️")


def _po_badge(supplier_id: int) -> tuple[str, str]:
    """Return (base_label, badge_label) with pending-count if >0."""
    base = "📦 Purchase Orders"
    try:
        active = get_purchase_orders_for_supplier(supplier_id)
        pending = sum(po["status"] == "Pending" for po in active)
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
    Render sidebar, manage session_state[nav_page], return current page label.
    Active button = blue gradient highlight (disabled so it can't be re-clicked).
    """
    _inject_sidebar_css()  # must run after set_page_config()

    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = "🏠 Home"
    current = st.session_state[STATE_KEY]

    with st.sidebar:
        st.title("📌 Navigation")
        _supplier_card(supplier)
        st.divider()

        # ---- Home ----------------------------------------------------------
        if st.button("🏠 Home", use_container_width=True,
                     disabled=current == "🏠 Home", key="nav_home"):
            st.session_state[STATE_KEY] = "🏠 Home"
            st.rerun()

        # ---- Purchase Orders ----------------------------------------------
        base_po, po_label = _po_badge(supplier["supplierid"])
        if st.button(po_label, use_container_width=True,
                     disabled=current.startswith("📦"), key="nav_po"):
            st.session_state[STATE_KEY] = base_po
            st.rerun()

        # ---- Supplier Dashboard -------------------------------------------
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
