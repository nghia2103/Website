import sqlite3
from utils.db import get_db_connection

class SignupModel:
    @staticmethod
    def email_exists(email):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    @staticmethod
    def create_user(first_name, last_name, email, password):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (first_name, last_name, email, password, phone, birthdate) VALUES (?, ?, ?, ?, ?, ?)",
            (first_name, last_name, email, password, None, None)
        )
        conn.commit()
        conn.close()