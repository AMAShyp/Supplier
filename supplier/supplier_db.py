# supplier/supplier_handler.py
from db_handler import get_db

db = get_db()   # ← cached singleton

# ────────────────── metadata for the profile form ──────────────────
SUPPLIER_FIELDS = {
    "suppliername":  "Supplier Name",
    "suppliertype":  "Supplier Type",
    "country":       "Country",
    "city":          "City",
    "address":       "Address",
    "postalcode":    "Postal Code",
    "contactname":   "Contact Name",
    "contactphone":  "Contact Phone",
    "paymentterms":  "Payment Terms",
    "bankdetails":   "Bank Details",
}

# ────────────────── CRUD helpers ──────────────────
def get_supplier_by_email(email: str):
    q = "SELECT * FROM supplier WHERE contactemail = %s"
    return db.fetch_one(q, (email,))

def create_supplier(contactemail: str):
    q = """
        INSERT INTO supplier (suppliername, contactemail)
        VALUES (%s, %s)
        RETURNING supplierid, suppliername, contactemail
    """
    return db.execute(q, ("", contactemail), returning=True)

def get_or_create_supplier(contactemail: str):
    sup = get_supplier_by_email(contactemail)
    return sup or create_supplier(contactemail)

def get_missing_fields(supplier_row: dict):
    return [k for k in SUPPLIER_FIELDS if not supplier_row.get(k)]

def get_form_structure():
    """Returned to Streamlit for dynamic UI building."""
    return {
        "suppliertype": {"label": "Supplier Type", "type": "select",
                         "options": ["Manufacturer", "Distributor", "Retailer", "Other"]},
        "country":      {"label": "Country",       "type": "text"},
        "city":         {"label": "City",          "type": "text"},
        "address":      {"label": "Address",       "type": "text"},
        "postalcode":   {"label": "Postal Code",   "type": "text"},
        "contactname":  {"label": "Contact Name",  "type": "text"},
        "contactphone": {"label": "Contact Phone", "type": "text"},
        "paymentterms": {"label": "Payment Terms", "type": "textarea"},
        "bankdetails":  {"label": "Bank Details",  "type": "textarea"},
    }

def save_supplier_details(supplierid: int, data: dict):
    q = """
        UPDATE supplier
        SET suppliername = %s, suppliertype = %s, country = %s, city = %s,
            address = %s, postalcode = %s, contactname = %s, contactphone = %s,
            paymentterms = %s, bankdetails = %s
        WHERE supplierid = %s
    """
    params = (
        data.get("suppliername", ""), data.get("suppliertype", ""), data.get("country", ""),
        data.get("city", ""),        data.get("address", ""),       data.get("postalcode", ""),
        data.get("contactname", ""), data.get("contactphone", ""),  data.get("paymentterms", ""),
        data.get("bankdetails", ""), supplierid
    )
    db.execute(q, params)
