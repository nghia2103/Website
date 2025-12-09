# controllers/user_management_controller.py
from flask import render_template, jsonify, session, flash, redirect, url_for, request
from models.user_management import UserManagement
import logging
from utils.db import get_db_connection

logger = logging.getLogger(__name__)

class UserManagementController:
    def user_management(self):
        logger.debug("Accessing user_management")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session, redirecting to login")
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            admin_id = session['admin_id']
            users = UserManagement.get_users()
            cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
            admin = cursor.fetchone()
            if not admin:
                logger.debug(f"Admin not found for admin_id={admin_id}")
                flash("Tài khoản admin không tồn tại", "error")
                session.pop('admin_id', None)
                conn.close()
                return redirect(url_for('login'))
            conn.close()
            return render_template('admin_dashboard/dashboard/user_management.html', users=users, admin=dict(admin))
        except Exception as e:
            logger.error(f"Error in user_management: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return jsonify({'success': False, 'message': str(e)}), 500

    def add_user(self):
        logger.debug("Adding user")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session")
            return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
        try:
            data = request.get_json()
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')
            password = data.get('password')
            role = data.get('role')

            if not all([first_name, last_name, email, password, role]):
                logger.warning("Missing required fields for adding user")
                return jsonify({'success': False, 'message': 'Thiếu thông tin bắt buộc'}), 400

            if role not in ['User', 'Admin']:
                logger.warning(f"Invalid role: {role}")
                return jsonify({'success': False, 'message': 'Vai trò không hợp lệ'}), 400

            if len(password) < 6:
                logger.warning("Password too short")
                return jsonify({'success': False, 'message': 'Mật khẩu phải có ít nhất 6 ký tự'}), 400

            user = UserManagement.add_user(first_name, last_name, email, password, role)
            if not user:
                logger.warning(f"Failed to add user: email={email}, possibly duplicate email")
                return jsonify({'success': False, 'message': 'Email đã tồn tại'}), 400

            logger.info(f"User added successfully: user_id={user['user_id']}")
            return jsonify({'success': True, 'user': user}), 200
        except sqlite3.Error as e:
            logger.error(f"Database error in add_user: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
        except Exception as e:
            logger.error(f"Unexpected error in add_user: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

    def edit_user(self, user_id):
        logger.debug(f"Editing user: user_id={user_id}")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session")
            return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
        try:
            data = request.get_json()
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            email = data.get('email')
            role = data.get('role')

            if not all([first_name, last_name, email, role]):
                logger.warning("Missing required fields for editing user")
                return jsonify({'success': False, 'message': 'Thiếu thông tin bắt buộc'}), 400

            if role not in ['User', 'Admin']:
                logger.warning(f"Invalid role: {role}")
                return jsonify({'success': False, 'message': 'Vai trò không hợp lệ'}), 400

            user = UserManagement.edit_user(user_id, first_name, last_name, email, role)
            if not user:
                logger.warning(f"User not found: user_id={user_id}")
                return jsonify({'success': False, 'message': 'Tài khoản không tồn tại hoặc email đã tồn tại'}), 404

            logger.info(f"User updated successfully: user_id={user_id}")
            return jsonify({'success': True, 'user': user}), 200
        except sqlite3.Error as e:
            logger.error(f"Database error in edit_user: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
        except Exception as e:
            logger.error(f"Unexpected error in edit_user: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

    def delete_user(self, user_id):
        logger.debug(f"Deleting user: user_id={user_id}")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session")
            return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
        try:
            success = UserManagement.delete_user(user_id)
            if not success:
                logger.warning(f"Cannot delete user: user_id={user_id}, not found or has dependencies")
                return jsonify({'success': False, 'message': 'Tài khoản không tồn tại hoặc có liên kết dữ liệu'}), 400

            logger.info(f"User deleted successfully: user_id={user_id}")
            return jsonify({'success': True}), 200
        except sqlite3.Error as e:
            logger.error(f"Database error in delete_user: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
        except Exception as e:
            logger.error(f"Unexpected error in delete_user: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500