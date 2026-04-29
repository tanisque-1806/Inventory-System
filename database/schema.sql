CREATE DATABASE IF NOT EXISTS inventory_py;
USE inventory_py;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role ENUM('ADMIN', 'SELLER', 'USER') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255)
);

CREATE TABLE sellers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    company_name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    gst_number VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sellers_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE products (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category_id BIGINT,
    brand VARCHAR(100),
    model_number VARCHAR(100),
    price DECIMAL(12,2) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    min_stock_threshold INT NOT NULL DEFAULT 20,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE seller_products (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    seller_id BIGINT NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category_id BIGINT,
    brand VARCHAR(100),
    model_number VARCHAR(100),
    price DECIMAL(12,2) NOT NULL,
    stock_quantity INT NOT NULL DEFAULT 0,
    min_stock_threshold INT NOT NULL DEFAULT 20,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_seller_products_seller FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE CASCADE,
    CONSTRAINT fk_seller_products_category FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE cart_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INT NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_cart_user_product (user_id, product_id),
    CONSTRAINT fk_cart_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_cart_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE orders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL DEFAULT 0,
    status ENUM('PENDING', 'CONFIRMED', 'SHIPPED', 'DELIVERED', 'CANCELLED') NOT NULL DEFAULT 'PENDING',
    shipping_address TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE order_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(12,2) NOT NULL,
    total_price DECIMAL(12,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_order_items_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    CONSTRAINT fk_order_items_product FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE admin_procurement_carts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    admin_user_id BIGINT NOT NULL,
    status ENUM('DRAFT', 'SUBMITTED') NOT NULL DEFAULT 'DRAFT',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_proc_carts_admin FOREIGN KEY (admin_user_id) REFERENCES users(id)
);

CREATE TABLE admin_procurement_cart_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    cart_id BIGINT NOT NULL,
    seller_product_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    price_per_unit DECIMAL(12,2) NOT NULL,
    total_value DECIMAL(12,2) GENERATED ALWAYS AS (quantity * price_per_unit) STORED,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_cart_supplier_item (cart_id, seller_product_id),
    CONSTRAINT fk_proc_items_cart FOREIGN KEY (cart_id) REFERENCES admin_procurement_carts(id) ON DELETE CASCADE,
    CONSTRAINT fk_proc_items_seller_product FOREIGN KEY (seller_product_id) REFERENCES seller_products(id)
);

CREATE TABLE supply_requests (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    admin_cart_id BIGINT,
    seller_id BIGINT NOT NULL,
    seller_product_id BIGINT NOT NULL,
    admin_product_id BIGINT NULL,
    quantity INT NOT NULL,
    price_per_unit DECIMAL(12,2) NOT NULL,
    total_value DECIMAL(12,2) GENERATED ALWAYS AS (quantity * price_per_unit) STORED,
    status ENUM('PENDING', 'APPROVED', 'REJECTED') NOT NULL DEFAULT 'PENDING',
    admin_notes TEXT,
    seller_remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_supply_cart FOREIGN KEY (admin_cart_id) REFERENCES admin_procurement_carts(id) ON DELETE SET NULL,
    CONSTRAINT fk_supply_seller FOREIGN KEY (seller_id) REFERENCES sellers(id),
    CONSTRAINT fk_supply_seller_product FOREIGN KEY (seller_product_id) REFERENCES seller_products(id),
    CONSTRAINT fk_supply_admin_product FOREIGN KEY (admin_product_id) REFERENCES products(id)
);

CREATE TABLE notifications (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NULL,
    role_target ENUM('ADMIN', 'SELLER', 'USER', 'ALL') NOT NULL DEFAULT 'ADMIN',
    type ENUM('LOW_STOCK', 'ORDER', 'SUPPLY', 'SYSTEM') NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    related_table VARCHAR(50),
    related_id BIGINT,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notifications_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE VIEW vw_admin_inventory AS
SELECT p.id, p.name, p.description, p.brand, p.model_number, p.price,
       p.stock_quantity, p.min_stock_threshold, p.is_active,
       c.name AS category_name, p.created_at, p.updated_at
FROM products p
LEFT JOIN categories c ON c.id = p.category_id;

CREATE VIEW vw_store_products AS
SELECT p.id, p.name, p.description, p.brand, p.model_number, p.price,
       p.stock_quantity, p.min_stock_threshold, c.name AS category_name
FROM products p
LEFT JOIN categories c ON c.id = p.category_id
WHERE p.is_active = 1;

CREATE VIEW vw_low_stock_alerts AS
SELECT p.id, p.name, p.stock_quantity, p.min_stock_threshold, c.name AS category_name
FROM products p
LEFT JOIN categories c ON c.id = p.category_id
WHERE p.is_active = 1 AND p.stock_quantity < 20;

CREATE VIEW vw_available_supplier_inventory AS
SELECT sp.id AS seller_product_id, sp.seller_id, sp.name AS product_name, sp.description,
       sp.brand, sp.model_number, sp.price AS price_per_unit, sp.stock_quantity AS available_stock,
       c.name AS category_name, s.company_name AS seller_name
FROM seller_products sp
JOIN sellers s ON s.id = sp.seller_id
LEFT JOIN categories c ON c.id = sp.category_id
WHERE sp.is_active = 1 AND s.is_active = 1 AND sp.stock_quantity > 0;

CREATE VIEW vw_supply_request_admin AS
SELECT sr.id, sr.status, sr.quantity, sr.price_per_unit, sr.total_value,
       sr.admin_notes, sr.seller_remarks, sr.created_at, sr.updated_at,
       s.company_name AS seller_name, sp.name AS product_name
FROM supply_requests sr
JOIN sellers s ON s.id = sr.seller_id
JOIN seller_products sp ON sp.id = sr.seller_product_id;

CREATE VIEW vw_supply_request_seller AS
SELECT sr.id, sr.seller_id, sr.status, sr.quantity, sr.price_per_unit, sr.total_value,
       sr.admin_notes, sr.seller_remarks, sr.created_at, sr.updated_at,
       sp.name AS product_name
FROM supply_requests sr
JOIN seller_products sp ON sp.id = sr.seller_product_id;

CREATE VIEW vw_order_summary AS
SELECT o.id, o.user_id, u.name AS customer_name, u.email, o.total_amount, o.status,
       o.shipping_address, o.notes, o.created_at, o.updated_at
FROM orders o
JOIN users u ON u.id = o.user_id;

DELIMITER $$

CREATE TRIGGER trg_notify_low_stock_after_product_update
AFTER UPDATE ON products
FOR EACH ROW
BEGIN
    IF NEW.stock_quantity < 20 AND (OLD.stock_quantity IS NULL OR OLD.stock_quantity >= 20 OR OLD.stock_quantity <> NEW.stock_quantity) THEN
        INSERT INTO notifications(user_id, role_target, type, title, message, related_table, related_id)
        SELECT u.id, 'ADMIN', 'LOW_STOCK',
               CONCAT('Low stock: ', NEW.name),
               CONCAT(NEW.name, ' stock dropped below 20. Current quantity: ', NEW.stock_quantity),
               'products',
               NEW.id
        FROM users u
        WHERE u.role = 'ADMIN' AND u.is_active = 1;
    END IF;
END$$

CREATE TRIGGER trg_notify_low_stock_after_seller_update
AFTER UPDATE ON seller_products
FOR EACH ROW
BEGIN
    IF NEW.stock_quantity < 20 AND (OLD.stock_quantity IS NULL OR OLD.stock_quantity >= 20 OR OLD.stock_quantity <> NEW.stock_quantity) THEN
        INSERT INTO notifications(user_id, role_target, type, title, message, related_table, related_id)
        SELECT u.id, 'ADMIN', 'LOW_STOCK',
               CONCAT('Supplier low stock: ', NEW.name),
               CONCAT('Supplier item ', NEW.name, ' is below 20. Current quantity: ', NEW.stock_quantity),
               'seller_products',
               NEW.id
        FROM users u
        WHERE u.role = 'ADMIN' AND u.is_active = 1;
    END IF;
END$$

CREATE PROCEDURE sp_add_to_user_cart(
    IN p_user_id BIGINT,
    IN p_product_id BIGINT,
    IN p_quantity INT,
    OUT p_cart_item_id BIGINT
)
BEGIN
    DECLARE v_stock INT;
    DECLARE v_existing_id BIGINT;

    SELECT stock_quantity INTO v_stock
    FROM products
    WHERE id = p_product_id AND is_active = 1;

    IF v_stock IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Product not found';
    END IF;

    IF p_quantity IS NULL OR p_quantity <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Quantity must be greater than zero';
    END IF;

    IF v_stock < p_quantity THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient stock';
    END IF;

    SELECT id INTO v_existing_id
    FROM cart_items
    WHERE user_id = p_user_id AND product_id = p_product_id
    LIMIT 1;

    IF v_existing_id IS NULL THEN
        INSERT INTO cart_items(user_id, product_id, quantity)
        VALUES(p_user_id, p_product_id, p_quantity);
        SET p_cart_item_id = LAST_INSERT_ID();
    ELSE
        UPDATE cart_items
        SET quantity = quantity + p_quantity
        WHERE id = v_existing_id;
        SET p_cart_item_id = v_existing_id;
    END IF;

    SELECT 'Added to cart' AS message;
END$$

CREATE PROCEDURE sp_place_order(
    IN p_user_id BIGINT,
    IN p_shipping_address TEXT,
    IN p_notes TEXT,
    OUT p_order_id BIGINT
)
BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE v_product_id BIGINT;
    DECLARE v_quantity INT;
    DECLARE v_price DECIMAL(12,2);
    DECLARE v_stock INT;
    DECLARE v_total DECIMAL(12,2) DEFAULT 0;

    DECLARE cur CURSOR FOR
        SELECT ci.product_id, ci.quantity, p.price
        FROM cart_items ci
        JOIN products p ON p.id = ci.product_id
        WHERE ci.user_id = p_user_id;
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    IF p_shipping_address IS NULL OR LENGTH(TRIM(p_shipping_address)) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Shipping address is required';
    END IF;

    IF (SELECT COUNT(*) FROM cart_items WHERE user_id = p_user_id) = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cart is empty';
    END IF;

    OPEN cur;
    read_loop: LOOP
        FETCH cur INTO v_product_id, v_quantity, v_price;
        IF done THEN
            LEAVE read_loop;
        END IF;
        SELECT stock_quantity INTO v_stock FROM products WHERE id = v_product_id;
        IF v_stock < v_quantity THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient stock for one or more items';
        END IF;
        SET v_total = v_total + (v_quantity * v_price);
    END LOOP;
    CLOSE cur;

    INSERT INTO orders(user_id, total_amount, shipping_address, notes)
    VALUES(p_user_id, v_total, p_shipping_address, p_notes);
    SET p_order_id = LAST_INSERT_ID();

    INSERT INTO order_items(order_id, product_id, quantity, unit_price, total_price)
    SELECT p_order_id, ci.product_id, ci.quantity, p.price, (ci.quantity * p.price)
    FROM cart_items ci
    JOIN products p ON p.id = ci.product_id
    WHERE ci.user_id = p_user_id;

    UPDATE products p
    JOIN cart_items ci ON ci.product_id = p.id
    SET p.stock_quantity = p.stock_quantity - ci.quantity
    WHERE ci.user_id = p_user_id;

    DELETE FROM cart_items WHERE user_id = p_user_id;

    INSERT INTO notifications(user_id, role_target, type, title, message, related_table, related_id)
    SELECT u.id, 'ADMIN', 'ORDER', 'New customer order',
           CONCAT('A new order #', p_order_id, ' has been placed by user ID ', p_user_id),
           'orders',
           p_order_id
    FROM users u
    WHERE u.role = 'ADMIN' AND u.is_active = 1;

    SELECT CONCAT('Order placed successfully. Order #', p_order_id) AS message;
END$$

CREATE PROCEDURE sp_add_procurement_cart_item(
    IN p_admin_user_id BIGINT,
    IN p_seller_product_id BIGINT,
    IN p_quantity INT,
    IN p_notes TEXT,
    OUT p_cart_id BIGINT
)
BEGIN
    DECLARE v_existing_cart BIGINT;
    DECLARE v_price DECIMAL(12,2);
    DECLARE v_stock INT;

    IF p_quantity IS NULL OR p_quantity <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Quantity must be greater than zero';
    END IF;

    SELECT stock_quantity, price INTO v_stock, v_price
    FROM seller_products
    WHERE id = p_seller_product_id AND is_active = 1;

    IF v_stock IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Supplier item not found';
    END IF;

    IF v_stock < p_quantity THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Requested quantity exceeds supplier availability';
    END IF;

    SELECT id INTO v_existing_cart
    FROM admin_procurement_carts
    WHERE admin_user_id = p_admin_user_id AND status = 'DRAFT'
    ORDER BY id DESC LIMIT 1;

    IF v_existing_cart IS NULL THEN
        INSERT INTO admin_procurement_carts(admin_user_id, notes)
        VALUES(p_admin_user_id, p_notes);
        SET v_existing_cart = LAST_INSERT_ID();
    END IF;

    INSERT INTO admin_procurement_cart_items(cart_id, seller_product_id, quantity, price_per_unit, notes)
    VALUES(v_existing_cart, p_seller_product_id, p_quantity, v_price, p_notes)
    ON DUPLICATE KEY UPDATE
        quantity = VALUES(quantity),
        price_per_unit = VALUES(price_per_unit),
        notes = VALUES(notes);

    SET p_cart_id = v_existing_cart;
    SELECT 'Item added to admin procurement cart' AS message;
END$$

CREATE PROCEDURE sp_submit_procurement_cart(
    IN p_admin_user_id BIGINT,
    OUT p_request_count INT
)
BEGIN
    DECLARE v_cart_id BIGINT;

    SELECT id INTO v_cart_id
    FROM admin_procurement_carts
    WHERE admin_user_id = p_admin_user_id AND status = 'DRAFT'
    ORDER BY id DESC LIMIT 1;

    IF v_cart_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No draft procurement cart found';
    END IF;

    INSERT INTO supply_requests(admin_cart_id, seller_id, seller_product_id, quantity, price_per_unit, admin_notes)
    SELECT pci.cart_id, sp.seller_id, pci.seller_product_id, pci.quantity, pci.price_per_unit, pci.notes
    FROM admin_procurement_cart_items pci
    JOIN seller_products sp ON sp.id = pci.seller_product_id
    WHERE pci.cart_id = v_cart_id;

    SET p_request_count = ROW_COUNT();

    UPDATE admin_procurement_carts
    SET status = 'SUBMITTED'
    WHERE id = v_cart_id;

    INSERT INTO notifications(user_id, role_target, type, title, message, related_table, related_id)
    SELECT su.user_id, 'SELLER', 'SUPPLY',
           'New admin supply request',
           CONCAT('Admin sent a new supply request cart #', v_cart_id),
           'admin_procurement_carts',
           v_cart_id
    FROM sellers su
    WHERE su.id IN (
        SELECT DISTINCT seller_id FROM supply_requests WHERE admin_cart_id = v_cart_id
    );

    SELECT sr.id, sr.seller_id, sr.seller_product_id, sr.quantity, sr.status
    FROM supply_requests sr
    WHERE sr.admin_cart_id = v_cart_id
    ORDER BY sr.id DESC;
END$$

CREATE PROCEDURE sp_respond_supply_request(
    IN p_request_id BIGINT,
    IN p_seller_id BIGINT,
    IN p_status VARCHAR(20),
    IN p_seller_remarks TEXT
)
BEGIN
    DECLARE v_product_id BIGINT;
    DECLARE v_quantity INT;
    DECLARE v_name VARCHAR(200);
    DECLARE v_category_id BIGINT;
    DECLARE v_brand VARCHAR(100);
    DECLARE v_model VARCHAR(100);
    DECLARE v_price DECIMAL(12,2);
    DECLARE v_stock INT;

    IF p_status NOT IN ('APPROVED', 'REJECTED') THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Status must be APPROVED or REJECTED';
    END IF;

    SELECT sr.seller_product_id, sr.quantity, sp.name, sp.category_id, sp.brand, sp.model_number, sp.price, sp.stock_quantity
    INTO v_product_id, v_quantity, v_name, v_category_id, v_brand, v_model, v_price, v_stock
    FROM supply_requests sr
    JOIN seller_products sp ON sp.id = sr.seller_product_id
    WHERE sr.id = p_request_id AND sr.seller_id = p_seller_id AND sr.status = 'PENDING';

    IF v_product_id IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Pending supply request not found';
    END IF;

    IF p_status = 'APPROVED' THEN
        IF v_stock < v_quantity THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient seller stock to approve request';
        END IF;

        UPDATE seller_products
        SET stock_quantity = stock_quantity - v_quantity
        WHERE id = v_product_id;

        IF EXISTS (
            SELECT 1 FROM products
            WHERE name = v_name
              AND IFNULL(category_id, 0) = IFNULL(v_category_id, 0)
              AND IFNULL(brand, '') = IFNULL(v_brand, '')
              AND IFNULL(model_number, '') = IFNULL(v_model, '')
            LIMIT 1
        ) THEN
            UPDATE products
            SET stock_quantity = stock_quantity + v_quantity
            WHERE name = v_name
              AND IFNULL(category_id, 0) = IFNULL(v_category_id, 0)
              AND IFNULL(brand, '') = IFNULL(v_brand, '')
              AND IFNULL(model_number, '') = IFNULL(v_model, '');
        ELSE
            INSERT INTO products(name, description, category_id, brand, model_number, price, stock_quantity, min_stock_threshold)
            SELECT name, description, category_id, brand, model_number, price, v_quantity, min_stock_threshold
            FROM seller_products
            WHERE id = v_product_id;
        END IF;
    END IF;

    UPDATE supply_requests
    SET status = p_status, seller_remarks = p_seller_remarks
    WHERE id = p_request_id;

    INSERT INTO notifications(user_id, role_target, type, title, message, related_table, related_id)
    SELECT u.id, 'ADMIN', 'SUPPLY',
           CONCAT('Supplier request ', p_status),
           CONCAT('Supplier has ', LOWER(p_status), ' supply request #', p_request_id),
           'supply_requests',
           p_request_id
    FROM users u
    WHERE u.role = 'ADMIN' AND u.is_active = 1;

    SELECT CONCAT('Supply request ', LOWER(p_status), ' successfully') AS message;
END$$

DELIMITER ;

INSERT INTO users(name, email, password_hash, phone, role) VALUES
('Admin Owner', 'admin@inventory.com', '$2b$12$0w3HnG1LSz5.mVmAUF/D1e1igvNxPq4dB/STekkIo8WcKTwxgS4f2', '9999999999', 'ADMIN'),
('Volt Supplier', 'seller@inventory.com', '$2b$12$f6PGaN8fl5Yss8/tdnlWEOyTGrVdVBxND.HOfWqZnOVZuF9z7S2yG', '8888888888', 'SELLER'),
('Mini Dealer', 'user@inventory.com', '$2b$12$l26G.TXnFs.1058KUN4roOc.M2ADtKEkOm.ylWNSTHLA2XIIuTekq', '7777777777', 'USER');

INSERT INTO sellers(user_id, company_name, phone, address, gst_number) VALUES
(2, 'Volt Supplier Co.', '8888888888', 'Delhi Warehouse', 'GSTSUPP001');

INSERT INTO categories(name, description) VALUES
('Fan', 'Ceiling and wall fans'),
('Bulb', 'LED and decorative bulbs'),
('AC', 'Air conditioners'),
('Wires', 'Electrical wires and cables');

INSERT INTO products(name, description, category_id, brand, model_number, price, stock_quantity, min_stock_threshold) VALUES
('Warehouse Fan', 'Admin warehouse fan stock', 1, 'Bajaj', 'FAN-10', 1500.00, 35, 20),
('LED Bulb', 'Retail LED bulb', 2, 'Philips', 'BULB-9W', 120.00, 60, 20);

INSERT INTO seller_products(seller_id, name, description, category_id, brand, model_number, price, stock_quantity, min_stock_threshold) VALUES
(1, 'Warehouse Fan', 'Supplier fan stock', 1, 'Bajaj', 'FAN-10', 1300.00, 55, 20),
(1, 'Split AC', 'Supplier AC stock', 3, 'LG', 'AC-1.5T', 29500.00, 24, 20),
(1, 'Copper Wire Bundle', 'Supplier wire stock', 4, 'Havells', 'WIRE-100', 2100.00, 18, 20);
