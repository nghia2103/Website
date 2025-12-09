from flask import request, jsonify
from models.order_admin import OrderAdmin
import logging

logger = logging.getLogger(__name__)

class OrderAdminController:
    def order_options(self):
        logger.debug("Accessing order_options")
        try:
            options = OrderAdmin.get_order_options()
            return jsonify(options), 200
        except Exception as e:
            logger.error(f"Error in order_options: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def create_order(self):
        logger.debug("Creating order")
        try:
            data = request.get_json()
            customer_id = data.get('customer_id')
            product_id = data.get('product_id')
            quantity = int(data.get('quantity'))
            store_id = data.get('store_id')
            size = data.get('size', 'M')
            status = data.get('status', 'Pending')

            order = OrderAdmin.create_order(customer_id, product_id, quantity, store_id, size, status)
            return jsonify({'success': True, 'order': order}), 200
        except ValueError as e:
            logger.error(f"Validation error in create_order: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Error in create_order: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def update_order(self, order_id):
        logger.debug(f"Updating order: order_id={order_id}")
        try:
            data = request.get_json()
            customer_id = data.get('customer_id')
            product_id = data.get('product_id')
            quantity = int(data.get('quantity'))
            store_id = data.get('store_id')
            status = data.get('status')
            size = data.get('size', 'M')

            order = OrderAdmin.update_order(order_id, customer_id, product_id, quantity, store_id, status, size)
            return jsonify({'success': True, 'order': order}), 200
        except ValueError as e:
            logger.error(f"Validation error in update_order: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Error in update_order: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def delete_order(self, order_id):
        logger.debug(f"Deleting order: order_id={order_id}")
        try:
            OrderAdmin.delete_order(order_id)
            return jsonify({'success': True}), 200
        except ValueError as e:
            logger.error(f"Validation error in delete_order: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Error in delete_order: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def mark_delivered(self, order_id):
        logger.debug(f"Marking order delivered: order_id={order_id}")
        try:
            order = OrderAdmin.mark_delivered(order_id)
            return jsonify({'success': True, 'order': order}), 200
        except ValueError as e:
            logger.error(f"Validation error in mark_delivered: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Error in mark_delivered: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def mark_cancelled(self, order_id):
        logger.debug(f"Marking order cancelled: order_id={order_id}")
        try:
            order = OrderAdmin.mark_cancelled(order_id)
            return jsonify({'success': True, 'order': order}), 200
        except ValueError as e:
            logger.error(f"Validation error in mark_cancelled: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 400
        except Exception as e:
            logger.error(f"Error in mark_cancelled: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500