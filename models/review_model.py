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
    
    @staticmethod
    def submit_review(customer_id, product_id, size_id, order_id, rating, comment, review_date, review_img):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT customer_id FROM users WHERE customer_id = ?', (customer_id,))
            if not cursor.fetchone():
                return None, "Khách hàng không tồn tại"
            cursor.execute('SELECT product_id FROM products WHERE product_id = ?', (product_id,))
            if not cursor.fetchone():
                return None, "Sản phẩm không tồn tại"
            cursor.execute('SELECT size_id FROM product_size WHERE size_id = ? AND product_id = ?', (size_id, product_id))
            if not cursor.fetchone():
                return None, "Kích thước không hợp lệ hoặc không liên kết với sản phẩm"
            cursor.execute('SELECT order_id FROM orders WHERE order_id = ? AND customer_id = ?', (order_id, customer_id))
            if not cursor.fetchone():
                return None, "Đơn hàng không tồn tại hoặc không thuộc về bạn"
            cursor.execute('''
                SELECT review_id 
                FROM reviews 
                WHERE customer_id = ? AND product_id = ? AND size_id = ? AND order_id = ?
            ''', (customer_id, product_id, size_id, order_id))
            if cursor.fetchone():
                return None, "Bạn đã đánh giá sản phẩm này cho đơn hàng này rồi"
            cursor.execute('SELECT status FROM orders WHERE order_id = ?', (order_id,))
            order_status = cursor.fetchone()
            if order_status['status'].lower() != 'delivered':
                return None, "Chỉ có thể đánh giá đơn hàng đã được giao"
            cursor.execute('''
                INSERT INTO reviews (customer_id, product_id, size_id, order_id, rating, comment, review_date, review_img)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, product_id, size_id, order_id, rating, comment, review_date, review_img))
            conn.commit()
            cursor.execute("SELECT review_id FROM reviews WHERE rowid = last_insert_rowid()")
            review_id = cursor.fetchone()['review_id']
            return review_id, None
        except sqlite3.Error as e:
            conn.rollback()
            return None, f"Lỗi cơ sở dữ liệu: {str(e)}"
        finally:
            conn.close()

    @staticmethod
    def check_review(customer_id, product_id, size_id, order_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT review_id 
            FROM reviews 
            WHERE customer_id = ? AND product_id = ? AND size_id = ? AND order_id = ?
        ''', (customer_id, product_id, size_id, order_id))
        review = cursor.fetchone()
        conn.close()
        return review, None