import sqlite3
import uuid
from utils.db import get_db_connection
import logging

logger = logging.getLogger(__name__)

class AddressModel:
    @staticmethod
    def get_addresses(customer_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT address_id, contact_name, phone, address, is_default
            FROM addresses
            WHERE customer_id = ?
        ''', (customer_id,))
        addresses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return addresses

    @staticmethod
    def add_address(customer_id, contact_name, phone, address, is_default):
        conn = get_db_connection()
        cursor = conn.cursor()
        address_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO addresses (address_id, customer_id, contact_name, phone, address, is_default)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (address_id, customer_id, contact_name, phone, address, is_default))
        conn.commit()
        conn.close()
        return address_id

    @staticmethod
    def update_address(customer_id, address_id, contact_name, phone, address, is_default):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM addresses WHERE address_id = ? AND customer_id = ?', (address_id, customer_id))
        if not cursor.fetchone():
            conn.close()
            return False
        cursor.execute('''
            UPDATE addresses
            SET contact_name = ?, phone = ?, address = ?, is_default = ?
            WHERE address_id = ? AND customer_id = ?
        ''', (contact_name, phone, address, is_default, address_id, customer_id))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def delete_address(customer_id, address_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM addresses WHERE address_id = ? AND customer_id = ?', (address_id, customer_id))
        if not cursor.fetchone():
            conn.close()
            return False
        cursor.execute('DELETE FROM addresses WHERE address_id = ? AND customer_id = ?', (address_id, customer_id))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def set_default_address(customer_id, address_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM addresses WHERE address_id = ? AND customer_id = ?', (address_id, customer_id))
        if not cursor.fetchone():
            conn.close()
            return False
        cursor.execute('UPDATE addresses SET is_default = 0 WHERE customer_id = ?', (customer_id,))
        cursor.execute('UPDATE addresses SET is_default = 1 WHERE address_id = ? AND customer_id = ?', (address_id, customer_id))
        conn.commit()
        conn.close()
        return True