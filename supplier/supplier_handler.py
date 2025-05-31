# supplier/supplier_handler.py
"""Business-logic helpers for Supplier profile CRUD."""

from typing import Dict, List
from db_handler import get_db

db = get_db()                # cached DatabaseManager singleton

# ───────────────────────────────────────────────────────────────
# Field metadata (label shown in the profile form)
# ───────────────────────────────────────────────────────────────
SUPPLIER_FIELDS: Dict[str, str] = {
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

# ───────────────────────────────────────────────────────────────
# CRUD helpers
# ───────────────────────────────────────────────────────────────
def get_supplier_by_email(email: str) -> Dict | None:
    """Return the supplier row for a given contact email, or None."""
    q = "SELECT * FROM supplier WHERE contactemail = %s"
    return db.fetch_one(q, (email,))

def create_supplier(contactemail: str) -> Dict:
    """Insert a minimal supplier record (blank name) and return the new row."""
    q = """
        INSERT INTO supplier (suppliername, contactemail)
        VALUES (%s, %s)
        RETURNING *
    """
    return db.execute(q, ("", contactemail), returning=True)

def get_or_create_supplier(contactemail: str) -> Dict:
    """Fetch supplier by email or create one if absent."""
    return get_supplier_by_email(contactemail) or create_supplier(contactemail)

def get_missing_fields(supplier_row: Dict) -> List[str]:
    """Return list of required columns that are NULL / empty for this supplier."""
    return [k for k in SUPPLIER_FIELDS if not supplier_row.get(k)]

# ───────────────────────────────────────────────────────────────
# Profile-form schema handed to Streamlit UI
# ───────────────────────────────────────────────────────────────
def get_supplier_form_structure() -> Dict[str, Dict]:
    """
    Metadata for dynamic form rendering:
    {field_key: {label, type, options?}}
    """
    return {
        "suppliertype": {"label": "Supplier Type", "type": "select",
                         "options": ["Manufacturer", "Distributor",
                                     "Retailer", "Other"]},
        "country":      {"label": "Country",       "type": "text"},
        "city":         {"label": "City",          "type": "text"},
        "address":      {"label": "Address",       "type": "text"},
        "postalcode":   {"label": "Postal Code",   "type": "text"},
        "contactname":  {"label": "Contact Name",  "type": "text"},
        "contactphone": {"label": "Contact Phone", "type": "text"},
        "paymentterms": {"label": "Payment Terms", "type": "textarea"},
        "bankdetails":  {"label": "Bank Details",  "type": "textarea"},
    }

# (Optional) legacy alias so older code calling get_form_structure() keeps working
get_form_structure = get_supplier_form_structure

# ───────────────────────────────────────────────────────────────
# Update helper
# ───────────────────────────────────────────────────────────────
def save_supplier_details(supplierid: int, data: Dict):
    """Persist edits from the profile form."""
    q = """
        UPDATE supplier
        SET suppliername = %s, suppliertype = %s, country = %s, city = %s,
            address = %s, postalcode = %s, contactname = %s, contactphone = %s,
            paymentterms = %s, bankdetails = %s
        WHERE supplierid = %s
    """
    params = (
        data.get("suppliername", ""), data.get("suppliertype", ""),
        data.get("country", ""),      data.get("city", ""),
        data.get("address", ""),      data.get("postalcode", ""),
        data.get("contactname", ""),  data.get("contactphone", ""),
        data.get("paymentterms", ""), data.get("bankdetails", ""),
        supplierid,
    )
    db.execute(q, params)
