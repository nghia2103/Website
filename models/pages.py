# models/pages.py
import sqlite3
from datetime import datetime
import logging
import os
import uuid
import random
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

try:
    from utils.db import get_db_connection
    logger.info("Imported get_db_connection successfully")
except ImportError as e:
    logger.error(f"Failed to import get_db_connection: {str(e)}")
    raise e

class Pages:
    @staticmethod
    def get_admin_data(admin_id):
        logger.debug(f"Fetching admin data for admin_id={admin_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
            admin = cursor.fetchone()
            if not admin:
                logger.debug(f"Admin not found for admin_id={admin_id}")
                return None
            return dict(admin)
        except sqlite3.Error as e:
            logger.error(f"SQLite error in get_admin_data: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        finally:
            conn.close()

    @staticmethod
    def get_invoice_data(filter_date=None, filter_customer=None):
        logger.debug(f"Fetching invoice data with filter_date={filter_date}, filter_customer={filter_customer}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            query = """
                SELECT o.order_id AS code, u.first_name || ' ' || u.last_name AS customer_name, 
                       o.order_date AS date, o.status
                FROM orders o
                JOIN users u ON o.customer_id = u.customer_id
                WHERE o.status = 'Delivered'
            """
            params = []
            if filter_date:
                try:
                    date_obj = datetime.strptime(filter_date, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                    query += " AND o.order_date LIKE ?"
                    params.append(f"{formatted_date}%")
                except ValueError:
                    logger.warning(f"Invalid date format: {filter_date}")
            if filter_customer:
                query += " AND LOWER(u.first_name || ' ' || u.last_name) = LOWER(?)"
                params.append(filter_customer)

            cursor.execute(query, params)
            invoices = cursor.fetchall()

            invoices_list = []
            total_amount = 0
            for row in invoices:
                cursor.execute("""
                    SELECT p.product_name, od.quantity, ps.size
                    FROM order_details od
                    JOIN products p ON od.product_id = p.product_id
                    JOIN product_size ps ON od.size_id = ps.size_id
                    WHERE od.order_id = ?
                """, (row['code'],))
                products = cursor.fetchall()

                cursor.execute("""
                    SELECT SUM(total_price) as order_total
                    FROM order_details
                    WHERE order_id = ?
                """, (row['code'],))
                order_total = cursor.fetchone()['order_total'] or 0

                product_list = []
                for product in products:
                    product_list.append({
                        'product_name': product['product_name'],
                        'quantity': product['quantity'],
                        'size': product['size']
                    })

                total_amount += order_total
                invoices_list.append({
                    'code': row['code'],
                    'customer_name': row['customer_name'],
                    'date': row['date'],
                    'total_price': order_total,
                    'status': row['status'],
                    'description': f"Payment for order {row['code']}",
                    'products': product_list
                })

            cursor.execute("""
                SELECT DISTINCT u.first_name || ' ' || u.last_name AS customer_name 
                FROM orders o
                JOIN users u ON o.customer_id = u.customer_id
                WHERE o.status = 'Delivered'
            """)
            customers = [row['customer_name'] for row in cursor.fetchall()]

            return {
                'invoices': invoices_list,
                'customers': customers,
                'total_amount': total_amount
            }
        except sqlite3.Error as e:
            logger.error(f"SQLite error in get_invoice_data: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        finally:
            conn.close()

    @staticmethod
    def get_admins_data():
        logger.debug("Fetching admins data")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT admin_id, first_name, last_name, email, phone, admin_img FROM admins')
            admins = [
                {
                    'admin_id': row['admin_id'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'email': row['email'],
                    'phone': row['phone'],
                    'admin_img': row['admin_img']
                }
                for row in cursor.fetchall()
            ]
            return admins
        except sqlite3.Error as e:
            logger.error(f"SQLite error in get_admins_data: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        finally:
            conn.close()

    @staticmethod
    def get_events_data(year, month):
        logger.debug(f"Fetching events data for year={year}, month={month}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT event_id, event_name, date, time, admin_id, adminname, color
                FROM events
                WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            """, (year, month.zfill(2)))
            events = [
                {
                    'event_id': row['event_id'],
                    'event_name': row['event_name'],
                    'date': row['date'],
                    'time': row['time'],
                    'admin_id': row['admin_id'],
                    'adminname': row['adminname'],
                    'color': row['color']
                }
                for row in cursor.fetchall()
            ]
            return events
        except sqlite3.Error as e:
            logger.error(f"SQLite error in get_events_data: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        finally:
            conn.close()

    @staticmethod
    def get_all_events_data():
        logger.debug("Fetching all events data")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT event_id, event_name, date, time, admin_id, adminname, color
                FROM events
                ORDER BY date ASC, time ASC
            """)
            events = [
                {
                    'event_id': row['event_id'],
                    'event_name': row['event_name'],
                    'date': row['date'],
                    'time': row['time'],
                    'admin_id': row['admin_id'],
                    'adminname': row['adminname'],
                    'color': row['color']
                }
                for row in cursor.fetchall()
            ]
            return events
        except sqlite3.Error as e:
            logger.error(f"SQLite error in get_all_events_data: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        finally:
            conn.close()

    @staticmethod
    def create_event_data(data, admin_id):
        logger.debug(f"Creating event data for admin_id={admin_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            event_name = data.get('event_name')
            date = data.get('date')
            time = data.get('time')
            adminname = data.get('adminname')
            color = data.get('color') or random.choice(['green', 'blue', 'pink', 'purple', 'orange', 'yellow', 'red'])

            if not all([event_name, date, time, admin_id, adminname, color]):
                raise ValueError('Thiếu thông tin bắt buộc')

            try:
                datetime.strptime(date, '%Y-%m-%d')
                datetime.strptime(time, '%H:%M')
            except ValueError:
                raise ValueError('Định dạng ngày hoặc giờ không hợp lệ')

            cursor.execute('SELECT admin_id FROM admins WHERE admin_id = ?', (admin_id,))
            if not cursor.fetchone():
                raise ValueError('ID admin không hợp lệ')

            cursor.execute("""
                INSERT INTO events (event_name, date, time, admin_id, adminname, color)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (event_name, date, time, admin_id, adminname, color))

            cursor.execute("""
                SELECT event_id, event_name, date, time, admin_id, adminname, color
                FROM events
                WHERE rowid = last_insert_rowid()
            """)
            event = cursor.fetchone()

            conn.commit()
            return {
                'event_id': event['event_id'],
                'event_name': event['event_name'],
                'date': event['date'],
                'time': event['time'],
                'admin_id': event['admin_id'],
                'adminname': event['adminname'],
                'color': event['color']
            }
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"SQLite error in create_event_data: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        except ValueError as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def update_admin_data(admin_id, form_data, files):
        logger.debug(f"Updating admin data for admin_id={admin_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            first_name = form_data.get('first_name')
            last_name = form_data.get('last_name')
            email = form_data.get('email')
            phone = form_data.get('phone')
            admin_img = files.get('admin_img')

            if not all([first_name, last_name, email, phone]):
                raise ValueError('Thiếu thông tin bắt buộc')

            cursor.execute('SELECT admin_id, admin_img FROM admins WHERE admin_id = ?', (admin_id,))
            admin = cursor.fetchone()
            if not admin:
                raise ValueError('Admin không tồn tại')

            cursor.execute('SELECT admin_id FROM admins WHERE email = ? AND admin_id != ?', (email, admin_id))
            if cursor.fetchone():
                raise ValueError('Email đã được sử dụng')

            admin_img_path = admin['admin_img']
            if admin_img and Pages.allowed_file(admin_img.filename):
                filename = secure_filename(admin_img.filename)
                ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{ext}"
                file_path = os.path.join('views/static/Upload', unique_filename)
                admin_img.save(file_path)
                admin_img_path = f"/Upload/{unique_filename}"  # Sửa đường dẫn để khớp với route tĩnh

            cursor.execute("""
                UPDATE admins
                SET first_name = ?, last_name = ?, email = ?, phone = ?, admin_img = ?
                WHERE admin_id = ?
            """, (first_name, last_name, email, phone, admin_img_path, admin_id))

            cursor.execute("""
                SELECT admin_id, first_name, last_name, email, phone, admin_img
                FROM admins
                WHERE admin_id = ?
            """, (admin_id,))
            updated_admin = cursor.fetchone()

            conn.commit()
            return {
                'admin_id': updated_admin['admin_id'],
                'first_name': updated_admin['first_name'],
                'last_name': updated_admin['last_name'],
                'email': updated_admin['email'],
                'phone': updated_admin['phone'],
                'admin_img': updated_admin['admin_img']
            }
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"SQLite error in update_admin_data: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        except ValueError as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def update_event_data(event_id, data, admin_id):
        logger.debug(f"Updating event data for event_id={event_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            event_name = data.get('event_name')
            date = data.get('date')
            time = data.get('time')
            adminname = data.get('adminname')
            color = data.get('color')

            if not all([event_name, date, time, admin_id, adminname, color]):
                raise ValueError('Thiếu thông tin bắt buộc')

            try:
                datetime.strptime(date, '%Y-%m-%d')
                datetime.strptime(time, '%H:%M')
            except ValueError:
                raise ValueError('Định dạng ngày hoặc giờ không hợp lệ')

            cursor.execute('SELECT admin_id FROM admins WHERE admin_id = ?', (admin_id,))
            if not cursor.fetchone():
                raise ValueError('ID admin không hợp lệ')

            cursor.execute('SELECT event_id FROM events WHERE event_id = ?', (event_id,))
            if not cursor.fetchone():
                raise ValueError('Sự kiện không tồn tại')

            cursor.execute("""
                UPDATE events
                SET event_name = ?, date = ?, time = ?, admin_id = ?, adminname = ?, color = ?
                WHERE event_id = ?
            """, (event_name, date, time, admin_id, adminname, color, event_id))

            cursor.execute("""
                SELECT event_id, event_name, date, time, admin_id, adminname, color
                FROM events
                WHERE event_id = ?
            """, (event_id,))
            event = cursor.fetchone()

            conn.commit()
            return {
                'event_id': event['event_id'],
                'event_name': event['event_name'],
                'date': event['date'],
                'time': event['time'],
                'admin_id': event['admin_id'],
                'adminname': event['adminname'],
                'color': event['color']
            }
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"SQLite error in update_event_data: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        except ValueError as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_event_data(event_id):
        logger.debug(f"Deleting event data for event_id={event_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT event_id FROM events WHERE event_id = ?', (event_id,))
            if not cursor.fetchone():
                raise ValueError('Sự kiện không tồn tại')

            cursor.execute('DELETE FROM events WHERE event_id = ?', (event_id,))
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"SQLite error in delete_event_data: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        except ValueError as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png'}