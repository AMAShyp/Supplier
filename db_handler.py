# db_handler.py
import streamlit as st
import psycopg2
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor

# ─────────────────────────────────────────────────────────────
# 1. Keep one live connection per user session
# ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def _get_conn_cached(dsn: str):
    """Create (once) and return a live PostgreSQL connection."""
    return psycopg2.connect(dsn, cursor_factory=RealDictCursor)

# ─────────────────────────────────────────────────────────────
# 2. Thin database manager (auto-reconnect + helpers)
# ─────────────────────────────────────────────────────────────
class DatabaseManager:
    def __init__(self):
        self.dsn  = st.secrets["neon"]["dsn"]
        self.conn = _get_conn_cached(self.dsn)          # reused across reruns

    # ---------- internals ----------
    def _ensure_live(self):
        """
        1.  Reconnect if Neon closed the socket.
        2.  Roll back if a previous error left the connection in
            TRANSACTION_STATUS_INERROR, otherwise the next query
            would raise `InFailedSqlTransaction`.
        """
        # 1️⃣ reconnect if fully closed
        if self.conn.closed:               # 0 = open, >0 = closed
            _get_conn_cached.clear()
            self.conn = _get_conn_cached(self.dsn)

        # 2️⃣ recover from a failed transaction block
        if (
            self.conn.get_transaction_status()
            == extensions.TRANSACTION_STATUS_INERROR
        ):
            try:
                self.conn.rollback()       # clear the aborted Tx
            except Exception:
                # if rollback itself fails, start fresh
                _get_conn_cached.clear()
                self.conn = _get_conn_cached(self.dsn)
 
    def _retry_if_needed(self, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)                  # first attempt
        except OperationalError:
            _get_conn_cached.clear()                    # reconnect + retry once
            self.conn = _get_conn_cached(self.dsn)
            return fn(*args, **kwargs)

    # ---------- public helpers ----------
    def fetch(self, query: str, params=None):
        """Run SELECT and return list[dict]."""
        def _run():
            with self.conn.cursor() as cur:
                cur.execute(query, params or ())
                return cur.fetchall()
        self._ensure_live()
        return self._retry_if_needed(_run)

    def execute(self, query: str, params=None, returning=False):
        """Run INSERT/UPDATE/DELETE (optionally RETURNING one row)."""
        def _run():
            with self.conn.cursor() as cur:
                cur.execute(query, params or ())
                row = cur.fetchone() if returning else None
            self.conn.commit()
            return row
        self._ensure_live()
        return self._retry_if_needed(_run)

    # handy one-liner for a single row
    def fetch_one(self, query: str, params=None):
        rows = self.fetch(query, params)
        return rows[0] if rows else None

# ─────────────────────────────────────────────────────────────
# 3. Cached singleton for easy import everywhere
# ─────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_db() -> DatabaseManager:
    return DatabaseManager()
