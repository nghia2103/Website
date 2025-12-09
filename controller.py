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
        
# admin_controller.py
from flask import render_template, redirect, url_for, jsonify, request, session, flash
from models.admin_model import AdminModel
import logging

logger = logging.getLogger(__name__)

class AdminController:
    def dashboard(self):
        if 'admin_id' not in session:
            print("No admin_id in session, redirecting to login")
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        
        data, error = AdminModel.get_dashboard_data(session['admin_id'])
        if error:
            print(f"Error in dashboard: {error}")
            flash(error, "error")
            if "Tài khoản admin không tồn tại" in error:
                session.pop('admin_id', None)
                return redirect(url_for('login'))
            return jsonify({'success': False, 'message': error}), 500

        return render_template(
            'admin_dashboard/dashboard/dashboard.html',
            total_users=data['total_users'],
            total_orders=data['total_orders'],
            total_sales=data['total_sales'],
            total_pending=data['total_pending'],
            user_percentage=8.5,
            order_percentage=1.3,
            sales_percentage=4.3,
            pending_percentage=1.8,
            sales_data=data['sales_data'],
            deals=data['deals'],
            admin=dict(data['admin'])
        )

    def order_lists(self):
        if 'admin_id' not in session:
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        
        data, error = AdminModel.get_order_lists(session['admin_id'])
        if error:
            return jsonify({'success': False, 'message': error}), 500

        return render_template('admin_dashboard/dashboard/order_lists.html', orders=data['orders'], admin=data['admin'])

    def order_options(self):
        data, error = AdminModel.get_order_options()
        if error:
            return jsonify({'success': False, 'message': error}), 500

        return jsonify({
            'products': data['products'],
            'stores': data['stores'],
            'customers': data['customers']
        })

    def create_order(self):
        data = request.get_json()
        order, error = AdminModel.create_order(data)
        if error:
            return jsonify({'success': False, 'message': error}), 400 if 'Thiếu' in error or 'không hợp lệ' in error else 500

        return jsonify({
            'success': True,
            'order': order
        })

    def update_order(self, order_id):
        data = request.get_json()
        order, error = AdminModel.update_order(order_id, data)
        if error:
            return jsonify({'success': False, 'message': error}), 400 if 'Thiếu' in error or 'không hợp lệ' in error else 500

        return jsonify({
            'success': True,
            'order': order
        })

    def delete_order(self, order_id):
        success, error = AdminModel.delete_order(order_id)
        if error:
            return jsonify({'success': False, 'message': error}), 400 if 'not found' in error.lower() else 500

        return jsonify({'success': True})

    def mark_delivered(self, order_id):
        order, error = AdminModel.mark_delivered(order_id)
        if error:
            return jsonify({'success': False, 'message': error}), 400 if 'not found' in error.lower() else 500

        return jsonify({
            'success': True,
            'order': order
        })

    def mark_cancelled(self, order_id):
        order, error = AdminModel.mark_cancelled(order_id)
        if error:
            return jsonify({'success': False, 'message': error}), 400 if 'not found' in error.lower() else 500

        return jsonify({
            'success': True,
            'order': order
        })

    def products(self):
        if 'admin_id' not in session:
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        
        data, error = AdminModel.get_products(session['admin_id'])
        if error:
            return jsonify({'success': False, 'message': error}), 500

        return render_template('admin_dashboard/dashboard/products.html', products_query=data['products'], admin=data['admin'])

    def favorites(self):
        if 'admin_id' not in session:
            print("No admin_id in session, redirecting to login")
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        
        data, error = AdminModel.get_favorites(session['admin_id'])
        if error:
            print(f"Error in favorites: {error}")
            flash(error, "error")
            if "Tài khoản admin không tồn tại" in error:
                session.pop('admin_id', None)
                return redirect(url_for('login'))
            return jsonify({'success': False, 'message': error}), 500

        return render_template(
            'admin_dashboard/dashboard/favorite.html',
            favorites=data['favorites'],
            admin=dict(data['admin'])
        )

    def add_favorite(self):
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
        
        data = request.get_json()
        success, error = AdminModel.add_favorite(session['admin_id'], data.get('product_id'))
        if error:
            return jsonify({'success': False, 'message': error}), 400 if 'not found' in error.lower() else 500

        return jsonify({'success': True})

    def user_management(self):
        if 'admin_id' not in session:
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        
        data, error = AdminModel.get_user_management_data(session['admin_id'])
        if error:
            flash(error, "error")
            if "Tài khoản admin không tồn tại" in error:
                session.pop('admin_id', None)
                return redirect(url_for('login'))
            return jsonify({'success': False, 'message': error}), 500

        return render_template(
            'admin_dashboard/dashboard/user_management.html',
            users=data['users'],
            admin=dict(data['admin'])
        )

    def add_user(self):
        data = request.get_json()
        user, error = AdminModel.add_user(data)
        if error:
            return jsonify({'success': False, 'message': error}), 400 if 'Thiếu' in error or 'không hợp lệ' in error or 'Email đã tồn tại' in error else 500

        return jsonify({
            'success': True,
            'user': user
        })

    def edit_user(self, user_id):
        data = request.get_json()
        user, error = AdminModel.edit_user(user_id, data)
        if error:
            return jsonify({'success': False, 'message': error}), 400 if 'Thiếu' in error or 'không hợp lệ' in error or 'Email đã tồn tại' in error else 500

        return jsonify({
            'success': True,
            'user': user
        })

    def delete_user(self, user_id):
        success, error = AdminModel.delete_user(user_id)
        if error:
            return jsonify({'success': False, 'message': error}), 400 if 'Tài khoản không tồn tại' in error or 'Không thể xóa' in error else 500

        return jsonify({'success': True})
    
    def delete_user(self, user_id):
        success, error = AdminModel.delete_user(user_id)

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
    
