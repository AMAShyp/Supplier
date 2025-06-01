"""
sidebar.py
Reusable sidebar component for the AMAS Supplier App.

Usage in app.py
---------------
from sidebar import render_sidebar

menu_choice = render_sidebar(supplier)
if menu_choice == "🏠 Home":
    ...
"""

import streamlit as st
from supplier.supplier_handler import get_missing_fields
from purchase_order.po_handler import get_purchase_orders_for_supplier  # for badge counts

# ───────────────────────────────────────────────────────────────
def _supplier_card(supplier: dict):
    """Small profile summary at the top of the sidebar."""
    st.markdown(
        f"**{supplier.get('suppliername') or 'New Supplier'}**\n\n"
        f"ID&nbsp;`{supplier['supplierid']}`  \n"
        f"✉️ {supplier['contactemail']}",
        unsafe_allow_html=True,
    )

    missing = get_missing_fields(supplier)
    if missing:
        st.warning("Profile incomplete", icon="⚠️")


def _po_badge(supplier_id: int) -> str:
    """Return '📦 Purchase Orders (n)' with pending count badge."""
    try:
        active_pos = get_purchase_orders_for_supplier(supplier_id)
        pending = sum(1 for po in active_pos if po["status"] == "Pending")
        if pending:
            return f"📦 Purchase Orders  ({pending})"
    except Exception:
        pass  # silently ignore DB hiccups for the sidebar
    return "📦 Purchase Orders"


# ───────────────────────────────────────────────────────────────
def render_sidebar(supplier: dict) -> str:
    """
    Build the sidebar and return the selected navigation label.
    - Displays a mini supplier profile card.
    - Shows dynamic badge for pending PO count.
    - Provides Log-out button.
    """
    with st.sidebar:
        st.title("📌 Navigation")

        _supplier_card(supplier)

        # Navigation radio with dynamic PO badge
        menu_choice = st.radio(
            "Go to:",
            (
                "🏠 Home",
                _po_badge(supplier["supplierid"]),
                "📊 Supplier Dashboard",
            ),
            label_visibility="collapsed",
        )

        st.divider()
        if st.button("Log out"):
            st.logout()
            st.rerun()

    # Strip badge count so app’s router can rely on plain text
    return menu_choice.split("  ")[0]   # keeps emoji + base text only
