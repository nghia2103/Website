-- Bật hỗ trợ FOREIGN KEY
PRAGMA foreign_keys = ON;

-- Xóa bảng theo thứ tự phụ thuộc ngược
DROP TABLE IF EXISTS order_details;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS stock_items;
DROP TABLE IF EXISTS favorites;
DROP TABLE IF EXISTS product_size;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS stores;
DROP TABLE IF EXISTS managers;
DROP TABLE IF EXISTS admins;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS user_sequence;
DROP TABLE IF EXISTS admin_sequence;
DROP TABLE IF EXISTS manager_sequence;
DROP TABLE IF EXISTS store_sequence;
DROP TABLE IF EXISTS product_sequence;
DROP TABLE IF EXISTS payment_sequence;
DROP TABLE IF EXISTS order_sequence;
DROP TABLE IF EXISTS order_detail_sequence;
DROP TABLE IF EXISTS message_sequence;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS stock_item_sequence;
DROP TABLE IF EXISTS favorite_sequence;
DROP TABLE IF EXISTS size_sequence;
DROP TABLE IF EXISTS cart;
DROP TABLE IF EXISTS cart_sequence;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS event_sequence;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS review_sequence;
DROP TABLE IF EXISTS addresses;
DROP TABLE IF EXISTS address_sequence;

-- Bảng khách hàng (users)
CREATE TABLE users (
    customer_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    phone TEXT,
    birthdate TEXT,
    user_add TEXT,
    user_img TEXT
);

