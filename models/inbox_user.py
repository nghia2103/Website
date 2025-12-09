import sqlite3
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

try:
    from utils.db import get_db_connection
    logger.info("Imported get_db_connection successfully")
except ImportError as e:
    logger.error(f"Failed to import get_db_connection: {str(e)}")
    raise e

class InboxUser:
    @staticmethod
    def get_user_data(customer_id):
        logger.debug(f"Fetching user data for customer_id={customer_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT customer_id, first_name, last_name, email, phone, birthdate, user_add, user_img FROM users WHERE customer_id = ?', (customer_id,))
            user = cursor.fetchone()
            if not user:
                logger.debug(f"User not found for customer_id={customer_id}")
                return None
            return dict(user)
        except sqlite3.Error as e:
            logger.error(f"SQLite error in get_user_data: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        finally:
            conn.close()

    @staticmethod
    def get_user_messages_data(user_id):
        logger.debug(f"Fetching messages for user_id={user_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT admin_id FROM user_admin_assignments WHERE user_id = ?", (user_id,))
            assigned_admin = cursor.fetchone()
            admin_id = assigned_admin['admin_id'] if assigned_admin else None

            cursor.execute("""
                SELECT m.message_id, m.user_id, m.admin_id, m.direction, 
                       m.content, m.timestamp, m.is_read,
                       CASE 
                           WHEN m.direction = 'user_to_admin' THEN (u.first_name || ' ' || u.last_name)
                           WHEN m.direction = 'admin_to_user' THEN (a.first_name || ' ' || a.last_name)
                       END AS sender_name
                FROM messages m
                LEFT JOIN users u ON m.user_id = u.customer_id
                LEFT JOIN admins a ON m.admin_id = a.admin_id
                WHERE m.user_id = ?
                ORDER BY m.timestamp ASC
            """, (user_id,))
            messages = []
            for row in cursor:
                dt = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                local_dt = dt.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
                time_str = local_dt.strftime('%I:%M %p')
                messages.append({
                    'message_id': row['message_id'],
                    'user_id': row['user_id'],
                    'admin_id': row['admin_id'],
                    'sender_name': row['sender_name'],
                    'content': row['content'],
                    'time': time_str,
                    'is_read': row['is_read'],
                    'direction': row['direction']
                })
            return messages
        except sqlite3.Error as e:
            logger.error(f"SQLite error in get_user_messages_data: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        finally:
            conn.close()

    @staticmethod
    def send_message_data(user_id, admin_id, direction, content, session):
        logger.debug(f"Sending message for user_id={user_id}, direction={direction}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if direction == 'user_to_admin' and session.get('customer_id') != user_id:
                raise ValueError('Bạn phải đăng nhập để gửi tin nhắn')
            if direction == 'admin_to_user' and session.get('admin_id') != admin_id:
                raise ValueError('Bạn phải đăng nhập với tư cách admin để gửi tin nhắn')

            cursor.execute('SELECT customer_id FROM users WHERE customer_id = ?', (user_id,))
            if not cursor.fetchone():
                raise ValueError('ID khách hàng không hợp lệ')

            if direction == 'user_to_admin':
                cursor.execute("SELECT admin_id FROM user_admin_assignments WHERE user_id = ?", (user_id,))
                assigned_admin = cursor.fetchone()
                admin_id = assigned_admin['admin_id'] if assigned_admin else None
            else:
                cursor.execute('SELECT admin_id FROM admins WHERE admin_id = ?', (admin_id,))
                if not cursor.fetchone():
                    raise ValueError('ID admin không hợp lệ')
                cursor.execute("SELECT admin_id FROM user_admin_assignments WHERE user_id = ?", (user_id,))
                assigned_admin = cursor.fetchone()
                if assigned_admin and assigned_admin['admin_id'] != admin_id:
                    raise ValueError('User đã được gán cho admin khác')

            cursor.execute("""
                INSERT INTO messages (message_id, user_id, admin_id, direction, content, timestamp, is_read)
                VALUES (NULL, ?, ?, ?, ?, ?, ?)
            """, (user_id, admin_id, direction, content, datetime.now().isoformat(), 0))
            cursor.execute('SELECT message_id FROM messages WHERE rowid = last_insert_rowid()')
            message = cursor.fetchone()
            conn.commit()
            return message['message_id']
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"SQLite error in send_message_data: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        except ValueError as e:
            conn.rollback()
            raise e
        finally:
            conn.close()