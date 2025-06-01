# app.py
import streamlit as st

from sup_signin import sign_in_with_google
from sidebar import render_sidebar               # NEW sidebar helper
from supplier.supplier_handler import get_or_create_supplier
from home import show_home_page
from purchase_order.main_po import show_main_po_page
from supplier.supplier import show_supplier_dashboard


def main() -> None:
    """AMAS Supplier App – Streamlit entry point."""
    st.set_page_config(page_title="AMAS Supplier App", page_icon="🛒")
    st.title("AMAS Supplier App")

    # 1️⃣ Google sign-in
    user_info = sign_in_with_google()
    if not user_info:        # sign_in_with_google() shows its own UI
        st.stop()

    # 2️⃣ Load (or create) supplier record
    supplier = get_or_create_supplier(user_info["email"])

    # 3️⃣ Sidebar & navigation
    menu_choice = render_sidebar(supplier)   # ← returns plain label

    # 4️⃣ Router
    if menu_choice == "🏠 Home":
        show_home_page()

    elif menu_choice.startswith("📦 Purchase Orders"):
        show_main_po_page(supplier)

    else:  # "📊 Supplier Dashboard"
        show_supplier_dashboard(supplier)


if __name__ == "__main__":
    main()
