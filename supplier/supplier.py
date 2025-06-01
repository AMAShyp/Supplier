"""
supplier/supplier.py
Supplier dashboard page – profile completeness + edit form.
"""

import streamlit as st
from supplier.supplier_handler import (
    SUPPLIER_FIELDS,
    get_missing_fields,
    get_supplier_form_structure,
    save_supplier_details,
    list_cities_for_country,
)

# ───────────────────────────────────────────────────────────────
def show_supplier_dashboard(supplier: dict):
    st.subheader("📊 Supplier Dashboard")

    name = supplier.get("suppliername") or supplier["contactemail"]
    st.markdown(f"Welcome, **{name}**")
    st.markdown(f"Supplier ID : **{supplier['supplierid']}**")

    missing = get_missing_fields(supplier)
    if missing:
        _profile_form(supplier, "📝 Complete your profile",
                      missing_only=True, missing_fields=missing)
    else:
        with st.expander("✏️ Edit profile"):
            _profile_form(supplier, None, missing_only=False)

# ───────────────────────────────────────────────────────────────
def _profile_form(supplier, title, missing_only, missing_fields=None):
    schema = get_supplier_form_structure()
    if title:
        st.info(title)

    with st.form("supplier_profile_form", clear_on_submit=False):
        data = {}

        # ----- Country first (needed for dependent city) -----
        country_options = schema["country"]["options"]
        pre_country = supplier.get("country", "")
        # Default to "Iraq" when the DB value is empty/NULL
        default_country = pre_country or "Iraq"
        data["country"] = st.selectbox(
            schema["country"]["label"],
            country_options,
            index=_safe_index(country_options, default_country),
        )

        # ----- Remaining fields -----
        for key, label in SUPPLIER_FIELDS.items():
            if key == "country":
                continue
            if missing_only and key not in (missing_fields or []):
                continue

            meta = schema.get(key, {"type": "text"})
            current = supplier.get(key, "")

            if meta["type"] == "dynamic_select":  # City
                options = list_cities_for_country(data["country"])
                if options:
                    data[key] = st.selectbox(label, options,
                                             index=_safe_index(options, current))
                else:
                    data[key] = st.text_input(label, value=current)

            elif meta["type"] == "select":
                data[key] = st.selectbox(label, meta["options"],
                                         index=_safe_index(meta["options"], current))
            elif meta["type"] == "textarea":
                data[key] = st.text_area(label, value=current)
            else:
                data[key] = st.text_input(label, value=current)

        if st.form_submit_button("💾 Save"):
            save_supplier_details(supplier["supplierid"], data)
            st.success("Profile updated successfully! 🎉")
            st.rerun()

def _safe_index(options, value):
    """Return options.index(value) or 0 if value not present."""
    try:
        return options.index(value)
    except ValueError:
        return 0
