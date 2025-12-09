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