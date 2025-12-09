import sqlite3
from utils.db import get_db_connection
import logging

logger = logging.getLogger(__name__)

class Favorites:
    @staticmethod
    def get_favorites(admin_id):
        logger.debug(f"Fetching favorites for admin_id={admin_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT p.product_id, p.product_name, p.image_url,
                       (SELECT ps.price FROM product_size ps WHERE ps.product_id = p.product_id AND ps.size = 'M' LIMIT 1) as price_m,
                       (SELECT CAST(AVG(r.rating) AS REAL)
                        FROM reviews r
                        JOIN orders o ON o.order_id = r.order_id
                        WHERE r.product_id = p.product_id AND o.status = 'Delivered') as avg_rating
                FROM favorites f
                JOIN products p ON f.product_id = p.product_id
                WHERE f.admin_id = ?
            """, (admin_id,))
            favorites = []
            for row in cursor.fetchall():
                product = dict(row)
                product['avg_rating'] = float(product['avg_rating']) if product['avg_rating'] is not None else 0.0
                favorites.append(product)
            logger.debug(f"Favorites retrieved: {len(favorites)} items")
            return favorites
        except sqlite3.Error as e:
            logger.error(f"Database error in get_favorites: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        finally:
            conn.close()

    @staticmethod
    def add_favorite(admin_id, product_id):
        logger.debug(f"Adding favorite: admin_id={admin_id}, product_id={product_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT product_id FROM products WHERE product_id = ?', (product_id,))
            if not cursor.fetchone():
                logger.error(f"Product not found: product_id={product_id}")
                raise ValueError("Product not found")
            cursor.execute('SELECT favorite_id FROM favorites WHERE admin_id = ? AND product_id = ?', (admin_id, product_id))
            if cursor.fetchone():
                logger.debug(f"Product already in favorites: product_id={product_id}")
                raise ValueError("Product already in favorites")
            cursor.execute("""
                INSERT INTO favorites (admin_id, product_id)
                VALUES (?, ?)
            """, (admin_id, product_id))
            conn.commit()
            logger.info(f"Favorite added: product_id={product_id}")
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error in add_favorite: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        except ValueError as e:
            raise e
        finally:
            conn.close()

    @staticmethod
    def remove_favorite(admin_id, product_id):
        logger.debug(f"Removing favorite: admin_id={admin_id}, product_id={product_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT favorite_id FROM favorites WHERE admin_id = ? AND product_id = ?', (admin_id, product_id))
            if not cursor.fetchone():
                logger.debug(f"Product not in favorites: product_id={product_id}")
                raise ValueError("Product not in favorites")
            cursor.execute("""
                DELETE FROM favorites
                WHERE admin_id = ? AND product_id = ?
            """, (admin_id, product_id))
            conn.commit()
            logger.info(f"Favorite removed: product_id={product_id}")
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error in remove_favorite: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        except ValueError as e:
            raise e
        finally:
            conn.close()