# cart_controller.py
from flask import jsonify, request, session
from models.cart_model import CartModel
import logging

logger = logging.getLogger(__name__)

class CartController:
    def get_cart(self):
        if 'customer_id' not in session:
            return jsonify({'error': 'Vui lòng đăng nhập'}), 401
        try:
            customer_id = session['customer_id']
            cart_items = CartModel.get_cart(customer_id)
            formatted_cart = []
            for row in cart_items:
                discount = row['discount'] or 0
                discounted_price = row['price'] * (1 - discount / 100)
                formatted_cart.append({
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
            return jsonify(formatted_cart), 200
        except Exception as e:
            logger.error(f"Lỗi khi lấy giỏ hàng: {str(e)}")
            return jsonify({"error": str(e)}), 500

    def add_to_cart(self):
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
            cart_id, price, discount = CartModel.add_to_cart(customer_id, product_id, quantity, size_id)
            discounted_price = price * (1 - discount / 100)
            logger.debug(f"Thêm vào giỏ hàng: cart_id={cart_id}, customer_id={customer_id}, discounted_price={discounted_price}")
            return jsonify({
                "message": "Đã thêm vào giỏ hàng",
                "cart_id": cart_id,
                "discounted_price": discounted_price
            }), 200
        except ValueError as e:
            logger.error(f"Lỗi dữ liệu khi thêm vào giỏ hàng: {str(e)}")
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            logger.error(f"Lỗi khi thêm vào giỏ hàng: {str(e)}")
            return jsonify({"error": str(e)}), 500

    def update_cart_item(self):
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
            rows_affected = CartModel.update_cart_item(customer_id, cart_id, quantity)
            if rows_affected == 0:
                logger.error(f"Không tìm thấy mục trong giỏ hàng: cart_id={cart_id}")
                return jsonify({"error": "Không tìm thấy mục trong giỏ hàng"}), 404
            logger.debug(f"Cập nhật giỏ hàng: cart_id={cart_id}, quantity={quantity}")
            return jsonify({"message": "Cập nhật giỏ hàng thành công"}), 200
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi cập nhật giỏ hàng: {str(e)}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật giỏ hàng: {str(e)}")
            return jsonify({"error": str(e)}), 500

    def remove_from_cart(self):
        if 'customer_id' not in session:
            return jsonify({'error': 'Vui lòng đăng nhập'}), 401
        try:
            customer_id = session['customer_id']
            data = request.json
            cart_id = data.get('cart_id')
            if not cart_id:
                logger.error("Thiếu cart_id trong yêu cầu")
                return jsonify({"error": "Thiếu cart_id"}), 400
            rows_affected = CartModel.remove_from_cart(customer_id, cart_id)
            if rows_affected == 0:
                logger.error(f"Sản phẩm không tồn tại trong giỏ hàng: cart_id={cart_id}")
                return jsonify({"error": "Sản phẩm không tồn tại trong giỏ hàng"}), 404
            logger.debug(f"Xóa sản phẩm khỏi giỏ hàng: cart_id={cart_id}")
            return jsonify({"message": "Đã xóa sản phẩm khỏi giỏ hàng"}), 200
        except Exception as e:
            logger.error(f"Lỗi khi xóa sản phẩm khỏi giỏ hàng: {str(e)}")
            return jsonify({"error": str(e)}), 500
        
# checkout_controller.py
from flask import render_template, redirect, url_for, jsonify, request, session, flash
from models.checkout_model import CheckoutModel
import logging

logger = logging.getLogger(__name__)

class CheckoutController:
    def checkout(self):
        if 'customer_id' not in session:
            flash("Vui lòng đăng nhập", "error")
            return redirect(url_for('login'))
        try:
            customer_id = session['customer_id']
            cart_items = CheckoutModel.get_cart(customer_id)
            formatted_cart = []
            for row in cart_items:
                discount = row['discount'] or 0
                discounted_price = row['price'] * (1 - discount / 100)
                formatted_cart.append({
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
            if not formatted_cart:
                flash("Giỏ hàng trống!", "error")
                return redirect(url_for('products_user'))
            return render_template('Checkout.html', cart=formatted_cart)
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi tải giỏ hàng: {str(e)}")
            flash(f"Lỗi cơ sở dữ liệu: {str(e)}", "error")
            return redirect(url_for('products_user'))
        except Exception as e:
            logger.error(f"Lỗi khi tải giỏ hàng: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return redirect(url_for('products_user'))

    def add_checkout(self):
        data = request.json
        session["cart"] = data
        return jsonify({"status": "OK"})

    def get_checkout(self):
        return jsonify(session.get("cart", []))
    
# forgot_password_controller.py
from flask import render_template, redirect, url_for, flash, request
from models.forgot_password_model import ForgotPasswordModel
import logging

logger = logging.getLogger(__name__)

class ForgotPasswordController:
    def forgot_password(self, form):
        if request.method == 'POST' and form.validate_on_submit():
            email = form.email.data
            if not ForgotPasswordModel.email_exists(email):
                flash("Email không tồn tại", "error")
                return render_template('signup/forgot_pass.html', form=form)
            flash("Succesfully sent email confirmation", "success")
            return redirect(url_for('login'))
        return render_template('signup/forgot_pass.html', form=form)
    
# order_controller.py
from flask import jsonify, request, session
from models.order_model import OrderModel
import logging

logger = logging.getLogger(__name__)

class OrderController:
    def create_user_order(self):
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
            order_id, total_amount = OrderModel.create_order(customer_id, items, note, card_info, calendar_info)
            session.pop('cart', None)
            session.pop('card-info', None)
            session.pop('calendar-info', None)
            logger.info(f"Tạo đơn hàng thành công: order_id={order_id}, customer_id={customer_id}, total_amount={total_amount}")
            return jsonify({
                "message": "Tạo đơn hàng thành công",
                "order_id": order_id,
                "total_amount": total_amount
            }), 200
        except ValueError as e:
            logger.error(f"Lỗi dữ liệu khi tạo đơn hàng: {str(e)}, customer_id={customer_id}")
            return jsonify({"error": str(e)}), 400
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi tạo đơn hàng: {str(e)}, customer_id={customer_id}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi không xác định khi tạo đơn hàng: {str(e)}, customer_id={customer_id}")
            return jsonify({"error": str(e)}), 500

    def confirm_card(self):
        if 'customer_id' not in session:
            return jsonify({'error': 'Vui lòng đăng nhập'}), 401
        data = request.json
        session["card-info"] = data
        return jsonify({"status": "OK"})

    def confirm_calendar(self):
        if 'customer_id' not in session:
            return jsonify({'error': 'Vui lòng đăng nhập'}), 401
        data = request.json
        session['calendar-info'] = data
        return jsonify({"status": "OK"})

# product_controller.py
from flask import render_template, redirect, url_for, jsonify, session, flash, request
from models.product_model import ProductModel
from models.account_model import AccountModel
import json
import logging

logger = logging.getLogger(__name__)

class ProductController:
    def products_user(self):
        try:
            products = ProductModel.get_all_products()
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
            customer_id = session.get('customer_id')
            user = AccountModel.get_user_details(customer_id) if customer_id else None
            return render_template(
                'Products/products.html',
                products=products_list,
                user=user or {'first_name': 'Guest', 'last_name': ''}
            )
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
        except Exception as e:
            logger.error(f"Lỗi: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def admin_products(self):
        if 'admin_id' not in session:
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        try:
            admin_id = session['admin_id']
            products = ProductModel.get_admin_products(admin_id)
            for product in products:
                product['avg_rating'] = float(product['avg_rating']) if product['avg_rating'] is not None else 0.0
            admin = AccountModel.get_user_details(admin_id) or {'first_name': 'Admin', 'last_name': ''}
            return render_template('admin_dashboard/dashboard/products.html', products_query=products, admin=admin)
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
        except Exception as e:
            logger.error(f"Lỗi: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def get_products(self):
        try:
            products = ProductModel.get_all_products()
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

    def get_product_by_id(self, product_id):
        try:
            product, sizes = ProductModel.get_product_by_id(product_id)
            if not product:
                return jsonify({"error": "Product not found"}), 404
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

    def get_top10_products(self):
        try:
            products_list = ProductModel.get_top10_products()
            logger.debug(f"Trả về {len(products_list)} sản phẩm bán chạy nhất")
            return jsonify(products_list), 200
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi lấy top 10 sản phẩm: {str(e)}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi khi lấy top 10 sản phẩm: {str(e)}")
            return jsonify({"error": str(e)}), 500
        
# review_controller.py
from flask import jsonify
from models.review_model import ReviewModel
import logging

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

# signup_controller.py
from flask import render_template, redirect, url_for, flash, request
from models.signup_model import SignupModel
import logging

logger = logging.getLogger(__name__)

class SignupController:
    def signup(self, form):
        if request.method == 'POST' and form.validate_on_submit():
            first_name = form.first_name.data
            last_name = form.last_name.data
            email = form.email.data
            password = form.password.data

            if SignupModel.email_exists(email):
                flash("Email đã tồn tại", "email_error")
                return render_template('signup/sign_up.html', form=form)

            SignupModel.create_user(first_name, last_name, email, password)
            flash("Successfully register, please log in", "success")
            return redirect(url_for('login'))

        return render_template('signup/sign_up.html', form=form)
    
# user_controller.py
from flask import render_template, redirect, url_for, jsonify, request, session, flash
from models.user import User
from models.product import Product
from forms.signup_form import SignupForm
from forms.forgot_password_form import ForgotPasswordForm
import logging

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