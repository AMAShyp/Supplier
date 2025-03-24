import base64
import io
from PIL import Image
from db_handler import run_query, run_transaction

def get_purchase_orders_for_supplier(supplier_id):
    """
    Retrieves active purchase orders (Pending, Accepted, Shipping)
    from PurchaseOrders for this supplier.
    """
    query = """
    SELECT 
        POID,
        OrderDate,
        ExpectedDelivery,
        Status,
        SupProposedDeliver,
        ProposedStatus,
        SupplierNote
    FROM PurchaseOrders
    WHERE SupplierID = %s
      AND Status IN ('Pending', 'Accepted', 'Shipping')
    ORDER BY OrderDate DESC;
    """
    return run_query(query, (supplier_id,))

def get_archived_purchase_orders(supplier_id):
    """
    Retrieves archived (Declined, Delivered, Completed) purchase orders for this supplier.
    """
    query = """
    SELECT
        POID,
        OrderDate,
        ExpectedDelivery,
        Status,
        SupProposedDeliver,
        ProposedStatus,
        SupplierNote
    FROM PurchaseOrders
    WHERE SupplierID = %s
      AND Status IN ('Declined', 'Delivered', 'Completed')
    ORDER BY OrderDate DESC;
    """
    return run_query(query, (supplier_id,))

def update_purchase_order_status(poid, status, expected_delivery=None, supplier_note=None):
    """
    Updates main PO status and (optionally) ExpectedDelivery and SupplierNote (if e.g. declining).
    Does NOT set ProposedStatus or SupProposedDeliver. Use update_po_order_proposal for that.
    """
    query = """
    UPDATE PurchaseOrders
    SET
        Status = %s,
        ExpectedDelivery = COALESCE(%s, ExpectedDelivery),
        SupplierNote = COALESCE(%s, SupplierNote)
    WHERE POID = %s;
    """
    run_transaction(query, (status, expected_delivery, supplier_note, poid))

def update_po_order_proposal(poid, proposed_deliver=None, proposed_status=None, supplier_note=None):
    """
    Lets the supplier propose an overall new Delivery Date (SupProposedDeliver)
    and set ProposedStatus to e.g. 'Proposed', plus optionally a note.
    """
    query = """
    UPDATE PurchaseOrders
    SET
        SupProposedDeliver = COALESCE(%s, SupProposedDeliver),
        ProposedStatus = COALESCE(%s, ProposedStatus),
        SupplierNote = COALESCE(%s, SupplierNote)
    WHERE POID = %s;
    """
    run_transaction(query, (proposed_deliver, proposed_status, supplier_note, poid))

def get_purchase_order_items(poid):
    """
    Retrieves items from PurchaseOrderItems, including:
    - ItemNameEnglish, ItemPicture (auto-detect format)
    - OrderedQuantity, EstimatedPrice
    - SupProposedQuantity, SupProposedPrice
    """
    query = """
    SELECT
        i.ItemID,
        i.ItemNameEnglish,
        encode(i.ItemPicture, 'base64') AS ItemPicture,
        poi.OrderedQuantity,
        poi.EstimatedPrice,
        poi.SupProposedQuantity,
        poi.SupProposedPrice
    FROM PurchaseOrderItems poi
    JOIN Item i ON poi.ItemID = i.ItemID
    WHERE poi.POID = %s;
    """
    results = run_query(query, (poid,))
    if not results:
        return []

    # Convert each item’s base64 → data URI for display
    for item in results:
        if item["itempicture"]:
            try:
                raw_b64 = item["itempicture"]
                image_bytes = base64.b64decode(raw_b64)

                # Detect image format
                img = Image.open(io.BytesIO(image_bytes))
                image_format = img.format or "PNG"

                buffer = io.BytesIO()
                img.save(buffer, format=image_format)
                reencoded_b64 = base64.b64encode(buffer.getvalue()).decode()

                if image_format.lower() in ["jpeg", "jpg"]:
                    mime_type = "jpeg"
                elif image_format.lower() == "png":
                    mime_type = "png"
                else:
                    mime_type = "png"

                item["itempicture"] = f"data:image/{mime_type};base64,{reencoded_b64}"
            except Exception:
                item["itempicture"] = None
        else:
            item["itempicture"] = None

    return results

def update_po_item_proposal(poid, itemid, sup_qty, sup_price):
    """
    Saves proposed changes for this item:
      - SupProposedQuantity
      - SupProposedPrice
    """
    query = """
    UPDATE PurchaseOrderItems
    SET
      SupProposedQuantity = %s,
      SupProposedPrice = %s
    WHERE POID = %s
      AND ItemID = %s;
    """
    run_transaction(query, (sup_qty, sup_price, poid, itemid))
