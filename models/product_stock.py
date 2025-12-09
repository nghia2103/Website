# models/product_stock.py
import sqlite3
from utils.db import get_db_connection
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ProductStock:
    @staticmethod
    def get_stock_items():
        logger.debug("Fetching stock items")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT si.stock_item_id, si.item_name, si.category, si.stock_quantity, si.store_id, si.last_updated, s.store_name
                FROM stock_items si
                JOIN stores s ON si.store_id = s.store_id
                ORDER BY si.last_updated DESC
            """)
            stock_items = []
            for row in cursor:
                last_updated = datetime.strptime(row['last_updated'], '%Y-%m-%d %H:%M:%S')
                formatted_last_updated = last_updated.strftime('%b %d, %Y - %I:%M %p')
                stock_items.append({
                    'stock_item_id': row['stock_item_id'],
                    'item_name': row['item_name'],
                    'category': row['category'],
                    'stock_quantity': row['stock_quantity'],
                    'store_id': row['store_id'],
                    'store_name': row['store_name'],
                    'last_updated': row['last_updated'],
                    'formatted_last_updated': formatted_last_updated
                })
            cursor.execute('SELECT store_id, store_name FROM stores')
            stores = [{'store_id': row['store_id'], 'store_name': row['store_name']} for row in cursor.fetchall()]
            logger.debug(f"Retrieved {len(stock_items)} stock items")
            return stock_items, stores
        except sqlite3.Error as e:
            logger.error(f"Database error in get_stock_items: {str(e)}")
            raise Exception(f"Lỗi cơ sở dữ liệu: {str(e)}")
        finally:
            conn.close()

    # Trong models/product_stock.py
# Chỉ thay phương thức add_stock_item trong class ProductStock
    @staticmethod
    def add_stock_item(item_name, category, stock_quantity, store_id):
        logger.debug(f"Adding stock item with item_name={item_name}, category={category}, stock_quantity={stock_quantity}, store_id={store_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
        # Kiểm tra store_id tồn tại
            cursor.execute("SELECT store_id, store_name FROM stores WHERE store_id = ?", (store_id,))
            store_row = cursor.fetchone()
            if not store_row:
                logger.warning(f"Store ID {store_id} not found in stores table")
                raise Exception(f"Store ID {store_id} không tồn tại")
            store_name = store_row['store_name']
            logger.debug(f"Found store: store_id={store_id}, store_name={store_name}")

        # Thêm stock item
            cursor.execute("""
                INSERT INTO stock_items (item_name, category, stock_quantity, store_id, last_updated)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (item_name, category, stock_quantity, store_id))
            conn.commit()  # Commit ngay sau khi thêm
            logger.debug("Stock item inserted and committed")

        # Lấy stock_item_id vừa thêm
            cursor.execute("SELECT MAX(stock_item_id) AS stock_item_id FROM stock_items WHERE item_name = ? AND store_id = ?", (item_name, store_id))
            row_id = cursor.fetchone()
            if not row_id:
                logger.error("Failed to retrieve stock_item_id after insertion")
                raise Exception("Không thể lấy stock_item_id vừa thêm")
            stock_item_id = row_id['stock_item_id']
            logger.debug(f"Inserted stock item with ID: {stock_item_id}")

        # Kiểm tra bản ghi vừa thêm
            cursor.execute("SELECT stock_item_id, item_name, category, stock_quantity, store_id, last_updated FROM stock_items WHERE stock_item_id = ?", (stock_item_id,))
            row = cursor.fetchone()
            if not row:
                logger.error(f"Failed to retrieve stock item {stock_item_id} from stock_items table")
                cursor.execute("SELECT * FROM stock_items WHERE item_name = ? AND store_id = ?", (item_name, store_id))
                debug_row = cursor.fetchone()
                logger.debug(f"Debug: Found item with item_name={item_name}, store_id={store_id}: {debug_row}")
                raise Exception("Không thể lấy thông tin sản phẩm vừa thêm từ bảng stock_items")

            last_updated = datetime.strptime(row['last_updated'], '%Y-%m-%d %H:%M:%S')
            formatted_last_updated = last_updated.strftime('%b %d, %Y - %I:%M %p')
            stock_item = {
                'stock_item_id': row['stock_item_id'],
                'item_name': row['item_name'],
                'category': row['category'],
                'stock_quantity': row['stock_quantity'],
                'store_id': row['store_id'],
                'store_name': store_name,  # Lấy từ truy vấn stores trước đó
                'last_updated': row['last_updated'],
                'formatted_last_updated': formatted_last_updated
            }
            logger.info(f"Stock item {stock_item_id} added successfully")
            return stock_item
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error in add_stock_item: {str(e)}")
            raise e
        except Exception as e:
            conn.rollback()
            logger.error(f"Unexpected error in add_stock_item: {str(e)}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def edit_stock_item(stock_item_id, item_name, category, stock_quantity, store_id):
        logger.debug(f"Editing stock item: stock_item_id={stock_item_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE stock_items
                SET item_name = ?, category = ?, stock_quantity = ?, store_id = ?, last_updated = datetime('now')
                WHERE stock_item_id = ?
            """, (item_name, category, stock_quantity, store_id, stock_item_id))
            if cursor.rowcount == 0:
                conn.close()
                return None
            
            conn.commit()
            cursor.execute("""
                SELECT si.stock_item_id, si.item_name, si.category, si.stock_quantity, si.store_id, si.last_updated, s.store_name
                FROM stock_items si
                JOIN stores s ON si.store_id = s.store_id
                WHERE si.stock_item_id = ?
            """, (stock_item_id,))
            row = cursor.fetchone()
            if not row:
                raise Exception("Không thể lấy thông tin sản phẩm vừa sửa")
            
            last_updated = datetime.strptime(row['last_updated'], '%Y-%m-%d %H:%M:%S')
            formatted_last_updated = last_updated.strftime('%b %d, %Y - %I:%M %p')
            stock_item = {
                'stock_item_id': row['stock_item_id'],
                'item_name': row['item_name'],
                'category': row['category'],
                'stock_quantity': row['stock_quantity'],
                'store_id': row['store_id'],
                'store_name': row['store_name'],
                'last_updated': row['last_updated'],
                'formatted_last_updated': formatted_last_updated
            }
            logger.info(f"Stock item {stock_item_id} updated successfully")
            return stock_item
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error in edit_stock_item: {str(e)}")
            raise e
        finally:
            conn.close()

    @staticmethod
    def delete_stock_item(stock_item_id):
        logger.debug(f"Deleting stock item: stock_item_id={stock_item_id}")
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT stock_item_id FROM stock_items WHERE stock_item_id = ?", (stock_item_id,))
            if not cursor.fetchone():
                conn.close()
                return False
            
            cursor.execute("DELETE FROM stock_items WHERE stock_item_id = ?", (stock_item_id,))
            conn.commit()
            logger.info(f"Stock item {stock_item_id} deleted successfully")
            return True
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error in delete_stock_item: {str(e)}")
            raise e
        finally:
            conn.close()