import sqlite3
import uuid
from utils.db import get_db_connection

class User:
    @staticmethod
    def get_user_by_email(email):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT customer_id, first_name, password FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        return user

    @staticmethod
    def get_admin_by_email(email):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT admin_id, first_name, password FROM admins WHERE email = ?", (email,))
        admin = cursor.fetchone()
        conn.close()
        return admin

    @staticmethod
    def get_admin_by_id(admin_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
        admin = cursor.fetchone()
        conn.close()
        return dict(admin) if admin else None


    @staticmethod
    def get_user_info(customer_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT first_name, last_name FROM users WHERE customer_id = ?', (customer_id,))
        user = cursor.fetchone()
        conn.close()
        return user

    @staticmethod
    def create_user(first_name, last_name, email, password, phone=None, birthdate=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        customer_id = str(uuid.uuid4())
        try:
            cursor.execute('''
                INSERT INTO users (customer_id, first_name, last_name, email, password, phone, birthdate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, first_name, last_name, email, password, phone, birthdate))
            conn.commit()
            return customer_id
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    @staticmethod
    def get_user_details(customer_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT customer_id, first_name, last_name, email, phone, birthdate, user_add, user_img FROM users WHERE customer_id = ?', (customer_id,))
        user = cursor.fetchone()
        conn.close()
        return user

    @staticmethod
    def update_profile(customer_id, first_name, last_name, phone, birthdate):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET first_name = ?, last_name = ?, phone = ?, birthdate = ?
            WHERE customer_id = ?
        ''', (first_name, last_name, phone or None, birthdate or None, customer_id))
        conn.commit()
        conn.close()

    @staticmethod
    def change_password(customer_id, current_password, new_password):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE customer_id = ?', (customer_id,))
        user = cursor.fetchone()
        if not user or user['password'] != current_password:
            conn.close()
            return False
        cursor.execute('UPDATE users SET password = ? WHERE customer_id = ?', (new_password, customer_id))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def update_profile_image(customer_id, image_url):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET user_img = ? WHERE customer_id = ?', (image_url, customer_id))
        conn.commit()
        conn.close()