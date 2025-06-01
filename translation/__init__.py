# translation/__init__.py
import json
import pathlib
import streamlit as st

TRANSL_DIR = pathlib.Path(__file__).parent
DEFAULT_LANG = "en"
SESSION_KEY = "lang"

# --- load dictionaries once per session ---
@st.cache_resource(show_spinner=False)
def _load_dict(lang: str) -> dict:
    file = TRANSL_DIR / f"{lang}.json"
    return json.loads(file.read_text(encoding="utf8"))

def set_language(lang_code: str):
    st.session_state[SESSION_KEY] = lang_code

def get_language() -> str:
    return st.session_state.get(SESSION_KEY, DEFAULT_LANG)

def _(key: str, **fmt) -> str:
    """Translate key using current language (fallback → key)."""
    lang = get_language()
    dictionary = _load_dict(lang)
    text = dictionary.get(key, key)
    return text.format(**fmt)

def is_rtl() -> bool:
    """Optional: read rtl_langs.txt to decide page direction."""
    rtl_codes = (TRANSL_DIR / "rtl_langs.txt").read_text().split()
    return get_language() in rtl_codes
