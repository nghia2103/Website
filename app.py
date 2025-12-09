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
from controllers.user_controller import register_user_routes
from controllers.dashboard_controller import DashboardController
from controllers.favorites_controller import FavoritesController
from controllers.inbox_controller import InboxController
from controllers.order_lists_controller import OrderListsController
from controllers.product_stock_controller import ProductStockController
from controllers.user_management_controller import UserManagementController
from controllers.productadmin_controller import ProductAdminController
from controllers.order_admin_controller import OrderAdminController
from controllers.pages_controller import PagesController
from controllers.inbox_user_controller import InboxUserController
from forms.signup_form import SignupForm
from forms.forgot_password_form import ForgotPasswordForm

app = Flask(__name__, template_folder='views/templates', static_folder='views/static')
CORS(app, supports_credentials=True, origins=['*'])
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Fixed secret key to avoid session issues
app.secret_key = 'fixed_secret_key_2025'
app.config['SECRET_KEY'] = app.secret_key

# Configure upload folder
UPLOAD_FOLDER = 'views/static/Upload'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'avif'}
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
dashboard_controller = DashboardController()
favorites_controller = FavoritesController()
inbox_controller = InboxController()
productadmin_controller = ProductAdminController()
product_stock_controller = ProductStockController()
order_lists_controller = OrderListsController()
user_management_controller = UserManagementController()
order_admin_controller = OrderAdminController()
pages_controller = PagesController()
inbox_user_controller = InboxUserController()


# Register user routes from user_controller
register_user_routes(app)

# Jinja filter for currency formatting
def format_currency(value):
    if value is None or not isinstance(value, (int, float)):
        return "N/A"
    return "{:,.0f}".format(value).replace(',', '.')

app.jinja_env.filters['format_currency'] = format_currency

# New review routes
@app.route('/api/reviews', methods=['POST'])
def submit_review():
    return review_controller.submit_review()

@app.route('/api/reviews', methods=['GET'])
def check_review():
    return review_controller.check_review()

