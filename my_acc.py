# app.py
from flask import Flask, render_template, redirect, url_for, jsonify, request, session, send_from_directory, flash
from flask_cors import CORS
import os
import logging
from controllers.auth_controller import AuthController
from controllers.signup_controller import SignupController
from controllers.forgot_password_controller import ForgotPasswordController
from controllers.product_controller import ProductController
from controllers.cart_controller import CartController
from controllers.checkout_controller import CheckoutController
from controllers.order_controller import OrderController
from controllers.review_controller import ReviewController
from controllers.account_controller import AccountController
from controllers.admin_controller import AdminController
from forms.signup_form import SignupForm
from forms.forgot_password_form import ForgotPasswordForm
# Additional imports for new functionality
from controllers.review_controller import ReviewController



app = Flask(__name__, template_folder='views/templates', static_folder='views/static')
CORS(app, supports_credentials=True, origins=['*'])
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app.secret_key = os.urandom(24).hex()
app.config['SECRET_KEY'] = app.secret_key

# Configure upload folder
UPLOAD_FOLDER = 'views/static/Upload'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize controllers
auth_controller = AuthController()
signup_controller = SignupController()
forgot_password_controller = ForgotPasswordController()
product_controller = ProductController()
cart_controller = CartController()
checkout_controller = CheckoutController()
order_controller = OrderController()
review_controller = ReviewController()
account_controller = AccountController()
admin_controller = AdminController()
# Re-initialize review_controller to ensure new methods are available
review_controller = ReviewController()

# Jinja filter for currency formatting
def format_currency(value):
    if value is None or not isinstance(value, (int, float)):
        return "N/A"
    return "{:,.0f}".format(value).replace(',', '.')

app.jinja_env.filters['format_currency'] = format_currency
# Existing imports and code remain unchanged...


# New review routes
@app.route('/api/reviews', methods=['POST'])
def submit_review():
    return review_controller.submit_review()

@app.route('/api/reviews', methods=['GET'])
def check_review():
    return review_controller.check_review()
# Routes
@app.route('/')
def index():
    return auth_controller.index()

@app.route('/dashboard')
def dashboard():
    return admin_controller.dashboard()

@app.route('/login', methods=['GET', 'POST'])
def login():
    return auth_controller.login()

@app.route('/logout')
def logout():
    return auth_controller.logout()

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return signup_controller.signup(SignupForm())

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    return forgot_password_controller.forgot_password(ForgotPasswordForm())

@app.route('/products')
def products_user():
    return product_controller.products_user()

@app.route('/admin/products')
def admin_products():
    return product_controller.admin_products()

@app.route('/api/products', methods=['GET'])
def get_products():
    return product_controller.get_products()

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product_by_id(product_id):
    return product_controller.get_product_by_id(product_id)

@app.route('/api/top10products', methods=['GET'])
def get_top10_products():
    return product_controller.get_top10_products()

@app.route('/api/reviews/product/<product_id>', methods=['GET'])
def get_reviews_by_product(product_id):
    return review_controller.get_reviews_by_product(product_id)

