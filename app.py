# app.py
import streamlit as st

# MUST be first Streamlit command
st.set_page_config(page_title="AMAS Supplier App", page_icon="🛒")

# Remaining imports (safe after page_config)
from sup_signin import sign_in_with_google
from sidebar import render_sidebar
from supplier.supplier_handler import get_or_create_supplier
from home import show_home_page
from purchase_order.main_po import show_main_po_page
from supplier.supplier import show_supplier_dashboard
from translation import is_rtl
if is_rtl():
    st.markdown("<style>html, body {direction: rtl}</style>", unsafe_allow_html=True)

def main() -> None:
    """AMAS Supplier App – Streamlit entry point."""
    st.title("AMAS Supplier App")

    # 1️⃣ Google sign-in
    user_info = sign_in_with_google()
    if not user_info:
        st.stop()

    # 2️⃣ Supplier record (create if new)
    supplier = get_or_create_supplier(user_info["email"])

    # 3️⃣ Sidebar navigation
    menu_choice = render_sidebar(supplier)

    # 4️⃣ Page router
    if menu_choice == "🏠 Home":
        show_home_page()

    elif menu_choice.startswith("📦"):
        show_main_po_page(supplier)

    else:  # "📊 Supplier Dashboard"
        show_supplier_dashboard(supplier)


if __name__ == "__main__":
    main()