# Endpoint to handle /get_customer_id
@app.route('/get_customer_id', methods=['GET'])
@app.route('/get_customer_id/', methods=['GET'])  # Handle trailing slash
def get_customer_id():
    logger.debug("Handling /get_customer_id request")
    try:
        if 'customer_id' in session:
            logger.debug(f"Returning customer_id: {session['customer_id']}")
            return jsonify({"customer_id": session['customer_id']}), 200
        else:
            logger.debug("No customer_id in session, user not logged in")
            return jsonify({"error": "Chưa đăng nhập"}), 401
    except Exception as e:
        logger.error(f"Lỗi khi lấy customer_id: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Other routes
@app.route('/')
def index():
    return auth_controller.index()


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

@app.route('/acc/myACC/my_wallet.html')
def my_wallet():
    return account_controller.my_wallet()

@app.route('/acc/myACC/my_order.html')
def my_order():
    return account_controller.my_order()

@app.route('/acc/myACC/my_address.html')
def my_address():
    return account_controller.my_address()

@app.route('/acc/myACC/review.html')
def review():
    return account_controller.review()


@app.route('/dashboard')
def dashboard():
    return dashboard_controller.get_dashboard()


@app.route('/favorites')
def favorites():
    logger.debug("Accessing favorites route")
    return favorites_controller.favorites()

@app.route('/favorite/add', methods=['POST'])
def add_favorite():
    logger.debug("Accessing add_favorite API")
    return favorites_controller.add_favorite()

@app.route('/favorite/remove', methods=['POST'])
def remove_favorite():
    logger.debug("Accessing remove_favorite API")
    return favorites_controller.remove_favorite()

@app.route('/inbox')
def inbox():
    logger.debug("Accessing inbox route")
    return inbox_controller.inbox()

@app.route('/get_threads')
def get_threads():
    logger.debug("Accessing get_threads API")
    return inbox_controller.get_threads()

@app.route('/get_messages/<user_id>')
def get_messages(user_id):
    logger.debug(f"Accessing get_messages API for user_id={user_id}")
    return inbox_controller.get_messages(user_id)

@app.route('/send_message', methods=['POST'])
def send_message():
    logger.debug("Accessing send_message API")
    return inbox_controller.send_message()

# @app.route('/api/user', methods=['GET'])
# def get_user():
#     return inbox_user_controller.get_user()

@app.route('/user_messages/<user_id>')
def user_messages(user_id):
    return inbox_user_controller.get_user_messages(user_id)


@app.route('/assign_admin', methods=['POST'])
def assign_admin():
    logger.debug("Accessing assign_admin API")
    return inbox_controller.assign_admin()

@app.route('/order_lists')
def order_lists():
    logger.debug("Accessing order_lists route")
    return order_lists_controller.order_lists()

@app.route('/stock/add', methods=['POST'])
def add_stock_item():
    logger.debug("Accessing add_stock_item API")
    return product_stock_controller.add_stock_item()

@app.route('/stock/edit/<item_id>', methods=['POST'])
def edit_stock_item(item_id):
    logger.debug(f"Accessing edit_stock_item API for item_id={item_id}")
    return product_stock_controller.edit_stock_item(item_id)

@app.route('/stock/delete/<item_id>', methods=['POST'])
def delete_stock_item(item_id):
    logger.debug(f"Accessing delete_stock_item API for item_id={item_id}")
    return product_stock_controller.delete_stock_item(item_id)


@app.route('/product_stock')
def product_stock():
    logger.debug("Accessing product_stock route")
    return product_stock_controller.product_stock()

@app.route('/user_management')
def user_management():
    logger.debug("Accessing user_management route")
    return user_management_controller.user_management()

@app.route('/users/add', methods=['POST'])
def add_user():
    logger.debug("Accessing add_user API")
    return user_management_controller.add_user()

@app.route('/users/edit/<user_id>', methods=['POST'])
def edit_user(user_id):
    logger.debug(f"Accessing edit_user API for user_id={user_id}")
    return user_management_controller.edit_user(user_id)

@app.route('/users/delete/<user_id>', methods=['POST'])
def delete_user(user_id):
    logger.debug(f"Accessing delete_user API for user_id={user_id}")
    return user_management_controller.delete_user(user_id)

# @app.route('/pricing')
# def pricing():
#     logger.debug("Accessing pricing route")
#     return pages_controller.pricing()

# @app.route('/calendar')
# def calendar():
#     logger.debug("Accessing calendar route")
#     return pages_controller.calendar()

# @app.route('/to_do_list')
# def to_do_list():
#     logger.debug("Accessing to_do_list route")
#     return pages_controller.to_do_list()

# @app.route('/contact')
# def contact():
#     logger.debug("Accessing contact route")
#     return pages_controller.contact()

# @app.route('/invoices')
# def invoices():
#     logger.debug("Accessing invoices route")
#     return pages_controller.invoices()

# @app.route('/setting')
# def setting():
#     logger.debug("Accessing setting route")
#     return pages_controller.setting()

@app.route('/product/add', methods=['POST'])
def add_product():
    logger.debug("Accessing add_product API")
    return productadmin_controller.add_product()

@app.route('/product/edit/<product_id>', methods=['POST'])
def edit_product(product_id):
    logger.debug(f"Accessing edit_product API for product_id={product_id}")
    return productadmin_controller.edit_product(product_id)

@app.route('/product/delete/<product_id>', methods=['POST'])
def delete_product(product_id):
    logger.debug(f"Accessing delete_product API for product_id={product_id}")
    return productadmin_controller.delete_product(product_id)


@app.route('/order/options', methods=['GET'])
def order_options():
    return order_admin_controller.order_options()


@app.route('/order/mark_delivered/<order_id>', methods=['POST'])
def mark_delivered(order_id):
    return order_admin_controller.mark_delivered(order_id)

@app.route('/order/mark_cancelled/<order_id>', methods=['POST'])
def mark_cancelled(order_id):
    return order_admin_controller.mark_cancelled(order_id)

@app.route('/pages/calendar')
def calendar():
    return pages_controller.calendar()


@app.route('/pages/contact')
def contact():
    return pages_controller.contact()

@app.route('/pages/invoices')
def invoices():
    return pages_controller.invoices()

@app.route('/pages/to_do_list')
def to_do_list():
    return pages_controller.to_do_list()

@app.route('/pages/setting')
def setting():
    return pages_controller.setting()

@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    return pages_controller.get_invoices()

@app.route('/pricing')
def pricing():
    logger.debug("Accessing pricing route")
    return pages_controller.pricing()

@app.route('/get_admins')
def get_admins():
    return pages_controller.get_admins()

@app.route('/get_events')
def get_events():
    return pages_controller.get_events()

@app.route('/get_all_events')
def get_all_events():
    return pages_controller.get_all_events()

@app.route('/create_event', methods=['POST'])
def create_event():
    return pages_controller.create_event()

@app.route('/update_admin/<admin_id>', methods=['POST'])
def update_admin(admin_id):
    return pages_controller.update_admin(admin_id)

@app.route('/update_event/<event_id>', methods=['POST'])
def update_event(event_id):
    return pages_controller.update_event(event_id)

@app.route('/delete_event/<event_id>', methods=['POST'])
def delete_event(event_id):
    return pages_controller.delete_event(event_id)


# New route to serve uploaded images
@app.route('/uploads/<path:filename>')
def serve_uploaded_image(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        logger.error(f"Lỗi khi phục vụ tệp upload {filename}: {str(e)}")
        return jsonify({"error": f"Không tìm thấy tệp: {filename}"}), 404

# Generic static file route (placed after specific routes)
@app.route('/<path:filename>')
def serve_static(filename):
    logger.debug(f"Yêu cầu tệp tĩnh: {filename}")
    try:
        # Bỏ qua các đường dẫn API
        if filename.startswith('api/'):
            logger.warning(f"Yêu cầu API không hợp lệ: {filename}")
            return jsonify({"error": f"Yêu cầu API không hợp lệ: {filename}"}), 404
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

# Log registered routes at startup
logger.info(f"Registered routes: {[rule.rule for rule in app.url_map.iter_rules()]}")

if __name__ == '__main__':
    logger.info("Starting Flask server with /get_customer_id endpoint - Version 2025-06-15-v4")
    app.run(debug=True)