-- Sequence và trigger cho customer_id (KH1, KH2,...)
CREATE TABLE user_sequence (seq INTEGER);
INSERT INTO user_sequence (seq) VALUES (0);
CREATE TRIGGER user_id_trigger 
AFTER INSERT ON users 
FOR EACH ROW 
WHEN NEW.customer_id IS NULL 
BEGIN 
    UPDATE user_sequence SET seq = seq + 1;
    UPDATE users SET customer_id = 'KH' || (SELECT seq FROM user_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;

-- Bảng admin (admins)
CREATE TABLE admins (
    admin_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    phone TEXT,
    admin_img TEXT
);

-- Sequence và trigger cho admin_id (AD1, AD2,...)
CREATE TABLE admin_sequence (seq INTEGER);
INSERT INTO admin_sequence (seq) VALUES (0);
CREATE TRIGGER admin_id_trigger 
AFTER INSERT ON admins 
FOR EACH ROW 
WHEN NEW.admin_id IS NULL 
BEGIN 
    UPDATE admin_sequence SET seq = seq + 1;
    UPDATE admins SET admin_id = 'AD' || (SELECT seq FROM admin_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;

-- Bảng quản lý (managers)
CREATE TABLE managers (
    manager_id TEXT PRIMARY KEY,
    manager_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    address TEXT NOT NULL
);

-- Sequence và trigger cho manager_id (MG1, MG2,...)
CREATE TABLE manager_sequence (seq INTEGER);
INSERT INTO manager_sequence (seq) VALUES (0);
CREATE TRIGGER manager_id_trigger 
AFTER INSERT ON managers 
FOR EACH ROW 
WHEN NEW.manager_id IS NULL 
BEGIN 
    UPDATE manager_sequence SET seq = seq + 1;
    UPDATE managers SET manager_id = 'MG' || (SELECT seq FROM manager_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;

-- Bảng cửa hàng (stores)
CREATE TABLE stores (
    store_id TEXT PRIMARY KEY,
    store_name TEXT NOT NULL,
    address TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL,
    manager_id TEXT NOT NULL,
    FOREIGN KEY (manager_id) REFERENCES managers(manager_id) ON DELETE RESTRICT
);

-- Sequence và trigger cho store_id (ST1, ST2,...)
CREATE TABLE store_sequence (seq INTEGER);
INSERT INTO store_sequence (seq) VALUES (0);
CREATE TRIGGER store_id_trigger 
AFTER INSERT ON stores 
FOR EACH ROW 
WHEN NEW.store_id IS NULL 
BEGIN 
    UPDATE store_sequence SET seq = seq + 1;
    UPDATE stores SET store_id = 'ST' || (SELECT seq FROM store_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;

-- Bảng sản phẩm (products)
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    stock INTEGER NOT NULL CHECK(stock >= 0),
    description TEXT,
    discount INTEGER,
    category TEXT NOT NULL,
    image_url TEXT,
    image_url_2 TEXT
);

-- Sequence và trigger cho product_id (PR1, PR2,...)
CREATE TABLE product_sequence (seq INTEGER);
INSERT INTO product_sequence (seq) VALUES (0);
CREATE TRIGGER product_id_trigger 
AFTER INSERT ON products 
FOR EACH ROW 
WHEN NEW.product_id IS NULL 
BEGIN 
    UPDATE product_sequence SET seq = seq + 1;
    UPDATE products SET product_id = 'PR' || (SELECT seq FROM product_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;

-- Bảng kích thước sản phẩm (product_size)
CREATE TABLE product_size (
    size_id TEXT PRIMARY KEY,
    product_id TEXT,
    size TEXT NOT NULL CHECK(size IN ('S','M','L')),
    price REAL NOT NULL CHECK (price >= 0),
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

-- Sequence và trigger cho size_id (SZ1, SZ2,...)
CREATE TABLE size_sequence (seq INTEGER);
INSERT INTO size_sequence (seq) VALUES (0);
CREATE TRIGGER size_id_trigger 
AFTER INSERT ON product_size 
FOR EACH ROW 
WHEN NEW.size_id IS NULL 
BEGIN 
    UPDATE size_sequence SET seq = seq + 1;
    UPDATE product_size SET size_id = 'SZ' || (SELECT seq FROM size_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;

-- Bảng yêu thích (favorites)
CREATE TABLE favorites (
    favorite_id TEXT PRIMARY KEY,
    admin_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    FOREIGN KEY (admin_id) REFERENCES admins(admin_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

-- Sequence và trigger cho favorite_id (FA1, FA2,...)
CREATE TABLE favorite_sequence (seq INTEGER);
INSERT INTO favorite_sequence (seq) VALUES (0);
CREATE TRIGGER favorite_id_trigger 
AFTER INSERT ON favorites 
FOR EACH ROW 
WHEN NEW.favorite_id IS NULL 
BEGIN 
    UPDATE favorite_sequence SET seq = seq + 1;
    UPDATE favorites SET favorite_id = 'FA' || (SELECT seq FROM favorite_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;

-- Bảng hàng hóa kho (stock_items)
CREATE TABLE stock_items (
    stock_item_id TEXT PRIMARY KEY,
    item_name TEXT NOT NULL,
    category TEXT,
    stock_quantity INTEGER NOT NULL CHECK(stock_quantity >= 0),
    store_id TEXT NOT NULL,
    last_updated TEXT NOT NULL,
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE RESTRICT
);

-- Sequence và trigger cho stock_item_id (STK1, STK2,...)
CREATE TABLE stock_item_sequence (seq INTEGER);
INSERT INTO stock_item_sequence (seq) VALUES (0);
CREATE TRIGGER stock_item_id_trigger 
AFTER INSERT ON stock_items 
FOR EACH ROW 
WHEN NEW.stock_item_id IS NULL 
BEGIN 
    UPDATE stock_item_sequence SET seq = seq + 1;
    UPDATE stock_items SET stock_item_id = 'STK' || (SELECT seq FROM stock_item_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;

-- Bảng giỏ hàng (cart)
CREATE TABLE cart (
    cart_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    size_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users(customer_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (size_id) REFERENCES product_size(size_id)
);

-- Sequence và trigger cho cart_id (CA1, CA2,...)
CREATE TABLE cart_sequence (seq INTEGER);
INSERT INTO cart_sequence (seq) VALUES (0);
CREATE TRIGGER cart_id_trigger 
AFTER INSERT ON cart 
FOR EACH ROW 
WHEN NEW.cart_id IS NULL 
BEGIN 
    UPDATE cart_sequence SET seq = seq + 1;
    UPDATE cart SET cart_id = 'CA' || (SELECT seq FROM cart_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;

-- Bảng đơn hàng (orders)
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Pending',
    store_id TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES users(customer_id) ON DELETE RESTRICT,
    FOREIGN KEY (store_id) REFERENCES stores(store_id) ON DELETE RESTRICT
);

-- Sequence và trigger cho order_id (OR1, OR2,...)
CREATE TABLE order_sequence (seq INTEGER);
INSERT INTO order_sequence (seq) VALUES (0);
CREATE TRIGGER order_id_trigger 
AFTER INSERT ON orders 
FOR EACH ROW 
WHEN NEW.order_id IS NULL 
BEGIN 
    UPDATE order_sequence SET seq = seq + 1;
    UPDATE orders SET order_id = 'OR' || (SELECT seq FROM order_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;

-- Bảng chi tiết đơn hàng (order_details)
CREATE TABLE order_details (
    order_detail_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    size_id TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price REAL CHECK(unit_price >= 0),
    total_price REAL CHECK(total_price >= 0),
    FOREIGN KEY (size_id) REFERENCES product_size(size_id) ON DELETE RESTRICT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE RESTRICT
);

-- Sequence và trigger cho order_detail_id (OD1, OD2,...)
CREATE TABLE order_detail_sequence (seq INTEGER);
INSERT INTO order_detail_sequence (seq) VALUES (0);
CREATE TRIGGER order_detail_id_trigger 
AFTER INSERT ON order_details 
FOR EACH ROW 
WHEN NEW.order_detail_id IS NULL 
BEGIN 
    UPDATE order_detail_sequence SET seq = seq + 1;
    UPDATE order_details SET order_detail_id = 'OD' || (SELECT seq FROM order_detail_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;

-- Bảng thanh toán (payments)
CREATE TABLE payments (
    payment_id TEXT PRIMARY KEY,
    payment_date TEXT NOT NULL,
    payment_method TEXT NOT NULL,
    order_id TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount >= 0),
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);

-- Sequence và trigger cho payment_id (PM1, PM2,...)
CREATE TABLE payment_sequence (seq INTEGER);
INSERT INTO payment_sequence (seq) VALUES (0);
CREATE TRIGGER payment_id_trigger 
AFTER INSERT ON payments 
FOR EACH ROW 
WHEN NEW.payment_id IS NULL 
BEGIN 
    UPDATE payment_sequence SET seq = seq + 1;
    UPDATE payments SET payment_id = 'PM' || (SELECT seq FROM payment_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;

-- Bảng tin nhắn giữa user và admin
CREATE TABLE messages (
    message_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    admin_id TEXT, -- Bỏ NOT NULL
    direction TEXT NOT NULL CHECK(direction IN ('user_to_admin', 'admin_to_user')),
    content TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
    is_read INTEGER DEFAULT 0 CHECK(is_read IN (0, 1)),
    FOREIGN KEY (user_id) REFERENCES users(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (admin_id) REFERENCES admins(admin_id) ON DELETE CASCADE
);

-- Sequence và trigger cho message_id (MS1, MS2,...)
DROP TABLE IF EXISTS message_sequence;
CREATE TABLE message_sequence (seq INTEGER);
INSERT INTO message_sequence (seq) VALUES (0);
CREATE TRIGGER message_id_trigger 
AFTER INSERT ON messages 
FOR EACH ROW 
WHEN NEW.message_id IS NULL 
BEGIN 
    UPDATE message_sequence SET seq = seq + 1;
    UPDATE messages SET message_id = 'MS' || (SELECT seq FROM message_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;


CREATE TABLE user_admin_assignments (
    user_id TEXT PRIMARY KEY,
    admin_id TEXT NOT NULL,
    assigned_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (admin_id) REFERENCES admins(admin_id) ON DELETE CASCADE
);

-- Bảng sự kiện (events)
CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    event_name TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    admin_id TEXT NOT NULL,
    adminname TEXT NOT NULL,
    color VARCHAR(50),
    FOREIGN KEY (admin_id) REFERENCES admins(admin_id) ON DELETE CASCADE
);

-- Sequence và trigger cho event_id (EV1, EV2,...)
CREATE TABLE event_sequence (seq INTEGER);
INSERT INTO event_sequence (seq) VALUES (0);
CREATE TRIGGER event_id_trigger 
AFTER INSERT ON events 
FOR EACH ROW 
WHEN NEW.event_id IS NULL 
BEGIN 
    UPDATE event_sequence SET seq = seq + 1;
    UPDATE events SET event_id = 'EV' || (SELECT seq FROM event_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;

-- Bảng đánh giá (reviews)
CREATE TABLE reviews (
    review_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    size_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
    comment TEXT,
    review_img TEXT,
    review_date TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (customer_id) REFERENCES users(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    FOREIGN KEY (size_id) REFERENCES product_size(size_id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    UNIQUE(customer_id, product_id, size_id, order_id)
);

-- Sequence và trigger cho review_id (RV1, RV2,...)
CREATE TABLE review_sequence (seq INTEGER);
INSERT INTO review_sequence (seq) VALUES (0);
CREATE TRIGGER review_id_trigger 
AFTER INSERT ON reviews 
FOR EACH ROW 
WHEN NEW.review_id IS NULL 
BEGIN 
    UPDATE review_sequence SET seq = seq + 1;
    UPDATE reviews SET review_id = 'RV' || (SELECT seq FROM review_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;

-- Bảng địa chỉ (addresses)
CREATE TABLE addresses (
    address_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    address TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (customer_id) REFERENCES users(customer_id) ON DELETE CASCADE
);

-- Sequence và trigger cho address_id (AD1, AD2,...)
CREATE TABLE address_sequence (seq INTEGER);
INSERT INTO address_sequence (seq) VALUES (0);
CREATE TRIGGER address_id_trigger 
AFTER INSERT ON addresses 
FOR EACH ROW 
WHEN NEW.address_id IS NULL 
BEGIN 
    UPDATE address_sequence SET seq = seq + 1;
    UPDATE addresses SET address_id = 'AD' || (SELECT seq FROM address_sequence LIMIT 1) WHERE rowid = NEW.rowid;
END;

-- Trigger để đồng bộ user_add trong bảng users với địa chỉ mặc định
CREATE TRIGGER update_user_add_insert
AFTER INSERT ON addresses
FOR EACH ROW
WHEN NEW.is_default = TRUE
BEGIN
    -- Đặt is_default = FALSE cho tất cả địa chỉ khác của cùng customer_id
    UPDATE addresses
    SET is_default = FALSE
    WHERE customer_id = NEW.customer_id
    AND address_id != NEW.address_id;
    
    -- Cập nhật user_add trong bảng users để phản ánh địa chỉ mặc định mới
    UPDATE users
    SET user_add = NEW.address
    WHERE customer_id = NEW.customer_id;
END;
-- DROP TRIGGER IF EXISTS update_user_add;
-- Trigger cho UPDATE để đảm bảo chỉ một địa chỉ mỗi customer_id có is_default = TRUE
CREATE TRIGGER update_user_add_update
AFTER UPDATE OF is_default ON addresses
FOR EACH ROW
WHEN NEW.is_default = TRUE
BEGIN
    -- Đặt is_default = FALSE cho tất cả địa chỉ khác của cùng customer_id
    UPDATE addresses
    SET is_default = FALSE
    WHERE customer_id = NEW.customer_id
    AND address_id != NEW.address_id;
    
    -- Cập nhật user_add trong bảng users để phản ánh địa chỉ mặc định mới
    UPDATE users
    SET user_add = NEW.address
    WHERE customer_id = NEW.customer_id;
END;
-- Thêm dữ liệu mẫu
INSERT OR IGNORE INTO users (customer_id, first_name, last_name, email, password, user_add) VALUES 
    (NULL, 'John', 'Doe', 'john@example.com', 'password', '123 Main St, Hanoi'),
    (NULL, 'Jane', 'Smith', 'jane.smith@example.com', 'password', '456 North Rd, Hanoi'),
    (NULL, 'Michael', 'Brown', 'michael.brown@example.com', 'password', NULL),
    (NULL, 'Emily', 'Davis', 'emily.davis@example.com', 'password', NULL),
    (NULL, 'David', 'Wilson', 'david.wilson@example.com', 'password', NULL),
    (NULL, 'Sarah', 'Taylor', 'sarah.taylor@example.com', 'password', NULL),
    (NULL, 'James', 'Anderson', 'james.anderson@example.com', 'password', NULL),
    (NULL, 'Laura', 'Thomas', 'laura.thomas@example.com', 'password', NULL),
    (NULL, 'Tom', 'Harris', 'tom.harris@example.com', 'password', NULL),
    (NULL, 'Anna', 'Lee', 'anna.lee@example.com', 'password', NULL);

INSERT OR IGNORE INTO admins (admin_id, first_name, last_name, email, password, phone) VALUES 
    (NULL, 'Alice', 'Nguyen', 'alice.nguyen@example.com', 'password', '0912345678'),
    (NULL, 'Bob', 'Tran', 'bob.tran@example.com', 'password', '0987654321'),
    (NULL, 'Charlie', 'Le', 'charlie.le@example.com', 'password', '0932123456'),
    (NULL, 'Diana', 'Pham', 'diana.pham@example.com', 'password', '0923456789'),
    (NULL, 'Ethan', 'Hoang', 'ethan.hoang@example.com', 'password', '0967890123'),
    (NULL, 'Fiona', 'Vo', 'fiona.vo@example.com', 'password', '0971234567'),
    (NULL, 'George', 'Bui', 'george.bui@example.com', 'password', '0945678901'),
    (NULL, 'Hannah', 'Do', 'hannah.do@example.com', 'password', '0956789012'),
    (NULL, 'Ivan', 'Ngo', 'ivan.ngo@example.com', 'password', '0934567890'),
    (NULL, 'Julia', 'Dang', 'julia.dang@example.com', 'password', '0909876543');

INSERT OR IGNORE INTO managers (manager_id, manager_name, email, address) VALUES 
    (NULL, 'Manager One', 'manager1@example.com', '123 Manager St'),
    (NULL, 'Manager Two', 'manager2@example.com', '456 Manager Rd'),
    (NULL, 'Manager Three', 'manager3@example.com', '789 Manager Ave'),
    (NULL, 'Manager Four', 'manager4@example.com', '321 Manager Blvd'),
    (NULL, 'Manager Five', 'manager5@example.com', '654 Manager Ln'),
    (NULL, 'Manager Six', 'manager6@example.com', '987 Manager Dr'),
    (NULL, 'Manager Seven', 'manager7@example.com', '111 Manager Ct'),
    (NULL, 'Manager Eight', 'manager8@example.com', '222 Manager Pl'),
    (NULL, 'Manager Nine', 'manager9@example.com', '333 Manager Way');

INSERT OR IGNORE INTO stores (store_id, store_name, address, phone, email, manager_id) VALUES 
    (NULL, 'Central Market', '123 Main St, Hanoi', '0123456789', 'central@example.com', (SELECT manager_id FROM managers WHERE manager_name = 'Manager One')),
    (NULL, 'North Plaza', '456 North Rd, Hanoi', '0987654321', 'north@example.com', (SELECT manager_id FROM managers WHERE manager_name = 'Manager Two')),
    (NULL, 'East Side Mall', '789 East Blvd, Hanoi', '0111222333', 'east@example.com', (SELECT manager_id FROM managers WHERE manager_name = 'Manager Three')),
    (NULL, 'West End Store', '321 West Ave, Hanoi', '0445566778', 'west@example.com', (SELECT manager_id FROM managers WHERE manager_name = 'Manager Four')),
    (NULL, 'Downtown Shop', '654 Downtown Ln, Hanoi', '0334455667', 'downtown@example.com', (SELECT manager_id FROM managers WHERE manager_name = 'Manager Five')),
    (NULL, 'Uptown Center', '987 Uptown Rd, Hanoi', '0667788990', 'uptown@example.com', (SELECT manager_id FROM managers WHERE manager_name = 'Manager Six')),
    (NULL, 'Suburban Outlet', '111 Suburb Dr, Hanoi', '0223344556', 'suburban@example.com', (SELECT manager_id FROM managers WHERE manager_name = 'Manager Seven')),
    (NULL, 'Harbor Retail', '222 Harbor St, Hanoi', '0556677889', 'harbor@example.com', (SELECT manager_id FROM managers WHERE manager_name = 'Manager Eight')),
    (NULL, 'Valley Store', '333 Valley Rd, Hanoi', '0778899001', 'valley@example.com', (SELECT manager_id FROM managers WHERE manager_name = 'Manager Nine'));

INSERT OR IGNORE INTO products (product_id, product_name, stock, description, discount, category, image_url, image_url_2) VALUES 
    (NULL, 'Americano', 90, 'Diluted espresso with hot water', NULL, 'Coffees', '/static/Upload/Americano.avif', '/static/Upload/Americano1.avif'),
    (NULL, 'Blueberry', 50, 'Blueberry-flavored drink', NULL, 'Drinks', '/static/Upload/blueberry.avif', '/static/Upload/blueberry1.avif'),
    (NULL, 'Breads', 40, 'Bread accompaniment', NULL, 'Foods', '/static/Upload/Breads.avif', '/static/Upload/Breads1.avif'),
    (NULL, 'Cappuccino', 100, 'Classic cappuccino with frothy milk', 10, 'Coffees', '/static/Upload/Capuchino.avif', '/static/Upload/Capuchino1.avif'),
    (NULL, 'CaramelMachiatto', 60, 'Caramel-flavored macchiato', 10, 'Coffees', '/static/Upload/CaramelMachiatto.avif', '/static/Upload/CaramelMachiatto1.avif'),
    (NULL, 'ColdBrew', 60, 'Smooth cold-brewed coffee', NULL, 'Coffees', '/static/Upload/ColdBrew.avif', '/static/Upload/ColdBrew1.avif'),
    (NULL, 'ColdMocha', 55, 'Cold mocha drink', NULL, 'Drinks', '/static/Upload/ColdMocha.avif', '/static/Upload/ColdMocha1.avif'),
    (NULL, 'EarlGrey', 45, 'Earl Grey tea latte', NULL, 'Drinks', '/static/Upload/EarlGrey.avif', '/static/Upload/EarlGrey1.avif'),
    (NULL, 'Espresso', 120, 'Strong espresso shot', 15, 'Coffees', '/static/Upload/Espresso.avif', '/static/Upload/Espresso1.avif'),
    (NULL, 'HotChocolate', 35, 'Warm chocolate drink', NULL, 'Drinks', '/static/Upload/HotChocolate.avif', '/static/Upload/HotChocolate1.avif'),
    (NULL, 'IcedLatte', 75, 'Chilled latte with ice', 15, 'Coffees', '/static/Upload/IcedLatte.avif', '/static/Upload/IcedLatte1.avif'),
    (NULL, 'Latte', 80, 'Smooth latte with steamed milk', NULL, 'Coffees', '/static/Upload/Latte.avif', '/static/Upload/Latte1.avif'),
    (NULL, 'Strawberry', 50, 'Strawberry-flavored drink', NULL, 'Drinks', '/static/Upload/strawberry.avif', '/static/Upload/strawberry1.avif'),
    (NULL, 'VanillaLatte', 65, 'Vanilla-flavored latte', NULL, 'Drinks', '/static/Upload/VanillaLatte.avif', '/static/Upload/VanillaLatte1.avif');
INSERT OR IGNORE INTO product_size (size_id, product_id, size, price) VALUES
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Americano'), 'S', 45000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Americano'), 'M', 50000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Americano'), 'L', 55000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Blueberry'), 'S', 55000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Blueberry'), 'M', 60000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Blueberry'), 'L', 65000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Breads'), 'S', 34000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Breads'), 'M', 40000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Breads'), 'L', 45000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Cappuccino'), 'S', 40000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Cappuccino'), 'M', 45000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Cappuccino'), 'L', 50000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'CaramelMachiatto'), 'S', 52000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'CaramelMachiatto'), 'M', 65000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'CaramelMachiatto'), 'L', 70000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'ColdBrew'), 'S', 50000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'ColdBrew'), 'M', 55000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'ColdBrew'), 'L', 60000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'ColdMocha'), 'S', 43200),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'ColdMocha'), 'M', 48000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'ColdMocha'), 'L', 52000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'EarlGrey'), 'S', 45000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'EarlGrey'), 'M', 50000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'EarlGrey'), 'L', 55000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Espresso'), 'S', 52700),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Espresso'), 'M', 62000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Espresso'), 'L', 67000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'HotChocolate'), 'S', 42000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'HotChocolate'), 'M', 47000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'HotChocolate'), 'L', 52000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'IcedLatte'), 'S', 48000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'IcedLatte'), 'M', 53000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'IcedLatte'), 'L', 58000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Latte'), 'S', 45000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Latte'), 'M', 50000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Latte'), 'L', 55000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Strawberry'), 'S', 56000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Strawberry'), 'M', 61000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'Strawberry'), 'L', 66000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'VanillaLatte'), 'S', 47000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'VanillaLatte'), 'M', 52000),
    (NULL, (SELECT product_id FROM products WHERE product_name = 'VanillaLatte'), 'L', 57000);
