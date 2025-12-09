# models/user_management.py
import sqlite3
from utils.db import get_db_connection
import logging

logger = logging.getLogger(__name__)

class UserManagement:
    @staticmethod
    def get_users():
        logger.debug("Fetching users")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
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
            logger.debug(f"Retrieved {len(users)} users")
            return users
        except sqlite3.Error as e:
            logger.error(f"Database error in get_users: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        finally:
            conn.close()

    @staticmethod
    def add_user(first_name, last_name, email, password, role):
        logger.debug(f"Adding user: email={email}, role={role}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Kiểm tra email trùng lặp
            cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                logger.warning(f"Email already exists in users: {email}")
                return None
            cursor.execute("SELECT email FROM admins WHERE email = ?", (email,))
            if cursor.fetchone():
                logger.warning(f"Email already exists in admins: {email}")
                return None

            # Tạo user_id theo định dạng KHxx hoặc ADxx
            if role == 'User':
                cursor.execute("SELECT MAX(CAST(SUBSTR(customer_id, 3) AS INTEGER)) FROM users WHERE customer_id LIKE 'KH%'")
                max_id = cursor.fetchone()[0]
                next_id = (max_id or 10) + 1  # Bắt đầu từ KH11 nếu không có
                user_id = f"KH{next_id:02d}"
                cursor.execute("""
                    INSERT INTO users (customer_id, first_name, last_name, email, password)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, first_name, last_name, email, password))
            else:  # role == 'Admin'
                cursor.execute("SELECT MAX(CAST(SUBSTR(admin_id, 3) AS INTEGER)) FROM admins WHERE admin_id LIKE 'AD%'")
                max_id = cursor.fetchone()[0]
                next_id = (max_id or 10) + 1  # Bắt đầu từ AD11 nếu không có
                user_id = f"AD{next_id:02d}"
                cursor.execute("""
                    INSERT INTO admins (admin_id, first_name, last_name, email, password)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, first_name, last_name, email, password))

            conn.commit()

            # Lấy thông tin user vừa thêm
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
            if not user:
                logger.error(f"Failed to retrieve user after adding: user_id={user_id}")
                raise Exception("Không thể lấy thông tin người dùng vừa thêm")

            logger.info(f"User added successfully: user_id={user_id}")
            return dict(user)
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error in add_user: {str(e)}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def edit_user(user_id, first_name, last_name, email, role):
        logger.debug(f"Editing user: user_id={user_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Kiểm tra user_id tồn tại và xác định bảng
            is_admin = False
            cursor.execute("SELECT admin_id, password FROM admins WHERE admin_id = ?", (user_id,))
            admin = cursor.fetchone()
            if admin:
                is_admin = True
            else:
                cursor.execute("SELECT customer_id, password FROM users WHERE customer_id = ?", (user_id,))
                user = cursor.fetchone()
                if not user:
                    logger.warning(f"User not found: user_id={user_id}")
                    return None

            # Kiểm tra email trùng lặp
            cursor.execute("SELECT customer_id FROM users WHERE email = ? AND customer_id != ?", (email, user_id))
            if cursor.fetchone():
                logger.warning(f"Email already exists in users: {email}")
                return None
            cursor.execute("SELECT admin_id FROM admins WHERE email = ? AND admin_id != ?", (email, user_id))
            if cursor.fetchone():
                logger.warning(f"Email already exists in admins: {email}")
                return None

            # Cập nhật hoặc chuyển bảng
            if is_admin and role == 'Admin':
                cursor.execute("""
                    UPDATE admins
                    SET first_name = ?, last_name = ?, email = ?
                    WHERE admin_id = ?
                """, (first_name, last_name, email, user_id))
            elif is_admin and role == 'User':
                cursor.execute("DELETE FROM admins WHERE admin_id = ?", (user_id,))
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
            else:  # not is_admin and role == 'Admin'
                cursor.execute("DELETE FROM users WHERE customer_id = ?", (user_id,))
                cursor.execute("""
                    INSERT INTO admins (admin_id, first_name, last_name, email, password)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, first_name, last_name, email, user['password']))

            conn.commit()

            # Lấy thông tin user vừa sửa
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
            if not user:
                logger.error(f"Failed to retrieve user after editing: user_id={user_id}")
                raise Exception("Không thể lấy thông tin người dùng vừa sửa")

            logger.info(f"User updated successfully: user_id={user_id}")
            return dict(user)
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error in edit_user: {str(e)}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_user(user_id):
        logger.debug(f"Deleting user: user_id={user_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Kiểm tra user_id tồn tại và xác định bảng
            is_admin = False
            cursor.execute("SELECT admin_id FROM admins WHERE admin_id = ?", (user_id,))
            if cursor.fetchone():
                is_admin = True
            else:
                cursor.execute("SELECT customer_id FROM users WHERE customer_id = ?", (user_id,))
                if not cursor.fetchone():
                    logger.warning(f"User not found: user_id={user_id}")
                    return False

            # Kiểm tra ràng buộc khóa ngoại
            if not is_admin:
                cursor.execute("SELECT order_id FROM orders WHERE customer_id = ?", (user_id,))
                if cursor.fetchone():
                    logger.warning(f"Cannot delete user due to orders: user_id={user_id}")
                    return False
                cursor.execute("SELECT review_id FROM reviews WHERE customer_id = ?", (user_id,))
                if cursor.fetchone():
                    logger.warning(f"Cannot delete user due to reviews: user_id={user_id}")
                    return False
                cursor.execute("SELECT message_id FROM messages WHERE user_id = ?", (user_id,))
                if cursor.fetchone():
                    logger.warning(f"Cannot delete user due to messages: user_id={user_id}")
                    return False
                cursor.execute("SELECT address_id FROM addresses WHERE customer_id = ?", (user_id,))
                if cursor.fetchone():
                    logger.warning(f"Cannot delete user due to addresses: user_id={user_id}")
                    return False
                cursor.execute("SELECT cart_id FROM cart WHERE customer_id = ?", (user_id,))
                if cursor.fetchone():
                    logger.warning(f"Cannot delete user due to cart: user_id={user_id}")
                    return False
            else:
                cursor.execute("SELECT favorite_id FROM favorites WHERE admin_id = ?", (user_id,))
                if cursor.fetchone():
                    logger.warning(f"Cannot delete admin due to favorites: user_id={user_id}")
                    return False
                cursor.execute("SELECT message_id FROM messages WHERE admin_id = ?", (user_id,))
                if cursor.fetchone():
                    logger.warning(f"Cannot delete admin due to messages: user_id={user_id}")
                    return False
                cursor.execute("SELECT event_id FROM events WHERE admin_id = ?", (user_id,))
                if cursor.fetchone():
                    logger.warning(f"Cannot delete admin due to events: user_id={user_id}")
                    return False

            # Xóa tài khoản
            if is_admin:
                cursor.execute("DELETE FROM admins WHERE admin_id = ?", (user_id,))
            else:
                cursor.execute("DELETE FROM users WHERE customer_id = ?", (user_id,))

            conn.commit()
            logger.info(f"User deleted successfully: user_id={user_id}")
            return True
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error in delete_user: {str(e)}")
            raise e
        finally:
            conn.close()