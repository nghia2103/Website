import sqlite3
from utils.db import get_db_connection

class AccountModel:
    @staticmethod
    def get_user_details(customer_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT first_name, last_name FROM users WHERE customer_id = ?', (customer_id,))
        user = cursor.fetchone()
        conn.close()
        return user