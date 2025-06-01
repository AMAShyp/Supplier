"""
sidebar.py
Sidebar component – navigation via individual buttons.
The currently-selected page is highlighted (teal) rather than greyed-out.
"""

import streamlit as st
from supplier.supplier_handler import get_missing_fields
from purchase_order.po_handler import get_purchase_orders_for_supplier

ACCENT = "#1ABC9C"   # AMAS teal

# ───────────────────────────────────────────────────────────────
def _inject_sidebar_css():
    _inject_sidebar_css()
    """Highlight disabled nav buttons with the accent colour."""
    _css = f"""
    <style>
    button[data-testid="baseButton-secondary"][disabled] {{
        background-color: {ACCENT} !important;
        color: white       !important;
        opacity: 1         !important;
    }}
    </style>
    """
    st.markdown(_css, unsafe_allow_html=True)


# ───────────────────────────────────────────────────────────────
def _supplier_card(supplier: dict):
    st.markdown(
        f"**{supplier.get('suppliername') or 'New Supplier'}**\n\n"
        f"ID&nbsp;`{supplier['supplierid']}`  \n"
        f"✉️ {supplier['contactemail']}",
        unsafe_allow_html=True,
    )
    if get_missing_fields(supplier):
        st.warning("Profile incomplete", icon="⚠️")


def _po_badge(supplier_id: int) -> tuple[str, str]:
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
def render_sidebar(supplier: dict) -> str:
    """
    Build sidebar, manage session_state["nav_page"], and return it.
    Navigation uses buttons; the active one is highlighted.
    """
    with st.sidebar:
        st.title("📌 Navigation")
        _supplier_card(supplier)
        st.divider()

        # session state for current page
        if "nav_page" not in st.session_state:
            st.session_state["nav_page"] = "🏠 Home"
        current = st.session_state["nav_page"]

        # ----- Home ----------------------------------------------------------
        if st.button("🏠 Home", use_container_width=True,
                     disabled=current == "🏠 Home", key="nav_home"):
            st.session_state["nav_page"] = "🏠 Home"
            st.rerun()

        # ----- Purchase Orders ----------------------------------------------
        base_po, po_label = _po_badge(supplier["supplierid"])
        if st.button(po_label, use_container_width=True,
                     disabled=current.startswith("📦"), key="nav_po"):
            st.session_state["nav_page"] = base_po
            st.rerun()

        # ----- Supplier Dashboard -------------------------------------------
        dash = "📊 Supplier Dashboard"
        if st.button(dash, use_container_width=True,
                     disabled=current == dash, key="nav_dash"):
            st.session_state["nav_page"] = dash
            st.rerun()

        st.divider()
        if st.button("Log out", use_container_width=True, key="sidebar_logout"):
            st.logout()
            st.rerun()

    return st.session_state["nav_page"]
