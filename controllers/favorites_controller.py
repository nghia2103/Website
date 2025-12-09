from flask import render_template, jsonify, request, session, flash, redirect, url_for
from models.favorites import Favorites
import logging
from utils.db import get_db_connection

logger = logging.getLogger(__name__)

class FavoritesController:
    def favorites(self):
        logger.debug("Accessing favorites")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session, redirecting to login")
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            admin_id = session['admin_id']
            favorites = Favorites.get_favorites(admin_id)
            cursor.execute('SELECT first_name, last_name FROM admins WHERE admin_id = ?', (admin_id,))
            admin = cursor.fetchone()
            if not admin:
                logger.debug(f"Admin not found for admin_id={admin_id}")
                flash("Tài khoản admin không tồn tại", "error")
                session.pop('admin_id', None)
                conn.close()
                return redirect(url_for('login'))
            conn.close()
            return render_template('admin_dashboard/dashboard/favorite.html', favorites=favorites, admin=dict(admin))
        except Exception as e:
            logger.error(f"Error in favorites: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return jsonify({'success': False, 'message': str(e)}), 500

    def add_favorite(self):
        logger.debug("Adding favorite")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session")
            return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
        try:
            data = request.get_json()
            product_id = data.get('product_id')
            admin_id = session['admin_id']
            if not product_id:
                logger.error("Missing product_id in request")
                return jsonify({'success': False, 'message': 'Missing product_id'}), 400
            Favorites.add_favorite(admin_id, product_id)
            return jsonify({'success': True}), 200
        except ValueError as e:
            logger.debug(f"ValueError in add_favorite: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Error in add_favorite: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def remove_favorite(self):
        logger.debug("Removing favorite")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session")
            return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
        try:
            data = request.get_json()
            product_id = data.get('product_id')
            admin_id = session['admin_id']
            if not product_id:
                logger.error("Missing product_id in request")
                return jsonify({'success': False, 'message': 'Missing product_id'}), 400
            Favorites.remove_favorite(admin_id, product_id)
            return jsonify({'success': True}), 200
        except ValueError as e:
            logger.debug(f"ValueError in remove_favorite: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Error in remove_favorite: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500