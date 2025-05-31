# purchase_order/po_handler.py
import base64, io
from PIL import Image

from db_handler import get_db

db = get_db()                     # ← cached DatabaseManager singleton
# ----------------------------------------------------------------------
# PO-level queries
# ----------------------------------------------------------------------
def get_purchase_orders_for_supplier(supplier_id: int):
    q = """
        SELECT POID, OrderDate, ExpectedDelivery, Status,
               SupProposedDeliver, OriginalPOID, SupplierNote, RespondedAt
        FROM PurchaseOrders
        WHERE SupplierID = %s
          AND Status IN ('Pending','Accepted','Shipping')
        ORDER BY OrderDate DESC
    """
    return db.fetch(q, (supplier_id,))

def get_archived_purchase_orders(supplier_id: int):
    q = """
        SELECT POID, OrderDate, ExpectedDelivery, Status,
               SupProposedDeliver, OriginalPOID, SupplierNote, RespondedAt
        FROM PurchaseOrders
        WHERE SupplierID = %s
          AND Status IN ('Declined','Declined by AMAS','Declined by Supplier',
                         'Delivered','Completed')
        ORDER BY OrderDate DESC
    """
    return db.fetch(q, (supplier_id,))

def update_purchase_order_status(
    poid: int, status: str, expected_delivery=None, supplier_note=None
):
    q = """
        UPDATE PurchaseOrders
        SET Status = %s,
            ExpectedDelivery = COALESCE(%s, ExpectedDelivery),
            SupplierNote     = COALESCE(%s, SupplierNote),
            RespondedAt      = NOW()
        WHERE POID = %s
    """
    db.execute(q, (status, expected_delivery, supplier_note, poid))

def propose_entire_po(poid: int, sup_proposed_deliver=None, supplier_note=None):
    q = """
        UPDATE PurchaseOrders
        SET Status            = 'Proposed by Supplier',
            SupProposedDeliver = COALESCE(%s, SupProposedDeliver),
            SupplierNote       = COALESCE(%s, SupplierNote),
            RespondedAt        = NOW()
        WHERE POID = %s
    """
    db.execute(q, (sup_proposed_deliver, supplier_note, poid))

# ----------------------------------------------------------------------
# Item-level helpers  (includes SupExpirationDate)
# ----------------------------------------------------------------------
def get_purchase_order_items(poid: int):
    """
    Returns list[dict]; each item includes base64 data-URI in 'itempicture'.
    """
    q = """
        SELECT i.ItemID,
               i.ItemNameEnglish,
               encode(i.ItemPicture,'base64') AS ItemPicture,
               poi.OrderedQuantity,
               poi.EstimatedPrice,
               poi.SupProposedQuantity,
               poi.SupProposedPrice,
               poi.SupExpirationDate
        FROM PurchaseOrderItems poi
        JOIN Item i ON poi.ItemID = i.ItemID
        WHERE poi.POID = %s
    """
    rows = db.fetch(q, (poid,))
    if not rows:
        return []

    for itm in rows:                              # convert raw to data-URI
        raw = itm["itempicture"]
        if not raw:
            continue
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
    poid: int, itemid: int, sup_qty=None, sup_price=None, sup_exp_date=None
):
    # First: update the item row
    q_item = """
        UPDATE PurchaseOrderItems
        SET SupProposedQuantity = COALESCE(%s, SupProposedQuantity),
            SupProposedPrice    = COALESCE(%s, SupProposedPrice),
            SupExpirationDate   = COALESCE(%s, SupExpirationDate)
        WHERE POID = %s
          AND ItemID = %s
    """
    db.execute(q_item, (sup_qty, sup_price, sup_exp_date, poid, itemid))

    # Second: mark the PO as "Proposed by Supplier"
    q_po = """
        UPDATE PurchaseOrders
        SET Status      = 'Proposed by Supplier',
            RespondedAt = NOW()
        WHERE POID = %s
    """
    db.execute(q_po, (poid,))
