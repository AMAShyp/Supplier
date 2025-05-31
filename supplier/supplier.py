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
# Public entry
# ───────────────────────────────────────────────────────────────
def show_supplier_dashboard(supplier: dict):
    """Top-level dashboard wrapper. Call from app.py."""
    st.subheader("📊 Supplier Dashboard")

    display_name = supplier.get("suppliername") or supplier["contactemail"]
    st.markdown(f"Welcome, **{display_name}**")
    st.markdown(f"Supplier ID : **{supplier['supplierid']}**")

    missing = get_missing_fields(supplier)
    if missing:
        _profile_form(
            supplier,
            title="📝 Complete your profile",
            missing_only=True,
            missing_fields=missing,
        )
    else:
        with st.expander("✏️ Edit profile"):
            _profile_form(supplier, title=None, missing_only=False)

    st.divider()
    if st.button("Log out"):
        st.logout()
        st.rerun()

# ───────────────────────────────────────────────────────────────
# Internal helpers
# ───────────────────────────────────────────────────────────────
def _profile_form(
    supplier: dict,
    title: str | None,
    missing_only: bool,
    missing_fields: list[str] | None = None,
):
    schema = get_supplier_form_structure()
    if title:
        st.info(title)

    with st.form("supplier_profile_form", clear_on_submit=False):
        data = {}
        # Capture/choose country first (needed for dynamic city options)
        preselected_country = supplier.get("country", "")
        if (not missing_only) or ("country" in (missing_fields or [])):
            data["country"] = st.selectbox(
                schema["country"]["label"],
                schema["country"]["options"],
                index=_safe_index(schema["country"]["options"], preselected_country),
            )
        else:
            data["country"] = preselected_country

        # Loop over the rest of the fields
        for field_key, field_label in SUPPLIER_FIELDS.items():
            if field_key in ("country",):  # already handled
                continue
            if missing_only and field_key not in (missing_fields or []):
                continue

            meta = schema.get(field_key, {"type": "text"})
            current_value = supplier.get(field_key, "")

            if meta["type"] == "dynamic_select":  # City (dependent)
                city_options = list_cities_for_country(data["country"])
                if city_options:
                    data[field_key] = st.selectbox(
                        meta["label"],
                        city_options,
                        index=_safe_index(city_options, current_value),
                    )
                else:  # fallback to free text
                    data[field_key] = st.text_input(meta["label"], value=current_value)

            elif meta["type"] == "select":
                data[field_key] = st.selectbox(
                    meta["label"],
                    meta["options"],
                    index=_safe_index(meta["options"], current_value),
                )
            elif meta["type"] == "textarea":
                data[field_key] = st.text_area(meta["label"], value=current_value)
            else:
                data[field_key] = st.text_input(meta["label"], value=current_value)

        if st.form_submit_button("💾 Save"):
            save_supplier_details(supplier["supplierid"], data)
            st.success("Profile updated successfully! 🎉")
            st.rerun()

def _safe_index(options: list[str], value: str) -> int:
    """Return list index or 0 if value not present."""
    try:
        return options.index(value)
    except ValueError:
        return 0
