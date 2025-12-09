import sqlite3
from utils.db import get_db_connection
import logging

logger = logging.getLogger(__name__)

class AuthModel:
    @staticmethod
    def get_user_by_email(email):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT customer_id, first_name, password FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            conn.close()
            if user is None:
                logger.warning(f"No user found for email: {email}")
                return None
            logger.debug(f"User found: customer_id={user['customer_id']}, first_name={user['first_name']}")
            return user
        except sqlite3.Error as e:
            logger.error(f"Database error in get_user_by_email: {str(e)}")
            return None

    @staticmethod
    def get_admin_by_email(email):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT admin_id, first_name, password FROM admins WHERE email = ?", (email,))
            admin = cursor.fetchone()
            conn.close()
            if admin is None:
                logger.warning(f"No admin found for email: {email}")
                return None
            logger.debug(f"Admin found: admin_id={admin['admin_id']}, first_name={admin['first_name']}")
            return admin
        except sqlite3.Error as e:
            logger.error(f"Database error in get_admin_by_email: {str(e)}")
            return None