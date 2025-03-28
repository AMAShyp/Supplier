import streamlit as st
import pandas as pd
import io
from PIL import Image

from purchase_order.po_handler import (
    get_purchase_orders_for_supplier,
    get_purchase_order_items,
    update_po_item_proposal,
    update_purchase_order_status,
    propose_entire_po
)

def show_purchase_orders_page(supplier):
    """
    Displays each active PO with 3 main buttons (Accept, Modify, Decline).
    Only shows the 'Modify Order' form after the user clicks 'Modify Order'.

    The Proposed Delivery Date is pre-filled with the original Expected Delivery date/time if present.
    """

    st.subheader("📦 Track Purchase Orders")

    # Track whether we've opened the 'Decline reason' text area
    if "decline_po_show_reason" not in st.session_state:
        st.session_state["decline_po_show_reason"] = {}

    # Track whether we've opened the 'Modify Order' section
    if "modify_po_show_form" not in st.session_state:
        st.session_state["modify_po_show_form"] = {}

    # 1) Fetch active POs
    purchase_orders = get_purchase_orders_for_supplier(supplier["supplierid"])
    if not purchase_orders:
        st.info("No active purchase orders.")
        return

    for po in purchase_orders:
        po_key = po["poid"]  # unique key for session state

        with st.expander(f"PO ID: {po_key} | Status: {po['status']}"):
            # Basic PO info
            st.write(f"**Order Date:** {po['orderdate']}")
            st.write(f"**Expected Delivery:** {po['expecteddelivery'] or 'Not Set'}")
            st.write(f"**Current Status:** {po['status']}")
            st.write(f"**Supplier Note (if any):** {po.get('suppliernote') or ''}")

            # Show items in read-only table
            items = get_purchase_order_items(po_key)
            if items:
                st.subheader("Ordered Items")
                rows = []
                for it in items:
                    # Build image HTML
                    if it["itempicture"]:
                        img_html = f'<img src="{it["itempicture"]}" width="50" />'
                    else:
                        img_html = "No Image"

                    sup_qty = it.get("supproposedquantity") or ""
                    sup_price = it.get("supproposedprice") or ""

                    rows.append({
                        "ItemID": it["itemid"],
                        "Picture": img_html,
                        "Item Name": it["itemnameenglish"],
                        "OrderedQty": it["orderedquantity"],
                        "EstPrice": it["estimatedprice"] or "N/A",
                        "SupQty": sup_qty,
                        "SupPrice": sup_price
                    })

                df = pd.DataFrame(rows, columns=[
                    "ItemID", "Picture", "Item Name",
                    "OrderedQty", "EstPrice", "SupQty", "SupPrice"
                ])
                st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
            else:
                st.info("No items found for this PO.")

            # If PO is "Pending", show 3 main buttons
            if po["status"] == "Pending":
                c1, c2, c3 = st.columns(3)

                # Accept Order
                with c1:
                    if st.button("Accept Order", key=f"accept_{po_key}"):
                        final_deliv = st.date_input("Final Delivery (Optional)", key=f"deliv_{po_key}")
                        update_purchase_order_status(
                            poid=po_key,
                            status="Accepted",
                            expected_delivery=final_deliv or None
                        )
                        st.success("Order Accepted!")
                        st.rerun()

                # Modify Order
                with c2:
                    if not st.session_state["modify_po_show_form"].get(po_key, False):
                        # Button to open the Modify form
                        if st.button("Modify Order", key=f"modify_{po_key}"):
                            st.session_state["modify_po_show_form"][po_key] = True
                            st.rerun()
                    else:
                        # The Modify form is open
                        st.subheader("Propose Changes to This Order")

                        # Pre-fill Proposed Delivery with existing 'ExpectedDelivery'
                        default_deliv = None
                        if po.get("expecteddelivery"):
                            default_deliv = po["expecteddelivery"]  # Streamlit can handle date/datetime

                        prop_deliv = st.date_input(
                            "Proposed Delivery Date",
                            value=default_deliv,
                            key=f"prop_deliv_{po_key}"
                        )

                        proposed_note = st.text_area(
                            "Supplier Note (Entire PO)",
                            key=f"prop_note_{po_key}",
                            value=po.get("suppliernote") or ""
                        )

                        st.write("**Item-Level Changes**")
                        item_proposals = {}
                        if items:
                            for it in items:
                                i_id = it["itemid"]
                                st.write(f"Item {i_id}: {it['itemnameenglish']}")
                                colA, colB = st.columns(2)
                                cur_qty = int(it.get("supproposedquantity") or 0)
                                cur_price = float(it.get("supproposedprice") or 0.0)

                                new_qty = colA.number_input(
                                    f"Proposed Qty (Item {i_id})",
                                    min_value=0,
                                    value=cur_qty,
                                    key=f"qty_{po_key}_{i_id}"
                                )
                                new_price = colB.number_input(
                                    f"Proposed Price (Item {i_id})",
                                    min_value=0.0,
                                    value=cur_price,
                                    step=0.1,
                                    key=f"price_{po_key}_{i_id}"
                                )
                                item_proposals[i_id] = (new_qty, new_price)
                                st.write("---")

                        if st.button("Submit Propose", key=f"submit_prop_{po_key}"):
                            # 1) Update item-level proposals
                            for i_id, (qty_val, price_val) in item_proposals.items():
                                update_po_item_proposal(
                                    poid=po_key,
                                    itemid=i_id,
                                    sup_qty=qty_val,
                                    sup_price=price_val
                                )

                            # 2) Propose entire PO
                            propose_entire_po(
                                poid=po_key,
                                sup_proposed_deliver=prop_deliv,
                                supplier_note=proposed_note
                            )
                            st.success("PO Proposed Successfully! Status => Proposed by Supplier.")
                            # close the form
                            st.session_state["modify_po_show_form"][po_key] = False
                            st.rerun()

                # Decline Order
                with c3:
                    if not st.session_state["decline_po_show_reason"].get(po_key, False):
                        if st.button("Decline Order", key=f"decline_{po_key}"):
                            st.session_state["decline_po_show_reason"][po_key] = True
                            st.rerun()
                    else:
                        st.write("**Reason for Declination**")
                        decline_note = st.text_area("Decline Reason:", key=f"decline_note_{po_key}")

                        dc1, dc2 = st.columns(2)
                        with dc1:
                            if st.button("Confirm Decline", key=f"confirm_decline_{po_key}"):
                                update_purchase_order_status(
                                    poid=po_key,
                                    status="Declined",
                                    supplier_note=decline_note
                                )
                                st.warning("Order Declined!")
                                st.session_state["decline_po_show_reason"][po_key] = False
                                st.rerun()
                        with dc2:
                            if st.button("Cancel", key=f"cancel_decline_{po_key}"):
                                st.session_state["decline_po_show_reason"][po_key] = False
                                st.rerun()

            # If the PO is 'Accepted', 'Shipping', etc. handle normal flow
            elif po["status"] == "Accepted":
                if st.button("Mark as Shipping", key=f"ship_{po_key}"):
                    update_purchase_order_status(poid=po_key, status="Shipping")
                    st.info("Order marked as Shipping.")
                    st.rerun()

            elif po["status"] == "Shipping":
                if st.button("Mark as Delivered", key=f"delivered_{po_key}"):
                    update_purchase_order_status(poid=po_key, status="Delivered")
                    st.success("Order marked as Delivered.")
                    st.rerun()
