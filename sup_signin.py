import streamlit as st

def sign_in_with_google():
    """
    Checks if the user is logged in using Streamlit's built-in OIDC.
    If not, displays a "Log in with Google" button that calls st.login().
    Returns a dictionary with the user's name and email if logged in.
    """
    # 1. Check if the user is logged in
    if not st.experimental_user.is_logged_in:
        st.write("You are not logged in.")
        # Provide a button to start Google login
        if st.button("Log in with Google"):
            st.login()  # Triggers the OIDC flow
        st.stop()  # Stop the script so user can complete sign-in

    # 2. If we reach here, the user is logged in
    user_info = {
        "name": st.experimental_user.name or "",
        "email": st.experimental_user.email or ""
    }
    return user_info
