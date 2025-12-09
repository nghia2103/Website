import sqlite3
from utils.db import get_db_connection
import logging

logger = logging.getLogger(__name__)

class ProductModel:
    @staticmethod
    def get_all_products():
        conn = get_db_connection()
        products = conn.execute('''
            SELECT p.*, ps.size, ps.price, ps.size_id
            FROM products p
            LEFT JOIN product_size ps ON p.product_id = ps.product_id
        ''').fetchall()
        conn.close()
        return products

    @staticmethod
    def get_product_by_id(product_id):
        conn = get_db_connection()
        product = conn.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
        sizes = conn.execute("SELECT size, price, size_id FROM product_size WHERE product_id = ?", (product_id,)).fetchall()
        conn.close()
        return product, sizes

    @staticmethod
    def get_top10_products():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                p.product_id, 
                p.product_name, 
                p.stock, 
                p.description, 
                p.image_url, 
                p.image_url_2, 
                p.discount, 
                p.category,
                SUM(od.quantity) as total_sold
            FROM products p
            JOIN order_details od ON p.product_id = od.product_id
            JOIN orders o ON od.order_id = o.order_id
            WHERE o.status = 'Delivered'
            GROUP BY p.product_id
            ORDER BY total_sold DESC
            LIMIT 10
        ''')
        top_products = [dict(row) for row in cursor.fetchall()]
        products_list = []
        for product in top_products:
            cursor.execute('''
                SELECT size_id, size, price
                FROM product_size
                WHERE product_id = ?
            ''', (product['product_id'],))
            sizes = [{'size_id': row['size_id'], 'size': row['size'], 'price': row['price']} for row in cursor.fetchall()]
            product['sizes'] = sizes
            products_list.append(product)
        conn.close()
        return products_list

    @staticmethod
    def get_admin_products(admin_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT p.product_id, p.product_name, p.stock, p.description, p.image_url,
                       p.discount, p.category, 
                       CASE WHEN f.favorite_id IS NOT NULL THEN 1 ELSE 0 END as favorited,
                       (SELECT ps.price FROM product_size ps WHERE ps.product_id = p.product_id AND ps.size = 'M' LIMIT 1) as price_m,
                       (SELECT ps.price FROM product_size ps WHERE ps.product_id = p.product_id AND ps.size = 'S' LIMIT 1) as price_s,
                       (SELECT ps.price FROM product_size ps WHERE ps.product_id = p.product_id AND ps.size = 'L' LIMIT 1) as price_l,
                       (SELECT CAST(AVG(r.rating) AS REAL)
                        FROM reviews r
                        JOIN orders o ON o.order_id = r.order_id
                        WHERE r.product_id = p.product_id AND o.status = 'Delivered') as avg_rating
                FROM products p
                LEFT JOIN favorites f ON p.product_id = f.product_id AND f.admin_id = ?
            """, (admin_id,))
            products = [dict(row) for row in cursor.fetchall()]
            return products
        except sqlite3.Error as e:
            logger.error(f"SQLite error in get_admin_products: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        finally:
            conn.close()