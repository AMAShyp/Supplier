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
    Displays active POs in a single interface:
      - Supplier can propose item-level changes (qty/price) for each item
      - Supplier can propose new overall delivery + note
      - All changes are submitted in ONE step with a single "Submit Proposals" button
    """
    st.subheader("📦 Track Purchase Orders")

    if "decline_po_show_reason" not in st.session_state:
        st.session_state["decline_po_show_reason"] = {}

    # 1) Fetch active POs
    purchase_orders = get_purchase_orders_for_supplier(supplier["supplierid"])
    if not purchase_orders:
        st.info("No active purchase orders.")
        return

    for po in purchase_orders:
        with st.expander(f"PO ID: {po['poid']} | Status: {po['status']}"):
            st.write(f"**Order Date:** {po['orderdate']}")
            st.write(f"**Current Expected Delivery:** {po['expecteddelivery'] or 'Not Set'}")
            st.write(f"**Current Status:** {po['status']}")
            st.write(f"**Current Supplier Note:** {po.get('suppliernote') or ''}")
            st.write("---")

            # 2) Build a form for BOTH item-level & order-level proposals
            st.write("**Propose Changes** (Single-Submit)")

            # A. Proposed Delivery (optional) and Note for entire PO
            proposed_deliv = st.date_input(
                "Proposed Overall Delivery Date",
                key=f"proposed_deliv_{po['poid']}",
                value=po.get("supproposeddeliver")  # if any
            )
            proposed_note = st.text_area(
                "Supplier Note (Entire PO)",
                key=f"proposed_note_{po['poid']}",
                value=po.get("suppliernote") or ""
            )

            # B. Retrieve items
            items = get_purchase_order_items(po["poid"])
            if not items:
                st.info("No items found for this PO.")
                # Possibly show accept/decline. Then continue
                continue

            st.write("### Items List")
            # We'll build a list for display + user input
            all_item_proposals = []

            # Build DataFrame rows that also let user propose new qty/price
            for it in items:
                item_id = it["itemid"]

                # Display item image
                if it["itempicture"]:
                    img_html = f'<img src="{it["itempicture"]}" width="50" />'
                else:
                    img_html = "No Image"

                # Show current proposed
                sup_qty = it.get("supproposedquantity") or 0
                sup_price = it.get("supproposedprice") or 0.0

                all_item_proposals.append({
                    "itemid": item_id,
                    "img_html": img_html,
                    "item_name": it["itemnameenglish"],
                    "ordered_qty": it["orderedquantity"],
                    "estimated_price": it["estimatedprice"] or 0.0,
                    "current_sup_qty": sup_qty,
                    "current_sup_price": sup_price,
                })

            # Convert to a DataFrame for display
            df_rows = []
            for row in all_item_proposals:
                df_rows.append({
                    "ItemID": row["itemid"],
                    "Picture": row["img_html"],
                    "Item Name": row["item_name"],
                    "OrderedQty": row["ordered_qty"],
                    "EstPrice": row["estimated_price"],
                    # We'll show the current sup props in the table, 
                    # but the actual inputs for new proposals will be below.
                    "SupQty (Existing)": row["current_sup_qty"],
                    "SupPrice (Existing)": row["current_sup_price"]
                })

            df = pd.DataFrame(df_rows, columns=[
                "ItemID", "Picture", "Item Name", "OrderedQty", "EstPrice", 
                "SupQty (Existing)", "SupPrice (Existing)"
            ])
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

            # Now let the user input the new proposals for each item
            st.write("### Update Proposals for Each Item")

            new_item_values = {}
            for row in all_item_proposals:
                i_id = row["itemid"]
                st.write(f"**ItemID {i_id}:** {row['item_name']}")
                c1, c2 = st.columns(2)
                new_qty = c1.number_input(
                    f"Proposed Qty (Item {i_id})",
                    min_value=0,
                    value=int(row["current_sup_qty"]),
                    key=f"prop_qty_{po['poid']}_{i_id}"
                )
                new_price = c2.number_input(
                    f"Proposed Price (Item {i_id})",
                    min_value=0.0,
                    value=float(row["current_sup_price"]),
                    step=0.1,
                    key=f"prop_price_{po['poid']}_{i_id}"
                )
                new_item_values[i_id] = (new_qty, new_price)
                st.write("---")

            # 3) Single "Submit Proposals" button
            if st.button("Submit All Proposals", key=f"submit_all_props_{po['poid']}"):
                # A. Update item-level proposals for each item
                for i_id, (qty_val, price_val) in new_item_values.items():
                    update_po_item_proposal(
                        poid=po["poid"],
                        itemid=i_id,
                        sup_qty=qty_val,
                        sup_price=price_val
                    )
                # B. Update entire PO (delivery date + note) => status to 'Proposed by Supplier'
                propose_entire_po(
                    poid=po["poid"],
                    sup_proposed_deliver=proposed_deliv,
                    supplier_note=proposed_note
                )
                st.success("All proposals submitted! Status => Proposed by Supplier.")
                st.rerun()

            st.write("---")
            st.write("#### Or Respond to PO Without Proposing")

            # Accept / Decline flow
            if po["status"] == "Pending":
                cA, cB = st.columns(2)

                with cA:
                    if st.button("Accept Order", key=f"accept_{po['poid']}"):
                        final_deliv = st.date_input("Final Delivery (Optional)", key=f"deliv_{po['poid']}")
                        update_purchase_order_status(
                            poid=po["poid"],
                            status="Accepted",
                            expected_delivery=final_deliv or None
                        )
                        st.success("Order Accepted!")
                        st.rerun()

                with cB:
                    if not st.session_state["decline_po_show_reason"].get(po["poid"], False):
                        if st.button("Decline Order", key=f"decline_{po['poid']}"):
                            st.session_state["decline_po_show_reason"][po["poid"]] = True
                            st.rerun()
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
                                st.rerun()
                        with dc2:
                            if st.button("Cancel", key=f"cancel_decline_{po['poid']}"):
                                st.session_state["decline_po_show_reason"][po["poid"]] = False
                                st.rerun()

            elif po["status"] == "Accepted":
                if st.button("Mark as Shipping", key=f"ship_{po['poid']}"):
                    update_purchase_order_status(poid=po["poid"], status="Shipping")
                    st.info("Order marked as Shipping.")
                    st.rerun()

            elif po["status"] == "Shipping":
                if st.button("Mark as Delivered", key=f"delivered_{po['poid']}"):
                    update_purchase_order_status(poid=po["poid"], status="Delivered")
                    st.success("Order marked as Delivered.")
                    st.rerun()
