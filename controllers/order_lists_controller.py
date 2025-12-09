# controllers/order_lists_controller.py
from flask import render_template, jsonify, session, flash, redirect, url_for
from models.order_lists import OrderLists
import logging
from utils.db import get_db_connection

logger = logging.getLogger(__name__)

class OrderListsController:
    def order_lists(self):
        logger.debug("Accessing order_lists")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session, redirecting to login")
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            admin_id = session['admin_id']
            orders = OrderLists.get_orders()
            cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
            admin = cursor.fetchone() or {'first_name': 'Admin', 'last_name': ''}
            conn.close()
            return render_template('admin_dashboard/dashboard/order_lists.html', orders=orders, admin=dict(admin))
        except Exception as e:
            logger.error(f"Error in order_lists: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return jsonify({'success': False, 'message': str(e)}), 500