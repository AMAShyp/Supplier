# supplier/supplier.py
import streamlit as st
from supplier.supplier_handler import (
    SUPPLIER_FIELDS,          # field names → nice labels
    get_missing_fields,
    get_supplier_form_structure,
    save_supplier_details,
)

# --------------------------------------------------------------
# Main dashboard
# --------------------------------------------------------------
def show_supplier_dashboard(supplier: dict):
    """Supplier landing page – profile completeness + quick edit form."""
    st.subheader("📊 Supplier Dashboard")

    # ——— Greeting / quick facts ———
    display_name = supplier.get("suppliername") or supplier["contactemail"]
    st.markdown(f"Welcome, **{display_name}**")
    st.markdown(f"Supplier ID : **{supplier['supplierid']}**")

    # ——— Profile completeness check ———
    missing = get_missing_fields(supplier)
    if missing:
        _show_profile_form(
            supplier,
            title="📝 Complete your profile",
            missing_only=True,
            missing_fields=missing,
        )
    else:
        with st.expander("✏️ Edit profile"):
            _show_profile_form(supplier, title=None, missing_only=False)

    # ——— Logout (nice to keep here) ———
    st.divider()
    if st.button("Log out"):
        st.logout()
        st.rerun()

# --------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------
def _show_profile_form(
    supplier: dict,
    title: str | None,
    missing_only: bool,
    missing_fields: list[str] | None = None,
):
    """Render a Streamlit form for supplier details and save on submit."""
    form_schema = get_supplier_form_structure()
    if title:
        st.info(title)

    with st.form(key="supplier_profile_form", clear_on_submit=False):
        # Collect inputs according to the schema
        submitted_data = {}
        for field_key, field_label in SUPPLIER_FIELDS.items():
            # Skip non-missing fields when we only ask for missing ones
            if missing_only and field_key not in (missing_fields or []):
                continue

            meta = form_schema.get(field_key, {"type": "text"})
            current_value = supplier.get(field_key, "")

            # Render input widgets based on meta["type"]
            if meta["type"] == "select":
                submitted_data[field_key] = st.selectbox(
                    meta["label"], meta["options"], index=_option_index(
                        meta["options"], current_value
                    )
                )
            elif meta["type"] == "textarea":
                submitted_data[field_key] = st.text_area(
                    meta["label"], value=current_value
                )
            else:  # default text input
                submitted_data[field_key] = st.text_input(
                    meta.get("label", field_label), value=current_value
                )

        # Save button
        if st.form_submit_button("💾 Save"):
            save_supplier_details(supplier["supplierid"], submitted_data)
            st.success("Profile updated successfully! 🎉")
            st.rerun()   # reload dashboard with fresh data

# small utility so selectbox picks the current value (else index 0)
def _option_index(options: list[str], current: str) -> int:
    try:
        return options.index(current)
    except ValueError:
        return 0
