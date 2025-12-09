# controllers/review_controller.py
from flask import jsonify, request, session
from models.review_model import ReviewModel
import logging
import os
import uuid
from datetime import datetime
from utils.db import get_db_connection
import sqlite3  # Import sqlite3

logger = logging.getLogger(__name__)

class ReviewController:
    def get_reviews_by_product(self, product_id):
        try:
            reviews = ReviewModel.get_reviews_by_product(product_id)
            reviews_list = [
                {
                    "review_id": row['review_id'],
                    "customer_name": f"{row['first_name']} {row['last_name']}",
                    "rating": row['rating'],
                    "comment": row['comment'],
                    "review_date": row['review_date'],
                    "review_img": row['review_img']
                } for row in reviews
            ]
            logger.debug(f"Trả về {len(reviews_list)} đánh giá cho product_id: {product_id}")
            return jsonify(reviews_list), 200
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi lấy đánh giá: {str(e)}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi khi lấy đánh giá: {str(e)}")
            return jsonify({"error": str(e)}), 500

    def submit_review(self):
        conn = None
        try:
            if 'customer_id' not in session:
                return jsonify({"error": "Vui lòng đăng nhập để gửi đánh giá"}), 401
            customer_id = session['customer_id']
            product_id = request.form.get('product_id')
            rating = request.form.get('rating')
            comment = request.form.get('comment')
            order_id = request.form.get('order_id')
            size_id = request.form.get('size_id')
            review_image = request.files.get('reviewImage')
            if not product_id or not rating or not comment or not order_id or not size_id:
                logger.error(f"Thiếu thông tin bắt buộc: product_id={product_id}, rating={rating}, comment={comment}, order_id={order_id}, size_id={size_id}")
                return jsonify({"error": "Thiếu thông tin bắt buộc (product_id, rating, comment, order_id, size_id)"}), 400
            try:
                rating = int(rating)
                if rating < 1 or rating > 5:
                    logger.error(f"Rating không hợp lệ: {rating}")
                    return jsonify({"error": "Rating phải là số nguyên từ 1 đến 5"}), 400
            except ValueError:
                logger.error(f"Rating không phải số nguyên: {rating}")
                return jsonify({"error": "Rating phải là số nguyên từ 1 đến 5"}), 400
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT customer_id FROM users WHERE customer_id = ?', (customer_id,))
            if not cursor.fetchone():
                logger.error(f"Customer không tồn tại: customer_id={customer_id}")
                conn.close()
                return jsonify({"error": "Khách hàng không tồn tại"}), 400
            cursor.execute('SELECT product_id FROM products WHERE product_id = ?', (product_id,))
            if not cursor.fetchone():
                logger.error(f"Product không tồn tại: product_id={product_id}")
                conn.close()
                return jsonify({"error": "Sản phẩm không tồn tại"}), 400
            cursor.execute('SELECT size_id FROM product_size WHERE size_id = ? AND product_id = ?', (size_id, product_id))
            if not cursor.fetchone():
                logger.error(f"Size không tồn tại hoặc không liên kết với sản phẩm: size_id={size_id}, product_id={product_id}")
                conn.close()
                return jsonify({"error": "Kích thước không hợp lệ hoặc không liên kết với sản phẩm"}), 400
            cursor.execute('SELECT order_id FROM orders WHERE order_id = ? AND customer_id = ?', (order_id, customer_id))
            if not cursor.fetchone():
                logger.error(f"Order không tồn tại hoặc không thuộc về khách hàng: order_id={order_id}, customer_id={customer_id}")
                conn.close()
                return jsonify({"error": "Đơn hàng không tồn tại hoặc không thuộc về bạn"}), 400
            cursor.execute('''
                SELECT review_id 
                FROM reviews 
                WHERE customer_id = ? AND product_id = ? AND size_id = ? AND order_id = ?
            ''', (customer_id, product_id, size_id, order_id))
            if cursor.fetchone():
                logger.error(f"Đánh giá đã tồn tại: customer_id={customer_id}, product_id={product_id}, size_id={size_id}, order_id={order_id}")
                conn.close()
                return jsonify({"error": "Bạn đã đánh giá sản phẩm này cho đơn hàng này rồi"}), 400
            cursor.execute('SELECT status FROM orders WHERE order_id = ?', (order_id,))
            order_status = cursor.fetchone()
            if order_status['status'].lower() != 'delivered':
                logger.error(f"Đơn hàng chưa được giao: order_id={order_id}, status={order_status['status']}")
                conn.close()
                return jsonify({"error": "Chỉ có thể đánh giá đơn hàng đã được giao"}), 400
            review_image_url = None
            if review_image:
                valid_extensions = {'.png', '.jpg', '.jpeg'}
                ext = os.path.splitext(review_image.filename)[1].lower()
                if ext not in valid_extensions:
                    logger.error(f"Loại tệp ảnh không hợp lệ: extension={ext}")
                    conn.close()
                    return jsonify({"error": "Loại tệp không hợp lệ. Chỉ cho phép PNG và JPEG"}), 400
                upload_folder = os.path.join('views/static', 'reviews_upload')  # Sử dụng đường dẫn tĩnh
                os.makedirs(upload_folder, exist_ok=True)
                filename = f"review_{customer_id}_{uuid.uuid4().hex}{ext}"
                file_path = os.path.join(upload_folder, filename)
                review_image.save(file_path)
                review_image_url = f"/reviews_upload/{filename}"
            review_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('''
                INSERT INTO reviews (customer_id, product_id, size_id, order_id, rating, comment, review_date, review_img)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, product_id, size_id, order_id, rating, comment, review_date, review_image_url))
            conn.commit()
            cursor.execute("SELECT review_id FROM reviews WHERE rowid = last_insert_rowid()")
            review_id = cursor.fetchone()['review_id']
            logger.info(f"Đã gửi đánh giá thành công: customer_id={customer_id}, product_id={product_id}, order_id={order_id}, review_id={review_id}")
            conn.close()
            return jsonify({"message": "Đánh giá được gửi thành công", "review_image_url": review_image_url, "review_id": review_id}), 200
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
                conn.close()
            logger.error(f"Lỗi cơ sở dữ liệu khi gửi đánh giá: {str(e)}, product_id={product_id}, size_id={size_id}, order_id={order_id}, customer_id={customer_id}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            if conn:
                conn.rollback()
                conn.close()
            logger.error(f"Lỗi khi gửi đánh giá: {str(e)}, product_id={product_id}, size_id={size_id}, order_id={order_id}, customer_id={customer_id}")
            return jsonify({"error": str(e)}), 500

    def check_review(self):
        if 'customer_id' not in session:
            return jsonify({'error': 'Vui lòng đăng nhập'}), 401
        try:
            order_id = request.args.get('order_id')
            product_id = request.args.get('product_id')
            size_id = request.args.get('size_id')
            customer_id = session['customer_id']
            conn = get_db_connection()
            review = conn.execute('''
                SELECT review_id 
                FROM reviews 
                WHERE customer_id = ? AND product_id = ? AND size_id = ? AND order_id = ?
            ''', (customer_id, product_id, size_id, order_id)).fetchone()
            conn.close()
            if review:
                return jsonify({"review_id": review['review_id']}), 200
            return jsonify({}), 200
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi kiểm tra đánh giá: {str(e)}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra đánh giá: {str(e)}")
            return jsonify({"error": str(e)}), 500