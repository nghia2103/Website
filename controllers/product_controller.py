from flask import render_template, redirect, url_for, jsonify, session, flash, request
from models.product_model import ProductModel
from models.account_model import AccountModel
import json
import logging

logger = logging.getLogger(__name__)

class ProductController:
    def products_user(self):
        try:
            products = ProductModel.get_all_products()
            product_dict = {}
            for row in products:
                product_id = row['product_id']
                if product_id not in product_dict:
                    product_dict[product_id] = {
                        "product_id": row['product_id'],
                        "product_name": row['product_name'],
                        "category": row['category'],
                        "stock": row['stock'],
                        "description": row['description'],
                        "image_url": row['image_url'],
                        "image_url_2": row['image_url_2'],
                        "discount": row['discount'] or 0,
                        "sizes": []
                    }
                if row['size']:
                    product_dict[product_id]['sizes'].append({
                        "size": row['size'],
                        "price": row['price'],
                        "size_id": row['size_id']
                    })
            products_list = list(product_dict.values())
            customer_id = session.get('customer_id')
            user = AccountModel.get_user_details(customer_id) if customer_id else None
            return render_template(
                'Products/products.html',
                products=products_list,
                user=user or {'first_name': 'Guest', 'last_name': ''}
            )
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
        except Exception as e:
            logger.error(f"Lỗi: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def admin_products(self):
        if 'admin_id' not in session:
            flash("Vui lòng đăng nhập với tư cách admin", "error")
            return redirect(url_for('login'))
        try:
            admin_id = session['admin_id']
            products = ProductModel.get_admin_products(admin_id)
            for product in products:
                product['avg_rating'] = float(product['avg_rating']) if product['avg_rating'] is not None else 0.0
            admin = AccountModel.get_user_details(admin_id) or {'first_name': 'Admin', 'last_name': ''}
            return render_template('admin_dashboard/dashboard/products.html', products_query=products, admin=admin)
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu: {str(e)}")
            return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
        except Exception as e:
            logger.error(f"Lỗi: {str(e)}")
            return jsonify({'success': False, 'message': str(e)}), 500

    def get_products(self):
        try:
            products = ProductModel.get_all_products()
            product_dict = {}
            for row in products:
                product_id = row['product_id']
                if product_id not in product_dict:
                    product_dict[product_id] = {
                        "product_id": row['product_id'],
                        "product_name": row['product_name'],
                        "category": row['category'],
                        "stock": row['stock'],
                        "description": row['description'],
                        "image_url": row['image_url'],
                        "image_url_2": row['image_url_2'],
                        "discount": row['discount'] or 0,
                        "sizes": []
                    }
                if row['size']:
                    product_dict[product_id]['sizes'].append({
                        "size": row['size'],
                        "price": row['price'],
                        "size_id": row['size_id']
                    })
            products_list = list(product_dict.values())
            logger.debug(f"Trả về {len(products_list)} sản phẩm: {json.dumps(products_list, ensure_ascii=False)}")
            return jsonify(products_list)
        except Exception as e:
            logger.error(f"Lỗi khi lấy sản phẩm: {str(e)}")
            return jsonify({"error": str(e)}), 500

    def get_product_by_id(self, product_id):
            logger.debug(f"Fetching product by ID: {product_id}")
            try:
                product, sizes = ProductModel.get_product_by_id(product_id)
                if not product:
                    logger.warning(f"Product not found: {product_id}")
                    return jsonify({'success': False, 'message': 'Sản phẩm không tồn tại'}), 404
            
                sizes_list = [{"size": row['size'], "price": row['price'], "size_id": row['size_id']} for row in sizes]
                logger.info(f"Product {product_id} fetched successfully")
                return jsonify({
                    'success': True,
                    'product': {
                        'product_id': product['product_id'],
                        'product_name': product['product_name'],
                        'category': product['category'],
                        'stock': product['stock'],
                        'description': product['description'] or '',
                        'image_url': product['image_url'] or '/static/Upload/default.jpg',
                        'image_url_2': product['image_url_2'] or '/static/Upload/default.jpg',
                        'discount': product['discount'] or 0
                    },
                    'sizes': sizes_list
                }), 200
            except sqlite3.Error as e:
                logger.error(f"Database error fetching product {product_id}: {str(e)}")
                return jsonify({'success': False, 'message': f'Lỗi cơ sở dữ liệu: {str(e)}'}), 500
            except Exception as e:
                logger.error(f"Unexpected error fetching product {product_id}: {str(e)}")
                return jsonify({'success': False, 'message': f'Lỗi server: {str(e)}'}), 500

    def get_top10_products(self):
        try:
            products_list = ProductModel.get_top10_products()
            logger.debug(f"Trả về {len(products_list)} sản phẩm bán chạy nhất")
            return jsonify(products_list), 200
        except sqlite3.Error as e:
            logger.error(f"Lỗi cơ sở dữ liệu khi lấy top 10 sản phẩm: {str(e)}")
            return jsonify({"error": f"Lỗi cơ sở dữ liệu: {str(e)}"}), 500
        except Exception as e:
            logger.error(f"Lỗi khi lấy top 10 sản phẩm: {str(e)}")
            return jsonify({"error": str(e)}), 500