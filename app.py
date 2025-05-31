import streamlit as st
from sup_signin import sign_in_with_google
from supplier.supplier_handler import get_or_create_supplier
from home import show_home_page
from purchase_order.main_po import show_main_po_page  # 🔥 Updated import for PO management
from supplier.supplier import show_supplier_dashboard

def main():
    """Main entry point for the AMAS Supplier App."""
    st.title("AMAS Supplier App")

    # 1. Sign in with Google
    user_info = sign_in_with_google()
    if not user_info:
        st.stop()

    # 2. Get supplier record
    supplier = get_or_create_supplier(user_info["email"])

    # 3. Sidebar Navigation
    st.sidebar.title("📌 Navigation")
    menu_choice = st.sidebar.radio("Go to:", ["🏠 Home", "📦 Purchase Orders", "📊 Supplier Dashboard"])

    # 4. Show the selected page
    if menu_choice == "🏠 Home":
        show_home_page()
    elif menu_choice == "📦 Purchase Orders":
        show_main_po_page(supplier)  # 🔥 Now using `main_po.py` to manage PO pages
    else:
        show_supplier_dashboard(supplier)

if __name__ == "__main__":
    main()
