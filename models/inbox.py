# models/inbox.py
import sqlite3
from utils.db import get_db_connection
import logging
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class Inbox:
    @staticmethod
    def get_threads(admin_id):
        logger.debug(f"Fetching threads for admin_id={admin_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT m.user_id, u.first_name || ' ' || u.last_name AS sender_name, 
                       m.content, m.timestamp, m.is_read, m.direction,
                       EXISTS (
                           SELECT 1 FROM messages m2
                           WHERE m2.user_id = m.user_id 
                           AND (m2.admin_id = ? OR m2.admin_id IS NULL)
                           AND m2.direction = 'user_to_admin' AND m2.is_read = 0
                       ) AS has_unread
                FROM messages m
                JOIN users u ON m.user_id = u.customer_id
                LEFT JOIN user_admin_assignments ua ON m.user_id = ua.user_id
                WHERE (m.admin_id = ? OR m.admin_id IS NULL) 
                AND (ua.admin_id = ? OR ua.admin_id IS NULL)
                AND m.message_id = (
                    SELECT message_id 
                    FROM messages m2 
                    WHERE m2.user_id = m.user_id 
                    AND (m2.admin_id = ? OR m2.admin_id IS NULL)
                    ORDER BY m2.timestamp DESC 
                    LIMIT 1
                )
                ORDER BY m.timestamp DESC
            """, (admin_id, admin_id, admin_id, admin_id))
            threads = []
            for row in cursor:
                dt = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                local_dt = dt.astimezone(pytz.timezone('Asia/Ho_Chi_Minh'))
                time_str = local_dt.strftime('%I:%M %p')
                threads.append({
                    'user_id': row['user_id'],
                    'sender_name': row['sender_name'],
                    'content': row['content'],
                    'time': time_str,
                    'is_read': row['is_read'],
                    'direction': row['direction'],
                    'has_unread': bool(row['has_unread'])
                })
            logger.debug(f"Retrieved {len(threads)} threads")
            return threads
        except sqlite3.Error as e:
            logger.error(f"Database error in get_threads: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        finally:
            conn.close()

    @staticmethod
    def get_messages(user_id, admin_id):
        logger.debug(f"Fetching messages for user_id={user_id}, admin_id={admin_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT admin_id FROM user_admin_assignments WHERE user_id = ?", (user_id,))
            assigned_admin = cursor.fetchone()
            if assigned_admin and assigned_admin['admin_id'] != admin_id:
                logger.debug(f"Conversation assigned to another admin: assigned_admin_id={assigned_admin['admin_id']}")
                raise ValueError("Cuộc trò chuyện này đã được admin khác xử lý")
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
                AND (m.admin_id = ? OR m.admin_id IS NULL)
                ORDER BY m.timestamp ASC
            """, (user_id, admin_id))
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
            cursor.execute("""
                UPDATE messages SET is_read = 1
                WHERE user_id = ? AND (admin_id = ? OR admin_id IS NULL) 
                AND direction = 'user_to_admin' AND is_read = 0
            """, (user_id, admin_id))
            conn.commit()
            logger.debug(f"Retrieved {len(messages)} messages")
            return messages
        except sqlite3.Error as e:
            logger.error(f"Database error in get_messages: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        except ValueError as e:
            raise e
        finally:
            conn.close()

    @staticmethod
    def send_message(user_id, admin_id, direction, content):
        logger.debug(f"Sending message: user_id={user_id}, admin_id={admin_id}, direction={direction}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if direction not in ['user_to_admin', 'admin_to_user']:
                logger.error(f"Invalid direction: {direction}")
                raise ValueError("Hướng tin nhắn không hợp lệ")
            cursor.execute('SELECT customer_id FROM users WHERE customer_id = ?', (user_id,))
            if not cursor.fetchone():
                logger.error(f"Invalid user_id: {user_id}")
                raise ValueError("ID khách hàng không hợp lệ")
            if direction == 'user_to_admin':
                cursor.execute("SELECT admin_id FROM user_admin_assignments WHERE user_id = ?", (user_id,))
                assigned_admin = cursor.fetchone()
                admin_id = assigned_admin['admin_id'] if assigned_admin else None
            else:
                cursor.execute('SELECT admin_id FROM admins WHERE admin_id = ?', (admin_id,))
                if not cursor.fetchone():
                    logger.error(f"Invalid admin_id: {admin_id}")
                    raise ValueError("ID admin không hợp lệ")
                cursor.execute("SELECT admin_id FROM user_admin_assignments WHERE user_id = ?", (user_id,))
                assigned_admin = cursor.fetchone()
                if assigned_admin and assigned_admin['admin_id'] != admin_id:
                    logger.debug(f"User assigned to another admin: assigned_admin_id={assigned_admin['admin_id']}")
                    raise ValueError("User đã được gán cho admin khác")
            cursor.execute("""
                INSERT INTO messages (message_id, user_id, admin_id, direction, content, timestamp, is_read)
                VALUES (NULL, ?, ?, ?, ?, ?, ?)
            """, (user_id, admin_id, direction, content, datetime.now().isoformat(), 0))
            cursor.execute('SELECT message_id FROM messages WHERE rowid = last_insert_rowid()')
            message = cursor.fetchone()
            conn.commit()
            logger.info(f"Message sent: message_id={message['message_id']}")
            return message['message_id']
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error in send_message: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        except ValueError as e:
            raise e
        finally:
            conn.close()

    @staticmethod
    def assign_admin(user_id, admin_id):
        logger.debug(f"Assigning admin: user_id={user_id}, admin_id={admin_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT customer_id FROM users WHERE customer_id = ?", (user_id,))
            if not cursor.fetchone():
                logger.error(f"Invalid user_id: {user_id}")
                raise ValueError("ID khách hàng không hợp lệ")
            cursor.execute("SELECT admin_id FROM user_admin_assignments WHERE user_id = ?", (user_id,))
            existing_assignment = cursor.fetchone()
            if existing_assignment:
                if existing_assignment['admin_id'] == admin_id:
                    logger.debug(f"Admin already assigned: admin_id={admin_id}")
                    return
                logger.debug(f"User already assigned to another admin: assigned_admin_id={existing_assignment['admin_id']}")
                raise ValueError("User đã được gán cho admin khác")
            cursor.execute("""
                INSERT INTO user_admin_assignments (user_id, admin_id)
                VALUES (?, ?)
            """, (user_id, admin_id))
            cursor.execute("""
                UPDATE messages
                SET admin_id = ?
                WHERE user_id = ? AND admin_id IS NULL
            """, (admin_id, user_id))
            conn.commit()
            logger.info(f"Admin assigned: user_id={user_id}, admin_id={admin_id}")
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error in assign_admin: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        except ValueError as e:
            raise e
        finally:
            conn.close()