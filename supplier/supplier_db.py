# supplier/supplier_handler.py (updated)
from db_handler import DatabaseManager

db = DatabaseManager()

SUPPLIER_FIELDS = {
    "suppliername": "Supplier Name",
    "suppliertype": "Supplier Type",
    "country": "Country",
    "city": "City",
    "address": "Address",
    "postalcode": "Postal Code",
    "contactname": "Contact Name",
    "contactphone": "Contact Phone",
    "paymentterms": "Payment Terms",
    "bankdetails": "Bank Details"
}

def get_supplier_by_email(email):
    query = "SELECT * FROM supplier WHERE contactemail = %s"
    df = db.fetch_df(query, (email,))
    return df.iloc[0].to_dict() if not df.empty else None

def create_supplier(contactemail):
    query = """
    INSERT INTO supplier (suppliername, contactemail)
    VALUES (%s, %s)
    RETURNING supplierid, suppliername, contactemail;
    """
    params = ("", contactemail)
    res = db.execute(query, params, returning=True)
    return {"supplierid": res[0], "suppliername": res[1], "contactemail": res[2]} if res else None

def get_or_create_supplier(contactemail):
    supplier = get_supplier_by_email(contactemail)
    return supplier or create_supplier(contactemail)

def get_missing_fields(supplier):
    return [key for key in SUPPLIER_FIELDS if not supplier.get(key)]

def get_supplier_form_structure():
    return {
        "suppliertype": {"label": "Supplier Type", "type": "select", "options": ["Manufacturer", "Distributor", "Retailer", "Other"]},
        "country": {"label": "Country", "type": "text"},
        "city": {"label": "City", "type": "text"},
        "address": {"label": "Address", "type": "text"},
        "postalcode": {"label": "Postal Code", "type": "text"},
        "contactname": {"label": "Contact Name", "type": "text"},
        "contactphone": {"label": "Contact Phone", "type": "text"},
        "paymentterms": {"label": "Payment Terms", "type": "textarea"},
        "bankdetails": {"label": "Bank Details", "type": "textarea"}
    }

def save_supplier_details(supplierid, form_data):
    query = """
    UPDATE supplier SET
        suppliername = %s, suppliertype = %s, country = %s, city = %s,
        address = %s, postalcode = %s, contactname = %s, contactphone = %s,
        paymentterms = %s, bankdetails = %s
    WHERE supplierid = %s
    """
    params = (
        form_data.get("suppliername", ""),
        form_data.get("suppliertype", ""),
        form_data.get("country", ""),
        form_data.get("city", ""),
        form_data.get("address", ""),
        form_data.get("postalcode", ""),
        form_data.get("contactname", ""),
        form_data.get("contactphone", ""),
        form_data.get("paymentterms", ""),
        form_data.get("bankdetails", ""),
        supplierid,
    )
    db.execute(query, params)
