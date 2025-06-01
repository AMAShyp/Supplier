"""
sidebar.py
Button-style navigation + language selector.
Active page highlighted with a light-blue bar.  All labels translated via `translation._`.
"""

import streamlit as st
from supplier.supplier_handler import get_missing_fields
from purchase_order.po_handler import get_purchase_orders_for_supplier
from translation import _, set_language, get_language

STATE_KEY = "nav_page"          # stores "home" | "pos" | "dash"

# ───────────────────────────────────────────────────────────────
# CSS
# ───────────────────────────────────────────────────────────────
def _inject_css() -> None:
    st.markdown(
        """
        <style>
        .nav-item{
            padding:0.45rem 0.75rem;
            width:100%;
            display:block;
            border-radius:0.35rem;
            text-align:center;
            cursor:pointer;
            margin-bottom:1rem;
        }
        .nav-item:hover{
            background:rgba(0,0,0,0.05);
        }
        .nav-item.active{
            background-color:#e9f4ff;
            color:#0056b3 !important;
            font-weight:600;
            border-left:4px solid #0d6efd;
            cursor:default;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# ───────────────────────────────────────────────────────────────
# Helper blocks
# ───────────────────────────────────────────────────────────────
def _language_selector():
    option = st.selectbox(
        _("language_label"),
        options=[("English", "en"), ("کوردی", "ku")],
        index=0 if get_language() == "en" else 1,
        format_func=lambda x: x[0],
    )
    set_language(option[1])

def _supplier_card(sup: dict):
    st.markdown(
        f"**{sup.get('suppliername') or 'New Supplier'}**<br>"
        f"ID&nbsp;`{sup['supplierid']}`<br>"
        f"✉️ {sup['contactemail']}",
        unsafe_allow_html=True
    )
    if get_missing_fields(sup):
        st.warning(_("profile_incomplete"), icon="⚠️")

def _pending_pos(supplier_id: int) -> int:
    try:
        rows = get_purchase_orders_for_supplier(supplier_id)
        return sum(po["status"] == "Pending" for po in rows)
    except Exception:
        return 0

def _nav_block(label: str, target_code: str):
    """Render either active DIV or clickable button."""
    current = st.session_state[STATE_KEY]
    if current == target_code:
        st.markdown(f'<div class="nav-item active">{label}</div>', unsafe_allow_html=True)
    else:
        if st.button(label, use_container_width=True, key=f"nav_{target_code}"):
            st.session_state[STATE_KEY] = target_code
            st.rerun()

# ───────────────────────────────────────────────────────────────
# Public API
# ───────────────────────────────────────────────────────────────
def render_sidebar(supplier: dict) -> str:
    _inject_css()

    # first run default page
    if STATE_KEY not in st.session_state:
        st.session_state[STATE_KEY] = "home"

    with st.sidebar:
        st.title(_("app_title"))
        _language_selector()
        st.divider()

        _supplier_card(supplier)
        st.divider()

        # ---- Navigation buttons ----
        _nav_block(_("nav_home"), "home")

        pending = _pending_pos(supplier["supplierid"])
        po_label = f"{_('nav_pos')} ({pending})" if pending else _("nav_pos")
        _nav_block(po_label, "pos")

        _nav_block(_("nav_dash"), "dash")

        st.divider()
        if st.button(_("logout"), use_container_width=True, key="sidebar_logout"):
            st.logout()
            st.rerun()

    return st.session_state[STATE_KEY]
