import streamlit as st
from purchase_order.track_po import show_purchase_orders_page
from purchase_order.archived_po import show_archived_po_page

def show_main_po_page(supplier):
    """Main page to switch between Track PO and Archived PO."""
    st.title("Purchase Orders Management")

    # Create tabs
    tab1, tab2 = st.tabs(["📦 Track PO", "📂 Archived PO"])

    with tab1:
        show_purchase_orders_page(supplier)  # 🔥 Active orders

    with tab2:
        show_archived_po_page(supplier)  # 🔥 Archived orders
