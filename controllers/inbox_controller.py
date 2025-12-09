# controllers/inbox_controller.py
from flask import render_template, jsonify, request, session, flash, redirect, url_for
from models.inbox import Inbox
import logging
from utils.db import get_db_connection

logger = logging.getLogger(__name__)

class InboxController:
    def inbox(self):
        logger.debug("Accessing inbox")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session, redirecting to login")
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            admin_id = session['admin_id']
            cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
            admin = cursor.fetchone()
            if not admin:
                logger.debug(f"Admin not found for admin_id={admin_id}")
                flash("Tài khoản admin không tồn tại", "error")
                session.pop('admin_id', None)
                conn.close()
                return redirect(url_for('login'))
            conn.close()
            return render_template('admin_dashboard/dashboard/inbox.html', admin=dict(admin))
        except Exception as e:
            logger.error(f"Error in inbox: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return jsonify({'success': False, 'message': str(e)}), 500

    def get_threads(self):
        logger.debug("Getting threads")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session")
            return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
        admin_id = session['admin_id']
        try:
            threads = Inbox.get_threads(admin_id)
            return jsonify({'success': True, 'threads': threads}), 200
        except Exception as e:
            logger.error(f"Error in get_threads: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def get_messages(self, user_id):
        logger.debug(f"Getting messages for user_id={user_id}")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session")
            return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
        admin_id = session['admin_id']
        try:
            messages = Inbox.get_messages(user_id, admin_id)
            return jsonify({'success': True, 'messages': messages}), 200
        except ValueError as e:
            logger.debug(f"ValueError in get_messages: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 403
        except Exception as e:
            logger.error(f"Error in get_messages: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def send_message(self):
        logger.debug("Sending message")
        if 'admin_id' not in session and 'customer_id' not in session:
            logger.debug("No admin_id or customer_id in session")
            return jsonify({'success': False, 'message': 'Vui lòng đăng nhập'}), 401
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            admin_id = data.get('admin_id')
            direction = data.get('direction')
            content = data.get('content')
            if not all([user_id, direction, content]):
                logger.error("Missing required fields in send_message request")
                return jsonify({'success': False, 'message': 'Thiếu thông tin bắt buộc'}), 400
            if direction == 'user_to_admin' and session.get('customer_id') != user_id:
                logger.debug(f"Unauthorized user_to_admin message: user_id={user_id}")
                return jsonify({'success': False, 'message': 'Bạn phải đăng nhập để gửi tin nhắn'}), 401
            if direction == 'admin_to_user' and session.get('admin_id') != admin_id:
                logger.debug(f"Unauthorized admin_to_user message: admin_id={admin_id}")
                return jsonify({'success': False, 'message': 'Bạn phải đăng nhập với tư cách admin để gửi tin nhắn'}), 401
            message_id = Inbox.send_message(user_id, admin_id, direction, content)
            return jsonify({'success': True, 'message_id': message_id}), 200
        except ValueError as e:
            logger.debug(f"ValueError in send_message: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Error in send_message: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def assign_admin(self):
        logger.debug("Assigning admin")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session")
            return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
        admin_id = session['admin_id']
        try:
            data = request.get_json()
            user_id = data.get('user_id')
            if not user_id:
                logger.error("Missing user_id in request")
                return jsonify({'success': False, 'message': 'Thiếu user_id'}), 400
            Inbox.assign_admin(user_id, admin_id)
            return jsonify({'success': True, 'message': 'Gán admin thành công'}), 200
        except ValueError as e:
            logger.debug(f"ValueError in assign_admin: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 403
        except Exception as e:
            logger.error(f"Error in assign_admin: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500