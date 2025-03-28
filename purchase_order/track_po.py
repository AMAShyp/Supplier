import streamlit as st
import io
from PIL import Image
import pandas as pd

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
    - If user clicks Modify, we show the item-level + order-level proposal form.
    - If user clicks Accept, we immediately accept the PO.
    - If user clicks Decline, we show a reason text area and finalize the decline.
    """

    st.subheader("📦 Track Purchase Orders")

    # For toggling "Decline reason" display
    if "decline_po_show_reason" not in st.session_state:
        st.session_state["decline_po_show_reason"] = {}

    # For toggling "Modify Order" display
    if "modify_po_show_form" not in st.session_state:
        st.session_state["modify_po_show_form"] = {}

    # 1. Fetch active POs
    purchase_orders = get_purchase_orders_for_supplier(supplier["supplierid"])
    if not purchase_orders:
        st.info("No active purchase orders.")
        return

    # Iterate through each PO
    for po in purchase_orders:
        with st.expander(f"PO ID: {po['poid']} | Status: {po['status']}"):
            # Basic PO info
            st.write(f"**Order Date:** {po['orderdate']}")
            st.write(f"**Current Expected Delivery:** {po['expecteddelivery'] or 'Not Set'}")
            st.write(f"**Current Status:** {po['status']}")
            st.write(f"**Supplier Note (if any):** {po.get('suppliernote') or ''}")

            # Show items in read-only table
            items = get_purchase_order_items(po["poid"])
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
                    "OrderedQty", "EstPrice",
                    "SupQty", "SupPrice"
                ])
                st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
            else:
                st.info("No items found for this PO.")

            # If the PO is "Pending", show 3 main buttons
            if po["status"] == "Pending":
                c1, c2, c3 = st.columns(3)

                # Accept Order
                with c1:
                    if st.button("Accept Order", key=f"accept_{po['poid']}"):
                        final_delivery = st.date_input("Final Delivery (Optional)", key=f"deliv_{po['poid']}")
                        update_purchase_order_status(
                            poid=po["poid"],
                            status="Accepted",
                            expected_delivery=final_delivery or None
                        )
                        st.success("Order Accepted!")
                        st.experimental_rerun()

                # Modify Order
                with c2:
                    # If user hasn't clicked "Modify Order" yet, show button
                    if not st.session_state["modify_po_show_form"].get(po["poid"], False):
                        if st.button("Modify Order", key=f"modify_{po['poid']}"):
                            st.session_state["modify_po_show_form"][po["poid"]] = True
                            st.experimental_rerun()
                    else:
                        # Show the modification form
                        st.subheader("Propose Changes for This PO")
                        # Entire PO: Proposed Delivery Date + Note
                        proposed_deliv = st.date_input(
                            "Proposed Delivery Date",
                            key=f"prop_deliv_{po['poid']}",
                            value=po.get("supproposeddeliver")  # if any
                        )
                        proposed_note = st.text_area(
                            "Supplier Note (Entire PO)",
                            key=f"prop_note_{po['poid']}",
                            value=po.get("suppliernote") or ""
                        )

                        # Let user input item-level changes
                        st.write("**Item-Level Changes**")
                        new_item_values = {}
                        if items:
                            for it in items:
                                i_id = it["itemid"]
                                st.write(f"Item {i_id}: {it['itemnameenglish']}")
                                colA, colB = st.columns(2)
                                cur_sup_qty = it.get("supproposedquantity") or 0
                                cur_sup_price = it.get("supproposedprice") or 0.0

                                new_qty = colA.number_input(
                                    f"Proposed Qty (Item {i_id})",
                                    min_value=0,
                                    value=int(cur_sup_qty),
                                    key=f"qty_{po['poid']}_{i_id}"
                                )
                                new_price = colB.number_input(
                                    f"Proposed Price (Item {i_id})",
                                    min_value=0.0,
                                    value=float(cur_sup_price),
                                    step=0.1,
                                    key=f"price_{po['poid']}_{i_id}"
                                )
                                new_item_values[i_id] = (new_qty, new_price)
                                st.write("---")

                        # Submit single button
                        if st.button("Submit Propose", key=f"submit_prop_{po['poid']}"):
                            # 1) Update items
                            for i_id, (qty_val, price_val) in new_item_values.items():
                                update_po_item_proposal(
                                    poid=po["poid"],
                                    itemid=i_id,
                                    sup_qty=qty_val,
                                    sup_price=price_val
                                )
                            # 2) Propose entire PO
                            propose_entire_po(
                                poid=po["poid"],
                                sup_proposed_deliver=proposed_deliv,
                                supplier_note=proposed_note
                            )
                            st.success("PO Proposed Successfully! Status => Proposed by Supplier.")
                            st.session_state["modify_po_show_form"][po["poid"]] = False
                            st.experimental_rerun()

                # Decline Order
                with c3:
                    # If user hasn't clicked "Decline Order" yet, show button
                    if not st.session_state["decline_po_show_reason"].get(po["poid"], False):
                        if st.button("Decline Order", key=f"decline_{po['poid']}"):
                            st.session_state["decline_po_show_reason"][po["poid"]] = True
                            st.experimental_rerun()
                    else:
                        st.write("**Reason for Declination**")
                        decline_note = st.text_area("Decline Reason:", key=f"decline_note_{po['poid']}")

                        dc1, dc2 = st.columns(2)
                        with dc1:
                            if st.button("Confirm Decline", key=f"confirm_decline_{po['poid']}"):
                                update_purchase_order_status(
                                    poid=po["poid"],
                                    status="Declined",
                                    supplier_note=decline_note
                                )
                                st.warning("Order Declined!")
                                st.session_state["decline_po_show_reason"][po["poid"]] = False
                                st.experimental_rerun()
                        with dc2:
                            if st.button("Cancel", key=f"cancel_decline_{po['poid']}"):
                                st.session_state["decline_po_show_reason"][po["poid"]] = False
                                st.experimental_rerun()

            # If status is not "Pending", handle your usual flow
            elif po["status"] == "Accepted":
                if st.button("Mark as Shipping", key=f"ship_{po['poid']}"):
                    update_purchase_order_status(poid=po["poid"], status="Shipping")
                    st.info("Order marked as Shipping.")
                    st.experimental_rerun()

            elif po["status"] == "Shipping":
                if st.button("Mark as Delivered", key=f"delivered_{po['poid']}"):
                    update_purchase_order_status(poid=po["poid"], status="Delivered")
                    st.success("Order marked as Delivered.")
                    st.experimental_rerun()
