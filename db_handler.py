# db_handler.py (updated for Supplier App)
import streamlit as st
import psycopg2
from psycopg2 import OperationalError
import pandas as pd

@st.cache_resource(show_spinner=False)
def get_conn(dsn: str):
    """Create (once) and return a live PostgreSQL connection."""
    return psycopg2.connect(dsn)

class DatabaseManager:
    def __init__(self):
        self.dsn = st.secrets["neon"]["dsn"]
        self.conn = get_conn(self.dsn)

    def _ensure_live_conn(self):
        if self.conn.closed:
            get_conn.clear()
            self.conn = get_conn(self.dsn)

    def fetch_df(self, query: str, params=None) -> pd.DataFrame:
        self._ensure_live_conn()
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params or ())
                rows = cur.fetchall()
                cols = [c[0] for c in cur.description]
        except OperationalError:
            get_conn.clear()
            self.conn = get_conn(self.dsn)
            with self.conn.cursor() as cur:
                cur.execute(query, params or ())
                rows = cur.fetchall()
                cols = [c[0] for c in cur.description]
        return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame()

    def execute(self, query: str, params=None, returning=False):
        self._ensure_live_conn()
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params or ())
                res = cur.fetchone() if returning else None
            self.conn.commit()
            return res
        except OperationalError:
            get_conn.clear()
            self.conn = get_conn(self.dsn)
            with self.conn.cursor() as cur:
                cur.execute(query, params or ())
                res = cur.fetchone() if returning else None
            self.conn.commit()
            return res
