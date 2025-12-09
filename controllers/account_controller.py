from flask import render_template, redirect, url_for, flash, jsonify, session
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

    def my_wallet(self):
        if 'customer_id' not in session:
            flash("Vui lòng đăng nhập", "error")
            return redirect(url_for('login'))
        try:
            return render_template('acc/myACC/my_wallet.html')
        except Exception as e:
            logger.error(f"Lỗi khi hiển thị my_wallet.html: {str(e)}")
            return jsonify({"error": "Không tìm thấy trang"}), 404

    def my_order(self):
        if 'customer_id' not in session:
            flash("Vui lòng đăng nhập", "error")
            return redirect(url_for('login'))
        try:
            return render_template('acc/myACC/my_order.html')
        except Exception as e:
            logger.error(f"Lỗi khi hiển thị my_order.html: {str(e)}")
            return jsonify({"error": "Không tìm thấy trang"}), 404

    def my_address(self):
        if 'customer_id' not in session:
            flash("Vui lòng đăng nhập", "error")
            return redirect(url_for('login'))
        try:
            return render_template('acc/myACC/my_address.html')
        except Exception as e:
            logger.error(f"Lỗi khi hiển thị my_address.html: {str(e)}")
            return jsonify({"error": "Không tìm thấy trang"}), 404

    def review(self):
        logger.debug("Accessing review route")
        if 'customer_id' not in session:
            flash("Vui lòng đăng nhập", "error")
            return redirect(url_for('login'))
        try:
            return render_template('acc/myACC/review.html')
        except Exception as e:
            logger.error(f"Lỗi khi hiển thị review.html: {str(e)}")
            return jsonify({"error": "Không tìm thấy trang"}), 404