import sqlite3
from utils.db import get_db_connection
import logging

logger = logging.getLogger(__name__)

class CheckoutModel:
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