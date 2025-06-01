# purchase_order/track_po.py
import streamlit as st
import pandas as pd
import datetime
from translation import _
from purchase_order.po_handler import (
    get_purchase_orders_for_supplier,
    get_purchase_order_items,
    update_po_item_proposal,
    update_purchase_order_status,
    propose_entire_po,
)

# -----------------------------------------------------------------------------
def show_purchase_orders_page(supplier):
    """Active PO page with Accept / Modify / Decline.
       * Accept flow collects per‑item expiration dates.
       * Modify flow lets user propose qty / price / expiration / note / delivery.
    """

    st.subheader(_("track_po_header"))

    st.session_state.setdefault("decline_po_show_reason", {})
    st.session_state.setdefault("modify_po_show_form", {})
    st.session_state.setdefault("accept_po_show_exp", {})

    po_list = get_purchase_orders_for_supplier(supplier["supplierid"])
    if not po_list:
        st.info(_("no_active_pos"))
        return

    # -------------------------------------------------------------------------
    for po in po_list:
        poid = po["poid"]

        with st.expander(_("po_expander", id=poid, status=po['status'])):
            # ----- Basic info
            st.write(_("order_date", date=po['orderdate']))
            st.write(_("expected_delivery", date=po['expecteddelivery'] or _('not_set')))
            st.write(_("current_status", status=po['status']))
            st.write(_("supplier_note", note=po.get('suppliernote') or ''))

            # ----- Items (read‑only table)
            items = get_purchase_order_items(poid)
            if items:
                rows = [{
                    "ItemID": it["itemid"],
                    "Item Name": it["itemnameenglish"],
                    "OrderedQty": it["orderedquantity"],
                    "EstPrice":  it["estimatedprice"] or "N/A",
                    "SupQty":     it.get("supproposedquantity") or "",
                    "SupPrice":   it.get("supproposedprice") or "",
                    "SupExpDate": it.get("supexpirationdate") or "",
                } for it in items]
                st.dataframe(pd.DataFrame(rows))
            else:
                st.info(_("no_items_found_po"))

            # ==================================================================
            #                          PENDING ACTIONS
            # ==================================================================
            if po["status"] == "Pending":
                c1, c2, c3 = st.columns(3)

                # ---------------- Accept Order ----------------
                with c1:
                    if not st.session_state["accept_po_show_exp"].get(poid):
                        if st.button(_("accept_order_btn"), key=f"accept_{poid}"):
                            st.session_state["accept_po_show_exp"][poid] = True
                            st.rerun()
                    else:
                        st.subheader(_("enter_expiration"))
                        exp_dates = {}
                        for it in items:
                            iid = it["itemid"]
                            default_exp = it.get("supexpirationdate") or datetime.date.today()
                            exp_dates[iid] = st.date_input(
                                _( "item_expiration", id=iid ), value=default_exp,
                                key=f"acc_exp_{poid}_{iid}"
                            )
                        d_date = st.date_input(_("final_delivery_date"), key=f"acc_date_{poid}")
                        d_time = st.time_input(_("final_delivery_time"), key=f"acc_time_{poid}")

                        if st.button(_("confirm_accept"), key=f"acc_confirm_{poid}"):
                            for iid, exp in exp_dates.items():
                                update_po_item_proposal(poid, iid, None, None, exp)
                            update_purchase_order_status(
                                poid, "Accepted",
                                expected_delivery=datetime.datetime.combine(d_date, d_time)
                            )
                            st.success(_("po_accepted_msg"))
                            st.session_state["accept_po_show_exp"][poid] = False
                            st.rerun()

                # ---------------- Modify Order ----------------
                with c2:
                    if not st.session_state["modify_po_show_form"].get(poid):
                        if st.button(_("modify_order_btn"), key=f"modify_{poid}"):
                            st.session_state["modify_po_show_form"][poid] = True
                            st.rerun()
                    else:
                        st.subheader(_("propose_changes_header"))

                        def_date, def_time = None, datetime.time(0, 0)
                        if isinstance(po.get("expecteddelivery"), datetime.datetime):
                            def_date = po["expecteddelivery"].date()
                            def_time = po["expecteddelivery"].time()

                        with st.form(key=f"mod_form_{poid}"):
                            p_date = st.date_input(_("proposed_delivery_date"),
                                                   value=def_date,
                                                   key=f"mod_pdate_{poid}")
                            p_time = st.time_input(_("proposed_delivery_time"),
                                                   value=def_time,
                                                   key=f"mod_ptime_{poid}")
                            p_note = st.text_area(_("supplier_note_label"),
                                                  value=po.get("suppliernote") or "",
                                                  key=f"mod_pnote_{poid}")

                            st.write(_("item_level_changes"))
                            item_changes = {}
                            for it in items:
                                iid = it["itemid"]
                                base_qty   = it.get("supproposedquantity") or it["orderedquantity"]
                                base_price = it.get("supproposedprice")    or (it["estimatedprice"] or 0)
                                base_exp   = it.get("supexpirationdate")  or datetime.date.today()

                                st.write(_("item_label", id=iid, name=it['itemnameenglish']))
                                cs1, cs2, cs3 = st.columns(3)
                                qty_in = cs1.number_input(_("qty_label"), min_value=0,
                                                          value=int(base_qty),
                                                          key=f"mod_qty_{poid}_{iid}")
                                prc_in = cs2.number_input(_("price_label"), min_value=0.0,
                                                          value=float(base_price),
                                                          step=0.1,
                                                          key=f"mod_prc_{poid}_{iid}")
                                exp_in = cs3.date_input(_("expiration_label"),
                                                        value=base_exp,
                                                        key=f"mod_exp_{poid}_{iid}")
                                item_changes[iid] = (qty_in, prc_in, exp_in)
                                st.write("---")

                            if st.form_submit_button(_("submit_propose_btn")):
                                for iid, (q, p, e) in item_changes.items():
                                    update_po_item_proposal(poid, iid, q, p, e)

                                propose_entire_po(
                                    poid,
                                    sup_proposed_deliver=datetime.datetime.combine(p_date, p_time),
                                    supplier_note=p_note,
                                )
                                st.success(_("proposal_sent"))
                                st.session_state["modify_po_show_form"][poid] = False
                                st.rerun()

                # ---------------- Decline Order ----------------
                with c3:
                    if not st.session_state["decline_po_show_reason"].get(poid):
                        if st.button(_("decline_order_btn"), key=f"decl_{poid}"):
                            st.session_state["decline_po_show_reason"][poid] = True
                            st.rerun()
                    else:
                        dec_reason = st.text_area(_("reason_label"), key=f"dec_note_{poid}")
                        d1, d2 = st.columns(2)
                        with d1:
                            if st.button(_("confirm_decline"), key=f"dec_ok_{poid}"):
                                update_purchase_order_status(poid, "Declined",
                                                             supplier_note=dec_reason)
                                st.warning(_("order_declined_msg"))
                                st.session_state["decline_po_show_reason"][poid] = False
                                st.rerun()
                        with d2:
                            if st.button(_("cancel_btn"), key=f"dec_cancel_{poid}"):
                                st.session_state["decline_po_show_reason"][poid] = False
                                st.rerun()

            # ---------------- Post‑pending buttons ----------------
            elif po["status"] == "Accepted":
                if st.button(_("mark_shipping_btn"), key=f"ship_{poid}"):
                    update_purchase_order_status(poid, "Shipping")
                    st.info(_("order_marked_shipping")); st.rerun()

            elif po["status"] == "Shipping":
                if st.button(_("mark_delivered_btn"), key=f"deliv_{poid}"):
                    update_purchase_order_status(poid, "Delivered")
                    st.success(_("order_marked_delivered")); st.rerun()
