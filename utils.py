import sqlite3 as sql
import pandas as pd
from flask import session, redirect, render_template, flash
from Encryption import AESCipher

# Encryption setup
key = b'\x89\xcc\x01y\xfd\xbd\xcd=Gv\x99m\xa5\x9f?f\x02\x86\xc9#\xea\xf7\xc3e\xd6\xa0\t\x06D\xad<\x84'
iv = b'w\xdb^K%\\\xf5,`\xc7\xbb\xabs\x1f\x06\x16'
cipher = AESCipher(key, iv)


def connect_db():
    """Establish a database connection."""
    return sql.connect("Library.db")


def fetch_all(query, params=()):
    """Execute a SELECT query and return results as a DataFrame."""
    with connect_db() as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute(query, params)
        return pd.DataFrame(cur.fetchall(), columns=[desc[0] for desc in cur.description])


def execute_query(query, params=()):
    """Execute an INSERT, UPDATE, or DELETE query."""
    with connect_db() as con:
        cur = con.cursor()
        cur.execute(query, params)
        con.commit()


def decrypt_columns(df, columns):
    """Decrypt specified columns in a DataFrame."""
    for col in columns:
        df[col] = df[col].apply(cipher.decrypt)
    return df


def require_login():
    """Redirect user to login page if not logged in."""
    if not session.get('logged_in'):
        return render_template('login.html')


def require_admin_level(level):
    """Check if the user has the required admin level."""
    if session.get('admin', 1) < level:
        flash("Insufficient privileges.")
        return redirect('/')
