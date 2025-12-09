import sqlite3
from utils.db import get_db_connection

class ForgotPasswordModel:
    @staticmethod
    def email_exists(email):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists