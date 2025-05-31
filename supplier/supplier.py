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

    st.divider()
    if st.button("Log out"):
        st.logout()
        st.rerun()

# ───────────────────────────────────────────────────────────────
def _profile_form(supplier, title, missing_only, missing_fields=None):
    schema = get_supplier_form_structure()
    if title:
        st.info(title)

    with st.form("supplier_profile_form", clear_on_submit=False):
        data = {}
        # ----- Country first (needed for dependent city) -----
        pre_country = supplier.get("country", "")
        if (not missing_only) or ("country" in (missing_fields or [])):
            data["country"] = st.selectbox(
                schema["country"]["label"],
                schema["country"]["options"],
                index=_safe_index(schema["country"]["options"], pre_country),
            )
        else:
            data["country"] = pre_country

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
    try:
        return options.index(value)
    except ValueError:
        return 0
