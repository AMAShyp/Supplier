# purchase_order/track_po.py
import streamlit as st
import pandas as pd
import datetime
from purchase_order.po_handler import (
    get_purchase_orders_for_supplier,
    get_purchase_order_items,
    update_po_item_proposal,
    update_purchase_order_status,
    propose_entire_po,
)

# ----------------------------------------------------------------------
def show_purchase_orders_page(supplier):
    """Active PO page with Accept / Modify / Decline.
       * Modify form: qty, price, expiration, note, delivery → 1 submit.
       * Accept flow: asks for per‑item expiration before final confirm.
    """

    st.subheader("📦 Track Purchase Orders")

    # session helpers
    st.session_state.setdefault("decline_po_show_reason", {})
    st.session_state.setdefault("modify_po_show_form", {})
    st.session_state.setdefault("accept_po_show_exp", {})   # NEW

    po_list = get_purchase_orders_for_supplier(supplier["supplierid"])
    if not po_list:
        st.info("No active purchase orders.")
        return

    for po in po_list:
        poid = po["poid"]

        with st.expander(f"PO ID: {poid} | Status: {po['status']}"):
            # ----- Basic info
            st.write(f"**Order Date:** {po['orderdate']}")
            st.write(f"**Expected Delivery:** {po['expecteddeliver
y'] or 'Not Set'}")
            st.write(f"**Current Status:** {po['status']}")
            st.write(f"**Supplier Note:** {po.get('suppliernote') or ''}")

            # ----- Items table (read‑only)
            items = get_purchase_order_items(poid)
            if items:
                rows = []
                for it in items:
                    rows.append({
                        "ItemID": it["itemid"],
                        "Item Name": it["itemnameenglish"],
                        "OrderedQty": it["orderedquantity"],
                        "EstPrice":  it["estimatedprice"] or "N/A",
                        "SupQty":    it.get("supproposedquantity") or "",
                        "SupPrice":  it.get("supproposedprice") or "",
                        "SupExpDate": it.get("supexpirationdate") or "",
                    })
                st.dataframe(pd.DataFrame(rows))
            else:
                st.info("No items found for this PO.")

            # ==================================================================
            #                       PENDING  ACTIONS
            # ==================================================================
            if po["status"] == "Pending":
                c1, c2, c3 = st.columns(3)

                # ---------------- Accept Order ----------------
                with c1:
                    if not st.session_state["accept_po_show_exp"].get(poid):
                        if st.button("Accept Order", key=f"accept_{poid}"):
                            st.session_state["accept_po_show_exp"][poid] = True
                            st.rerun()
                    else:
                        st.subheader("Enter Expiration Dates then Confirm Accept")
                        exp_dates = {}
                        for it in items:
                            iid = it["itemid"]
                            default_exp = (
                                it.get("supexpirationdate") or datetime.date.today()
                            )
                            exp_dates[iid] = st.date_input(
                                f"Item {iid} Expiration",
                                value=default_exp,
                                key=f"acc_exp_{poid}_{iid}",
                            )

                        # final delivery
                        deliv_date = st.date_input(
                            "Final Delivery Date", key=f"acc_date_{poid}"
                        )
                        deliv_time = st.time_input(
                            "Final Delivery Time", key=f"acc_time_{poid}"
                        )
                        if st.button("Confirm Accept", key=f"acc_confirm_{poid}"):
                            # save each item exp date
                            for iid, ed in exp_dates.items():
                                update_po_item_proposal(
                                    poid, iid, sup_qty=None, sup_price=None, sup_exp_date=ed
                                )
                            # update PO status
                            dt_final = datetime.datetime.combine(deliv_date, deliv_time)
                            update_purchase_order_status(
                                poid, "Accepted", expected_delivery=dt_final
                            )
                            st.success("PO Accepted with expiration dates saved.")
                            st.session_state["accept_po_show_exp"][poid] = False
                            st.rerun()

                # ---------------- Modify Order ----------------
                with c2:
                    if not st.session_state["modify_po_show_form"].get(poid):
                        if st.button("Modify Order", key=f"modify_{poid}"):
                            st.session_state["modify_po_show_form"][poid] = True
                            st.rerun()
                    else:
                        st.subheader("Propose Changes to This Order")

                        def_date, def_time = None, datetime.time(0, 0)
                        if isinstance(po.get("expecteddelivery"), datetime.datetime):
                            def_date = po["expecteddelivery"].date()
                            def_time = po["expecteddelivery"].time()

                        with st.form(key=f"mod_form_{poid}"):
                            p_date = st.date_input(
                                "Proposed Delivery Date", value=def_date,
                                key=f"mod_pdate_{poid}"
                            )
                            p_time = st.time_input(
                                "Proposed Delivery Time", value=def_time,
                                key=f"mod_ptime_{poid}"
                            )
                            p_note = st.text_area(
                                "Supplier Note", value=po.get("suppliernote") or "",
                                key=f"mod_pnote_{poid}"
                            )

                            item_changes = {}
                            for it in items:
                                iid   = it["itemid"]
                                base_qty   = it.get("supproposedquantity") or it["orderedquantity"]
                                base_price = it.get("supproposedprice")    or (it["estimatedprice"] or 0)
                                base_exp   = it.get("supexpirationdate")  or datetime.date.today()

                                st.write(f"Item {iid}: {it['itemnameenglish']}")
                                cA, cB, cC = st.columns(3)
                                qty_in = cA.number_input("Qty", min_value=0,
                                                         value=int(base_qty),
                                                         key=f"mod_qty_{poid}_{iid}")
                                prc_in = cB.number_input("Price", min_value=0.0,
                                                         value=float(base_price),
                                                         step=0.1,
                                                         key=f"mod_prc_{poid}_{iid}")
                                exp_in = cC.date_input("Expiration", value=base_exp,
                                                       key=f"mod_exp_{poid}_{iid}")
                                item_changes[iid] = (qty_in, prc_in, exp_in)
                                st.write("---")

                            if st.form_submit_button("Submit Propose"):
                                for iid, (q, p, e) in item_changes.items():
                                    update_po_item_proposal(poid, iid, q, p, e)

                                propose_entire_po(
                                    poid,
                                    sup_proposed_deliver=datetime.datetime.combine(p_date, p_time),
                                    supplier_note=p_note,
                                )
                                st.success("Proposal sent (status = Proposed by Supplier).")
                                st.session_state["modify_po_show_form"][poid] = False
                                st.rerun()

                # ---------------- Decline Order ----------------
                with c3:
                    if not st.session_state["decline_po_show_reason"].get(poid):
                        if st.button("Decline Order", key=f"decl_{poid}"):
                            st.session_state["decline_po_show_reason"][poid] = True
                            st.rerun()
                    else:
                        dec_reason = st.text_area("Reason:", key=f"dec_note_{poid}")
                        dA, dB = st.columns(2)
                        with dA:
                            if st.button("Confirm Decline", key=f"dec_ok_{poid}"):
                                update_purchase_order_status(poid, "Declined", supplier_note=dec_reason)
                                st.warning("Order Declined.")
                                st.session_state["decline_po_show_reason"][poid] = False
                                st.rerun()
                        with dB:
                            if st.button("Cancel", key=f"dec_cancel_{poid}"):
                                st.session_state["decline_po_show_reason"][poid] = False
                                st.rerun()

            # ==================================================================
            #  Accepted → Shipping → Delivered buttons remain unchanged
            # ==================================================================
            elif po["status"] == "Accepted":
                if st.button("Mark as Shipping", key=f"ship_{poid}"):
                    update_purchase_order_status(poid, "Shipping")
                    st.info("Order marked as Shipping.")
                    st.rerun()
            elif po["status"] == "Shipping":
                if st.button("Mark as Delivered", key=f"deliv_{poid}"):
                    update_purchase_order_status(poid, "Delivered")
                    st.success("Order marked as Delivered.")
                    st.rerun()
