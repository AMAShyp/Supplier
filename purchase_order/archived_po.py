import streamlit as st
import pandas as pd
from translation import _
from purchase_order.po_handler import get_archived_purchase_orders, get_purchase_order_items

def show_archived_po_page(supplier):
    """
    Displays archived POs (Declined, Declined by AMAS, Declined by Supplier, 
    Delivered, Completed) in the same style as Track PO:
      - Each archived PO is an expander row
      - Inside each expander, show key details + item info in read-only form
    """

    st.subheader(_("archived_po_header"))

    archived_orders = get_archived_purchase_orders(supplier["supplierid"])
    if not archived_orders:
        st.info(_("no_archived_orders"))
        return

    # Loop over each archived PO, creating an expander for details
    for po in archived_orders:
        po_key = po["poid"]
        with st.expander(_("po_expander", id=po_key, status=po['status'])):
            # Basic info
            st.write(_("order_date", date=po['orderdate']))
            st.write(_("supplier_responded", date=po['respondedat'] or 'N/A'))
            st.write(_("expected_delivery", date=po['expecteddelivery'] or 'N/A'))
            st.write(_("sup_proposed_deliver", val=po.get('supproposeddeliver') or 'N/A'))
            st.write(_("original_poid", val=po.get('originalpoid') or 'N/A'))
            st.write(_("supplier_note", note=po.get('suppliernote') or ''))

            # Show item details
            items = get_purchase_order_items(po_key)
            if items:
                st.write(_("item_details_header"))
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
                st.info(_("no_items_archived"))
