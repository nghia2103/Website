import sqlite3
import uuid
from datetime import datetime
import pytz
from utils.db import get_db_connection
import logging

logger = logging.getLogger(__name__)

class OrderModel:
    @staticmethod
    def create_order(customer_id, items, note, card_info, calendar_info):
        conn = get_db_connection()
        cursor = conn.cursor()
        order_date = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')
        default_store_id = 'ST1'
        cursor.execute('SELECT store_id FROM stores WHERE store_id = ?', (default_store_id,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Cửa hàng mặc định {default_store_id} không tồn tại")
        cursor.execute('''
            INSERT INTO orders (order_id, customer_id, order_date, status, store_id) 
            VALUES (NULL, ?, ?, ?, ?)
        ''', (customer_id, order_date, 'Pending', default_store_id))
        cursor.execute("SELECT order_id FROM orders WHERE rowid = last_insert_rowid()")
        order_id = cursor.fetchone()['order_id']
        total_amount = 0
        for item in items:
            order_detail_id = str(uuid.uuid4())
            cart_id = item.get('cart_id')
            quantity = item.get('quantity', 1)
            price = item.get('price')
            cursor.execute('''
                SELECT product_id, size_id 
                FROM cart 
                WHERE cart_id = ? AND customer_id = ?
            ''', (cart_id, customer_id))
            cart_item = cursor.fetchone()
            if not cart_item:
                conn.rollback()
                conn.close()
                raise ValueError(f"Mục giỏ hàng không tồn tại: cart_id={cart_id}")
            product_id, size_id = cart_item
            cursor.execute('''
                SELECT price, discount 
                FROM products p 
                JOIN product_size ps ON p.product_id = ps.product_id 
                WHERE p.product_id = ? AND ps.size_id = ?
            ''', (product_id, size_id))
            product = cursor.fetchone()
            if not product:
                conn.rollback()
                conn.close()
                raise ValueError(f"Sản phẩm hoặc kích cỡ không tồn tại")
            original_price = float(product['price'])
            discount = float(product['discount'] or 0)
            unit_price = price if price else original_price * (1 - discount / 100)
            total_price = unit_price * quantity
            total_amount += total_price
            cursor.execute('''
                INSERT INTO order_details (order_detail_id, order_id, product_id, size_id, quantity, unit_price, total_price) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (order_detail_id, order_id, product_id, size_id, quantity, unit_price, total_price))
        payment_id = str(uuid.uuid4())
        payment_method = card_info.get('payment_method', 'cod')
        cursor.execute('''
            INSERT INTO payments (payment_id, payment_date, payment_method, order_id, amount) 
            VALUES (?, ?, ?, ?, ?)
        ''', (payment_id, order_date, payment_method, order_id, total_amount))
        for item in items:
            cursor.execute('DELETE FROM cart WHERE cart_id = ? AND customer_id = ?', (item['cart_id'], customer_id))
        conn.commit()
        cursor.execute('SELECT order_id FROM orders WHERE order_id = ?', (order_id,))
        if not cursor.fetchone():
            conn.rollback()
            conn.close()
            raise ValueError(f"Order {order_id} not found after creation")
        conn.close()
        return order_id, total_amount
    
    @staticmethod
    def delete_user_order(customer_id, order_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT status FROM orders WHERE order_id = ? AND customer_id = ?', (order_id, customer_id))
        order = cursor.fetchone()
        if not order:
            conn.close()
            return False, "Không tìm thấy đơn hàng hoặc không thuộc về bạn"
        if order['status'].lower() != 'pending':
            conn.close()
            return False, "Chỉ có thể hủy đơn hàng đang chờ xử lý"
        cursor.execute('DELETE FROM orders WHERE order_id = ? AND customer_id = ?', (order_id, customer_id))
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        if rows_affected == 0:
            return False, "Không thể xóa đơn hàng"
        return True, None