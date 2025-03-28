import streamlit as st
import pandas as pd
from purchase_order.po_handler import (
    get_archived_purchase_orders, 
    get_purchase_order_items
)

def show_archived_po_page(supplier):
    """
    Displays a table of all archived POs (Declined, Declined by AMAS, 
    Declined by Supplier, Delivered, Completed).
    Also allows selecting an archived PO from a dropdown to see details 
    (including item details).
    """

    st.subheader("📂 Archived Purchase Orders")

    # 1) Fetch archived POs
    archived_orders = get_archived_purchase_orders(supplier["supplierid"])
    if not archived_orders:
        st.info("No archived purchase orders found.")
        return

    # 2) Build a DataFrame with columns: POID, Status, Order Date, Supplier Responded At
    rows = []
    for po in archived_orders:
        rows.append({
            "POID": po["poid"],
            "Status": po["status"],
            "Order Date": po["orderdate"],
            # rename respondedat to "Supplier Responded At"
            "Supplier Responded At": po["respondedat"],
        })

    df = pd.DataFrame(rows, columns=["POID", "Status", "Order Date", "Supplier Responded At"])
    st.dataframe(df)

    # 3) Dropdown to select an archived PO for more details
    st.write("### View Archived PO Details")
    poid_options = [str(po["poid"]) for po in archived_orders]
    selected_poid_str = st.selectbox("Select a PO to see its details:", ["(None)"] + poid_options)

    if selected_poid_str != "(None)":
        selected_poid = int(selected_poid_str)

        # Find the chosen PO in the list
        chosen_po = next((po for po in archived_orders if po["poid"] == selected_poid), None)
        if chosen_po:
            st.write(f"**PO ID:** {chosen_po['poid']}")
            st.write(f"**Status:** {chosen_po['status']}")
            st.write(f"**Order Date:** {chosen_po['orderdate']}")
            st.write(f"**Expected Delivery:** {chosen_po['expecteddelivery'] or 'None'}")
            st.write(f"**Supplier Responded At:** {chosen_po['respondedat'] or 'None'}")
            st.write(f"**SupProposedDeliver:** {chosen_po['supproposeddeliver'] or 'None'}")
            st.write(f"**OriginalPOID:** {chosen_po['originalpoid'] or 'None'}")
            st.write(f"**SupplierNote:** {chosen_po['suppliernote'] or ''}")

            # 4) Show item details for the selected archived PO
            st.write("#### Item Details for This Archived PO")
            items = get_purchase_order_items(selected_poid)
            if items:
                item_rows = []
                for it in items:
                    item_rows.append({
                        "ItemID": it["itemid"],
                        "Item Name": it["itemnameenglish"],
                        "OrderedQty": it["orderedquantity"],
                        "EstPrice": it["estimatedprice"] or 'N/A',
                    })
                item_df = pd.DataFrame(item_rows, columns=["ItemID", "Item Name", "OrderedQty", "EstPrice"])
                st.dataframe(item_df)
            else:
                st.info("No items found for this archived PO.")
