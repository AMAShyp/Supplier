import streamlit as st
from translation import _

def show_home_page():
    st.title(_("home_title"))
    st.write(_("home_intro"))
