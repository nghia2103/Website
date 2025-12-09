# controllers/pages_controller.py
from flask import render_template, jsonify, request, session, flash, redirect, url_for
import logging

logger = logging.getLogger(__name__)

try:
    from models.pages import Pages
    logger.info("Imported Pages model successfully")
except ImportError as e:
    logger.error(f"Failed to import Pages model: {str(e)}")
    raise e

class PagesController:
    def calendar(self):
        logger.debug("Entering calendar method")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session, redirecting to login")
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        
        try:
            admin_id = session['admin_id']
            logger.debug(f"Fetching admin data for admin_id={admin_id}")
            admin_data = Pages.get_admin_data(admin_id)
            if not admin_data:
                logger.debug(f"Admin not found for admin_id={admin_id}")
                flash("Tài khoản admin không tồn tại", "error")
                session.pop('admin_id', None)
                return redirect(url_for('login'))
            
            return render_template('admin_dashboard/pages/calendar.html', admin=admin_data)
        except Exception as e:
            logger.error(f"Error in calendar: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return jsonify({'success': False, 'message': str(e)}), 500

    def contact(self):
        logger.debug("Entering contact method")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session, redirecting to login")
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        
        try:
            admin_id = session['admin_id']
            logger.debug(f"Fetching admin data for admin_id={admin_id}")
            admin_data = Pages.get_admin_data(admin_id)
            if not admin_data:
                logger.debug(f"Admin not found for admin_id={admin_id}")
                flash("Tài khoản admin không tồn tại", "error")
                session.pop('admin_id', None)
                return redirect(url_for('login'))
            
            return render_template('admin_dashboard/pages/contact.html', admin=admin_data)
        except Exception as e:
            logger.error(f"Error in contact: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return jsonify({'success': False, 'message': str(e)}), 500

    def invoices(self):
        logger.debug("Entering invoices method")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session, redirecting to login")
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        
        try:
            admin_id = session['admin_id']
            logger.debug(f"Fetching admin data for admin_id={admin_id}")
            admin_data = Pages.get_admin_data(admin_id)
            if not admin_data:
                logger.debug(f"Admin not found for admin_id={admin_id}")
                flash("Tài khoản admin không tồn tại", "error")
                session.pop('admin_id', None)
                return redirect(url_for('login'))
            
            return render_template('admin_dashboard/pages/invoices.html', admin=admin_data)
        except Exception as e:
            logger.error(f"Error in invoices: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return jsonify({'success': False, 'message': str(e)}), 500

    def to_do_list(self):
        logger.debug("Entering to_do_list method")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session, redirecting to login")
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        
        try:
            admin_id = session['admin_id']
            logger.debug(f"Fetching admin data for admin_id={admin_id}")
            admin_data = Pages.get_admin_data(admin_id)
            if not admin_data:
                logger.debug(f"Admin not found for admin_id={admin_id}")
                flash("Tài khoản admin không tồn tại", "error")
                session.pop('admin_id', None)
                return redirect(url_for('login'))
            
            return render_template('admin_dashboard/pages/to_do_list.html', admin=admin_data)
        except Exception as e:
            logger.error(f"Error in to_do_list: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return jsonify({'success': False, 'message': str(e)}), 500

    def setting(self):
        logger.debug("Entering setting method")
        if 'admin_id' not in session:
            logger.debug("No admin_id in session, redirecting to login")
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        
        try:
            admin_id = session['admin_id']
            logger.debug(f"Fetching admin data for admin_id={admin_id}")
            admin_data = Pages.get_admin_data(admin_id)
            if not admin_data:
                logger.debug(f"Admin not found for admin_id={admin_id}")
                flash("Tài khoản admin không tồn tại", "error")
                session.pop('admin_id', None)
                return redirect(url_for('login'))
            
            return render_template('admin_dashboard/pages/setting.html', admin=admin_data)
        except Exception as e:
            logger.error(f"Error in setting: {str(e)}")
            flash(f"Lỗi: {str(e)}", "error")
            return jsonify({'success': False, 'message': str(e)}), 500

    def get_invoices(self):
        logger.debug("Entering get_invoices method")
        try:
            filter_date = request.args.get('date')
            filter_customer = request.args.get('customer')
            invoice_data = Pages.get_invoice_data(filter_date, filter_customer)
            logger.debug(f"Retrieved {len(invoice_data['invoices'])} invoices")
            return jsonify({
                'invoices': invoice_data['invoices'],
                'customers': invoice_data['customers'],
                'total_amount': invoice_data['total_amount']
            })
        except Exception as e:
            logger.error(f"Error in get_invoices: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def get_admins(self):
        logger.debug("Entering get_admins method")
        try:
            admins_data = Pages.get_admins_data()
            logger.debug(f"Retrieved {len(admins_data)} admins")
            return jsonify({'success': True, 'admins': admins_data})
        except Exception as e:
            logger.error(f"Error in get_admins: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def get_events(self):
        logger.debug("Entering get_events method")
        try:
            year = request.args.get('year')
            month = request.args.get('month')
            if not year or not month:
                logger.error("Missing year or month parameters")
                return jsonify({'success': False, 'message': 'Year and month are required.'}), 400
            events_data = Pages.get_events_data(year, month)
            logger.debug(f"Retrieved {len(events_data)} events")
            return jsonify({'success': True, 'events': events_data})
        except Exception as e:
            logger.error(f"Error in get_events: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def get_all_events(self):
        logger.debug("Entering get_all_events method")
        try:
            all_events_data = Pages.get_all_events_data()
            logger.debug(f"Retrieved {len(all_events_data)} events")
            return jsonify({'success': True, 'events': all_events_data})
        except Exception as e:
            logger.error(f"Error in get_all_events: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def create_event(self):
        logger.debug("Entering create_event method")
        try:
            if 'admin_id' not in session:
                logger.debug("No admin_id in session")
                return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
            data = request.get_json()
            event_data = Pages.create_event_data(data, session['admin_id'])
            logger.debug(f"Created event: {event_data['event_id']}")
            return jsonify({'success': True, 'event': event_data})
        except ValueError as e:
            logger.error(f"Validation error in create_event: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Error in create_event: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def update_admin(self, admin_id):
        logger.debug(f"Entering update_admin method for admin_id={admin_id}")
        try:
            if 'admin_id' not in session:
                logger.debug("No admin_id in session")
                return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
            admin_data = Pages.update_admin_data(admin_id, request.form, request.files)
            logger.debug(f"Updated admin: {admin_id}")
            return jsonify({'success': True, 'admin': admin_data})
        except ValueError as e:
            logger.error(f"Validation error in update_admin: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Error in update_admin: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def update_event(self, event_id):
        logger.debug(f"Entering update_event method for event_id={event_id}")
        try:
            if 'admin_id' not in session:
                logger.debug("No admin_id in session")
                return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
            data = request.get_json()
            event_data = Pages.update_event_data(event_id, data, session['admin_id'])
            logger.debug(f"Updated event: {event_id}")
            return jsonify({'success': True, 'event': event_data})
        except ValueError as e:
            logger.error(f"Validation error in update_event: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Error in update_event: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def delete_event(self, event_id):
        logger.debug(f"Entering delete_event method for event_id={event_id}")
        try:
            if 'admin_id' not in session:
                logger.debug("No admin_id in session")
                return jsonify({'success': False, 'message': 'Vui lòng đăng nhập với tư cách admin'}), 401
            Pages.delete_event_data(event_id)
            logger.debug(f"Deleted event: {event_id}")
            return jsonify({'success': True})
        except ValueError as e:
            logger.error(f"Validation error in delete_event: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Error in delete_event: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500