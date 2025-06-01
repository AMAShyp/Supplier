# app.py
import streamlit as st

# 1️⃣ MUST be the first Streamlit call
st.set_page_config(page_title="AMAS Supplier App", page_icon="🛒")

# ------------------------------------------------------------------
# Imports *after* page_config
# ------------------------------------------------------------------
from sup_signin import sign_in_with_google
from sidebar import render_sidebar                      # sidebar returns "home" / "pos" / "dash"
from supplier.supplier_handler import get_or_create_supplier
from home import show_home_page
from purchase_order.main_po import show_main_po_page
from supplier.supplier import show_supplier_dashboard
from translation import _, is_rtl                        # _() = translate helper

# Optional RTL support (Sorani Kurdish)
if is_rtl():
    st.markdown("<style>html, body {direction: rtl}</style>", unsafe_allow_html=True)

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
def main() -> None:
    st.title(_("app_title"))

    # Google OIDC
    user_info = sign_in_with_google()
    if not user_info:
        st.stop()

    # Supplier record
    supplier = get_or_create_supplier(user_info["email"])

    # Sidebar navigation
    nav = render_sidebar(supplier)      # "home" | "pos" | "dash"

    # Router
    if nav == "home":
        show_home_page()
    elif nav == "pos":
        show_main_po_page(supplier)
    else:  # "dash"
        show_supplier_dashboard(supplier)


if __name__ == "__main__":
    main()
