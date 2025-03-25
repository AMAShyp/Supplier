import base64
import io
from PIL import Image
from db_handler import run_query, run_transaction

def get_purchase_orders_for_supplier(supplier_id):
    """
    Retrieves only active purchase orders (e.g., 'Pending', 'Accepted', 'Shipping')
    from PurchaseOrders for this supplier.
    """
    query = """
    SELECT 
        POID,
        OrderDate,
        ExpectedDelivery,
        Status,
        SupProposedDeliver,
        OriginalPOID,
        SupplierNote
    FROM PurchaseOrders
    WHERE SupplierID = %s
      AND Status IN ('Pending', 'Accepted', 'Shipping')
    ORDER BY OrderDate DESC;
    """
    return run_query(query, (supplier_id,))

def get_archived_purchase_orders(supplier_id):
    """
    Retrieves archived purchase orders for this supplier
    (e.g., 'Declined', 'Delivered', 'Completed', 'Declined by Supplier', etc.).
    """
    query = """
    SELECT
        POID,
        OrderDate,
        ExpectedDelivery,
        Status,
        SupProposedDeliver,
        OriginalPOID,
        SupplierNote
    FROM PurchaseOrders
    WHERE SupplierID = %s
      AND Status IN ('Declined', 'Delivered', 'Completed')
    ORDER BY OrderDate DESC;
    """
    return run_query(query, (supplier_id,))

def update_purchase_order_status(poid, status, expected_delivery=None, supplier_note=None):
    """
    Updates the unified Status of a purchase order.
    Optionally adjusts 'ExpectedDelivery' and 'SupplierNote'.
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

def update_po_order_proposal(poid, sup_proposed_deliver=None, supplier_note=None):
    """
    Supplier proposes an overall new delivery date/time (SupProposedDeliver),
    plus an optional note. The Status can remain e.g. 'Proposed' or 'Adjusted' 
    if your system uses that.
    """
    query = """
    UPDATE PurchaseOrders
    SET
        SupProposedDeliver = COALESCE(%s, SupProposedDeliver),
        SupplierNote = COALESCE(%s, SupplierNote)
    WHERE POID = %s;
    """
    run_transaction(query, (sup_proposed_deliver, supplier_note, poid))

def get_purchase_order_items(poid):
    """
    Retrieves all items from PurchaseOrderItems for the given PO.
    Includes:
      - Raw item data (ItemNameEnglish, OrderedQuantity, EstimatedPrice)
      - Proposed columns (SupProposedQuantity, SupProposedPrice)
      - Decodes ItemPicture to base64 data URI for inline display.
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

    # Convert base64 to data:image/... for inline <img> display
    for item in results:
        if item["itempicture"]:
            try:
                raw_b64 = item["itempicture"]
                image_bytes = base64.b64decode(raw_b64)
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

def update_po_item_proposal(poid, itemid, sup_qty=None, sup_price=None):
    """
    Supplier proposes changes for a specific item:
      - SupProposedQuantity
      - SupProposedPrice
    """
    query = """
    UPDATE PurchaseOrderItems
    SET
      SupProposedQuantity = COALESCE(%s, SupProposedQuantity),
      SupProposedPrice = COALESCE(%s, SupProposedPrice)
    WHERE POID = %s
      AND ItemID = %s;
    """
    run_transaction(query, (sup_qty, sup_price, poid, itemid))
