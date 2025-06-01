"""
sidebar.py  ·  v4
Button-style navigation with a subtle blue highlight
for the active page and clean badge text.
"""

import streamlit as st
from supplier.supplier_handler import get_missing_fields
from purchase_order.po_handler import get_purchase_orders_for_supplier
from translation import _, set_language, get_language

STATE_KEY = "nav_page"

# ───────────────────────────────────────────────────────────────
# 1. Inject CSS (after page_config is set)
# ───────────────────────────────────────────────────────────────
def _inject_css() -> None:
    st.markdown(
        """
        <style>
        /* Base look for nav containers */
        .nav-item {
            padding: 0.45rem 0.75rem;
            width: 100%;
            display: block;
            border-radius: 0.35rem;
            text-align: center;          /* ← center the label */
            cursor: pointer;
            margin-bottom: 1rem;         /* your chosen spacing */
        }
        .nav-item:hover {
            background: rgba(0, 0, 0, 0.05);
        }
        /* Active highlight */
        .nav-item.active {
            background-color: #e9f4ff;   /* very-light blue */
            color: #0056b3 !important;
            font-weight: 600;
            border-left: 4px solid #0d6efd;     /* accent bar */
            cursor: default;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ───────────────────────────────────────────────────────────────
# 2. Sidebar helper blocks
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


def _pending_pos(supplier_id: int) -> int:
    try:
        active = get_purchase_orders_for_supplier(supplier_id)
        return sum(po["status"] == "Pending" for po in active)
    except Exception:
        return 0


def _nav_block(label: str, target: str) -> None:
    """
    Renders a nav element:
    • If current page == target => styled div (active highlight)
    • Otherwise => Streamlit button that sets nav_page and reruns.
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
# 3. Public entry
# ───────────────────────────────────────────────────────────────
def render_sidebar(supplier: dict) -> str:
    """Build sidebar; return the current page label."""
    _inject_css()

    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = "🏠 Home"

    with st.sidebar:
        st.title("📌 Navigation")
        _supplier_card(supplier)
        st.divider()

        # Home
        _nav_block("🏠 Home", "🏠 Home")

        # Purchase Orders + badge
        pending = _pending_pos(supplier["supplierid"])
        po_label = f"📦 Purchase Orders ({pending})" if pending else "📦 Purchase Orders"
        _nav_block(po_label, "📦 Purchase Orders")

        # Dashboard
        _nav_block("📊 Supplier Dashboard", "📊 Supplier Dashboard")

        st.divider()
        if st.button("Log out", use_container_width=True, key="sidebar_logout"):
            st.logout()
            st.rerun()

    return st.session_state[STATE_KEY]


def language_selector():
    opt = st.selectbox(
        "Language / زمان",
        options=[("English", "en"), ("کوردی", "ku")],
        index=0 if get_language() == "en" else 1,
        format_func=lambda x: x[0],
    )
    set_language(opt[1])
