import streamlit as st
import io
from PIL import Image
import pandas as pd
from purchase_order.po_handler import (
    get_purchase_orders_for_supplier,
    get_purchase_order_items,
    update_purchase_order_status,
    update_po_order_proposal,
    update_po_item_proposal
)

def show_purchase_orders_page(supplier):
    """Displays active purchase orders. Supplier can propose item-level changes (qty/price)
       and also propose an overall new delivery date & status at the order level."""
    st.subheader("📦 Track Purchase Orders")

    # For controlling the 'decline reason' flow
    if "decline_po_show_reason" not in st.session_state:
        st.session_state["decline_po_show_reason"] = {}

    # For controlling "modify item proposal" at item-level
    if "modify_item_proposal" not in st.session_state:
        st.session_state["modify_item_proposal"] = {}

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
            st.write(f"**Proposed Delivery:** {po.get('supproposeddeliver') or 'None'}")
            st.write(f"**Proposed Status:** {po.get('proposedstatus') or 'None'}")
            st.write(f"**Current Status:** {po['status']}")

            # Show items in a table + item-level proposals
            items = get_purchase_order_items(po["poid"])
            if items:
                st.subheader("Ordered Items")

                rows = []
                for item in items:
                    # Build <img> HTML
                    if item["itempicture"]:
                        img_html = f'<img src="{item["itempicture"]}" width="50" />'
                    else:
                        img_html = "No Image"

                    # Proposed quantity/price
                    sup_qty = item.get("supproposedquantity") or ""
                    sup_price = item.get("supproposedprice") or ""

                    rows.append({
                        "ItemID": item["itemid"],
                        "Picture": img_html,
                        "Item Name": item["itemnameenglish"],
                        "Ordered Qty": item["orderedquantity"],
                        "Est. Price": item["estimatedprice"] or "N/A",
                        "SupQty": sup_qty,
                        "SupPrice": sup_price
                    })

                df = pd.DataFrame(rows, columns=[
                    "ItemID", "Picture", "Item Name", 
                    "Ordered Qty", "Est. Price",
                    "SupQty", "SupPrice"
                ])
                df_html = df.to_html(escape=False, index=False)
                st.markdown(df_html, unsafe_allow_html=True)

                # Let the supplier pick an item to propose new qty/price
                st.write("**Propose Changes for an Item**")
                item_ids = [str(r["ItemID"]) for r in rows]
                selected_item = st.selectbox("Select an item to modify:", item_ids, key=f"item_select_{po['poid']}")

                if selected_item:
                    selected_item = int(selected_item)
                    colA, colB = st.columns(2)
                    new_qty = colA.number_input("Proposed Qty", min_value=0, value=0, key=f"qty_{po['poid']}_{selected_item}")
                    new_price = colB.number_input("Proposed Price", min_value=0.0, value=0.0, step=0.1, key=f"price_{po['poid']}_{selected_item}")

                    if st.button("Submit Item Proposal", key=f"submit_item_{po['poid']}_{selected_item}"):
                        update_po_item_proposal(
                            poid=po["poid"],
                            itemid=selected_item,
                            sup_qty=new_qty,
                            sup_price=new_price
                        )
                        st.success(f"Proposed changes saved for item {selected_item}!")
                        st.rerun()

            # Propose entire PO changes (delivery date, proposed status, note, etc.)
            st.write("---")
            st.write("**Propose Overall PO Changes** (like new delivery date, status, or note)")
            new_deliv = st.date_input("SupProposedDeliver", key=f"po_delivery_{po['poid']}")
            new_note = st.text_area("Supplier Note", key=f"po_note_{po['poid']}",
                                    value=po.get("suppliernote") or "")
            if st.button("Save PO Proposal", key=f"save_poprop_{po['poid']}"):
                update_po_order_proposal(
                    poid=po["poid"],
                    proposed_deliver=new_deliv,
                    proposed_status="Proposed",  # or "Adjusted" if you prefer
                    supplier_note=new_note
                )
                st.success("Entire PO proposal saved! Status now 'Proposed'.")
                st.rerun()

            # Supplier Actions at order level
            st.write("---")
            if po["status"] == "Pending":
                st.subheader("Respond to Order")
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("Accept Order", key=f"accept_{po['poid']}"):
                        deliver_date = st.date_input(
                            "Final Delivery Date (If needed)", 
                            key=f"date_{po['poid']}"
                        )
                        update_purchase_order_status(
                            poid=po["poid"],
                            status="Accepted",
                            expected_delivery=deliver_date or None
                        )
                        st.success("Order Accepted!")
                        st.rerun()

                with col2:
                    # Decline with reason
                    if not st.session_state["decline_po_show_reason"].get(po["poid"], False):
                        if st.button("Decline Order", key=f"decline_{po['poid']}"):
                            st.session_state["decline_po_show_reason"][po["poid"]] = True
                            st.rerun()
                    else:
                        st.write("**Reason for Declination**")
                        decline_note = st.text_area("Please provide a reason:", key=f"note_{po['poid']}")

                        confirm_col, cancel_col = st.columns(2)
                        with confirm_col:
                            if st.button("Confirm Decline", key=f"confirm_decline_{po['poid']}"):
                                update_purchase_order_status(
                                    poid=po["poid"],
                                    status="Declined",
                                    supplier_note=decline_note
                                )
                                st.warning("Order Declined!")
                                st.session_state["decline_po_show_reason"][po["poid"]] = False
                                st.rerun()

                        with cancel_col:
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
