from flask import request, jsonify, current_app
import logging
import os
import uuid
from werkzeug.utils import secure_filename
from models.productadmin import ProductAdmin
from utils.db import get_db_connection 
import sqlite3

logger = logging.getLogger(__name__)

class ProductAdminController:
    def add_product(self):
        logger.debug("Adding product")
        try:
            product_name = request.form.get('product_name')
            stock = int(request.form.get('stock'))
            description = request.form.get('description')
            discount = request.form.get('discount')
            category = request.form.get('category')
            size_s = request.form.get('size_s')
            price_s = request.form.get('price_s')
            size_m = request.form.get('size_m')
            price_m = request.form.get('price_m')
            size_l = request.form.get('size_l')
            price_l = request.form.get('price_l')

            if 'image_file' not in request.files or 'image_file_2' not in request.files:
                return jsonify({'success': False, 'message': 'Thiếu tệp ảnh.'}), 400

            image_file = request.files['image_file']
            image_file_2 = request.files['image_file_2']

            if image_file.filename == '' or image_file_2.filename == '':
                return jsonify({'success': False, 'message': 'Phải chọn cả hai tệp ảnh.'}), 400

            allowed_extensions = {'jpg', 'jpeg', 'png', 'avif'}
            if not ('.' in image_file.filename and image_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions) or \
               not ('.' in image_file_2.filename and image_file_2.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                return jsonify({'success': False, 'message': 'Định dạng ảnh không hợp lệ. Chỉ chấp nhận jpg, jpeg, png, avif.'}), 400

            if image_file.filename == image_file_2.filename:
                return jsonify({'success': False, 'message': 'Ảnh 1 và ảnh 2 không được trùng nhau.'}), 400

            image_filename = secure_filename(image_file.filename)
            image_filename_2 = secure_filename(image_file_2.filename)
            image_ext = image_filename.rsplit('.', 1)[1].lower()
            image_filename_2_ext = image_filename_2.rsplit('.', 1)[1].lower()
            unique_image_filename = f"{uuid.uuid4().hex}.{image_ext}"
            unique_image_filename_2 = f"{uuid.uuid4().hex}.{image_filename_2_ext}"

            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_image_filename)
            image_path_2 = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_image_filename_2)
            image_file.save(image_path)
            image_file_2.save(image_path_2)

            image_url = f"/static/Upload/{unique_image_filename}"
            image_url_2 = f"/static/Upload/{unique_image_filename_2}"

            if not all([product_name, stock >= 0, category in ['Coffees', 'Drinks', 'Foods', 'Yogurts']]):
                return jsonify({'success': False, 'message': 'Thông tin không hợp lệ hoặc thiếu.'}), 400

            sizes = []
            if size_s and price_s:
                price_s = float(price_s)
                if price_s <= 0:
                    return jsonify({'success': False, 'message': 'Giá cho kích thước S phải lớn hơn 0.'}), 400
                sizes.append(('S', price_s))
            if size_m and price_m:
                price_m = float(price_m)
                if price_m <= 0:
                    return jsonify({'success': False, 'message': 'Giá cho kích thước M phải lớn hơn 0.'}), 400
                sizes.append(('M', price_m))
            if size_l and price_l:
                price_l = float(price_l)
                if price_l <= 0:
                    return jsonify({'success': False, 'message': 'Giá cho kích thước L phải lớn hơn 0.'}), 400
                sizes.append(('L', price_l))
            
            if not sizes:
                return jsonify({'success': False, 'message': 'Phải cung cấp ít nhất một kích thước và giá.'}), 400

            discount_value = None
            if discount:
                try:
                    discount_value = int(discount)
                    if not (0 <= discount_value <= 100):
                        return jsonify({'success': False, 'message': 'Chiết khấu phải từ 0 đến 100.'}), 400
                except ValueError:
                    return jsonify({'success': False, 'message': 'Giá trị chiết khấu không hợp lệ.'}), 400

            product_id, price_m_value = ProductAdmin.add_product(
                product_name, stock, description, discount_value, category, sizes, image_url, image_url_2
            )

            return jsonify({
                'success': True,
                'product': {
                    'product_id': product_id,
                    'product_name': product_name,
                    'stock': stock,
                    'description': description,
                    'image_url': image_url,
                    'image_url_2': image_url_2,
                    'discount': discount_value,
                    'category': category,
                    'price_m': price_m_value or 0,
                    'avg_rating': 0
                }
            }), 200
        except sqlite3.Error as e:
            logger.error(f"Database error in add_product: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
        except Exception as e:
            logger.error(f"Unexpected error in add_product: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def edit_product(self, product_id):
        logger.debug(f"Editing product: product_id={product_id}")
        try:
            product_name = request.form.get('product_name')
            stock = request.form.get('stock')
            description = request.form.get('description')
            discount = request.form.get('discount')
            category = request.form.get('category')
            size_s = request.form.get('size_s')
            price_s = request.form.get('price_s')
            size_m = request.form.get('size_m')
            price_m = request.form.get('price_m')
            size_l = request.form.get('size_l')
            price_l = request.form.get('price_l')

            if not all([product_name, stock, category]):
                return jsonify({'success': False, 'message': 'Thiếu thông tin bắt buộc: tên sản phẩm, số lượng tồn kho, hoặc danh mục.'}), 400

            try:
                stock = int(stock)
                if stock < 0:
                    return jsonify({'success': False, 'message': 'Số lượng tồn kho phải lớn hơn hoặc bằng 0.'}), 400
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'Số lượng tồn kho phải là số nguyên.'}), 400

            if category not in ['Coffees', 'Drinks', 'Foods', 'Yogurts']:
                return jsonify({'success': False, 'message': 'Danh mục không hợp lệ.'}), 400

            discount_value = None
            if discount:
                try:
                    discount_value = int(discount)
                    if not (0 <= discount_value <= 100):
                        return jsonify({'success': False, 'message': 'Chiết khấu phải từ 0 đến 100.'}), 400
                except (ValueError, TypeError):
                    return jsonify({'success': False, 'message': 'Giá trị chiết khấu không hợp lệ.'}), 400

            sizes = []
            for size, price in [('S', price_s), ('M', price_m), ('L', price_l)]:
                if request.form.get(f'size_{size.lower()}') and price:
                    try:
                        price_value = float(price)
                        if price_value <= 0:
                            return jsonify({'success': False, 'message': f'Giá cho kích thước {size} phải lớn hơn 0.'}), 400
                        sizes.append((size, price_value))
                    except (ValueError, TypeError):
                        return jsonify({'success': False, 'message': f'Giá cho kích thước {size} không hợp lệ.'}), 400

            if not sizes:
                return jsonify({'success': False, 'message': 'Phải cung cấp ít nhất một kích thước và giá.'}), 400

            current_product, _ = ProductAdmin.get_product_by_id(product_id)
            if not current_product:
                return jsonify({'success': False, 'message': 'Sản phẩm không tồn tại.'}), 404

            image_url = current_product['image_url']
            image_url_2 = current_product['image_url_2']

            image_file = request.files.get('image_file')
            image_file_2 = request.files.get('image_file_2')

            allowed_extensions = {'jpg', 'jpeg', 'png', 'avif'}
            if image_file and image_file.filename and ('.' in image_file.filename and image_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                filename = secure_filename(image_file.filename)
                ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{ext}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                image_file.save(file_path)
                image_url = f"/static/Upload/{unique_filename}"

            if image_file_2 and image_file_2.filename and ('.' in image_file_2.filename and image_file_2.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
                filename = secure_filename(image_file_2.filename)
                ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{ext}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                image_file_2.save(file_path)
                image_url_2 = f"/static/Upload/{unique_filename}"

            product, price_m_value = ProductAdmin.edit_product(
                product_id, product_name, stock, description, discount_value, category, sizes, image_url, image_url_2
            )
            if not product:
                return jsonify({'success': False, 'message': 'Sản phẩm không tồn tại.'}), 404

            product['price_m'] = price_m_value or 0
            return jsonify({
                'success': True,
                'product': product,
                'sizes': sizes  # Trả về sizes để đồng bộ với GET /api/products/<product_id>
            }), 200
        except sqlite3.Error as e:
            logger.error(f"Database error in edit_product: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
        except Exception as e:
            logger.error(f"Unexpected error in edit_product: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    # Giữ nguyên phương thức delete_product

    def delete_product(self, product_id):
        logger.debug(f"Deleting product: product_id={product_id}")
        conn = None
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT product_id FROM products WHERE product_id = ?', (product_id,))
            product = cursor.fetchone()
            if not product:
                conn.close()
                return jsonify({'success': False, 'message': 'Product not found'}), 400

            cursor.execute('SELECT order_detail_id FROM order_details WHERE product_id = ?', (product_id,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Cannot delete product because it is used in orders'}), 400

            cursor.execute('DELETE FROM product_size WHERE product_id = ?', (product_id,))
            cursor.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
            conn.commit()
            conn.close()

            return jsonify({'success': True}), 200
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
                conn.close()
            logger.error(f"Database error in delete_product: {str(e)}")
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
        except Exception as e:
            if conn:
                conn.close()
            logger.error(f"Unexpected error in delete_product: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500