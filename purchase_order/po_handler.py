import base64
import io
from PIL import Image
from db_handler import run_query, run_transaction

def get_purchase_orders_for_supplier(supplier_id):
    """
    Retrieves only active purchase orders (Pending, Accepted, Shipping)
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
        SupplierNote,
        RespondedAt
    FROM PurchaseOrders
    WHERE SupplierID = %s
      AND Status IN ('Pending', 'Accepted', 'Shipping')
    ORDER BY OrderDate DESC;
    """
    return run_query(query, (supplier_id,))

def get_archived_purchase_orders(supplier_id):
    """
    Retrieves archived purchase orders for this supplier, i.e.
    Declined (any reason), Delivered, Completed, Declined by AMAS, Declined by Supplier.
    """
    query = """
    SELECT
        POID,
        OrderDate,
        ExpectedDelivery,
        Status,
        SupProposedDeliver,
        OriginalPOID,
        SupplierNote,
        RespondedAt
    FROM PurchaseOrders
    WHERE SupplierID = %s
      AND Status IN (
        'Declined',
        'Declined by AMAS',
        'Declined by Supplier',
        'Delivered',
        'Completed'
      )
    ORDER BY OrderDate DESC;
    """
    return run_query(query, (supplier_id,))

def update_purchase_order_status(poid, status, expected_delivery=None, supplier_note=None):
    """
    Updates the unified Status of a purchase order and sets RespondedAt = NOW().
    Optionally adjusts 'ExpectedDelivery' and 'SupplierNote'.
    """
    query = """
    UPDATE PurchaseOrders
    SET
        Status = %s,
        ExpectedDelivery = COALESCE(%s, ExpectedDelivery),
        SupplierNote = COALESCE(%s, SupplierNote),
        RespondedAt = NOW()
    WHERE POID = %s;
    """
    run_transaction(query, (status, expected_delivery, supplier_note, poid))

def propose_entire_po(poid, sup_proposed_deliver=None, supplier_note=None):
    """
    Supplier proposes an overall new delivery date/time,
    sets the PO's status to 'Proposed by Supplier',
    and updates the respondedAt timestamp.
    """
    query = """
    UPDATE PurchaseOrders
    SET
        Status = 'Proposed by Supplier',
        SupProposedDeliver = COALESCE(%s, SupProposedDeliver),
        SupplierNote = COALESCE(%s, SupplierNote),
        RespondedAt = NOW()
    WHERE POID = %s;
    """
    run_transaction(query, (sup_proposed_deliver, supplier_note, poid))

def get_purchase_order_items(poid):
    """
    Retrieves items from PurchaseOrderItems, including:
      - decode ItemPicture to data URI
      - Proposed columns: SupProposedQuantity, SupProposedPrice
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

    # Convert each item’s base64 → data URI
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
    Supplier proposes changes for a specific item, sets the PO status to 'Proposed by Supplier',
    and updates respondedAt to NOW().
    """
    # 1) Update item-level changes
    query_item = """
    UPDATE PurchaseOrderItems
    SET
      SupProposedQuantity = COALESCE(%s, SupProposedQuantity),
      SupProposedPrice = COALESCE(%s, SupProposedPrice)
    WHERE POID = %s
      AND ItemID = %s;
    """
    run_transaction(query_item, (sup_qty, sup_price, poid, itemid))

    # 2) Mark entire PO as Proposed by Supplier, updated responded time
    query_po = """
    UPDATE PurchaseOrders
    SET 
      Status = 'Proposed by Supplier',
      RespondedAt = NOW()
    WHERE POID = %s;
    """
    run_transaction(query_po, (poid,))  
