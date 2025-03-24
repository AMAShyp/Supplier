from db_handler import run_query

# List of required fields with their labels
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
    """Retrieve supplier record by email."""
    query = "SELECT * FROM supplier WHERE contactemail = %s"
    result = run_query(query, (email,))
    return result[0] if result else None

def create_supplier(contactemail):
    """Insert a new supplier record with minimal data (empty name)."""
    query = """
    INSERT INTO supplier (suppliername, contactemail)
    VALUES (%s, %s)
    RETURNING supplierid, suppliername, contactemail;
    """
    params = ("", contactemail)  # 🔥 Supplier name left empty for user input
    result = run_query(query, params)
    return result[0] if result else None

def get_or_create_supplier(contactemail):
    """Fetch supplier by email; create if not exists."""
    supplier = get_supplier_by_email(contactemail)
    return supplier if supplier else create_supplier(contactemail)

def get_missing_fields(supplier):
    """
    Identify missing required fields for a supplier.
    Ensures we detect `None` or empty values.
    """
    missing_fields = [
        key for key, label in SUPPLIER_FIELDS.items()
        if not supplier.get(key) or supplier[key] == ""
    ]
    return missing_fields

def get_supplier_form_structure():
    """
    Returns a structured dictionary defining the supplier form.
    - Defines the labels for each field.
    - Defines input types (text, select, etc.).
    """
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
    """Updates supplier details based on submitted form data."""
    query = """
    UPDATE supplier
    SET
        suppliername = %s,
        suppliertype = %s,
        country = %s,
        city = %s,
        address = %s,
        postalcode = %s,
        contactname = %s,
        contactphone = %s,
        paymentterms = %s,
        bankdetails = %s
    WHERE supplierid = %s
    """
    params = (
        form_data.get("suppliername", ""),  # 🔥 Now saves user-entered name
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
    run_query(query, params)
