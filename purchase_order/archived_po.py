import streamlit as st
import pandas as pd
from purchase_order.po_handler import get_archived_purchase_orders, get_purchase_order_items

def show_archived_po_page(supplier):
    """
    Displays archived POs (Declined, Declined by AMAS, Declined by Supplier, 
    Delivered, Completed) in the same style as Track PO:
      - Each archived PO is an expander row
      - Inside each expander, show key details + item info in read-only form
    """

    st.subheader("📂 Archived Purchase Orders")

    archived_orders = get_archived_purchase_orders(supplier["supplierid"])
    if not archived_orders:
        st.info("No archived purchase orders.")
        return

    # Loop over each archived PO, creating an expander for details
    for po in archived_orders:
        po_key = po["poid"]
        with st.expander(f"PO ID: {po_key} | Status: {po['status']}"):
            # Basic info
            st.write(f"**Order Date:** {po['orderdate']}")
            st.write(f"**Supplier Responded At:** {po['respondedat'] or 'N/A'}")
            st.write(f"**Expected Delivery:** {po['expecteddelivery'] or 'N/A'}")
            st.write(f"**SupProposedDeliver:** {po.get('supproposeddeliver') or 'N/A'}")
            st.write(f"**OriginalPOID:** {po.get('originalpoid') or 'N/A'}")
            st.write(f"**SupplierNote:** {po.get('suppliernote') or ''}")

            # Show item details
            items = get_purchase_order_items(po_key)
            if items:
                st.write("### Item Details")
                rows = []
                for it in items:
                    # Minimal item info for archived POs
                    rows.append({
                        "ItemID": it["itemid"],
                        "Item Name": it["itemnameenglish"],
                        "OrderedQty": it["orderedquantity"],
                        "EstPrice": it["estimatedprice"] or "N/A",
                    })
                df = pd.DataFrame(rows, columns=["ItemID", "Item Name", "OrderedQty", "EstPrice"])
                st.dataframe(df)
            else:
                st.info("No items found for this archived PO.")
