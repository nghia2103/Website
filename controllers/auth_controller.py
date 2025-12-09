from flask import render_template, redirect, url_for, session, flash, request, current_app
from models.auth_model import AuthModel
import logging

logger = logging.getLogger(__name__)

class AuthController:
    def index(self):
        if session.get('is_admin', False) and 'admin_id' in session:
            logger.debug("Admin đã đăng nhập, chuyển hướng đến dashboard")
            return redirect(url_for('dashboard'))
        elif 'customer_id' in session:
            logger.debug("User đã đăng nhập, chuyển hướng đến index")
            return render_template('index.html')
        logger.debug("Chưa đăng nhập, hiển thị trang index")
        return render_template('index.html')

    def login(self):
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            logger.debug(f"Login attempt: email={email}")
            if not email or not password:
                flash("Vui lòng nhập cả email và mật khẩu", "error")
                return render_template('signup/login.html', error="Vui lòng nhập cả email và mật khẩu")

            if email.startswith('admin/'):
                admin_email = email[6:]
                logger.debug(f"Admin login attempt: email={admin_email}")
                admin = AuthModel.get_admin_by_email(admin_email)
                if admin and admin['password'] == password:
                    session.clear()
                    session['admin_id'] = admin['admin_id']
                    session['first_name'] = admin['first_name']
                    session['is_admin'] = True
                    logger.info(f"Admin login successful: admin_id={admin['admin_id']}")
                    return redirect(url_for('dashboard'))
                else:
                    flash("Email hoặc mật khẩu admin không đúng", "error")
                    logger.warning(f"Admin login failed: email={admin_email}")
                    return render_template('signup/login.html', error="Email hoặc mật khẩu admin không đúng")
            else:
                user = AuthModel.get_user_by_email(email)
                if user and user['password'] == password:
                    session.clear()
                    session['customer_id'] = user['customer_id']
                    session['first_name'] = user['first_name']
                    session['is_admin'] = False
                    logger.info(f"User login successful: customer_id={user['customer_id']}")
                    logger.debug(f"Session after login: {session}")
                    return redirect(url_for('index'))
                else:
                    flash("Email hoặc mật khẩu không đúng", "error")
                    logger.warning(f"User login failed: email={email}")
                    return render_template('signup/login.html', error="Email hoặc mật khẩu không đúng")

        logger.debug("Hiển thị login.html")
        return render_template('signup/login.html')

    def logout(self):
        session.clear()
        flash("Đăng xuất thành công", "success")
        return redirect(url_for('login'))