import sqlite3
from utils.db import get_db_connection

class ProductAdmin:
    @staticmethod
    def get_admin_products(admin_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.product_id, p.product_name, p.stock, p.description, p.image_url,
                   p.discount, p.category, 
                   CASE WHEN f.favorite_id IS NOT NULL THEN 1 ELSE 0 END as favorited,
                   (SELECT ps.price FROM product_size ps WHERE ps.product_id = p.product_id AND ps.size = 'M' LIMIT 1) as price_m,
                   (SELECT CAST(AVG(r.rating) AS REAL)
                    FROM reviews r
                    JOIN orders o ON o.order_id = r.order_id
                    WHERE r.product_id = p.product_id AND o.status = 'Delivered') as avg_rating
            FROM products p
            LEFT JOIN favorites f ON p.product_id = f.product_id AND f.admin_id = ?
        """, (admin_id,))
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return products

    @staticmethod
    def get_product_by_id(product_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT product_id, product_name, stock, description, image_url, image_url_2, discount, category
            FROM products
            WHERE product_id = ?
        """, (product_id,))
        product = cursor.fetchone()
        cursor.execute("""
            SELECT size_id, size, price
            FROM product_size
            WHERE product_id = ?
        """, (product_id,))
        sizes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return dict(product) if product else None, sizes

    @staticmethod
    def get_product_images(product_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT image_url, image_url_2 FROM products WHERE product_id = ?", (product_id,))
        product = cursor.fetchone()
        conn.close()
        return product['image_url'] if product else None, product['image_url_2'] if product else None

    @staticmethod
    def add_product(product_name, stock, description, discount, category, sizes, image_url, image_url_2):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO products (product_id, product_name, stock, description, image_url, image_url_2, discount, category)
                VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)
            """, (product_name, stock, description, image_url, image_url_2, discount, category))
            cursor.execute("SELECT product_id FROM products WHERE rowid = last_insert_rowid()")
            product_id = cursor.fetchone()['product_id']
            price_m_value = None
            for size, price in sizes:
                cursor.execute("""
                    INSERT INTO product_size (size_id, product_id, size, price)
                    VALUES (NULL, ?, ?, ?)
                """, (product_id, size, price))
                if size == 'M':
                    price_m_value = price
            conn.commit()
            return product_id, price_m_value
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def edit_product(product_id, product_name, stock, description, discount, category, sizes, image_url, image_url_2):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT product_id FROM products WHERE product_id = ?", (product_id,))
            if not cursor.fetchone():
                return None
            cursor.execute("""
                UPDATE products
                SET product_name = ?, stock = ?, description = ?, image_url = ?, image_url_2 = ?, discount = ?, category = ?
                WHERE product_id = ?
            """, (product_name, stock, description, image_url, image_url_2, discount, category, product_id))
            cursor.execute("SELECT size, size_id FROM product_size WHERE product_id = ?", (product_id,))
            existing_sizes = {row['size']: row['size_id'] for row in cursor.fetchall()}
            submitted_sizes = {size for size, _ in sizes}
            sizes_to_delete = set(existing_sizes.keys()) - submitted_sizes
            for size in sizes_to_delete:
                size_id = existing_sizes[size]
                cursor.execute("SELECT 1 FROM order_details WHERE size_id = ?", (size_id,))
                if cursor.fetchone():
                    raise Exception(f'Không thể xóa kích thước {size} vì đã được sử dụng trong đơn hàng')
                cursor.execute("SELECT 1 FROM cart WHERE size_id = ?", (size_id,))
                if cursor.fetchone():
                    raise Exception(f'Không thể xóa kích thước {size} vì đang có trong giỏ hàng')
                cursor.execute("DELETE FROM product_size WHERE size_id = ?", (size_id,))
            price_m_value = None
            for size, price in sizes:
                if size in existing_sizes:
                    cursor.execute("""
                        UPDATE product_size
                        SET price = ?
                        WHERE product_id = ? AND size = ?
                    """, (price, product_id, size))
                else:
                    cursor.execute("""
                        INSERT INTO product_size (size_id, product_id, size, price)
                        VALUES (NULL, ?, ?, ?)
                    """, (product_id, size, price))
                if size == 'M':
                    price_m_value = price
            cursor.execute("""
                SELECT CAST(AVG(r.rating) AS REAL) as avg_rating
                FROM reviews r
                JOIN orders o ON o.order_id = r.order_id
                WHERE r.product_id = ? AND o.status = 'Delivered'
            """, (product_id,))
            avg_rating = cursor.fetchone()['avg_rating'] or 0.0
            cursor.execute("""
                SELECT product_id, product_name, stock, description, image_url, image_url_2, discount, category
                FROM products
                WHERE product_id = ?
            """, (product_id,))
            product = cursor.fetchone()
            conn.commit()
            product_dict = dict(product)
            product_dict['avg_rating'] = avg_rating
            return product_dict, price_m_value
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_product(product_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT product_id FROM products WHERE product_id = ?', (product_id,))
            if not cursor.fetchone():
                return False
            cursor.execute('SELECT order_detail_id FROM order_details WHERE product_id = ?', (product_id,))
            if cursor.fetchone():
                return False
            cursor.execute('DELETE FROM product_size WHERE product_id = ?', (product_id,))
            cursor.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
            conn.commit()
            return True
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def add_favorite(admin_id, product_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT product_id FROM products WHERE product_id = ?', (product_id,))
            if not cursor.fetchone():
                return False
            cursor.execute('SELECT favorite_id FROM favorites WHERE admin_id = ? AND product_id = ?', (admin_id, product_id))
            if cursor.fetchone():
                return False
            cursor.execute("""
                INSERT INTO favorites (admin_id, product_id)
                VALUES (?, ?)
            """, (admin_id, product_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def remove_favorite(admin_id, product_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT favorite_id FROM favorites WHERE admin_id = ? AND product_id = ?', (admin_id, product_id))
            if not cursor.fetchone():
                return False
            cursor.execute("""
                DELETE FROM favorites
                WHERE admin_id = ? AND product_id = ?
            """, (admin_id, product_id))
            conn.commit()
            return True
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()