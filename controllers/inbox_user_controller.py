from flask import jsonify, request, session
import logging

logger = logging.getLogger(__name__)

try:
    from models.inbox_user import InboxUser
    logger.info("Imported InboxUser model successfully")
except ImportError as e:
    logger.error(f"Failed to import InboxUser model: {str(e)}")
    raise e

class InboxUserController:
    def get_customer_id(self):
        logger.debug("Entering get_customer_id method")
        try:
            customer_id = session.get('customer_id')
            if not customer_id:
                logger.warning("No customer_id in session")
                return jsonify({'error': 'Vui lòng đăng nhập'}), 401
            logger.debug(f"Retrieved customer_id: {customer_id}")
            return jsonify({'customer_id': customer_id}), 200
        except Exception as e:
            logger.error(f"Error in get_customer_id: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def get_user(self):
        logger.debug("Entering get_user method")
        try:
            if 'customer_id' not in session:
                logger.warning("No customer_id in session")
                return jsonify({"error": "Vui lòng đăng nhập để xem thông tin người dùng"}), 401
            customer_id = session['customer_id']
            logger.debug(f"Fetching user data for customer_id={customer_id}")
            user_data = InboxUser.get_user_data(customer_id)
            if not user_data:
                logger.warning(f"User not found for customer_id={customer_id}")
                return jsonify({"error": "Không tìm thấy người dùng"}), 404
            return jsonify(user_data), 200
        except Exception as e:
            logger.error(f"Error in get_user: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def get_user_messages(self, user_id):
        logger.debug(f"Entering get_user_messages method for user_id={user_id}")
        try:
            if 'customer_id' not in session or session['customer_id'] != user_id:
                logger.warning(f"Unauthorized access attempt: session_customer_id={session.get('customer_id')}, requested_user_id={user_id}")
                return jsonify({'success': False, 'message': 'Không có quyền truy cập hoặc chưa đăng nhập'}), 401
            messages = InboxUser.get_user_messages_data(user_id)
            logger.debug(f"Retrieved {len(messages)} messages for user_id={user_id}")
            return jsonify({'success': True, 'messages': messages}), 200
        except Exception as e:
            logger.error(f"Error in get_user_messages: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def send_message(self):
        logger.debug("Entering send_message method")
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            admin_id = data.get('admin_id')
            direction = data.get('direction')
            content = data.get('content')

            if not all([user_id, direction, content]):
                logger.warning("Missing required fields in send_message")
                return jsonify({'success': False, 'message': 'Thiếu thông tin bắt buộc'}), 400

            if direction not in ['user_to_admin', 'admin_to_user']:
                logger.warning(f"Invalid direction: {direction}")
                return jsonify({'success': False, 'message': 'Hướng tin nhắn không hợp lệ'}), 400

            message_id = InboxUser.send_message_data(user_id, admin_id, direction, content, session)
            logger.debug(f"Sent message with message_id={message_id}")
            return jsonify({'success': True, 'message_id': message_id}), 200
        except ValueError as e:
            logger.error(f"Validation error in send_message: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Error in send_message: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500