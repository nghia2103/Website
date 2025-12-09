# account_model.py
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
    
# admin_model.py
import sqlite3
from utils.db import get_db_connection
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class AdminModel:
    @staticmethod
    def get_dashboard_data(admin_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
            admin = cursor.fetchone()
            if not admin:
                return None, "Tài khoản admin không tồn tại"

            cursor.execute('SELECT COUNT(*) as count FROM users')
            total_users = cursor.fetchone()['count']

            cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'Delivered'")
            total_orders = cursor.fetchone()['count']

            cursor.execute("""
                SELECT SUM(od.total_price) as total 
                FROM order_details od
                JOIN orders o ON od.order_id = o.order_id
                WHERE o.status = 'Delivered'
            """)
            total_sales = cursor.fetchone()['total'] or 0

            cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'Pending'")
            total_pending = cursor.fetchone()['count']

            sales_data = [0] * 12
            cursor.execute("""
                SELECT strftime('%m', o.order_date) as month, SUM(od.total_price) as total
                FROM order_details od
                JOIN orders o ON od.order_id = o.order_id
                WHERE o.status = 'Delivered' AND strftime('%Y', o.order_date) = '2025'
                GROUP BY month
            """)
            for row in cursor:
                month = int(row['month']) - 1
                sales_data[month] = row['total'] / 1_000_000 if row['total'] else 0

            cursor.execute("""
                SELECT p.product_name, s.address as location, o.order_date,
                       od.quantity, od.total_price, o.status
                FROM order_details od
                JOIN products p ON od.product_id = p.product_id
                JOIN orders o ON od.order_id = o.order_id
                JOIN stores s ON o.store_id = s.store_id
                WHERE o.status IN ('Delivered', 'Pending')
                ORDER BY o.order_date DESC
                LIMIT 10
            """)
            deals = []
            for row in cursor:
                status_color = {'Delivered': 'success', 'Pending': 'warning', 'Cancelled': 'danger'}.get(row['status'], 'secondary')
                deals.append({
                    'product_name': row['product_name'],
                    'location': row['location'],
                    'order_date': row['order_date'],
                    'quantity': row['quantity'],
                    'total_price': row['total_price'],
                    'status': row['status'],
                    'status_color': status_color
                })

            return {
                'admin': admin,
                'total_users': total_users,
                'total_orders': total_orders,
                'total_sales': total_sales,
                'total_pending': total_pending,
                'sales_data': sales_data,
                'deals': deals
            }, None
        except sqlite3.Error as e:
            return None, f"Lỗi cơ sở dữ liệu: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def get_order_lists(admin_id):
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
            cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
            admin = cursor.fetchone() or {'first_name': 'Admin', 'last_name': ''}
            return {'orders': orders, 'admin': admin}, None
        except sqlite3.Error as e:
            return None, f"Lỗi cơ sở dữ liệu: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def get_order_options():
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

            return {'products': products, 'stores': stores, 'customers': customers}, None
        except sqlite3.Error as e:
            return None, f"Lỗi cơ sở dữ liệu: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def create_order(data):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            customer_id = data.get('customer_id')
            product_id = data.get('product_id')
            quantity = int(data.get('quantity'))
            store_id = data.get('store_id')
            size = data.get('size', 'M')
            status = data.get('status', 'Pending')

            if not all([customer_id, product_id, quantity > 0, store_id, size]):
                return None, 'Thiếu hoặc sai thông tin bắt buộc'

            if size not in ['S', 'M', 'L']:
                return None, 'Kích cỡ không hợp lệ. Phải là S, M, hoặc L'

            cursor.execute('SELECT customer_id FROM users WHERE customer_id = ?', (customer_id,))
            if not cursor.fetchone():
                return None, 'ID khách hàng không hợp lệ'

            cursor.execute("""
                SELECT ps.size_id, ps.price, p.discount
                FROM product_size ps
                JOIN products p ON ps.product_id = p.product_id
                WHERE ps.product_id = ? AND ps.size = ?
            """, (product_id, size))
            size_data = cursor.fetchone()
            if not size_data:
                return None, 'ID sản phẩm hoặc kích cỡ không hợp lệ'

            size_id = size_data['size_id']
            unit_price = size_data['price']
            total_price = size_data['price'] * quantity * (1 - (size_data['discount'] or 0) / 100)

            cursor.execute('SELECT store_id FROM stores WHERE store_id = ?', (store_id,))
            if not cursor.fetchone():
                return None, 'ID cửa hàng không hợp lệ'

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
                return None, 'Không lấy được đơn hàng vừa tạo'

            formatted_date = datetime.strptime(order['order_date'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y - %I:%M %p')
            return {
                'order_id': order['order_id'],
                'first_name': document['first_name'],
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
            }, None
        except sqlite3.Error as e:
            conn.rollback()
            return None, f'Lỗi cơ sở dữ liệu: {str(e)}'
        finally:
            conn.close()

    @staticmethod
    def update_order(order_id, data):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            customer_id = data.get('customer_id')
            product_id = data.get('product_id')
            quantity = int(data.get('quantity'))
            store_id = data.get('store_id')
            status = data.get('status')
            size = data.get('size', 'M')

            if not all([customer_id, product_id, quantity > 0, store_id, status, size]):
                return None, 'Thiếu hoặc sai thông tin bắt buộc'

            if size not in ['S', 'M', 'L']:
                return None, 'Kích cỡ không hợp lệ. Phải là S, M, hoặc L'

            cursor.execute('SELECT order_id FROM orders WHERE order_id = ?', (order_id,))
            if not cursor.fetchone():
                return None, 'Không tìm thấy đơn hàng'

            cursor.execute('SELECT customer_id FROM users WHERE customer_id = ?', (customer_id,))
            if not cursor.fetchone():
                return None, 'ID khách hàng không hợp lệ'

            cursor.execute("""
                SELECT ps.size_id, ps.price, p.discount
                FROM product_size ps
                JOIN products p ON ps.product_id = p.product_id
                WHERE ps.product_id = ? AND ps.size = ?
            """, (product_id, size))
            size_data = cursor.fetchone()
            if not size_data:
                return None, 'ID sản phẩm hoặc kích cỡ không hợp lệ'

            size_id = size_data['size_id']
            unit_price = size_data['price']
            total_price = size_data['price'] * quantity * (1 - (size_data['discount'] or 0) / 100)

            cursor.execute('SELECT store_id FROM stores WHERE store_id = ?', (store_id,))
            if not cursor.fetchone():
                return None, 'ID cửa hàng không hợp lệ'

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
                return None, 'Không lấy được đơn hàng vừa cập nhật'

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
            }, None
        except sqlite3.Error as e:
            conn.rollback()
            return None, f'Lỗi cơ sở dữ liệu: {str(e)}'
        finally:
            conn.close()

    @staticmethod
    def delete_order(order_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT order_id FROM orders WHERE order_id = ?', (order_id,))
            if not cursor.fetchone():
                return None, 'Order not found'

            cursor.execute('DELETE FROM orders WHERE order_id = ?', (order_id,))
            conn.commit()
            return True, None
        except sqlite3.Error as e:
            conn.rollback()
            return None, f'Database error: {str(e)}'
        finally:
            conn.close()

    @staticmethod
    def mark_delivered(order_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT order_id FROM orders WHERE order_id = ?', (order_id,))
            if not cursor.fetchone():
                return None, 'Order not found'

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
                return None, 'Failed to retrieve updated order'

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
            }, None
        except sqlite3.Error as e:
            conn.rollback()
            return None, f'Database error: {str(e)}'
        finally:
            conn.close()

    @staticmethod
    def mark_cancelled(order_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT order_id FROM orders WHERE order_id = ?', (order_id,))
            if not cursor.fetchone():
                return None, 'Order not found'

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
                return None, 'Failed to retrieve updated order'

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
            }, None
        except sqlite3.Error as e:
            conn.rollback()
            return None, f'Database error: {str(e)}'
        finally:
            conn.close()

    @staticmethod
    def get_products(admin_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT p.product_id, p.product_name, p.stock, p.description, p.image_url,
                       p.discount, p.category, 
                       CASE WHEN f.favorite_id IS NOT NULL THEN 1 ELSE 0 END as favorited,
                       (SELECT ps.price FROM product_size ps WHERE ps.product_id = p.product_id AND ps.size = 'M' LIMIT 1) as price_m,
                       (SELECT CAST(AVG(r.rating) AS REAL)
                        FROM reviews r
                        JOIN orders o ON o.order_id = r.order_id
                        WHERE r.product_id = p.product_id AND o.status = 'Delivered') as avg_rating
                FROM products p
                LEFT JOIN favorites f ON p.product_id = f.product_id AND f.admin_id = ?
            """, (admin_id,))
            products = []
            for row in cursor.fetchall():
                product = dict(row)
                product['avg_rating'] = float(product['avg_rating']) if product['avg_rating'] is not None else 0.0
                products.append(product)
            cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
            admin = cursor.fetchone() or {'first_name': 'Admin', 'last_name': ''}
            return {'products': products, 'admin': admin}, None
        except sqlite3.Error as e:
            return None, f'Lỗi cơ sở dữ liệu: {str(e)}'
        finally:
            conn.close()

    @staticmethod
    def get_product(product_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT product_id, product_name, stock, description, image_url, image_url_2, discount, category
                FROM products
                WHERE product_id = ?
            """, (product_id,))
            product = cursor.fetchone()

            if not product:
                return None, 'Product not found'

            cursor.execute("""
                SELECT size_id, size, price
                FROM product_size
                WHERE product_id = ?
            """, (product_id,))
            sizes = [{'size'}]

            cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
            admin = cursor.fetchone()
            if not admin:
                return None, "Tài khoản admin không tồn tại"

            return {'favorites': favorites, 'admin': dict(admin)}, None
        except sqlite3.Error as e:
            return None, f"Lỗi cơ sở dữ liệu: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def add_favorite(admin_id, product_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT product_id FROM products WHERE product_id = ?', (product_id,))
            if not cursor.fetchone():
                return None, 'Product not found'

            cursor.execute('SELECT favorite_id FROM favorites WHERE admin_id = ? AND product_id = ?', (admin_id, product_id))
            if cursor.fetchone():
                return None, 'Product already in favorites'

            cursor.execute("""
                INSERT INTO favorites (favorite_id, admin_id, product_id)
                VALUES (?, ?, ?)
            """, (str(uuid.uuid4()), admin_id, product_id))
            conn.commit()
            return True, None
        except sqlite3.Error as e:
            conn.rollback()
            return None, f'Lỗi cơ sở dữ liệu: {str(e)}'
        finally:
            conn.close()

    @staticmethod
    def get_user_management_data(admin_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT first_name, last_name, admin_img FROM admins WHERE admin_id = ?', (admin_id,))
            admin = cursor.fetchone()
            if not admin:
                return None, "Tài khoản admin không tồn tại"

            cursor.execute("""
                SELECT customer_id AS user_id, first_name, last_name, email, 'User' AS role
                FROM users
            """)
            users = [dict(row) for row in cursor.fetchall()]

            cursor.execute("""
                SELECT admin_id AS user_id, first_name, last_name, email, 'Admin' AS role
                FROM admins
            """)
            users.extend([dict(row) for row in cursor.fetchall()])

            return {'users': users, 'admin': dict(admin)}, None
        except sqlite3.Error as e:
            return None, f"Lỗi cơ sở dữ liệu: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def add_user(data):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')
            password = data.get('password')
            role = data.get('role')

            if not all([first_name, last_name, email, password, role]):
                return None, 'Thiếu thông tin bắt buộc'

            if role not in ['User', 'Admin']:
                return None, 'Vai trò không hợp lệ'

            if len(password) < 6:
                return None, 'Mật khẩu phải có ít nhất 6 ký tự'

            cursor.execute('SELECT email FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                return None, 'Email đã tồn tại trong bảng users'
            cursor.execute('SELECT email FROM admins WHERE email = ?', (email,))
            if cursor.fetchone():
                return None, 'Email đã tồn tại trong bảng admins'

            if role == 'User':
                cursor.execute("""
                    INSERT INTO users (customer_id, first_name, last_name, email, password)
                    VALUES (NULL, ?, ?, ?, ?)
                """, (first_name, last_name, email, password))
            else:
                cursor.execute("""
                    INSERT INTO admins (admin_id, first_name, last_name, email, password)
                    VALUES (NULL, ?, ?, ?, ?)
                """, (first_name, last_name, email, password))

            conn.commit()

            if role == 'User':
                cursor.execute("SELECT customer_id FROM users WHERE rowid = last_insert_rowid()")
                user_id = cursor.fetchone()['customer_id']
                cursor.execute("""
                    SELECT customer_id AS user_id, first_name, last_name, email, 'User' AS role
                    FROM users
                    WHERE customer_id = ?
                """, (user_id,))
            else:
                cursor.execute("SELECT admin_id FROM admins WHERE rowid = last_insert_rowid()")
                user_id = cursor.fetchone()['admin_id']
                cursor.execute("""
                    SELECT admin_id AS user_id, first_name, last_name, email, 'Admin' AS role
                    FROM admins
                    WHERE admin_id = ?
                """, (user_id,))
            user = cursor.fetchone()

            return dict(user), None
        except sqlite3.Error as e:
            conn.rollback()
            return None, f'Lỗi cơ sở dữ liệu: {str(e)}'
        finally:
            conn.close()

    @staticmethod
    def edit_user(user_id, data):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')
            role = data.get('role')

            if not all([first_name, last_name, email, role]):
                return None, 'Thiếu thông tin bắt buộc'

            if role not in ['User', 'Admin']:
                return None, 'Vai trò không hợp lệ'

            is_admin = False
            cursor.execute('SELECT admin_id, password FROM admins WHERE admin_id = ?', (user_id,))
            admin = cursor.fetchone()
            if admin:
                is_admin = True
            else:
                cursor.execute('SELECT customer_id, password FROM users WHERE customer_id = ?', (user_id,))
                user = cursor.fetchone()
                if not user:
                    return None, 'Tài khoản không tồn tại'

            cursor.execute('SELECT customer_id FROM users WHERE email = ? AND customer_id != ?', (email, user_id))
            if cursor.fetchone():
                return None, 'Email đã tồn tại trong bảng users'
            cursor.execute('SELECT admin_id FROM admins WHERE email = ? AND admin_id != ?', (email, user_id))
            if cursor.fetchone():
                return None, 'Email đã tồn tại trong bảng admins'

            if is_admin and role == 'Admin':
                cursor.execute("""
                    UPDATE admins
                    SET first_name = ?, last_name = ?, email = ?
                    WHERE admin_id = ?
                """, (first_name, last_name, email, user_id))
            elif is_admin and role == 'User':
                cursor.execute('DELETE FROM admins WHERE admin_id = ?', (user_id,))
                cursor.execute("""
                    INSERT INTO users (customer_id, first_name, last_name, email, password)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, first_name, last_name, email, admin['password']))
            elif not is_admin and role == 'User':
                cursor.execute("""
                    UPDATE users
                    SET first_name = ?, last_name = ?, email = ?
                    WHERE customer_id = ?
                """, (first_name, last_name, email, user_id))
            else:
                cursor.execute('DELETE FROM users WHERE customer_id = ?', (user_id,))
                cursor.execute("""
                    INSERT INTO admins (admin_id, first_name, last_name, email, password)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, first_name, last_name, email, user['password']))

            conn.commit()

            if role == 'User':
                cursor.execute("""
                    SELECT customer_id AS user_id, first_name, last_name, email, 'User' AS role
                    FROM users
                    WHERE customer_id = ?
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT admin_id AS user_id, first_name, last_name, email, 'Admin' AS role
                    FROM admins
                    WHERE admin_id = ?
                """, (user_id,))
            user = cursor.fetchone()

            return dict(user), None
        except sqlite3.Error as e:
            conn.rollback()
            return None, f'Lỗi cơ sở dữ liệu: {str(e)}'
        finally:
            conn.close()

    @staticmethod
    def delete_user(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            is_admin = False
            cursor.execute('SELECT admin_id FROM admins WHERE admin_id = ?', (user_id,))
            if cursor.fetchone():
                is_admin = True
            else:
                cursor.execute('SELECT customer_id FROM users WHERE customer_id = ?', (user_id,))
                if not cursor.fetchone():
                    return None, 'Tài khoản không tồn tại'

            if not is_admin:
                cursor.execute('SELECT order_id FROM orders WHERE customer_id = ?', (user_id,))
                if cursor.fetchone():
                    return None, 'Không thể xóa user vì đã có đơn hàng'
                cursor.execute('SELECT review_id FROM reviews WHERE customer_id = ?', (user_id,))
                if cursor.fetchone():
                    return None, 'Không thể xóa user vì đã có đánh giá'
                cursor.execute('SELECT message_id FROM messages WHERE user_id = ?', (user_id,))
                if cursor.fetchone():
                    return None, 'Không thể xóa user vì đã có tin nhắn'
                cursor.execute('SELECT address_id FROM addresses WHERE customer_id = ?', (user_id,))
                if cursor.fetchone():
                    return None, 'Không thể xóa user vì đã có địa chỉ'
                cursor.execute('SELECT cart_id FROM cart WHERE customer_id = ?', (user_id,))
                if cursor.fetchone():
                    return None, 'Không thể xóa user vì đã có giỏ hàng'
            else:
                cursor.execute('SELECT favorite_id FROM favorites WHERE admin_id = ?', (user_id,))
                if cursor.fetchone():
                    return None, 'Không thể xóa admin vì đã có sản phẩm yêu thích'
                cursor.execute('SELECT message_id FROM messages WHERE admin_id = ?', (user_id,))
                if cursor.fetchone():
                    return None, 'Không thể xóa admin vì đã có tin nhắn'
                cursor.execute('SELECT event_id FROM events WHERE admin_id = ?', (user_id,))
                if cursor.fetchone():
                    return None, 'Không thể xóa admin vì đã có sự kiện'

            if is_admin:
                cursor.execute('DELETE FROM taxon_id = ?', (user_id,))
            else:
                cursor.execute('DELETE FROM users WHERE customer_id = ?', (user_id,))

            conn.commit()
            return True, None
        except sqlite3.Error as e:
            conn.rollback()
            return None, f'Lỗi cơ sở dữ liệu: {str(e)}'
        finally:
            conn.close()
            
# auth_model.py
import sqlite3
from utils.db import get_db_connection

class AuthModel:
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
    
# cart_model.py
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
    
# checkout_model.py
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
    
# forgot_password_model.py
import sqlite3
from utils.db import get_db_connection

class ForgotPasswordModel:
    @staticmethod
    def email_exists(email):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
# order_model.py
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
    
# product_model.py
import sqlite3
from utils.db import get_db_connection
import logging

logger = logging.getLogger(__name__)

class ProductModel:
    @staticmethod
    def get_all_products():
        conn = get_db_connection()
        products = conn.execute('''
            SELECT p.*, ps.size, ps.price, ps.size_id
            FROM products p
            LEFT JOIN product_size ps ON p.product_id = ps.product_id
        ''').fetchall()
        conn.close()
        return products

    @staticmethod
    def get_product_by_id(product_id):
        conn = get_db_connection()
        product = conn.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
        sizes = conn.execute("SELECT size, price, size_id FROM product_size WHERE product_id = ?", (product_id,)).fetchall()
        conn.close()
        return product, sizes

    @staticmethod
    def get_top10_products():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                p.product_id, 
                p.product_name, 
                p.stock, 
                p.description, 
                p.image_url, 
                p.image_url_2, 
                p.discount, 
                p.category,
                SUM(od.quantity) as total_sold
            FROM products p
            JOIN order_details od ON p.product_id = od.product_id
            JOIN orders o ON od.order_id = o.order_id
            WHERE o.status = 'Delivered'
            GROUP BY p.product_id
            ORDER BY total_sold DESC
            LIMIT 10
        ''')
        top_products = [dict(row) for row in cursor.fetchall()]
        products_list = []
        for product in top_products:
            cursor.execute('''
                SELECT size_id, size, price
                FROM product_size
                WHERE product_id = ?
            ''', (product['product_id'],))
            sizes = [{'size_id': row['size_id'], 'size': row['size'], 'price': row['price']} for row in cursor.fetchall()]
            product['sizes'] = sizes
            products_list.append(product)
        conn.close()
        return products_list

    @staticmethod
    def get_admin_products(admin_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.product_id, p.product_name, p.stock, p.description, p.image_url,
                   p.discount, p.category, 
                   CASE WHEN f.favorite_id IS NOT NULL THEN 1 ELSE 0 END as favorited,
                   (SELECT ps.price FROM product_size ps WHERE ps.product_id = p.product_id AND ps.size = 'M' LIMIT 1) as price_m,
                   (SELECT CAST(AVG(r.rating) AS REAL)
                    FROM reviews r
                    JOIN orders o ON o.order_id = r.order_id
                    WHERE r.product_id = p.product_id AND o.status = 'Delivered') as avg_rating
            FROM products p
            LEFT JOIN favorites f ON p.product_id = f.product_id AND f.admin_id = ?
        """, (admin_id,))
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return products
    
# review_model.py
import sqlite3
from utils.db import get_db_connection
import logging

logger = logging.getLogger(__name__)

class ReviewModel:
    @staticmethod
    def get_reviews_by_product(product_id):
        conn = get_db_connection()
        reviews = conn.execute('''
            SELECT r.review_id, r.customer_id, r.rating, r.comment, r.review_date, r.review_img, u.first_name, u.last_name
            FROM reviews r
            JOIN users u ON r.customer_id = u.customer_id
            WHERE r.product_id = ?
        ''', (product_id,)).fetchall()
        conn.close()
        return reviews
    
# signup_model.py
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
        
# user.py
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