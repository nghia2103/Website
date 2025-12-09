import sqlite3
import uuid
from utils.db import get_db_connection
import logging

logger = logging.getLogger(__name__)

class CartModel:
    @staticmethod
    def get_cart(customer_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.cart_id, c.product_id, c.quantity, c.size_id, ps.size, ps.price, 
                   p.product_name, p.image_url, p.discount
            FROM cart c
            JOIN product_size ps ON c.size_id = ps.size_id
            JOIN products p ON c.product_id = p.product_id
            WHERE c.customer_id = ?
        ''', (customer_id,))
        cart_items = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return cart_items

    @staticmethod
    def add_to_cart(customer_id, product_id, quantity, size_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ps.size_id, ps.price, p.discount 
            FROM product_size ps
            JOIN products p ON ps.product_id = p.product_id
            WHERE ps.product_id = ? AND ps.size_id = ?
        ''', (product_id, size_id))
        size_data = cursor.fetchone()
        if not size_data:
            conn.close()
            raise ValueError("Kích thước không hợp lệ")
        cart_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO cart (cart_id, customer_id, product_id, size_id, quantity)
            VALUES (?, ?, ?, ?, ?)
        ''', (cart_id, customer_id, product_id, size_id, quantity))
        conn.commit()
        conn.close()
        return cart_id, size_data['price'], size_data['discount'] or 0

    @staticmethod
    def update_cart_item(customer_id, cart_id, quantity):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE cart 
            SET quantity = ? 
            WHERE cart_id = ? AND customer_id = ?
        ''', (quantity, cart_id, customer_id))
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_affected

    @staticmethod
    def remove_from_cart(customer_id, cart_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart WHERE cart_id = ? AND customer_id = ?', (cart_id, customer_id))
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        return rows_affected