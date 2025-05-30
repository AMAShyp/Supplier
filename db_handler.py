# db_handler.py
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor

NEON_DSN = st.secrets["neon"]["dsn"]

def get_connection():
    try:
        conn = psycopg2.connect(NEON_DSN, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        st.error(f"🚨 Database Connection Error: {e}")
        raise

def run_query(query, params=None):
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                lower_query = query.strip().lower()

                if lower_query.startswith("select") or " returning " in lower_query:
                    return cur.fetchall()
                else:
                    conn.commit()
                    return None
    except Exception as e:
        st.error(f"🚨 Query Execution Error: {e}")
        raise
    finally:
        conn.close()

def run_transaction(query, params=None):
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
            conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"🚨 Transaction Failed: {e}")
        raise
    finally:
        conn.close()
