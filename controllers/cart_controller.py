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