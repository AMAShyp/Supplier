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
    Displays active POs. Supplier can accept, decline, or propose changes.
    OFRespondedAt is automatically set upon each supplier response.
    """
    st.subheader("📦 Track Purchase Orders")

    if "decline_po_show_reason" not in st.session_state:
        st.session_state["decline_po_show_reason"] = {}

    purchase_orders = get_purchase_orders_for_supplier(supplier["supplierid"])
    if not purchase_orders:
        st.info("No active purchase orders.")
        return

    for po in purchase_orders:
        with st.expander(f"PO ID: {po['poid']} | Status: {po['status']}"):
            st.write(f"**Order Date:** {po['orderdate']}")
            st.write(f"**Expected Delivery:** {po['expecteddelivery'] or 'Not Set'}")
            st.write(f"**Proposed Delivery:** {po.get('supproposeddeliver') or 'N/A'}")
            st.write(f"**Current Status:** {po['status']}")
            st.write(f"**Supplier Note:** {po.get('suppliernote') or ''}")
            # If the DB has a "OFRespondedAt" column:
            responded_at = po.get("ofrespondedat")
            if responded_at:
                st.write(f"**Responded At:** {responded_at}")
            else:
                st.write("**Responded At:** N/A")

            items = get_purchase_order_items(po["poid"])
            if items:
                st.subheader("Ordered Items + Proposed Changes")

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
                        "Name": it["itemnameenglish"],
                        "OrderedQty": it["orderedquantity"],
                        "EstPrice": it["estimatedprice"] or "N/A",
                        "SupQty": sup_qty,
                        "SupPrice": sup_price
                    })

                df = pd.DataFrame(rows, columns=[
                    "ItemID", "Picture", "Name", 
                    "OrderedQty", "EstPrice",
                    "SupQty", "SupPrice"
                ])
                df_html = df.to_html(escape=False, index=False)
                st.markdown(df_html, unsafe_allow_html=True)

                # Supplier proposes item-level changes for one item
                st.write("**Propose Item-Level Changes**")
                item_ids = [str(r["ItemID"]) for r in rows]
                selected_item_id = st.selectbox("Select an item:", item_ids, key=f"sel_item_{po['poid']}")

                if selected_item_id:
                    selected_item_id = int(selected_item_id)
                    c1, c2 = st.columns(2)
                    new_qty = c1.number_input("Proposed Qty", min_value=0, value=0, key=f"qty_{po['poid']}_{selected_item_id}")
                    new_price = c2.number_input("Proposed Price", min_value=0.0, value=0.0, step=0.1, key=f"price_{po['poid']}_{selected_item_id}")

                    if st.button("Submit Item Proposal", key=f"item_prop_{po['poid']}_{selected_item_id}"):
                        update_po_item_proposal(
                            poid=po["poid"],
                            itemid=selected_item_id,
                            sup_qty=new_qty,
                            sup_price=new_price
                        )
                        st.success(f"Item {selected_item_id} changes proposed! Status -> Proposed.")
                        st.rerun()

            # Propose entire PO changes
            st.write("---")
            st.write("**Propose Overall PO Changes**")
            new_deliv = st.date_input("SupProposedDeliver", key=f"delv_{po['poid']}")
            new_note = st.text_area("Supplier Note", key=f"sup_note_{po['poid']}", value=po.get("suppliernote") or "")

            if st.button("Save PO Proposal", key=f"save_po_{po['poid']}"):
                propose_entire_po(
                    poid=po["poid"],
                    sup_proposed_deliver=new_deliv,
                    supplier_note=new_note
                )
                st.success("Entire PO proposal saved! Status -> Proposed.")
                st.rerun()

            # Main order-level responses
            st.write("---")
            if po["status"] == "Pending":
                st.subheader("Respond to Order")
                cA, cB = st.columns(2)

                with cA:
                    if st.button("Accept Order", key=f"accept_{po['poid']}"):
                        # Optionally set a final delivery date
                        final_deliv = st.date_input("Final Delivery (Optional)", key=f"fdeliv_{po['poid']}")
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
                        decline_note = st.text_area("Decline reason:", key=f"decline_nt_{po['poid']}")

                        d1, d2 = st.columns(2)
                        with d1:
                            if st.button("Confirm Decline", key=f"cnf_decline_{po['poid']}"):
                                update_purchase_order_status(
                                    poid=po["poid"],
                                    status="Declined",
                                    supplier_note=decline_note
                                )
                                st.warning("Order Declined!")
                                st.session_state["decline_po_show_reason"][po["poid"]] = False
                                st.rerun()

                        with d2:
                            if st.button("Cancel", key=f"cancel_decl_{po['poid']}"):
                                st.session_state["decline_po_show_reason"][po["poid"]] = False
                                st.rerun()

            elif po["status"] == "Accepted":
                if st.button("Mark as Shipping", key=f"ship_{po['poid']}"):
                    update_purchase_order_status(poid=po["poid"], status="Shipping")
                    st.info("Order status updated to Shipping.")
                    st.rerun()

            elif po["status"] == "Shipping":
                if st.button("Mark as Delivered", key=f"delv_{po['poid']}"):
                    update_purchase_order_status(poid=po["poid"], status="Delivered")
                    st.success("Order status updated to Delivered.")
                    st.rerun()
