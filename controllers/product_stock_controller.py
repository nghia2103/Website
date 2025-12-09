# controllers/product_stock_controller.py
from flask import render_template, jsonify, session, flash, redirect, url_for, request
from models.product_stock import ProductStock
import logging
from utils.db import get_db_connection
import sqlite3

logger = logging.getLogger(__name__)

class ProductStockController:
    def product_stock(self):
        logger.debug("Accessing product_stock")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session, redirecting to login")
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            admin_id = session['admin_id']
            stock_items, stores = ProductStock.get_stock_items()
            cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
            admin = cursor.fetchone() or {'first_name': 'Admin', 'last_name': ''}
            conn.close()
            return render_template('admin_dashboard/dashboard/product_stock.html', stock_items=stock_items, stores=stores, admin=dict(admin))
        except Exception as e:
            logger.error(f"Error in product_stock: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return jsonify({'success': False, 'message': str(e)}), 500

    def add_stock_item(self):
        logger.debug("Adding stock item")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session")
            return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
        try:
            data = request.get_json()
            item_name = data.get('item_name')
            category = data.get('category')
            stock_quantity = int(data.get('stock_quantity', 0))
            store_id = data.get('store_id')

            if not all([item_name, category, stock_quantity >= 0, store_id]):
                logger.warning("Invalid or missing data for adding stock item")
                return jsonify({'success': False, 'message': 'Thông tin không hợp lệ hoặc thiếu'}), 400

            stock_item = ProductStock.add_stock_item(item_name, category, stock_quantity, store_id)
            logger.info(f"Stock item {stock_item['stock_item_id']} added successfully")
            return jsonify({'success': True, 'item': stock_item}), 200
        except ValueError:
            logger.warning("Invalid stock quantity format")
            return jsonify({'success': False, 'message': 'Số lượng tồn kho phải là số nguyên'}), 400
        except sqlite3.Error as e:
            logger.error(f"Database error in add_stock_item: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
        except Exception as e:
            logger.error(f"Unexpected error in add_stock_item: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

    def edit_stock_item(self, item_id):
        logger.debug(f"Editing stock item: item_id={item_id}")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session")
            return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
        try:
            data = request.get_json()
            item_name = data.get('item_name')
            category = data.get('category')
            stock_quantity = int(data.get('stock_quantity', 0))
            store_id = data.get('store_id')

            if not all([item_name, category, stock_quantity >= 0, store_id]):
                logger.warning("Invalid or missing data for editing stock item")
                return jsonify({'success': False, 'message': 'Thông tin không hợp lệ hoặc thiếu'}), 400

            stock_item = ProductStock.edit_stock_item(item_id, item_name, category, stock_quantity, store_id)
            if not stock_item:
                logger.warning(f"Stock item {item_id} not found")
                return jsonify({'success': False, 'message': 'Sản phẩm không tồn tại'}), 404

            logger.info(f"Stock item {item_id} updated successfully")
            return jsonify({'success': True, 'item': stock_item}), 200
        except ValueError:
            logger.warning("Invalid stock quantity format")
            return jsonify({'success': False, 'message': 'Số lượng tồn kho phải là số nguyên'}), 400
        except sqlite3.Error as e:
            logger.error(f"Database error in edit_stock_item: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
        except Exception as e:
            logger.error(f"Unexpected error in edit_stock_item: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

    def delete_stock_item(self, item_id):
        logger.debug(f"Deleting stock item: item_id={item_id}")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session")
            return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
        try:
            success = ProductStock.delete_stock_item(item_id)
            if not success:
                logger.warning(f"Cannot delete stock item {item_id}: Not found")
                return jsonify({'success': False, 'message': 'Sản phẩm không tồn tại'}), 404

            logger.info(f"Stock item {item_id} deleted successfully")
            return jsonify({'success': True}), 200
        except sqlite3.Error as e:
            logger.error(f"Database error in delete_stock_item: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
        except Exception as e:
            logger.error(f"Unexpected error in delete_stock_item: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500