import sqlite3
import json
from datetime import datetime
import uuid
from utils.db import get_db_connection
import logging

logger = logging.getLogger(__name__)

class OrderAdmin:
    @staticmethod
    def get_order_options():
        logger.debug("Fetching order options")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT p.product_id, p.product_name, p.discount,
                       (SELECT json_group_array(
                           json_object(
                               'size', ps.size,
                               'price', ps.price,
                               'size_id', ps.size_id
                           )
                       ) FROM product_size ps WHERE ps.product_id = p.product_id) AS sizes
                FROM products p
            """)
            products = [
                {
                    'product_id': row['product_id'],
                    'product_name': row['product_name'],
                    'discount': row['discount'],
                    'sizes': json.loads(row['sizes'])
                }
                for row in cursor.fetchall()
            ]

            cursor.execute('SELECT store_id, store_name FROM stores')
            stores = [{'store_id': row['store_id'], 'store_name': row['store_name']} for row in cursor.fetchall()]

            cursor.execute('SELECT customer_id, first_name, last_name FROM users')
            customers = [{'customer_id': row['customer_id'], 'first_name': row['first_name'], 'last_name': row['last_name']} for row in cursor.fetchall()]

            return {
                'products': products,
                'stores': stores,
                'customers': customers
            }
        except sqlite3.Error as e:
            logger.error(f"Database error in get_order_options: {str(e)}")
            raise Exception(f'Database error: {str(e)}')
        finally:
            conn.close()

    @staticmethod
    def create_order(customer_id, product_id, quantity, store_id, size='M', status='Pending'):
        logger.debug(f"Creating order: customer_id={customer_id}, product_id={product_id}, quantity={quantity}, store_id={store_id}, size={size}, status={status}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if not all([customer_id, product_id, quantity > 0, store_id, size]):
                raise ValueError('Thiếu hoặc sai thông tin bắt buộc')
            if size not in ['S', 'M', 'L']:
                raise ValueError('Kích cỡ không hợp lệ. Phải là S, M, hoặc L')

            cursor.execute('SELECT customer_id FROM users WHERE customer_id = ?', (customer_id,))
            if not cursor.fetchone():
                raise ValueError('ID khách hàng không hợp lệ')

            cursor.execute("""
                SELECT ps.size_id, ps.price, p.discount
                FROM product_size ps
                JOIN products p ON ps.product_id = p.product_id
                WHERE ps.product_id = ? AND ps.size = ?
            """, (product_id, size))
            size_data = cursor.fetchone()
            if not size_data:
                raise ValueError('ID sản phẩm hoặc kích cỡ không hợp lệ')

            size_id = size_data['size_id']
            unit_price = size_data['price']
            total_price = size_data['price'] * quantity * (1 - (size_data['discount'] or 0) / 100)

            cursor.execute('SELECT store_id FROM stores WHERE store_id = ?', (store_id,))
            if not cursor.fetchone():
                raise ValueError('ID cửa hàng không hợp lệ')

            order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            order_id = str(uuid.uuid4())[:8]
            order_detail_id = str(uuid.uuid4())[:8]
            cursor.execute("""
                INSERT INTO orders (order_id, customer_id, order_date, status, store_id)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, customer_id, order_date, status, store_id))

            cursor.execute("""
                INSERT INTO order_details (order_detail_id, order_id, product_id, size_id, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (order_detail_id, order_id, product_id, size_id, quantity, unit_price, total_price))

            conn.commit()

            cursor.execute("""
                SELECT o.order_id, u.first_name, u.last_name, p.product_name, od.quantity, 
                       od.total_price, 
                       o.order_date, o.status, od.product_id, o.store_id, ps.size,
                       CASE
                           WHEN o.status = 'Delivered' THEN 'success'
                           WHEN o.status = 'Pending' THEN 'warning'
                           WHEN o.status = 'Cancelled' THEN 'danger'
                           WHEN o.status = 'Processing' THEN 'info'
                           ELSE 'secondary'
                       END AS status_color
                FROM orders o
                JOIN order_details od ON o.order_id = od.order_id
                JOIN products p ON od.product_id = p.product_id
                JOIN users u ON o.customer_id = u.customer_id
                JOIN product_size ps ON od.size_id = ps.size_id
                WHERE o.order_id = ?
            """, (order_id,))
            order = cursor.fetchone()

            if not order:
                raise Exception('Không lấy được đơn hàng vừa tạo')

            formatted_date = datetime.strptime(order['order_date'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y - %I:%M %p')
            return {
                'order_id': order['order_id'],
                'first_name': order['first_name'],
                'last_name': order['last_name'],
                'products': [{
                    'product_name': order['product_name'],
                    'size': order['size'],
                    'total_price': order['total_price'],
                    'quantity': order['quantity']
                }],
                'order_date': formatted_date,
                'raw_date': order['order_date'],
                'status': order['status'],
                'status_color': order['status_color']
            }
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error in create_order: {str(e)}")
            raise Exception(f'Database error: {str(e)}')
        except ValueError as e:
            conn.rollback()
            logger.error(f"Validation error in create_order: {str(e)}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def update_order(order_id, customer_id, product_id, quantity, store_id, status, size='M'):
        logger.debug(f"Updating order: order_id={order_id}, customer_id={customer_id}, product_id={product_id}, quantity={quantity}, store_id={store_id}, status={status}, size={size}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if not all([customer_id, product_id, quantity > 0, store_id, status, size]):
                raise ValueError('Thiếu hoặc sai thông tin bắt buộc')
            if size not in ['S', 'M', 'L']:
                raise ValueError('Kích cỡ không hợp lệ. Phải là S, M, hoặc L')

            cursor.execute('SELECT order_id FROM orders WHERE order_id = ?', (order_id,))
            if not cursor.fetchone():
                raise ValueError('Không tìm thấy đơn hàng')

            cursor.execute('SELECT customer_id FROM users WHERE customer_id = ?', (customer_id,))
            if not cursor.fetchone():
                raise ValueError('ID khách hàng không hợp lệ')

            cursor.execute("""
                SELECT ps.size_id, ps.price, p.discount
                FROM product_size ps
                JOIN products p ON ps.product_id = p.product_id
                WHERE ps.product_id = ? AND ps.size = ?
            """, (product_id, size))
            size_data = cursor.fetchone()
            if not size_data:
                raise ValueError('ID sản phẩm hoặc kích cỡ không hợp lệ')

            size_id = size_data['size_id']
            unit_price = size_data['price']
            total_price = size_data['price'] * quantity * (1 - (size_data['discount'] or 0) / 100)

            cursor.execute('SELECT store_id FROM stores WHERE store_id = ?', (store_id,))
            if not cursor.fetchone():
                raise ValueError('ID cửa hàng không hợp lệ')

            cursor.execute("""
                UPDATE orders
                SET customer_id = ?, status = ?, store_id = ?
                WHERE order_id = ?
            """, (customer_id, status, store_id, order_id))

            cursor.execute('DELETE FROM order_details WHERE order_id = ?', (order_id,))

            order_detail_id = str(uuid.uuid4())[:8]
            cursor.execute("""
                INSERT INTO order_details (order_detail_id, order_id, product_id, size_id, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (order_detail_id, order_id, product_id, size_id, quantity, unit_price, total_price))

            conn.commit()

            cursor.execute("""
                SELECT o.order_id, u.first_name, u.last_name, p.product_name, od.quantity, 
                       od.total_price, 
                       o.order_date, o.status, od.product_id, o.store_id, ps.size,
                       CASE
                           WHEN o.status = 'Delivered' THEN 'success'
                           WHEN o.status = 'Pending' THEN 'warning'
                           WHEN o.status = 'Cancelled' THEN 'danger'
                           WHEN o.status = 'Processing' THEN 'info'
                           ELSE 'secondary'
                       END AS status_color
                FROM orders o
                JOIN order_details od ON o.order_id = od.order_id
                JOIN products p ON od.product_id = p.product_id
                JOIN users u ON o.customer_id = u.customer_id
                JOIN product_size ps ON od.size_id = ps.size_id
                WHERE o.order_id = ?
            """, (order_id,))
            order = cursor.fetchone()

            if not order:
                raise Exception('Không lấy được đơn hàng vừa cập nhật')

            formatted_date = datetime.strptime(order['order_date'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y - %I:%M %p')
            return {
                'order_id': order['order_id'],
                'first_name': order['first_name'],
                'last_name': order['last_name'],
                'products': [{
                    'product_name': order['product_name'],
                    'size': order['size'],
                    'total_price': order['total_price'],
                    'quantity': order['quantity']
                }],
                'order_date': formatted_date,
                'raw_date': order['order_date'],
                'status': order['status'],
                'status_color': order['status_color']
            }
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error in update_order: {str(e)}")
            raise Exception(f'Database error: {str(e)}')
        except ValueError as e:
            conn.rollback()
            logger.error(f"Validation error in update_order: {str(e)}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_order(order_id):
        logger.debug(f"Deleting order: order_id={order_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT order_id FROM orders WHERE order_id = ?', (order_id,))
            if not cursor.fetchone():
                raise ValueError('Order not found')

            cursor.execute('DELETE FROM orders WHERE order_id = ?', (order_id,))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error in delete_order: {str(e)}")
            raise Exception(f'Database error: {str(e)}')
        except ValueError as e:
            logger.error(f"Validation error in delete_order: {str(e)}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def mark_delivered(order_id):
        logger.debug(f"Marking order delivered: order_id={order_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT order_id FROM orders WHERE order_id = ?', (order_id,))
            if not cursor.fetchone():
                raise ValueError('Order not found')

            cursor.execute("""
                UPDATE orders
                SET status = 'Delivered'
                WHERE order_id = ?
            """, (order_id,))

            conn.commit()

            cursor.execute("""
                SELECT o.order_id, u.first_name, u.last_name, p.product_name, od.quantity, 
                       od.total_price, 
                       o.order_date, o.status, od.product_id, o.store_id, ps.size,
                       CASE
                           WHEN o.status = 'Delivered' THEN 'success'
                           WHEN o.status = 'Pending' THEN 'warning'
                           WHEN o.status = 'Cancelled' THEN 'danger'
                           WHEN o.status = 'Processing' THEN 'info'
                           ELSE 'secondary'
                       END AS status_color
                FROM orders o
                JOIN order_details od ON o.order_id = od.order_id
                JOIN products p ON od.product_id = p.product_id
                JOIN users u ON o.customer_id = u.customer_id
                JOIN product_size ps ON od.size_id = ps.size_id
                WHERE o.order_id = ?
            """, (order_id,))
            order = cursor.fetchone()

            if not order:
                raise Exception('Failed to retrieve updated order')

            formatted_date = datetime.strptime(order['order_date'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y - %I:%M %p')
            return {
                'order_id': order['order_id'],
                'first_name': order['first_name'],
                'last_name': order['last_name'],
                'products': [{
                    'product_name': order['product_name'],
                    'size': order['size'],
                    'total_price': order['total_price'],
                    'quantity': order['quantity']
                }],
                'order_date': formatted_date,
                'raw_date': order['order_date'],
                'status': order['status'],
                'status_color': order['status_color']
            }
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error in mark_delivered: {str(e)}")
            raise Exception(f'Database error: {str(e)}')
        except ValueError as e:
            logger.error(f"Validation error in mark_delivered: {str(e)}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def mark_cancelled(order_id):
        logger.debug(f"Marking order cancelled: order_id={order_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT order_id FROM orders WHERE order_id = ?', (order_id,))
            if not cursor.fetchone():
                raise ValueError('Order not found')

            cursor.execute("""
                UPDATE orders
                SET status = 'Cancelled'
                WHERE order_id = ?
            """, (order_id,))

            conn.commit()

            cursor.execute("""
                SELECT o.order_id, u.first_name, u.last_name, p.product_name, od.quantity, 
                       od.total_price, 
                       o.order_date, o.status, od.product_id, o.store_id, ps.size,
                       CASE
                           WHEN o.status = 'Delivered' THEN 'success'
                           WHEN o.status = 'Pending' THEN 'warning'
                           WHEN o.status = 'Cancelled' THEN 'danger'
                           WHEN o.status = 'Processing' THEN 'info'
                           ELSE 'secondary'
                       END AS status_color
                FROM orders o
                JOIN order_details od ON o.order_id = od.order_id
                JOIN products p ON od.product_id = p.product_id
                JOIN users u ON o.customer_id = u.customer_id
                JOIN product_size ps ON od.size_id = ps.size_id
                WHERE o.order_id = ?
            """, (order_id,))
            order = cursor.fetchone()

            if not order:
                raise Exception('Failed to retrieve updated order')

            formatted_date = datetime.strptime(order['order_date'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y - %I:%M %p')
            return {
                'order_id': order['order_id'],
                'first_name': order['first_name'],
                'last_name': order['last_name'],
                'products': [{
                    'product_name': order['product_name'],
                    'size': order['size'],
                    'total_price': order['total_price'],
                    'quantity': order['quantity']
                }],
                'order_date': formatted_date,
                'raw_date': order['order_date'],
                'status': order['status'],
                'status_color': order['status_color']
            }
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error in mark_cancelled: {str(e)}")
            raise Exception(f'Database error: {str(e)}')
        except ValueError as e:
            logger.error(f"Validation error in mark_cancelled: {str(e)}")
            raise e
        finally:
            conn.close()