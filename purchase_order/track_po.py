import streamlit as st
import io
from PIL import Image
import pandas as pd
from datetime import datetime, date, time
from purchase_order.po_handler import (
    get_purchase_orders_for_supplier,
    get_purchase_order_items,
    update_purchase_order_status,
    propose_entire_po,
    update_po_item_proposal
)

def show_purchase_orders_page(supplier):
    """
    Displays POs with 3 distinct buttons: 
      1) Accept Order
      2) Modify Order
      3) Decline Order

    If "Modify Order" is clicked, a section expands, allowing:
      - item-level changes (qty, price)
      - date/time changes
      - a single "Submit Modification" button
    """
    st.subheader("📦 Track Purchase Orders")

    # To handle showing/hiding the "Modify" section
    if "modify_po_show" not in st.session_state:
        st.session_state["modify_po_show"] = {}

    # For the decline reason toggle
    if "decline_po_show_reason" not in st.session_state:
        st.session_state["decline_po_show_reason"] = {}

    purchase_orders = get_purchase_orders_for_supplier(supplier["supplierid"])
    if not purchase_orders:
        st.info("No active purchase orders.")
        return

    for po in purchase_orders:
        with st.expander(f"PO ID: {po['poid']} | Status: {po['status']}"):
            st.write(f"**Order Date:** {po['orderdate']}")
            st.write(f"**Current Expected Delivery:** {po['expecteddelivery'] or 'Not Set'}")
            st.write(f"**Current Status:** {po['status']}")
            st.write(f"**Supplier Note:** {po.get('suppliernote') or ''}")

            items = get_purchase_order_items(po["poid"])
            if items:
                st.subheader("Items in this PO")
                # Build a read-only table with existing item data & any current proposed values
                rows = []
                for it in items:
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

            st.write("---")
            # Show 3 main buttons in one row: Accept, Modify, Decline
            c1, c2, c3 = st.columns(3)

            # 1) Accept
            with c1:
                if po["status"] == "Pending":
                    if st.button("Accept Order", key=f"accept_{po['poid']}"):
                        # Optionally let them pick a final date/time if needed
                        deliver_date = st.date_input(
                            "Final Delivery Date (Optional)",
                            key=f"accept_date_{po['poid']}"
                        )
                        # No time? We'll keep it simple. If needed, we can add a time_input
                        update_purchase_order_status(
                            poid=po["poid"],
                            status="Accepted",
                            expected_delivery=deliver_date or None
                        )
                        st.success("Order Accepted!")
                        st.experimental_rerun()
                else:
                    st.write("")

            # 2) Modify
            with c2:
                if not st.session_state["modify_po_show"].get(po["poid"], False):
                    # Show the button if we're not currently in "modify" mode
                    if po["status"] == "Pending":
                        if st.button("Modify Order", key=f"modify_{po['poid']}"):
                            st.session_state["modify_po_show"][po["poid"]] = True
                            st.experimental_rerun()
                else:
                    # If we're in "modify" mode, show the modification form
                    st.write("**Modifying This Order**")

            # 3) Decline
            with c3:
                if po["status"] == "Pending":
                    if not st.session_state["decline_po_show_reason"].get(po["poid"], False):
                        if st.button("Decline Order", key=f"decline_{po['poid']}"):
                            st.session_state["decline_po_show_reason"][po["poid"]] = True
                            st.experimental_rerun()
                    else:
                        st.write("**Reason for Declination**")
                        decline_note = st.text_area("Why are you declining?", key=f"decline_note_{po['poid']}")

                        dcol1, dcol2 = st.columns(2)
                        with dcol1:
                            if st.button("Confirm Decline", key=f"confirm_decline_{po['poid']}"):
                                update_purchase_order_status(
                                    poid=po["poid"],
                                    status="Declined",
                                    supplier_note=decline_note
                                )
                                st.warning("Order Declined!")
                                st.session_state["decline_po_show_reason"][po["poid"]] = False
                                st.experimental_rerun()
                        with dcol2:
                            if st.button("Cancel", key=f"cancel_decline_{po['poid']}"):
                                st.session_state["decline_po_show_reason"][po["poid"]] = False
                                st.experimental_rerun()

            # If status is accepted -> shipping, shipping -> delivered
            if po["status"] == "Accepted":
                if st.button("Mark as Shipping", key=f"ship_{po['poid']}"):
                    update_purchase_order_status(poid=po["poid"], status="Shipping")
                    st.info("Order marked as Shipping.")
                    st.experimental_rerun()

            elif po["status"] == "Shipping":
                if st.button("Mark as Delivered", key=f"delivered_{po['poid']}"):
                    update_purchase_order_status(poid=po["poid"], status="Delivered")
                    st.success("Order marked as Delivered.")
                    st.experimental_rerun()

            # ---- If in "modify" mode, show the entire propose section
            if st.session_state["modify_po_show"].get(po["poid"], False):
                st.write("---")
                st.write("### Modify & Propose All Changes Here")

                # A) Let them pick new date + time for SupProposedDeliver
                # If existing expectedDelivery is a datetime
                # We'll guess we have date & time, else pick now
                if po["expecteddelivery"]:
                    # We only have date, or do we have date/time?
                    # Let's attempt splitting if it's a datetime
                    current_dt = po["expecteddelivery"]
                    if isinstance(current_dt, str):
                        # fallback parse if needed
                        # or just show st.warning that we can't parse?
                        # We'll do a quick parse:
                        try:
                            current_dt = datetime.fromisoformat(current_dt)
                        except:
                            current_dt = datetime.now()
                    date_default = current_dt.date()
                    time_default = current_dt.time()
                else:
                    date_default = date.today()
                    time_default = datetime.now().time()

                # Let them pick date + time
                prop_date = st.date_input(
                    "Proposed Delivery Date",
                    key=f"modify_date_{po['poid']}",
                    value=date_default
                )
                prop_time = st.time_input(
                    "Proposed Delivery Time",
                    key=f"modify_time_{po['poid']}",
                    value=time_default
                )
                # Combine
                combined_dt = datetime.combine(prop_date, prop_time)

                # B) Let them add a supplier note
                mod_note = st.text_area(
                    "Supplier Note (Reason or context for modification)",
                    key=f"modify_note_{po['poid']}",
                    value=po.get("suppliernote") or ""
                )

                # C) Let them propose changes for each item at once
                st.write("#### Item-level Adjustments")
                mod_items = get_purchase_order_items(po["poid"])  # fresh call
                item_proposals = {}
                for it in mod_items:
                    item_id = it["itemid"]
                    sup_qty = it.get("supproposedquantity") or 0
                    sup_price = it.get("supproposedprice") or 0.0

                    st.write(f"**Item {item_id}** - {it['itemnameenglish']}")
                    cA, cB = st.columns(2)
                    new_qty = cA.number_input(
                        f"New Qty (Item {item_id})",
                        min_value=0,
                        value=int(sup_qty),
                        key=f"mod_qty_{po['poid']}_{item_id}"
                    )
                    new_price = cB.number_input(
                        f"New Price (Item {item_id})",
                        min_value=0.0,
                        value=float(sup_price),
                        step=0.1,
                        key=f"mod_price_{po['poid']}_{item_id}"
                    )
                    item_proposals[item_id] = (new_qty, new_price)

                # Single button => "Submit Modification"
                if st.button("Submit Modification", key=f"submit_mod_{po['poid']}"):
                    # 1) Loop items -> update
                    for iid, (q_val, p_val) in item_proposals.items():
                        update_po_item_proposal(
                            poid=po["poid"],
                            itemid=iid,
                            sup_qty=q_val,
                            sup_price=p_val
                        )
                    # 2) propose entire PO => sets Status = 'Proposed by Supplier'
                    propose_entire_po(
                        poid=po["poid"],
                        sup_proposed_deliver=combined_dt,
                        supplier_note=mod_note
                    )
                    st.success("All modifications submitted! Status => Proposed by Supplier.")
                    st.session_state["modify_po_show"][po["poid"]] = False
                    st.experimental_rerun()
