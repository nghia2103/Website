import sqlite3
import logging

logger = logging.getLogger(__name__)

try:
    from utils.db import get_db_connection
    logger.info("Imported get_db_connection successfully")
except ImportError as e:
    logger.error(f"Failed to import get_db_connection: {str(e)}")
    raise e

class Dashboard:
    @staticmethod
    def get_dashboard_data(admin_id):
        logger.debug(f"Fetching dashboard data for admin_id={admin_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Lấy thông tin admin
            cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
            admin = cursor.fetchone()
            if not admin:
                logger.debug(f"Admin not found for admin_id={admin_id}")
                raise ValueError("Admin không tồn tại")

            # Lấy tổng số users
            cursor.execute('SELECT COUNT(*) as count FROM users')
            total_users = cursor.fetchone()['count']
            logger.debug(f"Total users: {total_users}")

            # Lấy tổng số đơn hàng đã giao
            cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'Delivered'")
            total_orders = cursor.fetchone()['count']
            logger.debug(f"Total orders: {total_orders}")

            # Lấy tổng doanh thu
            cursor.execute("""
                SELECT SUM(od.total_price) as total 
                FROM order_details od
                JOIN orders o ON od.order_id = o.order_id
                WHERE o.status = 'Delivered'
            """)
            total_sales = cursor.fetchone()['total'] or 0
            logger.debug(f"Total sales: {total_sales}")

            # Lấy tổng số đơn hàng đang chờ
            cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'Pending'")
            total_pending = cursor.fetchone()['count']
            logger.debug(f"Total pending orders: {total_pending}")

            # Lấy dữ liệu doanh thu theo tháng
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
            logger.debug(f"Sales data: {sales_data}")

            # Lấy danh sách giao dịch gần đây
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
                status_color = {
                    'Delivered': 'success',
                    'Pending': 'warning',
                    'Cancelled': 'danger'
                }.get(row['status'], 'secondary')
                deals.append({
                    'product_name': row['product_name'],
                    'location': row['location'],
                    'order_date': row['order_date'],
                    'quantity': row['quantity'],
                    'total_price': row['total_price'],
                    'status': row['status'],
                    'status_color': status_color
                })
            logger.debug(f"Deals: {deals}")

            return {
                'admin': dict(admin),
                'total_users': total_users,
                'total_orders': total_orders,
                'total_sales': total_sales,
                'total_pending': total_pending,
                'sales_data': sales_data,
                'deals': deals
            }
        except ValueError as e:
            logger.error(f"ValueError in get_dashboard_data: {str(e)}")
            raise e
        except sqlite3.Error as e:
            logger.error(f"SQLite error in get_dashboard_data: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in get_dashboard_data: {str(e)}")
            raise e
        finally:
            conn.close()