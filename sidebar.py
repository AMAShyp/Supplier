"""
sidebar.py
Sidebar component – navigation via individual buttons (not radio).
"""

import streamlit as st
from supplier.supplier_handler import get_missing_fields
from purchase_order.po_handler import get_purchase_orders_for_supplier

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
    """
    Return (base_label, label_with_badge).
    Base label is used to store state; badge label is what the user sees.
    """
    base = "📦 Purchase Orders"
    try:
        active = get_purchase_orders_for_supplier(supplier_id)
        pending = sum(1 for po in active if po["status"] == "Pending")
        if pending:
            return base, f"{base}  ({pending})"
    except Exception:
        pass
    return base, base


# ───────────────────────────────────────────────────────────────
def render_sidebar(supplier: dict) -> str:
    """
    Draw sidebar, manage session_state["nav_page"], and return it.
    """
    with st.sidebar:
        st.title("📌 Navigation")
        _supplier_card(supplier)
        st.divider()

        # 1️⃣ ensure state
        if "nav_page" not in st.session_state:
            st.session_state["nav_page"] = "🏠 Home"

        current = st.session_state["nav_page"]

        # 2️⃣ navigation buttons
        # Home -----------------------------------------------------------------
        if st.button("🏠 Home", use_container_width=True,
                     disabled=current == "🏠 Home", key="nav_home"):
            st.session_state["nav_page"] = "🏠 Home"
            st.rerun()

        # Purchase Orders ------------------------------------------------------
        base_po, po_label = _po_badge(supplier["supplierid"])
        if st.button(po_label, use_container_width=True,
                     disabled=current.startswith("📦"), key="nav_po"):
            st.session_state["nav_page"] = base_po
            st.rerun()

        # Dashboard ------------------------------------------------------------
        if st.button("📊 Supplier Dashboard", use_container_width=True,
                     disabled=current == "📊 Supplier Dashboard",
                     key="nav_dash"):
            st.session_state["nav_page"] = "📊 Supplier Dashboard"
            st.rerun()

        st.divider()
        if st.button("Log out", use_container_width=True, key="sidebar_logout"):
            st.logout()
            st.rerun()

    return st.session_state["nav_page"]
