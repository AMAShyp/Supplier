import streamlit as st
import io
from PIL import Image
import pandas as pd
from purchase_order.po_handler import (
    get_purchase_orders_for_supplier,
    get_purchase_order_items,
    update_purchase_order_status,
    propose_entire_po,
    update_po_item_proposal
)

def show_purchase_orders_page(supplier):
    """
    Displays a simple UI with three main buttons for each Pending PO:
      - Accept Order
      - Modify Order (unhides the proposals section)
      - Decline Order
    Once "Modify Order" is clicked, we show item-level proposals & 
    order-level proposals, submitted in one step.
    """
    st.subheader("📦 Track Purchase Orders")

    # For toggling the "decline reason" prompt
    if "decline_po_show_reason" not in st.session_state:
        st.session_state["decline_po_show_reason"] = {}
    # For toggling the "modify order" section
    if "modify_po_show_form" not in st.session_state:
        st.session_state["modify_po_show_form"] = {}

    # Fetch active POs
    purchase_orders = get_purchase_orders_for_supplier(supplier["supplierid"])
    if not purchase_orders:
        st.info("No active purchase orders.")
        return

    for po in purchase_orders:
        with st.expander(f"PO ID: {po['poid']} | Status: {po['status']}"):
            # Basic PO info
            st.write(f"**Order Date:** {po['orderdate']}")
            st.write(f"**Expected Delivery:** {po['expecteddelivery'] or 'Not Set'}")
            st.write(f"**Supplier Proposed Delivery:** {po.get('supproposeddeliver') or 'N/A'}")
            st.write(f"**Current Status:** {po['status']}")
            st.write(f"**Supplier Note:** {po.get('suppliernote') or ''}")

            # Retrieve items
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
                        "Name": it["itemnameenglish"],
                        "OrderedQty": it["orderedquantity"],
                        "EstPrice": it["estimatedprice"] or "N/A",
                        "SupQty (Proposed)": sup_qty,
                        "SupPrice (Proposed)": sup_price
                    })

                df = pd.DataFrame(rows, columns=[
                    "ItemID", "Picture", "Name",
                    "OrderedQty", "EstPrice",
                    "SupQty (Proposed)", "SupPrice (Proposed)"
                ])
                df_html = df.to_html(escape=False, index=False)
                st.markdown(df_html, unsafe_allow_html=True)
            else:
                st.warning("No items found for this PO.")

            st.write("---")

            # MAIN BUTTONS:
            if po["status"] == "Pending":
                st.subheader("Respond to PO")

                col1, col2, col3 = st.columns(3)

                # 1) Accept
                with col1:
                    if st.button("Accept Order", key=f"accept_{po['poid']}"):
                        final_del = st.date_input("Final Delivery (Optional)", key=f"final_delivery_{po['poid']}")
                        update_purchase_order_status(
                            poid=po["poid"],
                            status="Accepted",
                            expected_delivery=final_del or None
                        )
                        st.success("Order Accepted!")
                        st.rerun()

                # 2) Modify Order
                with col2:
                    if not st.session_state["modify_po_show_form"].get(po["poid"], False):
                        if st.button("Modify Order", key=f"modify_{po['poid']}"):
                            st.session_state["modify_po_show_form"][po["poid"]] = True
                            st.rerun()
                    else:
                        st.info("You're currently editing your modifications below...")

                # 3) Decline
                with col3:
                    if not st.session_state["decline_po_show_reason"].get(po["poid"], False):
                        if st.button("Decline Order", key=f"decline_{po['poid']}"):
                            st.session_state["decline_po_show_reason"][po["poid"]] = True
                            st.rerun()
                    else:
                        st.write("**Reason for Declination**")
                        decline_note = st.text_area("Decline Reason:", key=f"decline_note_{po['poid']}")

                        dA, dB = st.columns(2)
                        with dA:
                            if st.button("Confirm Decline", key=f"confirm_decline_{po['poid']}"):
                                update_purchase_order_status(
                                    poid=po["poid"],
                                    status="Declined",
                                    supplier_note=decline_note
                                )
                                st.warning("Order Declined!")
                                st.session_state["decline_po_show_reason"][po["poid"]] = False
                                st.rerun()
                        with dB:
                            if st.button("Cancel", key=f"cancel_decline_{po['poid']}"):
                                st.session_state["decline_po_show_reason"][po["poid"]] = False
                                st.rerun()

                # If user clicked Modify, show single form to propose everything
                if st.session_state["modify_po_show_form"].get(po["poid"], False):
                    st.write("---")
                    st.subheader("Propose Changes to the Entire PO and Items")
                    
                    # A) Proposed Delivery + Note
                    proposed_deliv = st.date_input(
                        "Proposed Delivery Date",
                        key=f"deliv_{po['poid']}",
                        value=po.get("supproposeddeliver")
                    )
                    proposed_note = st.text_area(
                        "Supplier Note (Entire PO)",
                        key=f"note_{po['poid']}",
                        value=po.get("suppliernote") or ""
                    )

                    # B) Proposed item changes
                    st.write("**Propose Item-Level Changes**")
                    updated_item_values = {}
                    if items:
                        for it in items:
                            i_id = it["itemid"]
                            st.write(f"**Item {i_id}: {it['name']}**")
                            c1, c2 = st.columns(2)
                            new_qty = c1.number_input(
                                f"Proposed Qty (Item {i_id})",
                                min_value=0,
                                value=int(it.get("supproposedquantity") or 0),
                                key=f"sup_qty_{po['poid']}_{i_id}"
                            )
                            new_price = c2.number_input(
                                f"Proposed Price (Item {i_id})",
                                min_value=0.0,
                                value=float(it.get("supproposedprice") or 0.0),
                                step=0.1,
                                key=f"sup_price_{po['poid']}_{i_id}"
                            )
                            updated_item_values[i_id] = (new_qty, new_price)
                            st.write("---")

                    # Button: Submit single proposal
                    if st.button("Submit Proposals", key=f"submit_proposals_{po['poid']}"):
                        # 1) Save item-level proposals
                        for i_id, (qty_val, price_val) in updated_item_values.items():
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
                        st.success("All proposals submitted! Status => Proposed by Supplier.")
                        # Hide the form again
                        st.session_state["modify_po_show_form"][po["poid"]] = False
                        st.rerun()

            elif po["status"] == "Accepted":
                # Mark as Shipping
                if st.button("Mark as Shipping", key=f"ship_{po['poid']}"):
                    update_purchase_order_status(poid=po["poid"], status="Shipping")
                    st.info("Order marked as Shipping.")
                    st.rerun()

            elif po["status"] == "Shipping":
                # Mark as Delivered
                if st.button("Mark as Delivered", key=f"delivered_{po['poid']}"):
                    update_purchase_order_status(poid=po["poid"], status="Delivered")
                    st.success("Order marked as Delivered.")
                    st.rerun()