@app.route('/api/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'GET':
        return cart_controller.get_cart()
    return cart_controller.add_to_cart()

@app.route('/api/cart/update', methods=['POST'])
def update_cart_item():
    return cart_controller.update_cart_item()

@app.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    return cart_controller.remove_from_cart()

@app.route('/checkout')
def checkout():
    return checkout_controller.checkout()

@app.route('/api/checkout', methods=['GET', 'POST'])
def checkout_api():
    if request.method == 'GET':
        return checkout_controller.get_checkout()
    return checkout_controller.add_checkout()

@app.route('/api/create-order', methods=['POST'])
def create_user_order():
    return order_controller.create_user_order()

@app.route('/api/card-confirm', methods=['POST'])
def confirm_card():
    return order_controller.confirm_card()

@app.route('/api/calendar-confirm', methods=['POST'])
def confirm_calendar():
    return order_controller.confirm_calendar()

@app.route('/acc/myACC/my_account.html')
def my_account():
    return account_controller.my_account()

@app.route('/<path:filename>')
def serve_static(filename):
    logger.debug(f"Yêu cầu tệp tĩnh: {filename}")
    try:
        if filename.endswith('.html'):
            logger.warning(f"Yêu cầu file HTML không hợp lệ: {filename}")
            return jsonify({"error": f"Yêu cầu không hợp lệ: {filename}"}), 404
        if filename.startswith('templates/'):
            filename = filename[len('templates/'):]
        return send_from_directory('views/templates', filename)
    except Exception as e:
        logger.error(f"Lỗi khi phục vụ tệp tĩnh {filename}: {str(e)}")
        return jsonify({"error": f"Không tìm thấy tệp: {filename}"}), 404

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    try:
        return send_from_directory('views/templates', filename)
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

if __name__ == '__main__':
    app.run(debug=True)
    
# account_controller.py
from flask import render_template, redirect, url_for, jsonify, session, flash
import logging

logger = logging.getLogger(__name__)

class AccountController:
    def my_account(self):
        if 'customer_id' not in session:
            flash("Vui lòng đăng nhập", "error")
            return redirect(url_for('login'))
        try:
            return render_template('acc/myACC/my_account.html')
        except Exception as e:
            logger.error(f"Lỗi khi hiển thị my_account.html: {str(e)}")
            return jsonify({"error": "Không tìm thấy trang"}), 404
    
    def my_wallet():
        if 'customer_id' not in session:
            flash("Vui lòng đăng nhập", "error")
            return redirect(url_for('login'))
        try:
            return render_template('acc/myACC/my_wallet.html')
        except Exception as e:
            logger.error(f"Lỗi khi hiển thị my_wallet.html: {str(e)}")
            return jsonify({"error": "Không tìm thấy trang"}), 404

    
    def my_order():
        if 'customer_id' not in session:
            flash("Vui lòng đăng nhập", "error")
            return redirect(url_for('login'))
        try:
            return render_template('acc/myACC/my_order.html')
        except Exception as e:
            logger.error(f"Lỗi khi hiển thị my_order.html: {str(e)}")
            return jsonify({"error": "Không tìm thấy trang"}), 404


    
    def my_address():
        if 'customer_id' not in session:
            flash("Vui lòng đăng nhập", "error")
            return redirect(url_for('login'))
        try:
            return render_template('acc/myACC/my_address.html')
        except Exception as e:
            logger.error(f"Lỗi khi hiển thị my_address.html: {str(e)}")
            return jsonify({"error": "Không tìm thấy trang"}), 404


    
    def review():
        if 'customer_id' not in session:
            flash("Vui lòng đăng nhập", "error")
            return redirect(url_for('login'))
        try:
            return render_template('acc/myACC/review.html')
        except Exception as e:
            logger.error(f"Lỗi khi hiển thị review.html: {str(e)}")
            return jsonify({"error": "Không tìm thấy trang"}), 404
        
# auth_controller.py
from flask import render_template, redirect, url_for, session, flash, request
from models.auth_model import AuthModel
import logging

logger = logging.getLogger(__name__)

class AuthController:
    def index(self):
        if session.get('is_admin', False) and 'admin_id' in session:
            return redirect(url_for('dashboard'))
        return render_template('index.html')

    def login(self):
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            logger.debug(f"Login attempt: email={email}")
            if not email or not password:
                flash("Please fill in both email and password", "error")
                return render_template('signup/login.html', error="Please fill in both email and password")

            if email.startswith('admin/'):
                admin_email = email[6:]
                logger.debug(f"Admin login attempt: email={admin_email}")
                admin = AuthModel.get_admin_by_email(admin_email)
                if admin and admin['password'] == password:
                    session.clear()
                    session['admin_id'] = admin['admin_id']
                    session['first_name'] = admin['first_name']
                    session['is_admin'] = True
                    logger.info("Admin login successful")
                    return redirect(url_for('dashboard'))
                else:
                    flash("Invalid admin email or password", "error")
                    logger.warning("Admin login failed")
                    return render_template('signup/login.html', error="Invalid admin email or password")
            else:
                user = AuthModel.get_user_by_email(email)
                if user and user['password'] == password:
                    session.clear()
                    session['customer_id'] = user['customer_id']
                    session['first_name'] = user['first_name']
                    session['is_admin'] = False
                    logger.info("User login successful")
                    return redirect(url_for('index'))
                else:
                    flash("Invalid email or password", "error")
                    logger.warning("User login failed")
                    return render_template('signup/login.html', error="Invalid email or password")

        logger.debug("Displaying login.html")
        return render_template('signup/login.html')

    def logout(self):
        session.clear()
        flash("Đăng xuất thành công", "success")
        return redirect(url_for('login'))
    
# user_controller.py
from flask import render_template, redirect, url_for, jsonify, request, session, flash
from models.user import User
from models.product import Product
from forms.signup_form import SignupForm
from forms.forgot_password_form import ForgotPasswordForm
import logging

from flask import jsonify, session, request
import sqlite3
from utils.db import get_db_connection
import logging
import os
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

def register_user_routes(app):
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        try:
            if request.method == 'POST':
                email = request.form['email']
                password = request.form['password']
                logger.debug(f"Login attempt: email={email}")
                if not email or not password:
                    flash("Vui lòng nhập cả email và mật khẩu", "error")
                    return render_template('signup/login.html', error="Vui lòng nhập cả email và mật khẩu")

                if email.startswith('admin/'):
                    admin_email = email[6:]
                    logger.debug(f"Admin login attempt: email={admin_email}")
                    admin = User.get_admin_by_email(admin_email)
                    if admin and admin['password'] == password:
                        session.clear()
                        session['admin_id'] = admin['admin_id']
                        session['first_name'] = admin['first_name']
                        session['is_admin'] = True
                        logger.info("Đăng nhập admin thành công")
                        return redirect(url_for('dashboard'))
                    else:
                        flash("Email hoặc mật khẩu admin không đúng", "error")
                        logger.warning("Đăng nhập admin thất bại")
                        return render_template('signup/login.html', error="Email hoặc mật khẩu admin không đúng")
                else:
                    user = User.get_user_by_email(email)
                    if user and user['password'] == password:
                        session.clear()
                        session['customer_id'] = user['customer_id']
                        session['first_name'] = user['first_name']
                        session['is_admin'] = False
                        logger.info("Đăng nhập người dùng thành công")
                        return redirect(url_for('index'))
                    else:
                        flash("Email hoặc mật khẩu không đúng", "error")
                        logger.warning("Đăng nhập người dùng thất bại")
                        return render_template('signup/login.html', error="Email hoặc mật khẩu không đúng")

            logger.debug("Hiển thị login.html")
            return render_template('signup/login.html')
        except Exception as e:
            logger.error(f"Lỗi không xác định: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return render_template('signup/login.html', error=str(e))

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        form = SignupForm()
        try:
            if form.validate_on_submit():
                first_name = form.first_name.data
                last_name = form.last_name.data
                email = form.email.data
                password = form.password.data
                phone = form.phone.data
                birthdate = form.birthdate.data
                customer_id = User.create_user(first_name, last_name, email, password, phone, birthdate)
                if customer_id:
                    session['customer_id'] = customer_id
                    session['first_name'] = first_name
                    session['is_admin'] = False
                    flash("Đăng ký thành công!", "success")
                    logger.info(f"Đăng ký thành công: email={email}")
                    return redirect(url_for('index'))
                else:
                    flash("Email đã tồn tại", "error")
                    logger.warning(f"Đăng ký thất bại: email={email} đã tồn tại")
                    return render_template('signup/signup.html', form=form, error="Email đã tồn tại")
            return render_template('signup/signup.html', form=form)
        except Exception as e:
            logger.error(f"Lỗi khi đăng ký: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return render_template('signup/signup.html', form=form, error=str(e))

    @app.route('/forgot_password', methods=['GET', 'POST'])
    def forgot_password():
        form = ForgotPasswordForm()
        try:
            if form.validate_on_submit():
                email = form.email.data
                user = User.get_user_by_email(email)
                if user:
                    # Giả lập gửi email đặt lại mật khẩu
                    logger.info(f"Yêu cầu đặt lại mật khẩu: email={email}")
                    flash("Link đặt lại mật khẩu đã được gửi đến email của bạn", "success")
                else:
                    flash("Email không tồn tại", "error")
                    logger.warning(f"Yêu cầu đặt lại mật khẩu thất bại: email={email} không tồn tại")
                return redirect(url_for('login'))
            return render_template('signup/forgot_password.html', form=form)
        except Exception as e:
            logger.error(f"Lỗi khi đặt lại mật khẩu: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return render_template('signup/forgot_password.html', form=form, error=str(e))

    @app.route('/logout')
    def logout():
        session.clear()
        flash("Đăng xuất thành công", "success")
        return redirect(url_for('login'))

    @app.route('/checkout')
    def checkout():
        if 'customer_id' not in session:
            flash("Vui lòng đăng nhập", "error")
            return redirect(url_for('login'))
        try:
            customer_id = session['customer_id']
            cart_items = Product.get_cart(customer_id)
            for item in cart_items:
                discount = item['discount'] or 0
                item['discounted_price'] = item['price'] * (1 - discount / 100)
            if not cart_items:
                flash("Giỏ hàng trống!", "error")
                return redirect(url_for('products_user'))
            return render_template('Checkout.html', cart=cart_items)
        except Exception as e:
            logger.error(f"Lỗi khi tải giỏ hàng: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return redirect(url_for('products_user'))

    @app.route('/api/checkout', methods=['POST'])
    def add_checkout():
        try:
            data = request.json
            session['cart'] = data
            return jsonify({"status": "OK"})
        except Exception as e:
            logger.error(f"Lỗi khi thêm checkout: {str(e)}")
            return jsonify({"error": str(e)}), 500

    @app.route('/api/checkout', methods=['GET'])
    def get_checkout():
        try:
            return jsonify(session.get('cart', []))
        except Exception as e:
            logger.error(f"Lỗi khi lấy checkout: {str(e)}")
            return jsonify({"error": str(e)}), 500

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

    @app.route('/')
    def index():
        if session.get('is_admin', False) and 'admin_id' in session:
            return redirect(url_for('dashboard'))
        return render_template('index.html')

    @app.route('/dashboard')
    def dashboard():
        if 'admin_id' not in session:
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        return render_template('admin_dashboard/dashboard/dashboard.html')


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
            upload_folder = os.path.join('templates', 'Uploads', customer_id)
            os.makedirs(upload_folder, exist_ok=True)
            filename = f"profile_{customer_id}_{uuid.uuid4().hex}{ext}"
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
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
        
# account_model.py
import sqlite3
from utils.db import get_db_connection

class AccountModel:
    @staticmethod
    def get_user_details(customer_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT first_name, last_name FROM users WHERE customer_id = ?', (customer_id,))
        user = cursor.fetchone()
        conn.close()
        return user

# auth_model.py
import sqlite3
from utils.db import get_db_connection

class AuthModel:
    @staticmethod
    def get_user_by_email(email):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT customer_id, first_name, password FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        return user

    @staticmethod
    def get_admin_by_email(email):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT admin_id, first_name, password FROM admins WHERE email = ?", (email,))
        admin = cursor.fetchone()
        conn.close()
        return admin
# user.py
import sqlite3
import uuid
from utils.db import get_db_connection

class User:
    @staticmethod
    def get_user_by_email(email):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT customer_id, first_name, password FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        return user

    @staticmethod
    def get_admin_by_email(email):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT admin_id, first_name, password FROM admins WHERE email = ?", (email,))
        admin = cursor.fetchone()
        conn.close()
        return admin

    @staticmethod
    def get_user_info(customer_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT first_name, last_name FROM users WHERE customer_id = ?', (customer_id,))
        user = cursor.fetchone()
        conn.close()
        return user

    @staticmethod
    def create_user(first_name, last_name, email, password, phone=None, birthdate=None):
        conn = get_db_connection()
        cursor = conn.cursor()
        customer_id = str(uuid.uuid4())
        try:
            cursor.execute('''
                INSERT INTO users (customer_id, first_name, last_name, email, password, phone, birthdate)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (customer_id, first_name, last_name, email, password, phone, birthdate))
            conn.commit()
            return customer_id
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    @staticmethod
    def get_user_details(customer_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT customer_id, first_name, last_name, email, phone, birthdate, user_add, user_img FROM users WHERE customer_id = ?', (customer_id,))
        user = cursor.fetchone()
        conn.close()
        return user

    @staticmethod
    def update_profile(customer_id, first_name, last_name, phone, birthdate):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET first_name = ?, last_name = ?, phone = ?, birthdate = ?
            WHERE customer_id = ?
        ''', (first_name, last_name, phone or None, birthdate or None, customer_id))
        conn.commit()
        conn.close()

    @staticmethod
    def change_password(customer_id, current_password, new_password):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE customer_id = ?', (customer_id,))
        user = cursor.fetchone()
        if not user or user['password'] != current_password:
            conn.close()
            return False
        cursor.execute('UPDATE users SET password = ? WHERE customer_id = ?', (new_password, customer_id))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def update_profile_image(customer_id, image_url):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET user_img = ? WHERE customer_id = ?', (image_url, customer_id))
        conn.commit()
        conn.close()