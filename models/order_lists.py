# models/order_lists.py
import sqlite3
from utils.db import get_db_connection
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class OrderLists:
    @staticmethod
    def get_orders():
        logger.debug("Fetching orders")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    o.order_id, 
                    u.first_name, 
                    u.last_name, 
                    o.order_date, 
                    o.status,
                    o.order_date AS raw_date
                FROM orders o
                JOIN users u ON o.customer_id = u.customer_id
            """)
            orders = []
            for row in cursor.fetchall():
                order = dict(row)
                cursor.execute("""
                    SELECT 
                        p.product_name, 
                        od.quantity, 
                        ps.size, 
                        od.total_price
                    FROM order_details od
                    JOIN products p ON od.product_id = p.product_id
                    JOIN product_size ps ON od.size_id = ps.size_id
                    WHERE od.order_id = ?
                """, (order['order_id'],))
                order_details = cursor.fetchall()
                order['product_list'] = [f"{detail['product_name']} x{detail['quantity']}" for detail in order_details]
                order['size_list'] = [detail['size'] for detail in order_details]
                order['price_list'] = [detail['total_price'] for detail in order_details]
                formatted_date = datetime.strptime(order['order_date'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y - %I:%M %p')
                order['order_date'] = formatted_date
                order['status_color'] = {
                    'Delivered': 'success',
                    'Pending': 'warning',
                    'Cancelled': 'danger',
                    'Processing': 'info'
                }.get(order['status'], 'secondary')
                orders.append(order)
            logger.debug(f"Retrieved {len(orders)} orders")
            return orders
        except sqlite3.Error as e:
            logger.error(f"Database error in get_orders: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        finally:
            conn.close()