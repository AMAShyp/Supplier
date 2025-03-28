import streamlit as st
import pandas as pd
from purchase_order.po_handler import get_archived_purchase_orders

def show_archived_po_page(supplier):
    """
    Displays a simple table of archived purchase orders (Declined, Delivered, Completed,
    Declined by AMAS, Declined by Supplier) with relevant columns.
    """

    st.subheader("📂 Archived Purchase Orders")

    archived_orders = get_archived_purchase_orders(supplier["supplierid"])
    if not archived_orders:
        st.info("No archived purchase orders found.")
        return

    # Build a list of dictionaries for each PO
    rows = []
    for po in archived_orders:
        rows.append({
            "POID": po["poid"],
            "Status": po["status"],
            "OrderDate": po["orderdate"],
            "ExpectedDelivery": po["expecteddelivery"],
            "RespondedAt": po["respondedat"],
            "SupProposedDeliver": po["supproposeddeliver"],
            "OriginalPOID": po["originalpoid"],
            "SupplierNote": po["suppliernote"] or ""
        })

    # Convert to DataFrame
    df = pd.DataFrame(rows, columns=[
        "POID", "Status", "OrderDate", "ExpectedDelivery", 
        "RespondedAt", "SupProposedDeliver", 
        "OriginalPOID", "SupplierNote"
    ])
    st.dataframe(df)

    st.write("Select a row above for more details if needed. (You can add an Expander, etc.)")

    # If you want to show item details on click, you can add expanders or a select box,
    # but for now this is a simple table of archived POs only.
