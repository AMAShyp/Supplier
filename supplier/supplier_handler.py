"""
supplier/supplier_handler.py
Business-logic helpers for Supplier profile CRUD + country/city look-ups.
"""

from typing import Dict, List
import pycountry
import psycopg2       # for error inspection
from db_handler import get_db

db = get_db()         # cached DatabaseManager singleton

# ───────────────────────────────────────────────────────────────
# Static label map
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
# Country / city helpers
# ───────────────────────────────────────────────────────────────
def list_all_countries() -> List[str]:
    """Return ≈250 ISO country names, alphabetically."""
    return sorted(c.name for c in pycountry.countries)

def list_cities_for_country(country: str) -> List[str]:
    """
    Fetch city names from helper table `cities`.  
    If the table doesn't exist (or the country has no rows) → return [].
    """
    q = "SELECT city FROM cities WHERE country = %s ORDER BY city"
    try:
        rows = db.fetch(q, (country,))
        return [r["city"] for r in rows] if rows else []
    except psycopg2.errors.UndefinedTable:
        # first run: table hasn't been created yet ⇒ silently ignore
        return []
    except Exception:
        # any other DB issue ⇒ degrade gracefully
        return []

# ───────────────────────────────────────────────────────────────
# CRUD helpers
# ───────────────────────────────────────────────────────────────
def get_supplier_by_email(email: str) -> Dict | None:
    q = "SELECT * FROM supplier WHERE contactemail = %s"
    return db.fetch_one(q, (email,))

def create_supplier(contactemail: str) -> Dict:
    q = """
        INSERT INTO supplier (suppliername, contactemail)
        VALUES (%s, %s)
        RETURNING *
    """
    return db.execute(q, ("", contactemail), returning=True)

def get_or_create_supplier(contactemail: str) -> Dict:
    return get_supplier_by_email(contactemail) or create_supplier(contactemail)

def get_missing_fields(row: Dict) -> List[str]:
    return [k for k in SUPPLIER_FIELDS if not row.get(k)]

# ───────────────────────────────────────────────────────────────
# Form schema for Streamlit UI
# ───────────────────────────────────────────────────────────────
def get_supplier_form_structure() -> Dict[str, Dict]:
    return {
        "suppliertype": {"label": "Supplier Type", "type": "select",
                         "options": ["Manufacturer", "Distributor",
                                     "Retailer", "Other"]},
        "country":      {"label": "Country", "type": "select",
                         "options": list_all_countries()},
        "city":         {"label": "City",    "type": "dynamic_select"},
        "address":      {"label": "Address", "type": "text"},
        "postalcode":   {"label": "Postal Code", "type": "text"},
        "contactname":  {"label": "Contact Name",  "type": "text"},
        "contactphone": {"label": "Contact Phone", "type": "text"},
        "paymentterms": {"label": "Payment Terms", "type": "textarea"},
        "bankdetails":  {"label": "Bank Details", "type": "textarea"},
    }

# legacy alias
get_form_structure = get_supplier_form_structure

# ───────────────────────────────────────────────────────────────
# Update helper
# ───────────────────────────────────────────────────────────────
def save_supplier_details(supplierid: int, data: Dict):
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