INSERT OR IGNORE INTO addresses (address_id, customer_id, contact_name, phone, address, is_default) VALUES
    (NULL, (SELECT customer_id FROM users WHERE first_name = 'John' AND last_name = 'Doe'), 'John Doe', '0912345678', '123 Main St, Hanoi', TRUE),
    (NULL, (SELECT customer_id FROM users WHERE first_name = 'Jane' AND last_name = 'Smith'), 'Jane Smith', '0987654321', '456 North Rd, Hanoi', TRUE);

INSERT OR IGNORE INTO stock_items (stock_item_id, item_name, category, stock_quantity, store_id, last_updated) VALUES 
    (NULL, 'Whole Milk', 'Dairy', 120, (SELECT store_id FROM stores WHERE store_name = 'Central Market'), '2025-06-01 09:00:00'),
    (NULL, 'Skim Milk', 'Dairy', 80, (SELECT store_id FROM stores WHERE store_name = 'North Plaza'), '2025-06-01 09:00:00'),
    (NULL, 'Espresso Beans', 'Coffee Beans', 200, (SELECT store_id FROM stores WHERE store_name = 'East Side Mall'), '2025-06-01 09:00:00'),
    (NULL, 'Vanilla Syrup', 'Flavoring', 60, (SELECT store_id FROM stores WHERE store_name = 'West End Store'), '2025-06-01 09:00:00'),
    (NULL, 'Chocolate Syrup', 'Flavoring', 50, (SELECT store_id FROM stores WHERE store_name = 'Downtown Shop'), '2025-06-01 09:00:00'),
    (NULL, 'Paper Cups (12oz)', 'Packaging', 500, (SELECT store_id FROM stores WHERE store_name = 'Uptown Center'), '2025-06-01 09:00:00'),
    (NULL, 'Lids (12oz)', 'Packaging', 480, (SELECT store_id FROM stores WHERE store_name = 'Suburban Outlet'), '2025-06-01 09:00:00'),
    (NULL, 'Napkins', 'Supplies', 1000, (SELECT store_id FROM stores WHERE store_name = 'Harbor Retail'), '2025-06-01 09:00:00'),
    (NULL, 'Caramel Syrup', 'Flavoring', 45, (SELECT store_id FROM stores WHERE store_name = 'Valley Store'), '2025-06-01 09:00:00'),
    (NULL, 'Oat Milk', 'Dairy Alternative', 90, (SELECT store_id FROM stores WHERE store_name = 'Central Market'), '2025-06-01 09:00:00');

