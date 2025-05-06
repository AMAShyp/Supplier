# purchase_order/po_handler.py  (updated)

import base64, io, datetime
from PIL import Image
from db_handler import run_query, run_transaction


# ----------------------------------------------------------------------
# PO‑level queries (unchanged)
# ----------------------------------------------------------------------

def get_purchase_orders_for_supplier(supplier_id):
    query = """
    SELECT POID, OrderDate, ExpectedDelivery, Status,
           SupProposedDeliver, OriginalPOID, SupplierNote, RespondedAt
    FROM PurchaseOrders
    WHERE SupplierID = %s
      AND Status IN ('Pending','Accepted','Shipping')
    ORDER BY OrderDate DESC;
    """
    return run_query(query, (supplier_id,))


def get_archived_purchase_orders(supplier_id):
    query = """
    SELECT POID, OrderDate, ExpectedDelivery, Status,
           SupProposedDeliver, OriginalPOID, SupplierNote, RespondedAt
    FROM PurchaseOrders
    WHERE SupplierID = %s
      AND Status IN ('Declined','Declined by AMAS','Declined by Supplier',
                     'Delivered','Completed')
    ORDER BY OrderDate DESC;
    """
    return run_query(query, (supplier_id,))


def update_purchase_order_status(poid, status,
                                 expected_delivery=None, supplier_note=None):
    query = """
    UPDATE PurchaseOrders
    SET Status = %s,
        ExpectedDelivery = COALESCE(%s, ExpectedDelivery),
        SupplierNote     = COALESCE(%s, SupplierNote),
        RespondedAt      = NOW()
    WHERE POID = %s;
    """
    run_transaction(query, (status, expected_delivery, supplier_note, poid))


def propose_entire_po(poid, sup_proposed_deliver=None, supplier_note=None):
    query = """
    UPDATE PurchaseOrders
    SET Status            = 'Proposed by Supplier',
        SupProposedDeliver = COALESCE(%s, SupProposedDeliver),
        SupplierNote       = COALESCE(%s, SupplierNote),
        RespondedAt        = NOW()
    WHERE POID = %s;
    """
    run_transaction(query, (sup_proposed_deliver, supplier_note, poid))


# ----------------------------------------------------------------------
# Item‑level helpers  (NOW WITH SupExpirationDate)
# ----------------------------------------------------------------------

def get_purchase_order_items(poid):
    """Return list of dicts – each item now includes 'supexpirationdate'."""
    query = """
    SELECT i.ItemID,
           i.ItemNameEnglish,
           encode(i.ItemPicture,'base64') AS ItemPicture,
           poi.OrderedQuantity,
           poi.EstimatedPrice,
           poi.SupProposedQuantity,
           poi.SupProposedPrice,
           poi.SupExpirationDate          -- NEW
    FROM PurchaseOrderItems poi
    JOIN Item i ON poi.ItemID = i.ItemID
    WHERE poi.POID = %s;
    """
    rows = run_query(query, (poid,))
    if not rows:
        return []

    # convert pictures to data‑URI
    for itm in rows:
        raw = itm["itempicture"]
        if raw:
            try:
                img_bytes = base64.b64decode(raw)
                img = Image.open(io.BytesIO(img_bytes))
                fmt = (img.format or "PNG").lower()
                buf = io.BytesIO(); img.save(buf, format=img.format or "PNG")
                itm["itempicture"] = (
                    f"data:image/{'jpeg' if fmt in ('jpeg','jpg') else 'png'};"
                    f"base64,{base64.b64encode(buf.getvalue()).decode()}"
                )
            except Exception:
                itm["itempicture"] = None
    return rows


def update_po_item_proposal(
    poid, itemid, sup_qty=None, sup_price=None, sup_exp_date=None
):
    """
    Store supplier‑proposed qty, price, and expiration date for one item,
    then mark entire PO as 'Proposed by Supplier' + RespondedAt = NOW().
    """
    query_item = """
    UPDATE PurchaseOrderItems
    SET SupProposedQuantity = COALESCE(%s, SupProposedQuantity),
        SupProposedPrice    = COALESCE(%s, SupProposedPrice),
        SupExpirationDate   = COALESCE(%s, SupExpirationDate)
    WHERE POID   = %s
      AND ItemID = %s;
    """
    run_transaction(query_item, (sup_qty, sup_price, sup_exp_date, poid, itemid))

    query_po = """
    UPDATE PurchaseOrders
    SET Status      = 'Proposed by Supplier',
        RespondedAt = NOW()
    WHERE POID = %s;
    """
    run_transaction(query_po, (poid,))
