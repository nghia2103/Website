from flask import Flask, render_template, redirect, url_for, jsonify, request, session, send_from_directory, flash
import sqlite3
import os
from datetime import datetime
import pytz
import uuid
import random
import json 
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, Length, Optional
from flask_cors import CORS
import logging


app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app, supports_credentials=True, origins=['*'])
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class SignupForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(message="Vui lòng nhập tên"), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(message="Vui lòng nhập họ"), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(message="Vui lòng nhập email"), Email()])
    password = PasswordField('Password', validators=[DataRequired(message="Vui lòng nhập mật khẩu"), Length(min=6)])
    phone = StringField('Phone', validators=[Optional()])
    birthdate = DateField('Birthdate', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Submit')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(message="Vui lòng nhập email"), Email()])
    submit = SubmitField('Reset Password')

app = Flask(__name__)
app.secret_key = os.urandom(24).hex()
app.config['SECRET_KEY'] = app.secret_key

# Cấu hình upload
UPLOAD_FOLDER = 'static/Upload'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Đảm bảo thư mục uploads tồn tại
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Kiểm tra định dạng file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Kết nối database
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

# Format tiền tệ
def format_currency(value):
    if value is None or not isinstance(value, (int, float)):
        return "N/A"
    return "{:,.0f}".format(value).replace(',', '.')

app.jinja_env.filters['format_currency'] = format_currency

@app.route('/')
def index():
    if session.get('is_admin', False) and 'admin_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        print("No admin_id in session, redirecting to login")
        flash("Vui lòng đăng nhập với tư cách admin", "error")
        return redirect(url_for('login'))
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        admin_id = session['admin_id']  # Không dùng giá trị mặc định nữa
        print(f"Fetching admin with admin_id={admin_id}")
        cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
        admin = cursor.fetchone()
        if not admin:
            print(f"Admin not found for admin_id={admin_id}")
            flash("Tài khoản admin không tồn tại", "error")
            session.pop('admin_id', None)
            conn.close()
            return redirect(url_for('login'))

        cursor.execute('SELECT COUNT(*) as count FROM users')
        total_users = cursor.fetchone()['count']
        print(f"Total users: {total_users}")

        cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'Delivered'")
        total_orders = cursor.fetchone()['count']
        print(f"Total delivered orders: {total_orders}")

        cursor.execute("""
            SELECT SUM(od.total_price) as total 
            FROM order_details od
            JOIN orders o ON od.order_id = o.order_id
            WHERE o.status = 'Delivered'
        """)
        total_sales = cursor.fetchone()['total'] or 0
        print(f"Total sales: {total_sales}")

        cursor.execute("SELECT COUNT(*) as count FROM orders WHERE status = 'Pending'")
        total_pending = cursor.fetchone()['count']
        print(f"Total pending orders: {total_pending}")

        sales_data = [0] * 12
        cursor.execute("""
            SELECT strftime('%m', o.order_date) as month, SUM(od.total_price) as total
            FROM order_details od
            JOIN orders o ON od.order_id = o.order_id
            WHERE o.status = 'Delivered' AND strftime('%Y', o.order_date) = '2025'
            GROUP BY month
        """)
        for row in cursor:
            month = int(row['month']) - 1
            sales_data[month] = row['total'] / 1_000_000 if row['total'] else 0
        print(f"Sales data: {sales_data}")

        cursor.execute("""
            SELECT p.product_name, s.address as location, o.order_date,
                   od.quantity, od.total_price, o.status
            FROM order_details od
            JOIN products p ON od.product_id = p.product_id
            JOIN orders o ON od.order_id = o.order_id
            JOIN stores s ON o.store_id = s.store_id
            WHERE o.status IN ('Delivered', 'Pending')
            ORDER BY o.order_date DESC
            LIMIT 10
        """)
        deals = []
        for row in cursor:
            status_color = {'Delivered': 'success', 'Pending': 'warning', 'Cancelled': 'danger'}.get(row['status'], 'secondary')
            deals.append({
                'product_name': row['product_name'],
                'location': row['location'],
                'order_date': row['order_date'],
                'quantity': row['quantity'],
                'total_price': row['total_price'],
                'status': row['status'],
                'status_color': status_color
            })
        print(f"Deals: {deals}")

        conn.close()

        return render_template(
            'admin_dashboard/dashboard/dashboard.html',
            total_users=total_users,
            total_orders=total_orders,
            total_sales=total_sales,
            total_pending=total_pending,
            user_percentage=8.5,
            order_percentage=1.3,
            sales_percentage=4.3,
            pending_percentage=1.8,
            sales_data=sales_data,
            deals=deals,
            admin=dict(admin)
        )
    except sqlite3.Error as e:
        if conn:
            conn.close()
        print(f"Database error in dashboard: {str(e)}")
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        print(f"Unexpected error in dashboard: {str(e)}")
        flash(f"Lỗi: {str(e)}", "error")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/order_lists')
def order_lists():
    if 'admin_id' not in session:
        flash("Vui lòng đăng nhập với tư cách admin", "error")
        return redirect(url_for('login'))
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        admin_id = session['admin_id']
        cursor.execute("""
            SELECT 
                o.order_id, 
                u.first_name, 
                u.last_name, 
                o.order_date, 
                o.status,
                o.order_date AS raw_date
            FROM orders o
            JOIN users u ON o.customer_id = u.customer_id
        """)
        orders = []
        for row in cursor.fetchall():
            order = dict(row)
            cursor.execute("""
                SELECT 
                    p.product_name, 
                    od.quantity, 
                    ps.size, 
                    od.total_price
                FROM order_details od
                JOIN products p ON od.product_id = p.product_id
                JOIN product_size ps ON od.size_id = ps.size_id
                WHERE od.order_id = ?
            """, (order['order_id'],))
            order_details = cursor.fetchall()
            order['product_list'] = [f"{detail['product_name']} x{detail['quantity']}" for detail in order_details]
            order['size_list'] = [detail['size'] for detail in order_details]
            order['price_list'] = [detail['total_price'] for detail in order_details]
            formatted_date = datetime.strptime(order['order_date'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y - %I:%M %p')
            order['order_date'] = formatted_date
            order['status_color'] = {
                'Delivered': 'success',
                'Pending': 'warning',
                'Cancelled': 'danger',
                'Processing': 'info'
            }.get(order['status'], 'secondary')
            orders.append(order)
        cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
        admin = cursor.fetchone() or {'first_name': 'Admin', 'last_name': ''}
        conn.close()
        return render_template('admin_dashboard/dashboard/order_lists.html', orders=orders, admin=admin)
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/order/options')
def order_options():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT p.product_id, p.product_name, p.discount,
                   (SELECT json_group_array(
                       json_object(
                           'size', ps.size,
                           'price', ps.price,
                           'size_id', ps.size_id
                       )
                   ) FROM product_size ps WHERE ps.product_id = p.product_id) AS sizes
            FROM products p
        """)
        products = [
            {
                'product_id': row['product_id'],
                'product_name': row['product_name'],
                'discount': row['discount'],
                'sizes': json.loads(row['sizes'])
            }
            for row in cursor.fetchall()
        ]

        cursor.execute('SELECT store_id, store_name FROM stores')
        stores = [{'store_id': row['store_id'], 'store_name': row['store_name']} for row in cursor.fetchall()]

        cursor.execute('SELECT customer_id, first_name, last_name FROM users')
        customers = [{'customer_id': row['customer_id'], 'first_name': row['first_name'], 'last_name': row['last_name']} for row in cursor.fetchall()]

        conn.close()

        return jsonify({
            'products': products,
            'stores': stores,
            'customers': customers
        })
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/order/create', methods=['POST'])
def create_order():
    conn = None
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        product_id = data.get('product_id')
        quantity = int(data.get('quantity'))
        store_id = data.get('store_id')
        size = data.get('size', 'M')
        status = data.get('status', 'Pending')

        if not all([customer_id, product_id, quantity > 0, store_id, size]):
            return jsonify({'success': False, 'message': 'Thiếu hoặc sai thông tin bắt buộc'}), 400

        if size not in ['S', 'M', 'L']:
            return jsonify({'success': False, 'message': 'Kích cỡ không hợp lệ. Phải là S, M, hoặc L'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT customer_id FROM users WHERE customer_id = ?', (customer_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'ID khách hàng không hợp lệ'}), 400

        cursor.execute("""
            SELECT ps.size_id, ps.price, p.discount
            FROM product_size ps
            JOIN products p ON ps.product_id = p.product_id
            WHERE ps.product_id = ? AND ps.size = ?
        """, (product_id, size))
        size_data = cursor.fetchone()
        if not size_data:
            conn.close()
            return jsonify({'success': False, 'message': 'ID sản phẩm hoặc kích cỡ không hợp lệ'}), 400

        size_id = size_data['size_id']
        unit_price = size_data['price']  # Giá gốc
        total_price = size_data['price'] * quantity * (1 - (size_data['discount'] or 0) / 100)  # Giá sau discount

        cursor.execute('SELECT store_id FROM stores WHERE store_id = ?', (store_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'ID cửa hàng không hợp lệ'}), 400

        order_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        order_id = str(uuid.uuid4())[:8]
        order_detail_id = str(uuid.uuid4())[:8]
        cursor.execute("""
            INSERT INTO orders (order_id, customer_id, order_date, status, store_id)
            VALUES (?, ?, ?, ?, ?)
        """, (order_id, customer_id, order_date, status, store_id))

        cursor.execute("""
            INSERT INTO order_details (order_detail_id, order_id, product_id, size_id, quantity, unit_price, total_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (order_detail_id, order_id, product_id, size_id, quantity, unit_price, total_price))

        conn.commit()

        cursor.execute("""
            SELECT o.order_id, u.first_name, u.last_name, p.product_name, od.quantity, 
                   od.total_price, 
                   o.order_date, o.status, od.product_id, o.store_id, ps.size,
                   CASE
                       WHEN o.status = 'Delivered' THEN 'success'
                       WHEN o.status = 'Pending' THEN 'warning'
                       WHEN o.status = 'Cancelled' THEN 'danger'
                       WHEN o.status = 'Processing' THEN 'info'
                       ELSE 'secondary'
                   END AS status_color
            FROM orders o
            JOIN order_details od ON o.order_id = od.order_id
            JOIN products p ON od.product_id = p.product_id
            JOIN users u ON o.customer_id = u.customer_id
            JOIN product_size ps ON od.size_id = ps.size_id
            WHERE o.order_id = ?
        """, (order_id,))
        order = cursor.fetchone()

        if not order:
            conn.close()
            return jsonify({'success': False, 'message': 'Không lấy được đơn hàng vừa tạo'}), 500

        conn.close()

        formatted_date = datetime.strptime(order['order_date'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y - %I:%M %p')
        return jsonify({
            'success': True,
            'order': {
                'order_id': order['order_id'],
                'first_name': order['first_name'],
                'last_name': order['last_name'],
                'products': [{
                    'product_name': order['product_name'],
                    'size': order['size'],
                    'total_price': order['total_price'],
                    'quantity': order['quantity']
                }],
                'order_date': formatted_date,
                'raw_date': order['order_date'],
                'status': order['status'],
                'status_color': order['status_color']
            }
        })
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/order/update/<order_id>', methods=['POST'])
def update_order(order_id):
    conn = None
    try:
        data = request.get_json()
        customer_id = data.get('customer_id')
        product_id = data.get('product_id')
        quantity = int(data.get('quantity'))
        store_id = data.get('store_id')
        status = data.get('status')
        size = data.get('size', 'M')

        if not all([customer_id, product_id, quantity > 0, store_id, status, size]):
            return jsonify({'success': False, 'message': 'Thiếu hoặc sai thông tin bắt buộc'}), 400

        if size not in ['S', 'M', 'L']:
            return jsonify({'success': False, 'message': 'Kích cỡ không hợp lệ. Phải là S, M, hoặc L'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT order_id FROM orders WHERE order_id = ?', (order_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Không tìm thấy đơn hàng'}), 400

        cursor.execute('SELECT customer_id FROM users WHERE customer_id = ?', (customer_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'ID khách hàng không hợp lệ'}), 400

        cursor.execute("""
            SELECT ps.size_id, ps.price, p.discount
            FROM product_size ps
            JOIN products p ON ps.product_id = p.product_id
            WHERE ps.product_id = ? AND ps.size = ?
        """, (product_id, size))
        size_data = cursor.fetchone()
        if not size_data:
            conn.close()
            return jsonify({'success': False, 'message': 'ID sản phẩm hoặc kích cỡ không hợp lệ'}), 400

        size_id = size_data['size_id']
        unit_price = size_data['price']  # Giá gốc
        total_price = size_data['price'] * quantity * (1 - (size_data['discount'] or 0) / 100)  # Giá sau discount

        cursor.execute('SELECT store_id FROM stores WHERE store_id = ?', (store_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'ID cửa hàng không hợp lệ'}), 400

        cursor.execute("""
            UPDATE orders
            SET customer_id = ?, status = ?, store_id = ?
            WHERE order_id = ?
        """, (customer_id, status, store_id, order_id))

        cursor.execute('DELETE FROM order_details WHERE order_id = ?', (order_id,))

        order_detail_id = str(uuid.uuid4())[:8]
        cursor.execute("""
            INSERT INTO order_details (order_detail_id, order_id, product_id, size_id, quantity, unit_price, total_price)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (order_detail_id, order_id, product_id, size_id, quantity, unit_price, total_price))

        conn.commit()

        cursor.execute("""
            SELECT o.order_id, u.first_name, u.last_name, p.product_name, od.quantity, 
                   od.total_price, 
                   o.order_date, o.status, od.product_id, o.store_id, ps.size,
                   CASE
                       WHEN o.status = 'Delivered' THEN 'success'
                       WHEN o.status = 'Pending' THEN 'warning'
                       WHEN o.status = 'Cancelled' THEN 'danger'
                       WHEN o.status = 'Processing' THEN 'info'
                       ELSE 'secondary'
                   END AS status_color
            FROM orders o
            JOIN order_details od ON o.order_id = od.order_id
            JOIN products p ON od.product_id = p.product_id
            JOIN users u ON o.customer_id = u.customer_id
            JOIN product_size ps ON od.size_id = ps.size_id
            WHERE o.order_id = ?
        """, (order_id,))
        order = cursor.fetchone()

        if not order:
            conn.close()
            return jsonify({'success': False, 'message': 'Không lấy được đơn hàng vừa cập nhật'}), 500

        conn.close()

        formatted_date = datetime.strptime(order['order_date'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y - %I:%M %p')
        return jsonify({
            'success': True,
            'order': {
                'order_id': order['order_id'],
                'first_name': order['first_name'],
                'last_name': order['last_name'],
                'products': [{
                    'product_name': order['product_name'],
                    'size': order['size'],
                    'total_price': order['total_price'],
                    'quantity': order['quantity']
                }],
                'order_date': formatted_date,
                'raw_date': order['order_date'],
                'status': order['status'],
                'status_color': order['status_color']
            }
        })
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/order/delete/<order_id>', methods=['POST'])
def delete_order(order_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT order_id FROM orders WHERE order_id = ?', (order_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Order not found'}), 400

        cursor.execute('DELETE FROM orders WHERE order_id = ?', (order_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/order/mark_delivered/<order_id>', methods=['POST'])
def mark_delivered(order_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT order_id FROM orders WHERE order_id = ?', (order_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Order not found'}), 400

        cursor.execute("""
            UPDATE orders
            SET status = 'Delivered'
            WHERE order_id = ?
        """, (order_id,))

        conn.commit()

        cursor.execute("""
            SELECT o.order_id, u.first_name, u.last_name, p.product_name, od.quantity, 
                   od.total_price, 
                   o.order_date, o.status, od.product_id, o.store_id, ps.size,
                   CASE
                       WHEN o.status = 'Delivered' THEN 'success'
                       WHEN o.status = 'Pending' THEN 'warning'
                       WHEN o.status = 'Cancelled' THEN 'danger'
                       WHEN o.status = 'Processing' THEN 'info'
                       ELSE 'secondary'
                   END AS status_color
            FROM orders o
            JOIN order_details od ON o.order_id = od.order_id
            JOIN products p ON od.product_id = p.product_id
            JOIN users u ON o.customer_id = u.customer_id
            JOIN product_size ps ON od.size_id = ps.size_id
            WHERE o.order_id = ?
        """, (order_id,))
        order = cursor.fetchone()

        if not order:
            conn.close()
            return jsonify({'success': False, 'message': 'Failed to retrieve updated order'}), 500

        conn.close()

        formatted_date = datetime.strptime(order['order_date'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y - %I:%M %p')
        return jsonify({
            'success': True,
            'order': {
                'order_id': order['order_id'],
                'first_name': order['first_name'],
                'last_name': order['last_name'],
                'products': [{
                    'product_name': order['product_name'],
                    'size': order['size'],
                    'total_price': order['total_price'],
                    'quantity': order['quantity']
                }],
                'order_date': formatted_date,
                'raw_date': order['order_date'],
                'status': order['status'],
                'status_color': order['status_color']
            }
        })
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/order/mark_cancelled/<order_id>', methods=['POST'])
def mark_cancelled(order_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT order_id FROM orders WHERE order_id = ?', (order_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Order not found'}), 400

        cursor.execute("""
            UPDATE orders
            SET status = 'Cancelled'
            WHERE order_id = ?
        """, (order_id,))

        conn.commit()

        cursor.execute("""
            SELECT o.order_id, u.first_name, u.last_name, p.product_name, od.quantity, 
                   od.total_price, 
                   o.order_date, o.status, od.product_id, o.store_id, ps.size,
                   CASE
                       WHEN o.status = 'Delivered' THEN 'success'
                       WHEN o.status = 'Pending' THEN 'warning'
                       WHEN o.status = 'Cancelled' THEN 'danger'
                       WHEN o.status = 'Processing' THEN 'info'
                       ELSE 'secondary'
                   END AS status_color
            FROM orders o
            JOIN order_details od ON o.order_id = od.order_id
            JOIN products p ON od.product_id = p.product_id
            JOIN users u ON o.customer_id = u.customer_id
            JOIN product_size ps ON od.size_id = ps.size_id
            WHERE o.order_id = ?
        """, (order_id,))
        order = cursor.fetchone()

        if not order:
            conn.close()
            return jsonify({'success': False, 'message': 'Failed to retrieve updated order'}), 500

        conn.close()

        formatted_date = datetime.strptime(order['order_date'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y - %I:%M %p')
        return jsonify({
            'success': True,
            'order': {
                'order_id': order['order_id'],
                'first_name': order['first_name'],
                'last_name': order['last_name'],
                'products': [{
                    'product_name': order['product_name'],
                    'size': order['size'],
                    'total_price': order['total_price'],
                    'quantity': order['quantity']
                }],
                'order_date': formatted_date,
                'raw_date': order['order_date'],
                'status': order['status'],
                'status_color': order['status_color']
            }
        })
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/admin/products')
def products():
    if 'admin_id' not in session:
        flash("Vui lòng đăng nhập với tư cách admin", "error")
        return redirect(url_for('login'))
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        admin_id = session['admin_id']
        cursor.execute("""
            SELECT p.product_id, p.product_name, p.stock, p.description, p.image_url,
                   p.discount, p.category, 
                   CASE WHEN f.favorite_id IS NOT NULL THEN 1 ELSE 0 END as favorited,
                   (SELECT ps.price FROM product_size ps WHERE ps.product_id = p.product_id AND ps.size = 'M' LIMIT 1) as price_m,
                   (SELECT CAST(AVG(r.rating) AS REAL)
                    FROM reviews r
                    JOIN orders o ON o.order_id = r.order_id
                    WHERE r.product_id = p.product_id AND o.status = 'Delivered') as avg_rating
            FROM products p
            LEFT JOIN favorites f ON p.product_id = f.product_id AND f.admin_id = ?
        """, (admin_id,))
        products = []
        for row in cursor.fetchall():
            product = dict(row)
            product['avg_rating'] = float(product['avg_rating']) if product['avg_rating'] is not None else 0.0
            products.append(product)
        cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
        admin = cursor.fetchone() or {'first_name': 'Admin', 'last_name': ''}
        conn.close()
        return render_template('admin_dashboard/dashboard/products.html', products_query=products, admin=admin)
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/product/<product_id>', methods=['GET'])
def get_product(product_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT product_id, product_name, stock, description, image_url, image_url_2, discount, category
            FROM products
            WHERE product_id = ?
        """, (product_id,))
        product = cursor.fetchone()

        if not product:
            conn.close()
            return jsonify({'success': False, 'message': 'Product not found'}), 404

        cursor.execute("""
            SELECT size_id, size, price
            FROM product_size
            WHERE product_id = ?
        """, (product_id,))
        sizes = [{'size_id': row['size_id'], 'size': row['size'], 'price': row['price']} for row in cursor.fetchall()]

        conn.close()
        return jsonify({
            'success': True,
            'product': {
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'stock': product['stock'],
                'description': product['description'],
                'image_url': product['image_url'],
                'image_url_2': product['image_url_2'],
                'discount': product['discount'],
                'category': product['category']
            },
            'sizes': sizes
        })
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/product/add', methods=['POST'])
def add_product():
    conn = None
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

        # Xử lý ảnh
        if 'image_file' not in request.files or 'image_file_2' not in request.files:
            return jsonify({'success': False, 'message': 'Thiếu tệp ảnh.'}), 400

        image_file = request.files['image_file']
        image_file_2 = request.files['image_file_2']

        if image_file.filename == '' or image_file_2.filename == '':
            return jsonify({'success': False, 'message': 'Phải chọn cả hai tệp ảnh.'}), 400

        if not allowed_file(image_file.filename) or not allowed_file(image_file_2.filename):
            return jsonify({'success': False, 'message': 'Định dạng ảnh không hợp lệ. Chỉ chấp nhận jpg, jpeg, png.'}), 400

        if image_file.filename == image_file_2.filename:
            return jsonify({'success': False, 'message': 'Ảnh 1 và ảnh 2 không được trùng nhau.'}), 400

        # Lưu ảnh vào thư mục uploads
        image_filename = secure_filename(image_file.filename)
        image_filename_2 = secure_filename(image_file_2.filename)

        # Đặt tên file duy nhất để tránh trùng
        image_ext = image_filename.rsplit('.', 1)[1].lower()
        image_filename_2_ext = image_filename_2.rsplit('.', 1)[1].lower()
        unique_image_filename = f"{uuid.uuid4().hex}.{image_ext}"
        unique_image_filename_2 = f"{uuid.uuid4().hex}.{image_filename_2_ext}"

        image_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_image_filename)
        image_path_2 = os.path.join(app.config['UPLOAD_FOLDER'], unique_image_filename_2)
        image_file.save(image_path)
        image_file_2.save(image_path_2)

        # Đường dẫn ảnh để lưu vào cơ sở dữ liệu
        image_url = f"/{image_path}"
        image_url_2 = f"/{image_path_2}"

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

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO products (product_id, product_name, stock, description, image_url, image_url_2, discount, category)
            VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)
        """, (product_name, stock, description, image_url, image_url_2, discount_value, category))

        cursor.execute("SELECT product_id FROM products WHERE rowid = last_insert_rowid()")
        product_id = cursor.fetchone()['product_id']

        price_m_value = None
        for size, price in sizes:
            cursor.execute("""
                INSERT INTO product_size (size_id, product_id, size, price)
                VALUES (NULL, ?, ?, ?)
            """, (product_id, size, price))
            if size == 'M':
                price_m_value = price

        cursor.execute("""
            SELECT product_id, product_name, stock, description, image_url, image_url_2, discount, category
            FROM products
            WHERE product_id = ?
        """, (product_id,))
        product = cursor.fetchone()

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'product': {
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'stock': product['stock'],
                'description': product['description'],
                'image_url': product['image_url'],
                'image_url_2': product['image_url_2'],
                'discount': product['discount'],
                'category': product['category'],
                'price_m': price_m_value or 0,
                'avg_rating': 0  # New product, no reviews yet
            }
        })
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/checkout')
def checkout():
    if 'customer_id' not in session:
        flash("Vui lòng đăng nhập", "error")
        return redirect(url_for('login'))
    conn = None
    try:
        customer_id = session['customer_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.cart_id, c.product_id, c.quantity, c.size_id, ps.size, ps.price, 
                   p.product_name, p.image_url, p.discount
            FROM cart c
            JOIN product_size ps ON c.size_id = ps.size_id
            JOIN products p ON c.product_id = p.product_id
            WHERE c.customer_id = ?
        ''', (customer_id,))
        cart_items = []
        for row in cursor.fetchall():
            discount = row['discount'] or 0
            discounted_price = row['price'] * (1 - discount / 100)
            cart_items.append({
                'cart_id': row['cart_id'],
                'product_id': row['product_id'],
                'quantity': row['quantity'],
                'size_id': row['size_id'],
                'size': row['size'],
                'price': row['price'],
                'discounted_price': discounted_price,
                'product_name': row['product_name'],
                'image_url': row['image_url']
            })
        conn.close()
        if not cart_items:
            flash("Giỏ hàng trống!", "error")
            return redirect(url_for('products_user'))
        return render_template('Checkout.html', cart=cart_items)
    except sqlite3.Error as e:
        if conn:
            conn.close()
        logger.error(f"Lỗi cơ sở dữ liệu khi tải giỏ hàng: {str(e)}")
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
        return redirect(url_for('products_user'))
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Lỗi khi tải giỏ hàng: {str(e)}")
        flash(f"Lỗi: {str(e)}", "error")
        return redirect(url_for('products_user'))
        
@app.route('/product/edit/<product_id>', methods=['POST'])
def edit_product(product_id):
    conn = None
    try:
        # Log dữ liệu nhận được để debug
        print("Received form data:", dict(request.form))
        print("Received files:", list(request.files.keys()))

        # Lấy dữ liệu từ form
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

        # Kiểm tra dữ liệu bắt buộc
        if not all([product_name, stock, category]):
            return jsonify({'success': False, 'message': 'Thiếu thông tin bắt buộc: tên sản phẩm, số lượng tồn kho, hoặc danh mục.'}), 400

        # Kiểm tra stock
        try:
            stock = int(stock)
            if stock < 0:
                return jsonify({'success': False, 'message': 'Số lượng tồn kho phải lớn hơn hoặc bằng 0.'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Số lượng tồn kho phải là số nguyên.'}), 400

        # Kiểm tra danh mục
        if category not in ['Coffees', 'Drinks', 'Foods', 'Yogurts']:
            return jsonify({'success': False, 'message': 'Danh mục không hợp lệ.'}), 400

        # Kiểm tra discount
        discount_value = None
        if discount:
            try:
                discount_value = int(discount)
                if not (0 <= discount_value <= 100):
                    return jsonify({'success': False, 'message': 'Chiết khấu phải từ 0 đến 100.'}), 400
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'Giá trị chiết khấu không hợp lệ.'}), 400

        # Kiểm tra kích thước và giá
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

        # Kết nối database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Kiểm tra product_id
        cursor.execute("SELECT product_id, image_url, image_url_2 FROM products WHERE product_id = ?", (product_id,))
        current_product = cursor.fetchone()
        if not current_product:
            conn.close()
            return jsonify({'success': False, 'message': 'Sản phẩm không tồn tại.'}), 404

        image_url = current_product['image_url']
        image_url_2 = current_product['image_url_2']

        # Xử lý ảnh mới
        image_file = request.files.get('image_file')
        image_file_2 = request.files.get('image_file_2')

        if image_file and image_file.filename and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            ext = filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            image_file.save(file_path)
            image_url = f"/{file_path}"

        if image_file_2 and image_file_2.filename and allowed_file(image_file_2.filename):
            filename = secure_filename(image_file_2.filename)
            ext = filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            image_file_2.save(file_path)
            image_url_2 = f"/{file_path}"

        # Cập nhật sản phẩm
        cursor.execute("""
            UPDATE products
            SET product_name = ?, stock = ?, description = ?, image_url = ?, image_url_2 = ?, discount = ?, category = ?
            WHERE product_id = ?
        """, (product_name, stock, description, image_url, image_url_2, discount_value, category, product_id))

        # Lấy danh sách kích thước hiện tại
        cursor.execute("SELECT size, size_id FROM product_size WHERE product_id = ?", (product_id,))
        existing_sizes = {row['size']: row['size_id'] for row in cursor.fetchall()}

        # Danh sách kích thước được gửi từ form
        submitted_sizes = {size for size, _ in sizes}

        # Kiểm tra kích thước cần xóa
        sizes_to_delete = set(existing_sizes.keys()) - submitted_sizes
        for size in sizes_to_delete:
            size_id = existing_sizes[size]
            # Kiểm tra xem size_id có được tham chiếu trong order_details hoặc cart không
            cursor.execute("SELECT 1 FROM order_details WHERE size_id = ?", (size_id,))
            if cursor.fetchone():
                conn.close()
                return jsonify({
                    'success': False,
                    'message': f'Không thể xóa kích thước {size} vì đã được sử dụng trong đơn hàng.'
                }), 400
            cursor.execute("SELECT 1 FROM cart WHERE size_id = ?", (size_id,))
            if cursor.fetchone():
                conn.close()
                return jsonify({
                    'success': False,
                    'message': f'Không thể xóa kích thước {size} vì đang có trong giỏ hàng.'
                }), 400
            # Xóa kích thước nếu không được tham chiếu
            cursor.execute("DELETE FROM product_size WHERE size_id = ?", (size_id,))

        # Cập nhật hoặc thêm kích thước
        price_m_value = None
        for size, price in sizes:
            if size in existing_sizes:
                # Cập nhật giá cho kích thước hiện có
                cursor.execute("""
                    UPDATE product_size
                    SET price = ?
                    WHERE product_id = ? AND size = ?
                """, (price, product_id, size))
            else:
                # Thêm kích thước mới
                cursor.execute("""
                    INSERT INTO product_size (size_id, product_id, size, price)
                    VALUES (NULL, ?, ?, ?)
                """, (product_id, size, price))
            if size == 'M':
                price_m_value = price

        # Lấy đánh giá trung bình
        cursor.execute("""
            SELECT CAST(AVG(r.rating) AS REAL) as avg_rating
            FROM reviews r
            JOIN orders o ON o.order_id = r.order_id
            WHERE r.product_id = ? AND o.status = 'Delivered'
        """, (product_id,))
        avg_rating = cursor.fetchone()['avg_rating'] or 0.0

        # Lấy thông tin sản phẩm sau cập nhật
        cursor.execute("""
            SELECT product_id, product_name, stock, description, image_url, image_url_2, discount, category
            FROM products
            WHERE product_id = ?
        """, (product_id,))
        product = cursor.fetchone()

        if not product:
            conn.close()
            return jsonify({'success': False, 'message': 'Không thể lấy thông tin sản phẩm sau cập nhật.'}), 500

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'product': {
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'stock': product['stock'],
                'description': product['description'],
                'image_url': product['image_url'],
                'image_url_2': product['image_url_2'],
                'discount': product['discount'],
                'category': product['category'],
                'price_m': price_m_value or 0,
                'avg_rating': float(avg_rating)
            }
        })
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        print(f"SQLite error in edit_product: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        print(f"Unexpected error in edit_product: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'}), 500

@app.route('/product/delete/<product_id>', methods=['POST'])
def delete_product(product_id):
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

        return jsonify({'success': True})
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/favorites')
def favorites():
    if 'admin_id' not in session:
        print("No admin_id in session, redirecting to login")
        flash("Vui lòng đăng nhập với tư cách admin", "error")
        return redirect(url_for('login'))
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        admin_id = session.get('admin_id')
        print(f"Fetching favorites for admin_id={admin_id}")
        cursor.execute("""
            SELECT p.product_id, p.product_name, p.image_url,
                   (SELECT ps.price FROM product_size ps WHERE ps.product_id = p.product_id AND ps.size = 'M' LIMIT 1) as price_m,
                   (SELECT CAST(AVG(r.rating) AS REAL)
                    FROM reviews r
                    JOIN orders o ON o.order_id = r.order_id
                    WHERE r.product_id = p.product_id AND o.status = 'Delivered') as avg_rating
            FROM favorites f
            JOIN products p ON f.product_id = p.product_id
            WHERE f.admin_id = ?
        """, (admin_id,))
        favorites = []
        for row in cursor.fetchall():
            product = dict(row)
            product['avg_rating'] = float(product['avg_rating']) if product['avg_rating'] is not None else 0.0
            favorites.append(product)
        print(f"Favorites: {favorites}")

        cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
        admin = cursor.fetchone()
        if not admin:
            print(f"Admin not found for admin_id={admin_id}")
            flash("Tài khoản admin không tồn tại", "error")
            session.pop('admin_id', None)
            conn.close()
            return redirect(url_for('login'))

        conn.close()

        return render_template(
            'admin_dashboard/dashboard/favorite.html',
            favorites=favorites,
            admin=dict(admin)
        )
    except sqlite3.Error as e:
        if conn:
            conn.close()
        print(f"Database error in favorites: {str(e)}")
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        print(f"Unexpected error in favorites: {str(e)}")
        flash(f"Lỗi: {str(e)}", "error")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/favorite/add', methods=['POST'])
def add_favorite():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
    conn = None
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        admin_id = session['admin_id']
        if not product_id:
            return jsonify({'success': False, 'message': 'Missing product_id'}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT product_id FROM products WHERE product_id = ?', (product_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Product not found'}), 400
        cursor.execute('SELECT favorite_id FROM favorites WHERE admin_id = ? AND product_id = ?', (admin_id, product_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Product already in favorites'}), 400
        cursor.execute("""
            INSERT INTO favorites (admin_id, product_id)
            VALUES (?, ?)
        """, (admin_id, product_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/favorite/remove', methods=['POST'])
def remove_favorite():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
    conn = None
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        admin_id = session['admin_id']
        if not product_id:
            return jsonify({'success': False, 'message': 'Missing product_id'}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT favorite_id FROM favorites WHERE admin_id = ? AND product_id = ?', (admin_id, product_id))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Product not in favorites'}), 400
        cursor.execute("""
            DELETE FROM favorites
            WHERE admin_id = ? AND product_id = ?
        """, (admin_id, product_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/product_stock')
def product_stock():
    if 'admin_id' not in session:
        flash("Vui lòng đăng nhập với tư cách admin", "error")
        return redirect(url_for('login'))
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT si.stock_item_id, si.item_name, si.category, si.stock_quantity, si.store_id, si.last_updated, s.store_name
            FROM stock_items si
            JOIN stores s ON si.store_id = s.store_id
            ORDER BY si.last_updated DESC
        """)
        stock_items = []
        for row in cursor:
            last_updated = datetime.strptime(row['last_updated'], '%Y-%m-%d %H:%M:%S')
            formatted_last_updated = last_updated.strftime('%b %d, %Y - %I:%M %p')
            stock_items.append({
                'stock_item_id': row['stock_item_id'],
                'item_name': row['item_name'],
                'category': row['category'],
                'stock_quantity': row['stock_quantity'],
                'store_id': row['store_id'],
                'store_name': row['store_name'],
                'last_updated': row['last_updated'],
                'formatted_last_updated': formatted_last_updated
            })
        cursor.execute('SELECT store_id, store_name FROM stores')
        stores = [{'store_id': row['store_id'], 'store_name': row['store_name']} for row in cursor.fetchall()]
        admin_id = session['admin_id']
        cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
        admin = cursor.fetchone() or {'first_name': 'Admin', 'last_name': ''}
        conn.close()
        return render_template('admin_dashboard/dashboard/product_stock.html', stock_items=stock_items, stores=stores, admin=admin)
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/stock/add', methods=['POST'])
def add_stock():
    conn = None
    try:
        data = request.get_json()
        item_name = data.get('item_name')
        category = data.get('category')
        stock_quantity = int(data.get('stock_quantity'))
        store_id = data.get('store_id')

        if not all([item_name, category, stock_quantity >= 0, store_id]):
            return jsonify({'success': False, 'message': 'Missing or invalid fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO stock_items (item_name, category, stock_quantity, store_id, last_updated)
            VALUES (?, ?, ?, ?, ?)
        """, (item_name, category, stock_quantity, store_id, last_updated))

        cursor.execute("""
            SELECT si.stock_item_id, si.item_name, si.category, si.stock_quantity, si.store_id, si.last_updated, s.store_name
            FROM stock_items si
            JOIN stores s ON si.store_id = s.store_id
            WHERE si.rowid = last_insert_rowid()
        """)
        item = cursor.fetchone()

        conn.commit()
        conn.close()

        formatted_last_updated = datetime.strptime(item['last_updated'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y - %I:%M %p')
        return jsonify({
            'success': True,
            'item': {
                'stock_item_id': item['stock_item_id'],
                'item_name': item['item_name'],
                'category': item['category'],
                'stock_quantity': item['stock_quantity'],
                'store_id': item['store_id'],
                'store_name': item['store_name'],
                'last_updated': item['last_updated'],
                'formatted_last_updated': formatted_last_updated
            }
        })
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/stock/edit/<stock_item_id>', methods=['POST'])
def edit_stock(stock_item_id):
    conn = None
    try:
        data = request.get_json()
        item_name = data.get('item_name')
        category = data.get('category')
        stock_quantity = int(data.get('stock_quantity'))
        store_id = data.get('store_id')

        if not all([item_name, category, stock_quantity >= 0, store_id]):
            return jsonify({'success': False, 'message': 'Missing or invalid fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT stock_item_id FROM stock_items WHERE stock_item_id = ?', (stock_item_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Stock item not found'}), 400

        last_updated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            UPDATE stock_items
            SET item_name = ?, category = ?, stock_quantity = ?, store_id = ?, last_updated = ?
            WHERE stock_item_id = ?
        """, (item_name, category, stock_quantity, store_id, last_updated, stock_item_id))

        cursor.execute("""
            SELECT si.stock_item_id, si.item_name, si.category, si.stock_quantity, si.store_id, si.last_updated, s.store_name
            FROM stock_items si
            JOIN stores s ON si.store_id = s.store_id
            WHERE si.stock_item_id = ?
        """, (stock_item_id,))
        item = cursor.fetchone()

        conn.commit()
        conn.close()

        formatted_last_updated = datetime.strptime(item['last_updated'], '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y - %I:%M %p')
        return jsonify({
            'success': True,
            'item': {
                'stock_item_id': item['stock_item_id'],
                'item_name': item['item_name'],
                'category': item['category'],
                'stock_quantity': item['stock_quantity'],
                'store_id': item['store_id'],
                'store_name': item['store_name'],
                'last_updated': item['last_updated'],
                'formatted_last_updated': formatted_last_updated
            }
        })
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/stock/delete/<stock_item_id>', methods=['POST'])
def delete_stock(stock_item_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT stock_item_id FROM stock_items WHERE stock_item_id = ?', (stock_item_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Stock item not found'}), 400

        cursor.execute('DELETE FROM stock_items WHERE stock_item_id = ?', (stock_item_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

# @app.route('/inbox')
# def inbox():
#     if 'admin_id' not in session:
#         return jsonify({'success': False, 'message': 'Vui lòng đăng nhập'}), 401
#     conn = None
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#         admin_id = session['admin_id']
#         cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
#         admin = cursor.fetchone()
#         if not admin:
#             conn.close()
#             return jsonify({'success': False, 'message': 'Admin không tồn tại'}), 404
#         conn.close()
#         return render_template('admin_dashboard/dashboard/inbox.html', admin=admin)
#     except sqlite3.Error as e:
#         if conn:
#             conn.close()
#         return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
#     except Exception as e:
#         if conn:
#             conn.close()
#         return jsonify({'success': False, 'message': str(e)}), 500


# Test
@app.route('/inbox')
def inbox():
    if 'admin_id' not in session:
        flash("Vui lòng đăng nhập với tư cách admin", "error")
        return redirect(url_for('login'))
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        admin_id = session['admin_id']
        cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
        admin = cursor.fetchone()
        if not admin:
            conn.close()
            return jsonify({'success': False, 'message': 'Admin không tồn tại'}), 404
        conn.close()
        return render_template('admin_dashboard/dashboard/inbox.html', admin=admin)
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

# @app.route('/test_send_user_message', methods=['POST'])
# def test_send_user_message():
#     if 'customer_id' not in session:
#         return jsonify({'error': 'Vui lòng đăng nhập'}, 401)
#     return send_message()
# Test



@app.route('/get_threads')
def get_threads():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
    admin_id = session['admin_id']
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
        
        conn.close()
        return jsonify({'success': True, 'threads': threads})
    except sqlite3.Error as e:
        if conn:
            conn.close()
        logger.error(f"Lỗi cơ sở dữ liệu trong get_threads: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Lỗi không xác định trong get_threads: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/get_messages/<user_id>')
def get_messages(user_id):
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
    admin_id = session['admin_id']
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Kiểm tra xem user đã được gán cho admin khác chưa
        cursor.execute("SELECT admin_id FROM user_admin_assignments WHERE user_id = ?", (user_id,))
        assigned_admin = cursor.fetchone()
        if assigned_admin and assigned_admin['admin_id'] != admin_id:
            conn.close()
            return jsonify({'success': False, 'message': 'Cuộc trò chuyện này đã được admin khác xử lý'}), 403
        
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
        conn.close()
        return jsonify({'success': True, 'messages': messages})
    except sqlite3.Error as e:
        if conn:
            conn.close()
        logger.error(f"Lỗi cơ sở dữ liệu trong get_messages: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Lỗi không xác định trong get_messages: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/user_messages/<user_id>')
def user_messages(user_id):
    if 'customer_id' not in session or session['customer_id'] != user_id:
        return jsonify({'success': False, 'message': 'Không có quyền truy cập hoặc chưa đăng nhập'}), 401
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Lấy admin_id từ user_admin_assignments nếu đã gán
        cursor.execute("SELECT admin_id FROM user_admin_assignments WHERE user_id = ?", (user_id,))
        assigned_admin = cursor.fetchone()
        admin_id = assigned_admin['admin_id'] if assigned_admin else None
        
        # Lấy tất cả tin nhắn của user, bất kể admin_id
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
        
        conn.close()
        return jsonify({'success': True, 'messages': messages})
    except sqlite3.Error as e:
        if conn:
            conn.close()
        logger.error(f"Lỗi cơ sở dữ liệu trong user_messages: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Lỗi không xác định trong user_messages: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/assign_admin', methods=['POST'])
def assign_admin():
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
    admin_id = session['admin_id']
    conn = None
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'success': False, 'message': 'Thiếu user_id'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Kiểm tra user_id tồn tại
        cursor.execute("SELECT customer_id FROM users WHERE customer_id = ?", (user_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'ID khách hàng không hợp lệ'}), 400
        
        # Kiểm tra xem user đã được gán chưa
        cursor.execute("SELECT admin_id FROM user_admin_assignments WHERE user_id = ?", (user_id,))
        existing_assignment = cursor.fetchone()
        if existing_assignment:
            conn.close()
            if existing_assignment['admin_id'] == admin_id:
                return jsonify({'success': True, 'message': 'Đã gán admin cho user này'})
            return jsonify({'success': False, 'message': 'User đã được gán cho admin khác'}), 403
        
        # Gán admin cho user
        cursor.execute("""
            INSERT INTO user_admin_assignments (user_id, admin_id)
            VALUES (?, ?)
        """, (user_id, admin_id))
        
        # Cập nhật admin_id cho các tin nhắn hiện tại của user
        cursor.execute("""
            UPDATE messages
            SET admin_id = ?
            WHERE user_id = ? AND admin_id IS NULL
        """, (admin_id, user_id))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Gán admin thành công'})
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        logger.error(f"Lỗi cơ sở dữ liệu trong assign_admin: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Lỗi không xác định trong assign_admin: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/send_message', methods=['POST'])
def send_message():
    conn = None
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        admin_id = data.get('admin_id')
        direction = data.get('direction')
        content = data.get('content')

        if not all([user_id, direction, content]):
            return jsonify({'success': False, 'message': 'Thiếu thông tin bắt buộc'}), 400

        if direction not in ['user_to_admin', 'admin_to_user']:
            return jsonify({'success': False, 'message': 'Hướng tin nhắn không hợp lệ'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Kiểm tra quyền đăng nhập
        if direction == 'user_to_admin' and session.get('customer_id') != user_id:
            conn.close()
            return jsonify({'success': False, 'message': 'Bạn phải đăng nhập để gửi tin nhắn'}), 401
        if direction == 'admin_to_user' and session.get('admin_id') != admin_id:
            conn.close()
            return jsonify({'success': False, 'message': 'Bạn phải đăng nhập với tư cách admin để gửi tin nhắn'}), 401

        # Kiểm tra user_id tồn tại
        cursor.execute('SELECT customer_id FROM users WHERE customer_id = ?', (user_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'ID khách hàng không hợp lệ'}), 400

        # Nếu là user gửi, kiểm tra user_admin_assignments để gán admin_id
        if direction == 'user_to_admin':
            cursor.execute("SELECT admin_id FROM user_admin_assignments WHERE user_id = ?", (user_id,))
            assigned_admin = cursor.fetchone()
            admin_id = assigned_admin['admin_id'] if assigned_admin else None
        else:
            # Kiểm tra admin_id tồn tại
            cursor.execute('SELECT admin_id FROM admins WHERE admin_id = ?', (admin_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'ID admin không hợp lệ'}), 400
            
            # Kiểm tra gán admin
            cursor.execute("SELECT admin_id FROM user_admin_assignments WHERE user_id = ?", (user_id,))
            assigned_admin = cursor.fetchone()
            if assigned_admin and assigned_admin['admin_id'] != admin_id:
                conn.close()
                return jsonify({'success': False, 'message': 'User đã được gán cho admin khác'}), 403

        # Lưu tin nhắn
        cursor.execute("""
            INSERT INTO messages (message_id, user_id, admin_id, direction, content, timestamp, is_read)
            VALUES (NULL, ?, ?, ?, ?, ?, ?)
        """, (user_id, admin_id, direction, content, datetime.now().isoformat(), 0))
        cursor.execute('SELECT message_id FROM messages WHERE rowid = last_insert_rowid()')
        message = cursor.fetchone()
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message_id': message['message_id']})
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        logger.error(f"Lỗi cơ sở dữ liệu trong send_message: {str(e)}")
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Lỗi không xác định trong send_message: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500




@app.route('/login', methods=['GET', 'POST'])
def login():
    conn = None
    try:
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            logger.debug(f"Login attempt: email={email}")
            if not email or not password:
                flash("Please fill in both email and password", "error")
                return render_template('signup/login.html', error="Please fill in both email and password")

            conn = get_db_connection()
            cursor = conn.cursor()

            if email.startswith('admin/'):
                admin_email = email[6:]
                logger.debug(f"Admin login attempt: email={admin_email}")
                cursor.execute("SELECT admin_id, first_name, password FROM admins WHERE email = ?", (admin_email,))
                admin = cursor.fetchone()
                if admin and admin['password'] == password:
                    session.clear()  # Clear old session before admin login
                    session['admin_id'] = admin['admin_id']
                    session['first_name'] = admin['first_name']
                    session['is_admin'] = True
                    conn.close()
                    logger.info("Admin login successful")
                    return redirect(url_for('dashboard'))
                else:
                    flash("Invalid admin email or password", "error")
                    conn.close()
                    logger.warning("Admin login failed")
                    return render_template('signup/login.html', error="Invalid admin email or password")
            else:
                cursor.execute("SELECT customer_id, first_name, password FROM users WHERE email = ?", (email,))
                user = cursor.fetchone()
                if user and user['password'] == password:
                    session.clear()  # Clear old session before user login
                    session['customer_id'] = user['customer_id']
                    session['first_name'] = user['first_name']
                    session['is_admin'] = False
                    conn.close()
                    logger.info("User login successful")
                    return redirect(url_for('index'))
                else:
                    flash("Invalid email or password", "error")
                    conn.close()
                    logger.warning("User login failed")
                    return render_template('signup/login.html', error="Invalid email or password")

        logger.debug("Displaying login.html")
        return render_template('signup/login.html')
    except sqlite3.Error as e:
        if conn:
            conn.close()
        logger.error(f"Database error: {str(e)}")
        flash(f"Database error: {str(e)}", "error")
        return render_template('signup/login.html', error=f"Database error: {str(e)}")
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Unknown error: {str(e)}")
        flash(f"Error: {str(e)}", "error")
        return render_template('signup/login.html', error=str(e))


@app.route('/get_customer_id')
def get_customer_id():
    customer_id = session.get('customer_id')
    if not customer_id:
        return jsonify({'error': 'Vui lòng đăng nhập'}, 401)
    return jsonify({'customer_id': customer_id})

@app.route('/pages/pricing')
def pricing():
    if 'admin_id' not in session:
        flash("Vui lòng đăng nhập với tư cách admin", "error")
        return redirect(url_for('login'))
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        admin_id = session['admin_id']
        cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
        admin = cursor.fetchone() or {'first_name': 'Admin', 'last_name': ''}
        conn.close()
        return render_template('admin_dashboard/pages/pricing.html', admin=admin)
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/pages/to_do_list')
def to_do_list():
    if 'admin_id' not in session:
        flash("Vui lòng đăng nhập với tư cách admin", "error")
        return redirect(url_for('login'))
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        admin_id = session['admin_id']
        cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
        admin = cursor.fetchone() or {'first_name': 'Admin', 'last_name': ''}
        conn.close()
        return render_template('admin_dashboard/pages/to_do_list.html', admin=admin)
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/pages/invoices')
def invoices():
    if 'admin_id' not in session:
        flash("Vui lòng đăng nhập với tư cách admin", "error")
        return redirect(url_for('login'))
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        admin_id = session['admin_id']
        cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
        admin = cursor.fetchone() or {'first_name': 'Admin', 'last_name': ''}
        conn.close()
        return render_template('admin_dashboard/pages/invoices.html', admin=admin)
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500



@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

      
        filter_date = request.args.get('date')
        filter_customer = request.args.get('customer')

        
        query = """
        SELECT o.order_id AS code, u.first_name || ' ' || u.last_name AS customer_name, o.order_date AS date, o.status
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
                pass
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

        conn.close()

        return jsonify({
            'invoices': invoices_list,
            'customers': customers,
            'total_amount': total_amount
        })
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500
    
@app.route('/pages/setting')
def setting():
    if 'admin_id' not in session:
        flash("Vui lòng đăng nhập với tư cách admin", "error")
        return redirect(url_for('login'))
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        admin_id = session['admin_id']
        cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
        admin = cursor.fetchone() or {'first_name': 'Admin', 'last_name': ''}
        conn.close()
        return render_template('admin_dashboard/pages/setting.html', admin=admin)
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    flash("Đăng xuất thành công", "success")
    return redirect(url_for('login'))
    
@app.route('/productuser')
def product_user():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT product_id, product_name, stock, description, image_url, image_url_2, discount, category
            FROM products
        """)
        products = [dict(row) for row in cursor.fetchall()]
        customer_id = session.get('customer_id')
        user = None
        if customer_id:
            cursor.execute('SELECT first_name, last_name FROM users WHERE customer_id = ?', (customer_id,))
            user = cursor.fetchone()
        conn.close()
        return render_template(
            'productuser/productuser.html',
            products=products,
            user=user or {'first_name': 'Guest', 'last_name': ''}
        )
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/<path:filename>')
def serve_static(filename):
    logger.debug(f"Yêu cầu tệp tĩnh: {filename}")
    try:
        if filename.endswith('.html'):
            logger.warning(f"Yêu cầu file HTML không hợp lệ: {filename}")
            return jsonify({"error": f"Yêu cầu không hợp lệ: {filename}"}), 404
        if filename.startswith('templates/'):
            filename = filename[len('templates/'):]
        return send_from_directory('templates', filename)
    except Exception as e:
        logger.error(f"Lỗi khi phục vụ tệp tĩnh {filename}: {str(e)}")
        return jsonify({"error": f"Không tìm thấy tệp: {filename}"}), 404

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    try:
        return send_from_directory('templates', filename)
    except Exception as e:
        logger.error(f"Lỗi khi phục vụ tệp tài nguyên {filename}: {str(e)}")
        return jsonify({"error": f"Không tìm thấy tệp: {filename}"}), 404

@app.route('/reviews_upload/<filename>')
def serve_review_image(filename):
    try:
        return send_from_directory(os.path.join(app.static_folder, 'reviews_upload'), filename)
    except FileNotFoundError:
        logger.error(f"Tệp không tồn tại: {filename}")
        return jsonify({"error": f"Không tìm thấy tệp: {filename}"}), 404
    except Exception as e:
        logger.error(f"Lỗi khi phục vụ tệp {filename}: {str(e)}")
        return jsonify({"error": f"Lỗi khi phục vụ tệp: {str(e)}"}), 500


@app.route('/get_admins')
def get_admins():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
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
        conn.close()
        return jsonify({'success': True, 'admins': admins})
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/get_events')
def get_events():
    conn = None
    try:
        year = request.args.get('year')
        month = request.args.get('month')
        if not year or not month:
            return jsonify({'success': False, 'message': 'Year and month are required.'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        # Lấy thêm cột color
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
        conn.close()
        return jsonify({'success': True, 'events': events})
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/create_event', methods=['POST'])
def create_event():
    conn = None
    try:
        data = request.get_json()
        event_name = data.get('event_name')
        date = data.get('date')
        time = data.get('time')
        admin_id = data.get('admin_id')
        adminname = data.get('adminname')
        color = data.get('color') or random.choice(['green', 'blue', 'pink', 'purple', 'orange', 'yellow', 'red'])

        if not all([event_name, date, time, admin_id, adminname, color]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        # Kiểm tra định dạng ngày và giờ
        try:
            datetime.strptime(date, '%Y-%m-%d')
            datetime.strptime(time, '%H:%M')
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date or time format'}), 400

        # Kiểm tra admin_id tồn tại
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT admin_id FROM admins WHERE admin_id = ?', (admin_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid admin ID'}), 400

        # Chèn sự kiện vào database (event_id sẽ được trigger tự động tạo)
        cursor.execute("""
            INSERT INTO events (event_name, date, time, admin_id, adminname, color)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (event_name, date, time, admin_id, adminname, color))

        # Lấy sự kiện vừa tạo
        cursor.execute("""
            SELECT event_id, event_name, date, time, admin_id, adminname, color
            FROM events
            WHERE rowid = last_insert_rowid()
        """)
        event = cursor.fetchone()

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'event': {
                'event_id': event['event_id'],
                'event_name': event['event_name'],
                'date': event['date'],
                'time': event['time'],
                'admin_id': event['admin_id'],
                'adminname': event['adminname'],
                'color': event['color']
            }
        })
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500



@app.route('/get_all_events')
def get_all_events():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
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
        conn.close()
        return jsonify({'success': True, 'events': events})
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/update_event/<event_id>', methods=['POST'])
def update_event(event_id):
    conn = None
    try:
        data = request.get_json()
        event_name = data.get('event_name')
        date = data.get('date')
        time = data.get('time')
        admin_id = data.get('admin_id')
        adminname = data.get('adminname')
        color = data.get('color')

        if not all([event_name, date, time, admin_id, adminname, color]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        try:
            datetime.strptime(date, '%Y-%m-%d')
            datetime.strptime(time, '%H:%M')
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date or time format'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT admin_id FROM admins WHERE admin_id = ?', (admin_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid admin ID'}), 400

        cursor.execute('SELECT event_id FROM events WHERE event_id = ?', (event_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Event not found'}), 400

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
        conn.close()

        return jsonify({
            'success': True,
            'event': {
                'event_id': event['event_id'],
                'event_name': event['event_name'],
                'date': event['date'],
                'time': event['time'],
                'admin_id': event['admin_id'],
                'adminname': event['adminname'],
                'color': event['color']
            }
        })
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/delete_event/<event_id>', methods=['POST'])
def delete_event(event_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT event_id FROM events WHERE event_id = ?', (event_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Event not found'}), 400

        cursor.execute('DELETE FROM events WHERE event_id = ?', (event_id,))
        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/update_admin/<admin_id>', methods=['POST'])
def update_admin(admin_id):
    conn = None
    try:
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        admin_img = request.files.get('admin_img')

        if not all([first_name, last_name, email, phone]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if admin_id exists
        cursor.execute('SELECT admin_id, admin_img FROM admins WHERE admin_id = ?', (admin_id,))
        admin = cursor.fetchone()
        if not admin:
            conn.close()
            return jsonify({'success': False, 'message': 'Admin not found'}), 400

        # Check for duplicate email
        cursor.execute('SELECT admin_id FROM admins WHERE email = ? AND admin_id != ?', (email, admin_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Email already in use'}), 400

        # Handle image upload
        admin_img_path = admin['admin_img']
        if admin_img and allowed_file(admin_img.filename):
            filename = secure_filename(admin_img.filename)
            ext = filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{ext}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            admin_img.save(file_path)
            admin_img_path = f"/{file_path}"

        # Update admin
        cursor.execute("""
            UPDATE admins
            SET first_name = ?, last_name = ?, email = ?, phone = ?, admin_img = ?
            WHERE admin_id = ?
        """, (first_name, last_name, email, phone, admin_img_path, admin_id))

        # Fetch updated admin
        cursor.execute("""
            SELECT admin_id, first_name, last_name, email, phone, admin_img
            FROM admins
            WHERE admin_id = ?
        """, (admin_id,))
        updated_admin = cursor.fetchone()

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'admin': {
                'admin_id': updated_admin['admin_id'],
                'first_name': updated_admin['first_name'],
                'last_name': updated_admin['last_name'],
                'email': updated_admin['email'],
                'phone': updated_admin['phone'],
                'admin_img': updated_admin['admin_img']
            }
        })
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    conn = None
    try:
        if request.method == 'POST':
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            email = request.form.get('email')
            password = request.form.get('password')

            if not all([first_name, last_name, email, password]):
                flash("Vui lòng điền đầy đủ các trường", "error")
                return render_template('signup/sign_up.html')

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                flash("Email đã tồn tại", "email_error")
                conn.close()
                return render_template('signup/sign_up.html')

            cursor.execute(
                "INSERT INTO users (first_name, last_name, email, password, phone, birthdate) VALUES (?, ?, ?, ?, ?, ?)",
                (first_name, last_name, email, password, None, None)
            )
            conn.commit()
            conn.close()
            flash("Successfully register, please log in", "success")
            return redirect(url_for('login'))

        return render_template('signup/sign_up.html')
    except sqlite3.Error as e:
        if conn:
            conn.close()
        print(f"Database error: {str(e)}")
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
        return render_template('signup/sign_up.html')
    except Exception as e:
        if conn:
            conn.close()
        print(f"Unexpected error: {str(e)}")
        flash(f"Lỗi: {str(e)}", "error")
        return render_template('signup/sign_up.html')


@app.route('/pages/calendar')
def calendar():
    if 'admin_id' not in session:
        flash("Vui lòng đăng nhập với tư cách admin", "error")
        return redirect(url_for('login'))
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        admin_id = session['admin_id']
        cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
        admin = cursor.fetchone() or {'first_name': 'Admin', 'last_name': ''}
        conn.close()
        return render_template('admin_dashboard/pages/calendar.html', admin=admin)
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/pages/contact')
def contact():
    if 'admin_id' not in session:
        flash("Vui lòng đăng nhập với tư cách admin", "error")
        return redirect(url_for('login'))
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        admin_id = session['admin_id']
        cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
        admin = cursor.fetchone() or {'first_name': 'Admin', 'last_name': ''}
        conn.close()
        return render_template('admin_dashboard/pages/contact.html', admin=admin)
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500


# error 404 
@app.errorhandler(404)
def page_not_found(e):
    conn = None
    try:
        admin_id = session.get('admin_id')
        admin = {'first_name': 'Admin', 'last_name': ''} if admin_id else {'first_name': 'Guest', 'last_name': ''}
        if admin_id:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
            admin_row = cursor.fetchone()
            if admin_row:
                admin = dict(admin_row)
            conn.close()
        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_time = datetime.now(vietnam_tz).strftime('%b %d, %Y - %I:%M %p')
        return render_template(
            'admin_dashboard/error/404.html',
            admin=admin,
            current_time=current_time,
            error_message=str(e)
        ), 404
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if conn:
            conn.close()


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    conn = None
    try:
        if request.method == 'POST' and form.validate_on_submit():
            email = form.email.data
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            conn.close()
            if not user:
                flash("Email không tồn tại", "error")
                return render_template('signup/forgot_pass.html', form=form)
            flash("Succesfully sent email confirmation", "success")
            return redirect(url_for('login'))
        return render_template('signup/forgot_pass.html', form=form)
    except sqlite3.Error as e:
        if conn:
            conn.close()
        print(f"Database error: {str(e)}")
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
        return render_template('signup/forgot_pass.html', form=form)
    except Exception as e:
        if conn:
            conn.close()
        print(f"Unexpected error: {str(e)}")
        flash(f"Lỗi: {str(e)}", "error")
        return render_template('signup/forgot_pass.html', form=form)

@app.route('/api/products', methods=['GET'])
def get_products():
    try:
        conn = get_db_connection()
        products = conn.execute('''
            SELECT p.*, ps.size, ps.price, ps.size_id
            FROM products p
            LEFT JOIN product_size ps ON p.product_id = ps.product_id
        ''').fetchall()
        conn.close()
        product_dict = {}
        for row in products:
            product_id = row['product_id']
            if product_id not in product_dict:
                product_dict[product_id] = {
                    "product_id": row['product_id'],
                    "product_name": row['product_name'],
                    "category": row['category'],
                    "stock": row['stock'],
                    "description": row['description'],
                    "image_url": row['image_url'],
                    "image_url_2": row['image_url_2'],
                    "discount": row['discount'] or 0,
                    "sizes": []
                }
            if row['size']:
                product_dict[product_id]['sizes'].append({
                    "size": row['size'],
                    "price": row['price'],
                    "size_id": row['size_id']
                })
        products_list = list(product_dict.values())
        logger.debug(f"Trả về {len(products_list)} sản phẩm: {json.dumps(products_list, ensure_ascii=False)}")
        return jsonify(products_list)
    except Exception as e:
        logger.error(f"Lỗi khi lấy sản phẩm: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/products/<product_id>', methods=['GET'])
def get_product_by_id(product_id):
    try:
        conn = get_db_connection()
        product = conn.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
        if not product:
            conn.close()
            return jsonify({"error": "Product not found"}), 404
        sizes = conn.execute("SELECT size, price, size_id FROM product_size WHERE product_id = ?", (product_id,)).fetchall()
        conn.close()
        sizes_list = [{"size": row['size'], "price": row['price'], "size_id": row['size_id']} for row in sizes]
        return jsonify({
            "product_id": product['product_id'],
            "product_name": product['product_name'],
            "category": product['category'],
            "sizes": sizes_list,
            "stock": product['stock'],
            "description": product['description'],
            "image_url": product['image_url'],
            "image_url_2": product['image_url_2'],
            "discount": product['discount'] or 0
        })
    except Exception as e:
        logger.error(f"Lỗi khi lấy sản phẩm: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/checkout", methods=["POST"])
def add_checkout():
    data = request.json
    session["cart"] = data
    return jsonify({"status": "OK"})


@app.route("/api/checkout", methods=["GET"])
def get_checkout():
    return jsonify(session.get("cart", []))

# API lấy giỏ hàng
@app.route('/api/cart', methods=['GET'])
def get_cart():
    if 'customer_id' not in session:
        return jsonify({'error': 'Vui lòng đăng nhập'}), 401
    try:
        customer_id = session['customer_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.cart_id, c.product_id, c.quantity, c.size_id, ps.size, ps.price, 
                   p.product_name, p.image_url, p.discount
            FROM cart c
            JOIN product_size ps ON c.size_id = ps.size_id
            JOIN products p ON c.product_id = p.product_id
            WHERE c.customer_id = ?
        ''', (customer_id,))
        cart_items = []
        for row in cursor.fetchall():
            discount = row['discount'] or 0
            discounted_price = row['price'] * (1 - discount / 100)
            cart_items.append({
                'cart_id': row['cart_id'],
                'product_id': row['product_id'],
                'quantity': row['quantity'],
                'size_id': row['size_id'],
                'size': row['size'],
                'price': row['price'],
                'discounted_price': discounted_price,
                'product_name': row['product_name'],
                'image_url': row['image_url']
            })
        conn.close()
        return jsonify(cart_items), 200
    except Exception as e:
        logger.error(f"Lỗi khi lấy giỏ hàng: {str(e)}")
        return jsonify({"error": str(e)}), 500

# API thêm vào giỏ hàng
@app.route('/api/cart', methods=['POST'])
def add_to_cart():
    if 'customer_id' not in session:
        return jsonify({'error': 'Vui lòng đăng nhập'}), 401
    try:
        customer_id = session['customer_id']
        data = request.json
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        size_id = data.get('size_id')
        if not all([product_id, quantity, size_id]):
            logger.error(f"Thiếu thông tin sản phẩm: {data}")
            return jsonify({"error": "Thiếu product_id, quantity hoặc size_id"}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ps.size_id, ps.price, p.discount 
            FROM product_size ps
            JOIN products p ON ps.product_id = p.product_id
            WHERE ps.product_id = ? AND ps.size_id = ?
        ''', (product_id, size_id))
        size_data = cursor.fetchone()
        if not size_data:
            conn.close()
            logger.error(f"Kích thước không hợp lệ: product_id={product_id}, size_id={size_id}")
            return jsonify({"error": "Kích thước không hợp lệ"}), 400
        price = size_data['price']
        discount = size_data['discount'] or 0
        discounted_price = price * (1 - discount / 100)
        cart_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO cart (cart_id, customer_id, product_id, size_id, quantity)
            VALUES (?, ?, ?, ?, ?)
        ''', (cart_id, customer_id, product_id, size_id, quantity))
        conn.commit()
        conn.close()
        logger.debug(f"Thêm vào giỏ hàng: cart_id={cart_id}, customer_id={customer_id}, discounted_price={discounted_price}")
        return jsonify({
            "message": "Đã thêm vào giỏ hàng",
            "cart_id": cart_id,
            "discounted_price": discounted_price
        }), 200
    except Exception as e:
        logger.error(f"Lỗi khi thêm vào giỏ hàng: {str(e)}")
        return jsonify({"error": str(e)}), 500

# API cập nhật số lượng trong giỏ hàng
@app.route('/api/cart/update', methods=['POST'])
def update_cart_item():
    if 'customer_id' not in session:
        return jsonify({'error': 'Vui lòng đăng nhập'}), 401
    try:
        data = request.json
        cart_id = data.get('cart_id')
        quantity = data.get('quantity')
        if not cart_id or not quantity:
            logger.error(f"Thiếu cart_id hoặc quantity: {data}")
            return jsonify({"error": "Thiếu cart_id hoặc quantity"}), 400
        if not isinstance(quantity, int) or quantity < 1:
            logger.error(f"Số lượng không hợp lệ: {quantity}")
            return jsonify({"error": "Số lượng phải là số nguyên dương"}), 400
        customer_id = session['customer_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE cart 
            SET quantity = ? 
            WHERE cart_id = ? AND customer_id = ?
        ''', (quantity, cart_id, customer_id))
        if cursor.rowcount == 0:
            conn.close()
            logger.error(f"Không tìm thấy mục trong giỏ hàng: cart_id={cart_id}")
            return jsonify({"error": "Không tìm thấy mục trong giỏ hàng"}), 404
        conn.commit()
        conn.close()
        logger.debug(f"Cập nhật giỏ hàng: cart_id={cart_id}, quantity={quantity}")
        return jsonify({"message": "Cập nhật giỏ hàng thành công"}), 200
    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu khi cập nhật giỏ hàng: {str(e)}")
        return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Lỗi khi cập nhật giỏ hàng: {str(e)}")
        return jsonify({"error": str(e)}), 500

# API xóa khỏi giỏ hàng
@app.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    if 'customer_id' not in session:
        return jsonify({'error': 'Vui lòng đăng nhập'}), 401
    try:
        customer_id = session['customer_id']
        data = request.json
        cart_id = data.get('cart_id')
        if not cart_id:
            logger.error("Thiếu cart_id trong yêu cầu")
            return jsonify({"error": "Thiếu cart_id"}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart WHERE cart_id = ? AND customer_id = ?', (cart_id, customer_id))
        if cursor.rowcount == 0:
            conn.close()
            logger.error(f"Sản phẩm không tồn tại trong giỏ hàng: cart_id={cart_id}")
            return jsonify({"error": "Sản phẩm không tồn tại trong giỏ hàng"}), 404
        conn.commit()
        conn.close()
        logger.debug(f"Xóa sản phẩm khỏi giỏ hàng: cart_id={cart_id}")
        return jsonify({"message": "Đã xóa sản phẩm khỏi giỏ hàng"}), 200
    except Exception as e:
        logger.error(f"Lỗi khi xóa sản phẩm khỏi giỏ hàng: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/products')
def products_user():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT product_id, product_name, stock, description, image_url, image_url_2, discount, category
            FROM products
        """)
        products = [dict(row) for row in cursor.fetchall()]
        customer_id = session.get('customer_id')
        user = None
        if customer_id:
            cursor.execute('SELECT first_name, last_name FROM users WHERE customer_id = ?', (customer_id,))
            user = cursor.fetchone()
        conn.close()
        return render_template(
            'Products/products.html',
            products=products,
            user=user or {'first_name': 'Guest', 'last_name': ''}
        )
    except sqlite3.Error as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/card-confirm', methods=["POST"])
def confirm_card():
    if 'customer_id' not in session:
        return jsonify({'error': 'Vui lòng đăng nhập'}), 401
    data = request.json
    session["card-info"] = data
    return jsonify({"status": "OK"})


# API xác nhận lịch
@app.route('/api/calendar-confirm', methods=["POST"])
def confirm_calendar():
    if 'customer_id' not in session:
        return jsonify({'error': 'Vui lòng đăng nhập'}), 401
    data = request.json
    session['calendar-info'] = data
    return jsonify({"status": "OK"})


# API tạo đơn hàng
@app.route('/api/create-order', methods=["POST"])
def create_user_order():
    if 'customer_id' not in session:
        return jsonify({'error': 'Vui lòng đăng nhập'}), 401
    try:
        data = request.json
        note = data.get('note', '')
        items = data.get('items', [])
        card_info = session.get('card-info', {'payment_method': data.get('paymentMethod', 'cod')})
        calendar_info = session.get('calendar-info', {})
        customer_id = session['customer_id']
        if not items:
            logger.error(f"Order creation failed: Empty cart for customer_id={customer_id}")
            return jsonify({"error": "Giỏ hàng trống"}), 400
        if not card_info:
            logger.error(f"Order creation failed: Missing card info for customer_id={customer_id}")
            return jsonify({"error": "Thiếu thông tin thẻ thanh toán"}), 400
        if not calendar_info:
            logger.error(f"Order creation failed: Missing calendar info for customer_id={customer_id}")
            return jsonify({"error": "Thiếu thông tin lịch giao hàng"}), 400
        logger.debug(f"Nội dung đơn hàng: {items}")
        order_date = datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%Y-%m-%d %H:%M:%S')
        conn = get_db_connection()
        cursor = conn.cursor()
        # Use default store_id (ST1 from schema.sql)
        default_store_id = 'ST1'
        cursor.execute('SELECT store_id FROM stores WHERE store_id = ?', (default_store_id,))
        if not cursor.fetchone():
            logger.error(f"Default store_id {default_store_id} does not exist")
            raise ValueError(f"Cửa hàng mặc định {default_store_id} không tồn tại")
        cursor.execute('''
            INSERT INTO orders (order_id, customer_id, order_date, status, store_id) 
            VALUES (NULL, ?, ?, ?, ?)
        ''', (customer_id, order_date, 'Pending', default_store_id))
        cursor.execute("SELECT order_id FROM orders WHERE rowid = last_insert_rowid()")
        order_id = cursor.fetchone()['order_id']
        total_amount = 0
        for item in items:
            order_detail_id = str(uuid.uuid4())
            cart_id = item.get('cart_id')
            quantity = item.get('quantity', 1)
            price = item.get('price')
            cursor.execute('''
                SELECT product_id, size_id 
                FROM cart 
                WHERE cart_id = ? AND customer_id = ?
            ''', (cart_id, customer_id))
            cart_item = cursor.fetchone()
            if not cart_item:
                logger.error(f"Mục giỏ hàng không tồn tại: cart_id={cart_id}, customer_id={customer_id}")
                raise ValueError(f"Mục giỏ hàng không tồn tại: cart_id={cart_id}")
            product_id, size_id = cart_item
            cursor.execute('''
                SELECT price, discount 
                FROM products p 
                JOIN product_size ps ON p.product_id = ps.product_id 
                WHERE p.product_id = ? AND ps.size_id = ?
            ''', (product_id, size_id))
            product = cursor.fetchone()
            if not product:
                logger.error(f"Sản phẩm hoặc kích cỡ không tồn tại: product_id={product_id}, size_id={size_id}")
                raise ValueError(f"Sản phẩm hoặc kích cỡ không tồn tại")
            original_price = float(product['price'])
            discount = float(product['discount'] or 0)
            unit_price = price if price else original_price * (1 - discount / 100)
            total_price = unit_price * quantity
            total_amount += total_price
            cursor.execute('''
                INSERT INTO order_details (order_detail_id, order_id, product_id, size_id, quantity, unit_price, total_price) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (order_detail_id, order_id, product_id, size_id, quantity, unit_price, total_price))
        payment_id = str(uuid.uuid4())
        payment_method = card_info.get('payment_method', 'cod')
        cursor.execute('''
            INSERT INTO payments (payment_id, payment_date, payment_method, order_id, amount) 
            VALUES (?, ?, ?, ?, ?)
        ''', (payment_id, order_date, payment_method, order_id, total_amount))
        for item in items:
            cursor.execute('DELETE FROM cart WHERE cart_id = ? AND customer_id = ?', (item['cart_id'], customer_id))
        conn.commit()
        # Verify order was saved
        cursor.execute('SELECT order_id FROM orders WHERE order_id = ?', (order_id,))
        if not cursor.fetchone():
            logger.error(f"Order verification failed: order_id={order_id} not found after commit")
            raise ValueError(f"Order {order_id} not found after creation")
        session.pop('cart', None)
        session.pop('card-info', None)
        session.pop('calendar-info', None)
        logger.info(f"Tạo đơn hàng thành công: order_id={order_id}, customer_id={customer_id}, total_amount={total_amount}")
        return jsonify({
            "message": "Tạo đơn hàng thành công",
            "order_id": order_id,
            "total_amount": total_amount
        }), 200
    except sqlite3.Error as e:
        logger.error(f"Lỗi cơ sở dữ liệu khi tạo đơn hàng: {str(e)}, customer_id={customer_id}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
    except ValueError as e:
        logger.error(f"Lỗi dữ liệu khi tạo đơn hàng: {str(e)}, customer_id={customer_id}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Lỗi không xác định khi tạo đơn hàng: {str(e)}, customer_id={customer_id}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()


@app.route('/acc/myACC/my_account.html')
def my_account():
    if 'customer_id' not in session:
        flash("Vui lòng đăng nhập", "error")
        return redirect(url_for('login'))
    try:
        return render_template('acc/myACC/my_account.html')
    except Exception as e:
        logger.error(f"Lỗi khi hiển thị my_account.html: {str(e)}")
        return jsonify({"error": "Không tìm thấy trang"}), 404


@app.route('/acc/myACC/my_wallet.html')
def my_wallet():
    if 'customer_id' not in session:
        flash("Vui lòng đăng nhập", "error")
        return redirect(url_for('login'))
    try:
        return render_template('acc/myACC/my_wallet.html')
    except Exception as e:
        logger.error(f"Lỗi khi hiển thị my_wallet.html: {str(e)}")
        return jsonify({"error": "Không tìm thấy trang"}), 404

@app.route('/acc/myACC/my_order.html')
def my_order():
    if 'customer_id' not in session:
        flash("Vui lòng đăng nhập", "error")
        return redirect(url_for('login'))
    try:
        return render_template('acc/myACC/my_order.html')
    except Exception as e:
        logger.error(f"Lỗi khi hiển thị my_order.html: {str(e)}")
        return jsonify({"error": "Không tìm thấy trang"}), 404


@app.route('/acc/myACC/my_address.html')
def my_address():
    if 'customer_id' not in session:
        flash("Vui lòng đăng nhập", "error")
        return redirect(url_for('login'))
    try:
        return render_template('acc/myACC/my_address.html')
    except Exception as e:
        logger.error(f"Lỗi khi hiển thị my_address.html: {str(e)}")
        return jsonify({"error": "Không tìm thấy trang"}), 404


@app.route('/acc/myACC/review.html')
def review():
    if 'customer_id' not in session:
        flash("Vui lòng đăng nhập", "error")
        return redirect(url_for('login'))
    try:
        return render_template('acc/myACC/review.html')
    except Exception as e:
        logger.error(f"Lỗi khi hiển thị review.html: {str(e)}")
        return jsonify({"error": "Không tìm thấy trang"}), 404


@app.route('/api/user', methods=['GET'])
def get_user():
    try:
        if 'customer_id' not in session:
            return jsonify({"error": "Vui lòng đăng nhập để xem thông tin người dùng"}), 401
        customer_id = session['customer_id']
        conn = get_db_connection()
        user = conn.execute('SELECT customer_id, first_name, last_name, email, phone, birthdate, user_add, user_img FROM users WHERE customer_id = ?', (customer_id,)).fetchone()
        conn.close()
        if not user:
            return jsonify({"error": "Không tìm thấy người dùng"}), 404
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
        if not ext in valid_extensions:
            return jsonify({"error": "Loại tệp không hợp lệ. Chỉ cho phép PNG và JPEG"}), 400

        # Sử dụng thư mục templates/Uploads/<customer_id> thay vì static
        upload_folder = os.path.join('templates', 'Uploads', customer_id)
        os.makedirs(upload_folder, exist_ok=True)

        filename = f"profile_{customer_id}_{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)

        # URL ảnh sẽ sử dụng /assets/ để phù hợp với route serve_assets
        image_url = f"/assets/Uploads/{customer_id}/{filename}"

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
            try:
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
                query += ' AND DATE(o.order_date) BETWEEN ? AND ?'
                params.extend([start_date, end_date])
            except ValueError:
                logger.warning(f"Invalid date format: start_date={start_date}, end_date={end_date}")
                return jsonify({"error": "Định dạng ngày không hợp lệ, phải là YYYY-MM-DD"}), 400
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

 

# API gửi đánh giá
@app.route('/api/reviews', methods=['POST'])
def submit_review():
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

        # Kiểm tra các trường bắt buộc
        if not product_id or not rating or not comment or not order_id or not size_id:
            logger.error(f"Thiếu thông tin bắt buộc: product_id={product_id}, rating={rating}, comment={comment}, order_id={order_id}, size_id={size_id}")
            return jsonify({"error": "Thiếu thông tin bắt buộc (product_id, rating, comment, order_id, size_id)"}), 400
        
        # Kiểm tra rating
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

        # Kiểm tra customer_id
        cursor.execute('SELECT customer_id FROM users WHERE customer_id = ?', (customer_id,))
        if not cursor.fetchone():
            logger.error(f"Customer không tồn tại: customer_id={customer_id}")
            conn.close()
            return jsonify({"error": "Khách hàng không tồn tại"}), 400

        # Kiểm tra product_id
        cursor.execute('SELECT product_id FROM products WHERE product_id = ?', (product_id,))
        if not cursor.fetchone():
            logger.error(f"Product không tồn tại: product_id={product_id}")
            conn.close()
            return jsonify({"error": "Sản phẩm không tồn tại"}), 400

        # Kiểm tra size_id và liên kết với product_id
        cursor.execute('SELECT size_id FROM product_size WHERE size_id = ? AND product_id = ?', (size_id, product_id))
        if not cursor.fetchone():
            logger.error(f"Size không tồn tại hoặc không liên kết với sản phẩm: size_id={size_id}, product_id={product_id}")
            conn.close()
            return jsonify({"error": "Kích thước không hợp lệ hoặc không liên kết với sản phẩm"}), 400

        # Kiểm tra order_id và liên kết với customer_id
        cursor.execute('SELECT order_id FROM orders WHERE order_id = ? AND customer_id = ?', (order_id, customer_id))
        if not cursor.fetchone():
            logger.error(f"Order không tồn tại hoặc không thuộc về khách hàng: order_id={order_id}, customer_id={customer_id}")
            conn.close()
            return jsonify({"error": "Đơn hàng không tồn tại hoặc không thuộc về bạn"}), 400

        # Kiểm tra xem đánh giá đã tồn tại chưa
        cursor.execute('''
            SELECT review_id 
            FROM reviews 
            WHERE customer_id = ? AND product_id = ? AND size_id = ? AND order_id = ?
        ''', (customer_id, product_id, size_id, order_id))
        if cursor.fetchone():
            logger.error(f"Đánh giá đã tồn tại: customer_id={customer_id}, product_id={product_id}, size_id={size_id}, order_id={order_id}")
            conn.close()
            return jsonify({"error": "Bạn đã đánh giá sản phẩm này cho đơn hàng này rồi"}), 400

        # Kiểm tra đơn hàng đã giao (Delivered)
        cursor.execute('SELECT status FROM orders WHERE order_id = ?', (order_id,))
        order_status = cursor.fetchone()
        if order_status['status'].lower() != 'delivered':
            logger.error(f"Đơn hàng chưa được giao: order_id={order_id}, status={order_status['status']}")
            conn.close()
            return jsonify({"error": "Chỉ có thể đánh giá đơn hàng đã được giao"}), 400

        # Xử lý ảnh đánh giá
        review_image_url = None
        if review_image:
            valid_extensions = {'.png', '.jpg', '.jpeg'}
            ext = os.path.splitext(review_image.filename)[1].lower()
            if ext not in valid_extensions:
                logger.error(f"Loại tệp ảnh không hợp lệ: extension={ext}")
                conn.close()
                return jsonify({"error": "Loại tệp không hợp lệ. Chỉ cho phép PNG và JPEG"}), 400

            upload_folder = os.path.join(app.static_folder, 'reviews_upload')
            os.makedirs(upload_folder, exist_ok=True)
            filename = f"review_{customer_id}_{uuid.uuid4().hex}{ext}"
            file_path = os.path.join(upload_folder, filename)
            review_image.save(file_path)
            review_image_url = f"/reviews_upload/{filename}"

        # Chèn đánh giá
        review_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO reviews (customer_id, product_id, size_id, order_id, rating, comment, review_date, review_img)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (customer_id, product_id, size_id, order_id, rating, comment, review_date, review_image_url))
        conn.commit()

        # Lấy review_id vừa tạo
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

# API kiểm tra đánh giá
@app.route('/api/reviews', methods=['GET'])
def check_review():
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

# API lấy đánh giá theo sản phẩm
@app.route('/api/reviews/product/<product_id>', methods=['GET'])
def get_reviews_by_product(product_id):
    try:
        conn = get_db_connection()
        reviews = conn.execute('''
            SELECT r.review_id, r.customer_id, r.rating, r.comment, r.review_date, r.review_img, u.first_name, u.last_name
            FROM reviews r
            JOIN users u ON r.customer_id = u.customer_id
            WHERE r.product_id = ?
        ''', (product_id,)).fetchall()
        conn.close()
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


@app.route('/success')
def success():
    if 'customer_id' not in session:
        flash("Vui lòng đăng nhập", "error")
        return redirect(url_for('login'))
    return render_template('success.html', first_name=session.get('first_name', 'Guest'))

# Route để render trang quản lý user
@app.route('/user_management')
def user_management():
    if 'admin_id' not in session:
        flash("Vui lòng đăng nhập với tư cách admin", "error")
        return redirect(url_for('login'))
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        admin_id = session['admin_id']
        cursor.execute('SELECT first_name, last_name, admin_img FROM admins WHERE admin_id = ?', (admin_id,))
        admin = cursor.fetchone()
        if not admin:
            flash("Tài khoản admin không tồn tại", "error")
            session.pop('admin_id', None)
            conn.close()
            return redirect(url_for('login'))

        # Lấy danh sách users
        cursor.execute("""
            SELECT customer_id AS user_id, first_name, last_name, email, 'User' AS role
            FROM users
        """)
        users = [dict(row) for row in cursor.fetchall()]

        # Lấy danh sách admins
        cursor.execute("""
            SELECT admin_id AS user_id, first_name, last_name, email, 'Admin' AS role
            FROM admins
        """)
        users.extend([dict(row) for row in cursor.fetchall()])

        conn.close()

        return render_template(
            'admin_dashboard/dashboard/user_management.html',
            users=users,
            admin=dict(admin)
        )
    except sqlite3.Error as e:
        if conn:
            conn.close()
        flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        flash(f"Lỗi: {str(e)}", "error")
        return jsonify({'success': False, 'message': str(e)}), 500

# Route để thêm user
@app.route('/users/add', methods=['POST'])
def add_user():
    conn = None
    try:
        data = request.get_json()
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')

        if not all([first_name, last_name, email, password, role]):
            return jsonify({'success': False, 'message': 'Thiếu thông tin bắt buộc'}), 400

        if role not in ['User', 'Admin']:
            return jsonify({'success': False, 'message': 'Vai trò không hợp lệ'}), 400

        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Mật khẩu phải có ít nhất 6 ký tự'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Kiểm tra email trùng lặp
        cursor.execute('SELECT email FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Email đã tồn tại trong bảng users'}), 400
        cursor.execute('SELECT email FROM admins WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Email đã tồn tại trong bảng admins'}), 400

        if role == 'User':
            cursor.execute("""
                INSERT INTO users (customer_id, first_name, last_name, email, password)
                VALUES (NULL, ?, ?, ?, ?)
            """, (first_name, last_name, email, password))
        else:
            cursor.execute("""
                INSERT INTO admins (admin_id, first_name, last_name, email, password)
                VALUES (NULL, ?, ?, ?, ?)
            """, (first_name, last_name, email, password))

        conn.commit()

        # Lấy thông tin user vừa thêm
        if role == 'User':
            cursor.execute("SELECT customer_id FROM users WHERE rowid = last_insert_rowid()")
            user_id = cursor.fetchone()['customer_id']
            cursor.execute("""
                SELECT customer_id AS user_id, first_name, last_name, email, 'User' AS role
                FROM users
                WHERE customer_id = ?
            """, (user_id,))
        else:
            cursor.execute("SELECT admin_id FROM admins WHERE rowid = last_insert_rowid()")
            user_id = cursor.fetchone()['admin_id']
            cursor.execute("""
                SELECT admin_id AS user_id, first_name, last_name, email, 'Admin' AS role
                FROM admins
                WHERE admin_id = ?
            """, (user_id,))
        user = cursor.fetchone()

        conn.close()

        return jsonify({
            'success': True,
            'user': dict(user)
        })
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

# Route để sửa user
@app.route('/users/edit/<user_id>', methods=['POST'])
def edit_user(user_id):
    conn = None
    try:
        data = request.get_json()
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        email = data.get('email')
        role = data.get('role')

        if not all([first_name, last_name, email, role]):
            return jsonify({'success': False, 'message': 'Thiếu thông tin bắt buộc'}), 400

        if role not in ['User', 'Admin']:
            return jsonify({'success': False, 'message': 'Vai trò không hợp lệ'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Kiểm tra user_id tồn tại và xác định bảng
        is_admin = False
        cursor.execute('SELECT admin_id, password FROM admins WHERE admin_id = ?', (user_id,))
        admin = cursor.fetchone()
        if admin:
            is_admin = True
        else:
            cursor.execute('SELECT customer_id, password FROM users WHERE customer_id = ?', (user_id,))
            user = cursor.fetchone()
            if not user:
                conn.close()
                return jsonify({'success': False, 'message': 'Tài khoản không tồn tại'}), 400

        # Kiểm tra email trùng lặp
        cursor.execute('SELECT customer_id FROM users WHERE email = ? AND customer_id != ?', (email, user_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Email đã tồn tại trong bảng users'}), 400
        cursor.execute('SELECT admin_id FROM admins WHERE email = ? AND admin_id != ?', (email, user_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Email đã tồn tại trong bảng admins'}), 400

        # Cập nhật thông tin
        if is_admin and role == 'Admin':
            cursor.execute("""
                UPDATE admins
                SET first_name = ?, last_name = ?, email = ?
                WHERE admin_id = ?
            """, (first_name, last_name, email, user_id))
        elif is_admin and role == 'User':
            # Chuyển từ admin sang user
            cursor.execute('DELETE FROM admins WHERE admin_id = ?', (user_id,))
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
        else:
            # Chuyển từ user sang admin
            cursor.execute('DELETE FROM users WHERE customer_id = ?', (user_id,))
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

        conn.close()

        return jsonify({
            'success': True,
            'user': dict(user)
        })
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

# Route để xóa user
@app.route('/users/delete/<user_id>', methods=['POST'])
def delete_user(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Kiểm tra user_id tồn tại và xác định bảng
        is_admin = False
        cursor.execute('SELECT admin_id FROM admins WHERE admin_id = ?', (user_id,))
        if cursor.fetchone():
            is_admin = True
        else:
            cursor.execute('SELECT customer_id FROM users WHERE customer_id = ?', (user_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Tài khoản không tồn tại'}), 400

        # Kiểm tra ràng buộc khóa ngoại
        if not is_admin:
            cursor.execute('SELECT order_id FROM orders WHERE customer_id = ?', (user_id,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Không thể xóa user vì đã có đơn hàng'}), 400
            cursor.execute('SELECT review_id FROM reviews WHERE customer_id = ?', (user_id,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Không thể xóa user vì đã có đánh giá'}), 400
            cursor.execute('SELECT message_id FROM messages WHERE user_id = ?', (user_id,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Không thể xóa user vì đã có tin nhắn'}), 400
            cursor.execute('SELECT address_id FROM addresses WHERE customer_id = ?', (user_id,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Không thể xóa user vì đã có địa chỉ'}), 400
            cursor.execute('SELECT cart_id FROM cart WHERE customer_id = ?', (user_id,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Không thể xóa user vì đã có giỏ hàng'}), 400
        else:
            cursor.execute('SELECT favorite_id FROM favorites WHERE admin_id = ?', (user_id,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Không thể xóa admin vì đã có sản phẩm yêu thích'}), 400
            cursor.execute('SELECT message_id FROM messages WHERE admin_id = ?', (user_id,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Không thể xóa admin vì đã có tin nhắn'}), 400
            cursor.execute('SELECT event_id FROM events WHERE admin_id = ?', (user_id,))
            if cursor.fetchone():
                conn.close()
                return jsonify({'success': False, 'message': 'Không thể xóa admin vì đã có sự kiện'}), 400

        # Xóa tài khoản
        if is_admin:
            cursor.execute('DELETE FROM admins WHERE admin_id = ?', (user_id,))
        else:
            cursor.execute('DELETE FROM users WHERE customer_id = ?', (user_id,))

        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
    except Exception as e:
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

# top 10 products
@app.route('/api/top10products', methods=['GET'])
def get_top10_products():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                p.product_id, 
                p.product_name, 
                p.stock, 
                p.description, 
                p.image_url, 
                p.image_url_2, 
                p.discount, 
                p.category,
                SUM(od.quantity) as total_sold
            FROM products p
            JOIN order_details od ON p.product_id = od.product_id
            JOIN orders o ON od.order_id = o.order_id
            WHERE o.status = 'Delivered'
            GROUP BY p.product_id
            ORDER BY total_sold DESC
            LIMIT 10
        ''')
        top_products = [dict(row) for row in cursor.fetchall()]

        # Lấy kích thước cho từng sản phẩm
        products_list = []
        for product in top_products:
            cursor.execute('''
                SELECT size_id, size, price
                FROM product_size
                WHERE product_id = ?
            ''', (product['product_id'],))
            sizes = [{'size_id': row['size_id'], 'size': row['size'], 'price': row['price']} for row in cursor.fetchall()]
            product_dict = {
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'stock': product['stock'],
                'description': product['description'],
                'image_url': product['image_url'],
                'image_url_2': product['image_url_2'],
                'discount': product['discount'] or 0,
                'category': product['category'],
                'sizes': sizes
            }
            products_list.append(product_dict)

        conn.close()
        logger.debug(f"Trả về {len(products_list)} sản phẩm bán chạy nhất")
        return jsonify(products_list), 200
    except sqlite3.Error as e:
        if conn:
            conn.close()
        logger.error(f"Lỗi cơ sở dữ liệu khi lấy top 10 sản phẩm: {str(e)}")
        return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
    except Exception as e:
        if conn:
            conn.close()
        logger.error(f"Lỗi khi lấy top 10 sản phẩm: {str(e)}")
        return jsonify({"error": str(e)}), 500
if __name__ == '__main__':
    app.run(debug=True, port=5000)