INSERT OR IGNORE INTO orders (order_id, customer_id, order_date, status, store_id) VALUES
    (NULL, (SELECT customer_id FROM users WHERE first_name = 'John' AND last_name = 'Doe'), '2025-06-10 09:00:00', 'Pending', (SELECT store_id FROM stores WHERE store_name = 'Central Market')),
    (NULL, (SELECT customer_id FROM users WHERE first_name = 'John' AND last_name = 'Doe'), '2025-06-10 10:00:00', 'Delivered', (SELECT store_id FROM stores WHERE store_name = 'Central Market')),
    (NULL, (SELECT customer_id FROM users WHERE first_name = 'Jane' AND last_name = 'Smith'), '2025-06-09 12:00:00', 'Delivered', (SELECT store_id FROM stores WHERE store_name = 'Central Market'));

INSERT OR IGNORE INTO order_details (order_detail_id, order_id, product_id, size_id, quantity, unit_price, total_price) VALUES
    (NULL, (SELECT order_id FROM orders WHERE customer_id = (SELECT customer_id FROM users WHERE first_name = 'John' AND last_name = 'Doe') AND order_date = '2025-06-10 09:00:00'), (SELECT product_id FROM products WHERE product_name = 'Americano'), (SELECT size_id FROM product_size WHERE product_id = (SELECT product_id FROM products WHERE product_name = 'Americano') AND size = 'M'), 1, 50000, 45000),
    (NULL, (SELECT order_id FROM orders WHERE customer_id = (SELECT customer_id FROM users WHERE first_name = 'John' AND last_name = 'Doe') AND order_date = '2025-06-10 10:00:00'), (SELECT product_id FROM products WHERE product_name = 'Americano'), (SELECT size_id FROM product_size WHERE product_id = (SELECT product_id FROM products WHERE product_name = 'Americano') AND size = 'M'), 2, 50000, 90000),
    (NULL, (SELECT order_id FROM orders WHERE customer_id = (SELECT customer_id FROM users WHERE first_name = 'Jane' AND last_name = 'Smith') AND order_date = '2025-06-09 12:00:00'), (SELECT product_id FROM products WHERE product_name = 'Blueberry'), (SELECT size_id FROM product_size WHERE product_id = (SELECT product_id FROM products WHERE product_name = 'Blueberry') AND size = 'M'), 1, 60000, 60000);

