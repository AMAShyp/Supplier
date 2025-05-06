import streamlit as st
import pandas as pd
import datetime
import io
from PIL import Image

from purchase_order.po_handler import (
    get_purchase_orders_for_supplier,
    get_purchase_order_items,
    update_po_item_proposal,
    update_purchase_order_status,
    propose_entire_po
)

# … [imports and heading unchanged] …

def show_purchase_orders_page(supplier):
    st.subheader("📦 Track Purchase Orders")

    # Session‑state helpers
    if "decline_po_show_reason" not in st.session_state:
        st.session_state["decline_po_show_reason"] = {}
    if "modify_po_show_form" not in st.session_state:
        st.session_state["modify_po_show_form"] = {}

    purchase_orders = get_purchase_orders_for_supplier(supplier["supplierid"])
    if not purchase_orders:
        st.info("No active purchase orders.")
        return

    for po in purchase_orders:
        po_key = po["poid"]

        with st.expander(f"PO ID: {po_key} | Status: {po['status']}"):
            st.write(f"**Order Date:** {po['orderdate']}")
            st.write(f"**Expected Delivery:** {po['expecteddelivery'] or 'Not Set'}")
            st.write(f"**Current Status:** {po['status']}")
            st.write(f"**Supplier Note:** {po.get('suppliernote') or ''}")

            # ---------------- Item list (read‑only) ----------------
            items = get_purchase_order_items(po_key)
            if items:
                st.subheader("Ordered Items")
                rows = []
                for it in items:
                    img_html = (
                        f'<img src="{it["itempicture"]}" width="50" />'
                        if it["itempicture"]
                        else "No Image"
                    )

                    rows.append({
                        "ItemID": it["itemid"],
                        "Picture": img_html,
                        "Item Name": it["itemnameenglish"],
                        "OrderedQty": it["orderedquantity"],
                        "EstPrice": it["estimatedprice"] or "N/A",
                        "SupQty": it.get("supproposedquantity") or "",
                        "SupPrice": it.get("supproposedprice") or "",
                    })

                df = pd.DataFrame(rows, columns=[
                    "ItemID", "Picture", "Item Name",
                    "OrderedQty", "EstPrice", "SupQty", "SupPrice"
                ])
                st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)
            else:
                st.info("No items found for this PO.")

            # ============ ACTION BUTTONS (Pending only) ============
            if po["status"] == "Pending":
                col1, col2, col3 = st.columns(3)

                # ---------- Accept ----------
                with col1:
                    if st.button("Accept Order", key=f"accept_{po_key}"):
                        d = st.date_input("Final Delivery (Date)", key=f"final_date_{po_key}")
                        t = st.time_input("Final Delivery (Time)", key=f"final_time_{po_key}")
                        update_purchase_order_status(
                            poid=po_key,
                            status="Accepted",
                            expected_delivery=datetime.datetime.combine(d, t)
                        )
                        st.success("Order Accepted!")
                        st.rerun()

                # ---------- Modify ----------
                with col2:
                    if not st.session_state["modify_po_show_form"].get(po_key, False):
                        if st.button("Modify Order", key=f"modify_{po_key}"):
                            st.session_state["modify_po_show_form"][po_key] = True
                            st.rerun()
                    else:
                        st.subheader("Propose Changes to This Order")

                        # default date/time from ExpectedDelivery
                        def_date, def_time = None, datetime.time(0, 0)
                        if isinstance(po.get("expecteddelivery"), datetime.datetime):
                            def_date = po["expecteddelivery"].date()
                            def_time = po["expecteddelivery"].time()

                        with st.form(key=f"modify_form_{po_key}"):
                            prop_date = st.date_input(
                                "Proposed Delivery Date",
                                value=def_date,
                                key=f"prop_date_{po_key}"
                            )
                            prop_time = st.time_input(
                                "Proposed Delivery Time",
                                value=def_time,
                                key=f"prop_time_{po_key}"
                            )
                            prop_note = st.text_area(
                                "Supplier Note (Entire PO)",
                                key=f"prop_note_{po_key}",
                                value=po.get("suppliernote") or ""
                            )

                            st.write("**Item‑Level Changes**")
                            item_proposals = {}
                            for it in items:
                                i_id = it["itemid"]
                                cur_qty  = int(
                                    it.get("supproposedquantity")
                                    or it["orderedquantity"]      # ← default to ordered
                                )
                                cur_price = float(
                                    it.get("supproposedprice")
                                    or (it["estimatedprice"] or 0)  # ← default to est. price
                                )

                                st.write(f"Item {i_id}: {it['itemnameenglish']}")
                                cA, cB = st.columns(2)
                                qty_in = cA.number_input(
                                    f"Proposed Qty (Item {i_id})",
                                    min_value=0,
                                    value=cur_qty,
                                    key=f"qty_{po_key}_{i_id}"
                                )
                                price_in = cB.number_input(
                                    f"Proposed Price (Item {i_id})",
                                    min_value=0.0,
                                    value=cur_price,
                                    step=0.1,
                                    key=f"price_{po_key}_{i_id}"
                                )
                                item_proposals[i_id] = (qty_in, price_in)
                                st.write("---")

                            if st.form_submit_button("Submit Propose"):
                                for iid, (q, p) in item_proposals.items():
                                    update_po_item_proposal(po_key, iid, q, p)

                                combined_dt = datetime.datetime.combine(prop_date, prop_time)
                                propose_entire_po(po_key, combined_dt, prop_note)

                                st.success("PO Proposed Successfully! Status => Proposed by Supplier.")
                                st.session_state["modify_po_show_form"][po_key] = False
                                st.rerun()

                # ---------- Decline ----------
                with col3:
                    if not st.session_state["decline_po_show_reason"].get(po_key, False):
                        if st.button("Decline Order", key=f"decline_{po_key}"):
                            st.session_state["decline_po_show_reason"][po_key] = True
                            st.rerun()
                    else:
                        st.write("**Reason for Declination**")
                        dec_note = st.text_area("Decline Reason:", key=f"dec_note_{po_key}")
                        d1, d2 = st.columns(2)
                        with d1:
                            if st.button("Confirm Decline", key=f"confirm_dec_{po_key}"):
                                update_purchase_order_status(po_key, "Declined", supplier_note=dec_note)
                                st.warning("Order Declined!")
                                st.session_state["decline_po_show_reason"][po_key] = False
                                st.rerun()
                        with d2:
                            if st.button("Cancel", key=f"cancel_dec_{po_key}"):
                                st.session_state["decline_po_show_reason"][po_key] = False
                                st.rerun()

            # ===== Additional statuses =====
            elif po["status"] == "Accepted":
                if st.button("Mark as Shipping", key=f"ship_{po_key}"):
                    update_purchase_order_status(po_key, "Shipping")
                    st.info("Order marked as Shipping.")
                    st.rerun()

            elif po["status"] == "Shipping":
                if st.button("Mark as Delivered", key=f"delivered_{po_key}"):
                    update_purchase_order_status(po_key, "Delivered")
                    st.success("Order marked as Delivered.")
                    st.rerun()
