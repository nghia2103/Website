from flask import render_template, jsonify, request, session, flash, redirect, url_for
import logging

logger = logging.getLogger(__name__)

try:
    from models.dashboard import Dashboard
    logger.info("Imported Dashboard model successfully")
except ImportError as e:
    logger.error(f"Failed to import Dashboard model: {str(e)}")
    raise e

class DashboardController:
    def get_dashboard(self):
        logger.debug("Entering get_dashboard method")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session, redirecting to login")
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        
        try:
            admin_id = session['admin_id']
            logger.debug(f"Fetching dashboard data for admin_id={admin_id}")
            dashboard_data = Dashboard.get_dashboard_data(admin_id)
            
            if not dashboard_data['admin']:
                logger.debug(f"Admin not found for admin_id={admin_id}")
                flash("Tài khoản admin không tồn tại", "error")
                session.pop('admin_id', None)
                return redirect(url_for('login'))

            logger.debug(f"Dashboard data: total_users={dashboard_data['total_users']}, total_orders={dashboard_data['total_orders']}, total_sales={dashboard_data['total_sales']}, total_pending={dashboard_data['total_pending']}")
            return render_template(
                'admin_dashboard/dashboard/dashboard.html',
                total_users=dashboard_data['total_users'],
                total_orders=dashboard_data['total_orders'],
                total_sales=dashboard_data['total_sales'],
                total_pending=dashboard_data['total_pending'],
                user_percentage=8.5,
                order_percentage=1.3,
                sales_percentage=4.3,
                pending_percentage=1.8,
                sales_data=dashboard_data['sales_data'],
                deals=dashboard_data['deals'],
                admin=dashboard_data['admin']
            )
        except ValueError as e:
            logger.error(f"Lỗi dữ liệu khi lấy dashboard: {str(e)}")
            flash(str(e), "error")
            return redirect(url_for('login'))
        except Exception as e:
            logger.error(f"Lỗi khi lấy dashboard: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return jsonify({'success': False, 'message': str(e)}), 500