INSERT OR IGNORE INTO payments (payment_id, payment_date, payment_method, order_id, amount) VALUES
    (NULL, '2025-06-10 09:00:00', 'COD', (SELECT order_id FROM orders WHERE customer_id = (SELECT customer_id FROM users WHERE first_name = 'John' AND last_name = 'Doe') AND order_date = '2025-06-10 09:00:00'), 45000),
    (NULL, '2025-06-10 10:00:00', 'Card', (SELECT order_id FROM orders WHERE customer_id = (SELECT customer_id FROM users WHERE first_name = 'John' AND last_name = 'Doe') AND order_date = '2025-06-10 10:00:00'), 90000),
    (NULL, '2025-06-09 12:00:00', 'Card', (SELECT order_id FROM orders WHERE customer_id = (SELECT customer_id FROM users WHERE first_name = 'Jane' AND last_name = 'Smith') AND order_date = '2025-06-09 12:00:00'), 60000);

INSERT OR IGNORE INTO reviews (review_id, customer_id, product_id, order_id, size_id, rating, comment, review_date) VALUES
    (NULL, (SELECT customer_id FROM users WHERE first_name = 'John' AND last_name = 'Doe'), (SELECT product_id FROM products WHERE product_name = 'Americano'), (SELECT order_id FROM orders WHERE customer_id = (SELECT customer_id FROM users WHERE first_name = 'John' AND last_name = 'Doe') AND order_date = '2025-06-10 10:00:00'), (SELECT size_id FROM product_size WHERE product_id = (SELECT product_id FROM products WHERE product_name = 'Americano') AND size = 'M'), 4, 'Great coffee, but a bit expensive.', '2025-06-10 10:30:00'),
    (NULL, (SELECT customer_id FROM users WHERE first_name = 'Jane' AND last_name = 'Smith'), (SELECT product_id FROM products WHERE product_name = 'Blueberry'), (SELECT order_id FROM orders WHERE customer_id = (SELECT customer_id FROM users WHERE first_name = 'Jane' AND last_name = 'Smith') AND order_date = '2025-06-09 12:00:00'), (SELECT size_id FROM product_size WHERE product_id = (SELECT product_id FROM products WHERE product_name = 'Blueberry') AND size = 'M'), 5, 'Really enjoyed it!', '2025-06-09 12:30:00');