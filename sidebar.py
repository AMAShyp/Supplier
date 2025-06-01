"""
sidebar.py
Sidebar component – button navigation with a blue-gradient highlight
for the current (active) page.
"""

import streamlit as st
from supplier.supplier_handler import get_missing_fields
from purchase_order.po_handler import get_purchase_orders_for_supplier

ACCENT_GRAD = "linear-gradient(90deg, #0d6efd 0%, #1a74ff 100%)"
STATE_KEY = "nav_page"

# ───────────────────────────────────────────────────────────────
# CSS injected once per run (after page_config is set)
# ───────────────────────────────────────────────────────────────
def _inject_css():
    st.markdown(
        f"""
        <style>
        /* Base look for custom nav blocks */
        .nav-item {{
            padding: 0.45rem 0.75rem;
            width: 100%;
            display: block;
            border-radius: 0.33rem;
            text-align: left;
            cursor: pointer;
        }}
        .nav-item:hover {{
            background: rgba(0,0,0,0.05);
        }}
        .nav-item.active {{
            background: {ACCENT_GRAD};
            color: #ffffff !important;
            font-weight: 600;
            box-shadow: inset 0 0 0 2px rgba(255,255,255,0.15);
            cursor: default;
        }}
        .nav-badge {{
            float: right;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ───────────────────────────────────────────────────────────────
# Helper blocks
# ───────────────────────────────────────────────────────────────
def _supplier_card(supplier: dict):
    st.markdown(
        f"**{supplier.get('suppliername') or 'New Supplier'}**<br>"
        f"ID&nbsp;`{supplier['supplierid']}`<br>"
        f"✉️ {supplier['contactemail']}",
        unsafe_allow_html=True,
    )
    if get_missing_fields(supplier):
        st.warning("Profile incomplete", icon="⚠️")


def _pending_po_badge(supplier_id: int) -> int:
    try:
        active = get_purchase_orders_for_supplier(supplier_id)
        return sum(po["status"] == "Pending" for po in active)
    except Exception:
        return 0


def _nav_button(label: str, target: str) -> None:
    """
    Custom nav element:
    • If currently active → styled <div>, no click.
    • Else → st.button that updates session_state & reruns.
    """
    current = st.session_state[STATE_KEY]
    if current == target:
        st.markdown(f'<div class="nav-item active">{label}</div>',
                    unsafe_allow_html=True)
    else:
        if st.button(label, use_container_width=True, key=f"nav_{target}"):
            st.session_state[STATE_KEY] = target
            st.rerun()

# ───────────────────────────────────────────────────────────────
# Public API
# ───────────────────────────────────────────────────────────────
def render_sidebar(supplier: dict) -> str:
    """
    Builds sidebar and returns the selected page label.
    """
    _inject_css()

    # Initialise nav state the very first run
    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = "🏠 Home"

    with st.sidebar:
        st.title("📌 Navigation")
        _supplier_card(supplier)
        st.divider()

        # -------- Home --------
        _nav_button("🏠 Home", "🏠 Home")

        # -------- Purchase Orders (badge) --------
        pending = _pending_po_badge(supplier["supplierid"])
        po_label = f"📦 Purchase Orders{' <span class=\"nav-badge\">(' + str(pending) + ')</span>' if pending else ''}"
        _nav_button(po_label, "📦 Purchase Orders")

        # -------- Dashboard --------
        _nav_button("📊 Supplier Dashboard", "📊 Supplier Dashboard")

        st.divider()
        if st.button("Log out", use_container_width=True, key="sidebar_logout"):
            st.logout()
            st.rerun()

    return st.session_state[STATE_KEY]
