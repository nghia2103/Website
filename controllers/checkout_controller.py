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