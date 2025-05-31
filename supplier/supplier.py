import streamlit as st


def show_supplier_dashboard(supplier):
    """Display the supplier dashboard."""
    st.subheader("\U0001F4CA Supplier Dashboard")
    st.write(f"Welcome, **{supplier['suppliername']}**!")
    st.write(f"Your Supplier ID is: **{supplier['supplierid']}**")

    if st.button("Log out"):
        st.logout()
        st.rerun()
