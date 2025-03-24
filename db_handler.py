import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor

# Retrieve the Neon DSN from Streamlit secrets
NEON_DSN = st.secrets["neon"]["dsn"]

def get_connection():
    """
    Establish and return a new connection to the Neon PostgreSQL database
    using the DSN provided in the Streamlit secrets.
    """
    try:
        conn = psycopg2.connect(NEON_DSN, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        st.error(f"🚨 Database Connection Error: {e}")
        raise

def run_query(query, params=None):
    """
    Executes a SELECT query or a query with RETURNING clause.
    If it's a modification query (INSERT, UPDATE, DELETE), commits the transaction.
    
    Args:
        query (str): SQL query string.
        params (tuple or list, optional): Query parameters.

    Returns:
        list[dict] or None: Query result as a list of dictionaries, or None for modifications.
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Ensure params is a tuple, even if single element
                params = params if params is not None else ()
                cur.execute(query, params)
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
    """
    Executes a SQL transaction (INSERT, UPDATE, DELETE).
    
    Args:
        query (str): SQL query string.
        params (tuple or list, optional): Query parameters.
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                # Ensure params is a tuple
                params = params if params is not None else ()
                cur.execute(query, params)
            conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"🚨 Transaction Failed: {e}")
        raise
    finally:
        conn.close()
