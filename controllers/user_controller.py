from flask import jsonify, request, session, current_app
import logging
import sqlite3
from utils.db import get_db_connection
import os
import uuid

logger = logging.getLogger(__name__)

def register_user_routes(app):
    @app.route('/api/user', methods=['GET'])
    def get_user():
        try:
            if 'customer_id' not in session:
                logger.debug("No customer_id in session for /api/user")
                return jsonify({"error": "Vui lòng đăng nhập để xem thông tin người dùng"}), 401
            customer_id = session['customer_id']
            logger.debug(f"Fetching user data for customer_id: {customer_id}")
            conn = get_db_connection()
            user = conn.execute('SELECT customer_id, first_name, last_name, email, phone, birthdate, user_add, user_img FROM users WHERE customer_id = ?', (customer_id,)).fetchone()
            conn.close()
            if not user:
                logger.warning(f"No user found for customer_id: {customer_id}")
                return jsonify({"error": "Không tìm thấy người dùng"}), 404
            logger.debug(f"User data retrieved: {dict(user)}")
            return jsonify(dict(user)), 200
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi lấy người dùng: {str(e)}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi khi lấy người dùng: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/update-profile', methods=['POST'])
    def update_profile():
        if 'customer_id' not in session:
            return jsonify({'error': 'Vui lòng đăng nhập'}), 401
        try:
            data = request.json
            first_name = data.get('firstName')
            last_name = data.get('lastName')
            phone = data.get('phone')
            birthdate = data.get('birthdate')
            customer_id = session['customer_id']
            if not first_name or not last_name:
                return jsonify({"error": "Tên và họ là bắt buộc"}), 400
            conn = get_db_connection()
            conn.execute('''
                UPDATE users 
                SET first_name = ?, last_name = ?, phone = ?, birthdate = ?
                WHERE customer_id = ?
            ''', (first_name, last_name, phone or None, birthdate or None, customer_id))
            conn.commit()
            conn.close()
            logger.debug(f"Cập nhật hồ sơ cho customer_id: {customer_id}")
            return jsonify({"message": "Cập nhật hồ sơ thành công"}), 200
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi cập nhật hồ sơ: {str(e)}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật hồ sơ: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/change-password', methods=['POST'])
    def change_password():
        if 'customer_id' not in session:
            return jsonify({'error': 'Vui lòng đăng nhập'}), 401
        try:
            data = request.json
            current_password = data.get('currentPassword')
            new_password = data.get('newPassword')
            customer_id = session['customer_id']
            if not current_password or not new_password:
                return jsonify({"error": "Mật khẩu hiện tại và mới là bắt buộc"}), 400
            if len(new_password) < 8:
                return jsonify({"error": "Mật khẩu mới phải có ít nhất 8 ký tự"}), 400
            conn = get_db_connection()
            user = conn.execute('SELECT password FROM users WHERE customer_id = ?', (customer_id,)).fetchone()
            if not user:
                conn.close()
                return jsonify({"error": "Không tìm thấy người dùng"}), 404
            if user['password'] != current_password:
                conn.close()
                return jsonify({"error": "Mật khẩu hiện tại không đúng"}), 401
            conn.execute('UPDATE users SET password = ? WHERE customer_id = ?', (new_password, customer_id))
            conn.commit()
            conn.close()
            logger.debug(f"Đổi mật khẩu cho customer_id: {customer_id}")
            return jsonify({"message": "Đổi mật khẩu thành công"}), 200
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi đổi mật khẩu: {str(e)}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi khi đổi mật khẩu: {str(e)}")
            return jsonify({"error": f"Lỗi hệ thống: {str(e)}"}), 500

    @app.route('/api/upload-profile-image', methods=['POST'])
    def upload_profile_image():
        try:
            if 'customer_id' not in session:
                return jsonify({"error": "Vui lòng đăng nhập để tải ảnh hồ sơ"}), 401
            customer_id = session['customer_id']
            if 'image' not in request.files:
                return jsonify({"error": "Không có hình ảnh được cung cấp"}), 400
            file = request.files['image']
            if file.filename == '':
                return jsonify({"error": "Chưa chọn tệp"}), 400
            valid_extensions = {'.png', '.jpg', '.jpeg'}
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in valid_extensions:
                return jsonify({"error": "Loại tệp không hợp lệ. Chỉ cho phép PNG và JPEG"}), 400
            upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], customer_id)
            os.makedirs(upload_folder, exist_ok=True)
            filename = f"profile_{customer_id}_{uuid.uuid4().hex}{ext}"
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            image_url = f"/uploads/{customer_id}/{filename}"
            conn = get_db_connection()
            conn.execute('UPDATE users SET user_img = ? WHERE customer_id = ?', (image_url, customer_id))
            conn.commit()
            conn.close()
            logger.debug(f"Tải ảnh hồ sơ thành công cho customer_id: {customer_id}, image_url: {image_url}")
            return jsonify({"message": "Tải ảnh hồ sơ thành công", "image_url": image_url}), 200
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi tải ảnh: {str(e)}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi khi tải ảnh: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/addresses', methods=['GET'])
    def get_addresses():
        if 'customer_id' not in session:
            return jsonify({'error': 'Vui lòng đăng nhập'}), 401
        try:
            customer_id = session['customer_id']
            conn = get_db_connection()
            addresses = conn.execute('''
                SELECT address_id, contact_name, phone, address, is_default
                FROM addresses
                WHERE customer_id = ?
            ''', (customer_id,)).fetchall()
            conn.close()
            addresses_list = [dict(row) for row in addresses]
            logger.debug(f"Trả về {len(addresses_list)} địa chỉ cho customer_id: {customer_id}")
            return jsonify(addresses_list), 200
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi lấy địa chỉ: {str(e)}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi khi lấy địa chỉ: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/addresses', methods=['POST'])
    def add_address():
        if 'customer_id' not in session:
            return jsonify({'error': 'Vui lòng đăng nhập'}), 401
        try:
            data = request.json
            customer_id = session['customer_id']
            contact_name = data.get('contact_name')
            phone = data.get('phone')
            address = data.get('address')
            is_default = data.get('is_default', False)
            if not contact_name or not phone or not address:
                return jsonify({"error": "Thiếu thông tin liên hệ, số điện thoại hoặc địa chỉ"}), 400
            address_id = str(uuid.uuid4())
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO addresses (address_id, customer_id, contact_name, phone, address, is_default)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (address_id, customer_id, contact_name, phone, address, is_default))
            conn.commit()
            conn.close()
            logger.debug(f"Thêm địa chỉ cho customer_id: {customer_id}, address_id: {address_id}")
            return jsonify({"message": "Thêm địa chỉ thành công", "address_id": address_id}), 200
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi thêm địa chỉ: {str(e)}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi khi thêm địa chỉ: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/addresses/<address_id>', methods=['PUT'])
    def update_address(address_id):
        if 'customer_id' not in session:
            return jsonify({'error': 'Vui lòng đăng nhập'}), 401
        try:
            data = request.json
            customer_id = session['customer_id']
            contact_name = data.get('contact_name')
            phone = data.get('phone')
            address = data.get('address')
            is_default = data.get('is_default', False)
            if not contact_name or not phone or not address:
                return jsonify({"error": "Thiếu thông tin liên hệ, số điện thoại hoặc địa chỉ"}), 400
            conn = get_db_connection()
            cursor = conn.execute('SELECT * FROM addresses WHERE address_id = ? AND customer_id = ?', (address_id, customer_id))
            existing_address = cursor.fetchone()
            if not existing_address:
                conn.close()
                return jsonify({"error": "Không tìm thấy địa chỉ"}), 404
            conn.execute('''
                UPDATE addresses
                SET contact_name = ?, phone = ?, address = ?, is_default = ?
                WHERE address_id = ? AND customer_id = ?
            ''', (contact_name, phone, address, is_default, address_id, customer_id))
            conn.commit()
            conn.close()
            logger.debug(f"Cập nhật địa chỉ: address_id: {address_id}")
            return jsonify({"message": "Cập nhật địa chỉ thành công"}), 200
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi cập nhật địa chỉ: {str(e)}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật địa chỉ: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/addresses/<address_id>', methods=['DELETE'])
    def delete_address(address_id):
        if 'customer_id' not in session:
            return jsonify({'error': 'Vui lòng đăng nhập'}), 401
        try:
            customer_id = session['customer_id']
            conn = get_db_connection()
            cursor = conn.execute('SELECT * FROM addresses WHERE address_id = ? AND customer_id = ?', (address_id, customer_id))
            existing_address = cursor.fetchone()
            if not existing_address:
                conn.close()
                return jsonify({"error": "Không tìm thấy địa chỉ"}), 404
            conn.execute('DELETE FROM addresses WHERE address_id = ? AND customer_id = ?', (address_id, customer_id))
            conn.commit()
            conn.close()
            logger.debug(f"Xóa địa chỉ: address_id: {address_id}")
            return jsonify({"message": "Xóa địa chỉ thành công"}), 200
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi xóa địa chỉ: {str(e)}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi khi xóa địa chỉ: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/addresses/set-default/<address_id>', methods=['PUT'])
    def set_default_address(address_id):
        if 'customer_id' not in session:
            return jsonify({'error': 'Vui lòng đăng nhập'}), 401
        try:
            customer_id = session['customer_id']
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM addresses WHERE address_id = ? AND customer_id = ?', (address_id, customer_id))
            existing_address = cursor.fetchone()
            if not existing_address:
                conn.close()
                return jsonify({"error": "Không tìm thấy địa chỉ hoặc không thuộc về bạn"}), 404
            cursor.execute('UPDATE addresses SET is_default = 0 WHERE customer_id = ?', (customer_id,))
            cursor.execute('UPDATE addresses SET is_default = 1 WHERE address_id = ? AND customer_id = ?', (address_id, customer_id))
            conn.commit()
            conn.close()
            logger.debug(f"Đặt địa chỉ mặc định: address_id={address_id}, customer_id={customer_id}")
            return jsonify({"message": "Đặt địa chỉ mặc định thành công"}), 200
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi đặt địa chỉ mặc định: {str(e)}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi khi đặt địa chỉ mặc định: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/orders', methods=['GET'])
    def get_orders():
        if 'customer_id' not in session:
            logger.warning("Unauthorized access attempt to /api/orders")
            return jsonify({'error': 'Vui lòng đăng nhập'}), 401
        try:
            customer_id = session['customer_id']
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            conn = get_db_connection()
            query = '''
                SELECT o.order_id, o.order_date, o.status, od.product_id, od.quantity, od.unit_price, od.total_price, 
                       p.product_name, ps.size, ps.size_id, 
                       COALESCE(u.user_add, (SELECT address FROM addresses WHERE customer_id = u.customer_id AND is_default = TRUE LIMIT 1), 'Chưa cung cấp địa chỉ') AS user_add,
                       pm.payment_method
                FROM orders o
                JOIN order_details od ON o.order_id = od.order_id
                JOIN products p ON od.product_id = p.product_id
                JOIN product_size ps ON od.size_id = ps.size_id
                JOIN users u ON o.customer_id = u.customer_id
                LEFT JOIN payments pm ON o.order_id = pm.order_id
                WHERE o.customer_id = ?
            '''
            params = [customer_id]
            if start_date and end_date:
                query += ' AND DATE(o.order_date) BETWEEN ? AND ?'
                params.extend([start_date, end_date])
            query += ' ORDER BY o.order_date DESC, o.order_id'
            logger.debug(f"Executing orders query: {query} with params: {params}")
            orders = conn.execute(query, params).fetchall()
            logger.debug(f"Fetched orders: {[dict(row) for row in orders]}")
            conn.close()
            order_dict = {}
            for row in orders:
                order_id = row['order_id']
                if order_id not in order_dict:
                    order_dict[order_id] = {
                        'order_id': order_id,
                        'order_date': row['order_date'],
                        'status': row['status'],
                        'payment_method': row['payment_method'],
                        'products': [],
                        'total_amount': 0,
                        'shipping_address': row['user_add']
                    }
                order_dict[order_id]['products'].append({
                    'product_id': row['product_id'],
                    'product_name': row['product_name'],
                    'unit_price': float(row['unit_price']),
                    'total_price': float(row['total_price']),
                    'quantity': row['quantity'],
                    'size': row['size'] or 'Không xác định',
                    'size_id': row['size_id']
                })
                order_dict[order_id]['total_amount'] += float(row['total_price'])
            orders_list = list(order_dict.values())
            logger.info(f"Returning {len(orders_list)} orders for customer_id: {customer_id}")
            return jsonify(orders_list), 200
        except sqlite3.Error as e:
            logger.error(f"Database error fetching orders: {str(e)}, customer_id={customer_id}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Unexpected error fetching orders: {str(e)}, customer_id={customer_id}")
            return jsonify({"error": str(e)}), 500
        finally:
            if 'conn' in locals():
                conn.close()

    @app.route('/api/orders/<order_id>', methods=['DELETE'])
    def delete_user_order(order_id):
        if 'customer_id' not in session:
            return jsonify({'error': 'Vui lòng đăng nhập'}), 401
        try:
            customer_id = session['customer_id']
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM orders WHERE order_id = ? AND customer_id = ?', (order_id, customer_id))
            order = cursor.fetchone()
            if not order:
                conn.close()
                return jsonify({"error": "Không tìm thấy đơn hàng hoặc không thuộc về bạn"}), 404
            if order['status'].lower() != 'pending':
                conn.close()
                return jsonify({"error": "Chỉ có thể hủy đơn hàng đang chờ xử lý"}), 400
            cursor.execute('DELETE FROM orders WHERE order_id = ? AND customer_id = ?', (order_id, customer_id))
            if cursor.rowcount == 0:
                conn.close()
                return jsonify({"error": "Không thể xóa đơn hàng"}), 500
            conn.commit()
            conn.close()
            logger.debug(f"Xóa đơn hàng: order_id={order_id}, customer_id={customer_id}")
            return jsonify({"message": "Hủy và xóa đơn hàng thành công"}), 200
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi xóa đơn hàng: {str(e)}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi khi xóa đơn hàng: {str(e)}")
            return jsonify({"error": str(e)}), 500