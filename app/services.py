from .db_core import call_procedure, execute, fetch_all, fetch_one
from .security import check_password, hash_password


def login_user(email, password):
    user = fetch_one(
        """
        SELECT u.id, u.name, u.email, u.password_hash, u.role, u.phone, s.id AS seller_id
        FROM users u
        LEFT JOIN sellers s ON s.user_id = u.id
        WHERE u.email = %s AND u.is_active = 1
        """,
        (email,),
    )
    if not user or not check_password(password, user["password_hash"]):
        return None
    user.pop("password_hash", None)
    return user


def register_user(name, email, password, phone, role, company_name="", address="", gst_number=""):
    existing = fetch_one("SELECT id FROM users WHERE email = %s", (email,))
    if existing:
        raise ValueError("Email already exists")
    if role not in {"USER", "SELLER"}:
        raise ValueError("Only USER or SELLER registration is allowed")
    user_id = execute(
        """
        INSERT INTO users(name, email, password_hash, phone, role)
        VALUES(%s, %s, %s, %s, %s)
        """,
        (name, email, hash_password(password), phone, role),
    )
    if role == "SELLER":
        execute(
            """
            INSERT INTO sellers(user_id, company_name, phone, address, gst_number)
            VALUES(%s, %s, %s, %s, %s)
            """,
            (user_id, company_name or name, phone, address, gst_number),
        )
    return user_id


def admin_dashboard_data():
    summary = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM products WHERE is_active = 1) AS products,
            (SELECT COUNT(*) FROM sellers WHERE is_active = 1) AS sellers,
            (SELECT COUNT(*) FROM users WHERE role = 'USER' AND is_active = 1) AS users,
            (SELECT COUNT(*) FROM orders) AS orders,
            (SELECT COUNT(*) FROM notifications WHERE is_read = 0) AS unread_notifications
        """
    )
    low_stock = fetch_all("SELECT * FROM vw_low_stock_alerts ORDER BY stock_quantity ASC")
    return summary, low_stock


def low_stock_products():
    return fetch_all("SELECT * FROM vw_low_stock_alerts ORDER BY stock_quantity ASC")


def admin_analytics_data():
    monthly = fetch_all(
        """
        SELECT DATE_FORMAT(created_at, '%Y-%m') AS month_key,
               DATE_FORMAT(created_at, '%b %Y') AS month_label,
               SUM(total_amount) AS revenue,
               COUNT(*) AS order_count
        FROM orders
        GROUP BY DATE_FORMAT(created_at, '%Y-%m'), DATE_FORMAT(created_at, '%b %Y')
        ORDER BY month_key
        """
    )
    top_products = fetch_all(
        """
        SELECT p.name AS product_name, SUM(oi.quantity) AS total_quantity, SUM(oi.total_price) AS total_revenue
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        GROUP BY p.id, p.name
        ORDER BY total_quantity DESC, total_revenue DESC
        LIMIT 10
        """
    )
    return monthly, top_products


def list_categories():
    return fetch_all("SELECT id, name, description FROM categories ORDER BY name")


def create_category(name, description):
    return execute("INSERT INTO categories(name, description) VALUES(%s, %s)", (name, description))


def update_category(category_id, name, description):
    execute("UPDATE categories SET name = %s, description = %s WHERE id = %s", (name, description, category_id))


def delete_category(category_id):
    execute("DELETE FROM categories WHERE id = %s", (category_id,))


def list_admin_products():
    return fetch_all("SELECT * FROM vw_admin_inventory ORDER BY name")


def create_admin_product(data):
    return execute(
        """
        INSERT INTO products(name, description, category_id, brand, model_number, price, stock_quantity, min_stock_threshold)
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            data.get("name"),
            data.get("description"),
            data.get("category_id"),
            data.get("brand"),
            data.get("model_number"),
            data.get("price"),
            data.get("stock_quantity", 0),
            data.get("min_stock_threshold", 20),
        ),
    )


def update_admin_product(product_id, data):
    execute(
        """
        UPDATE products
        SET name=%s, description=%s, category_id=%s, brand=%s, model_number=%s, price=%s, stock_quantity=%s, min_stock_threshold=%s
        WHERE id=%s
        """,
        (
            data.get("name"),
            data.get("description"),
            data.get("category_id"),
            data.get("brand"),
            data.get("model_number"),
            data.get("price"),
            data.get("stock_quantity", 0),
            data.get("min_stock_threshold", 20),
            product_id,
        ),
    )


def delete_admin_product(product_id):
    execute("DELETE FROM products WHERE id = %s", (product_id,))


def list_users():
    return fetch_all(
        """
        SELECT id, name, email, phone, role, is_active, created_at
        FROM users
        ORDER BY created_at DESC
        """
    )


def get_user_by_id(user_id):
    return fetch_one(
        """
        SELECT u.id, u.name, u.email, u.phone, u.role, u.is_active, s.id AS seller_id
        FROM users u
        LEFT JOIN sellers s ON s.user_id = u.id
        WHERE u.id = %s
        """,
        (user_id,),
    )


def list_sellers():
    return fetch_all(
        """
        SELECT s.id, s.company_name, s.phone, s.address, s.gst_number, s.is_active, s.created_at,
               u.name AS owner_name, u.email AS owner_email
        FROM sellers s
        JOIN users u ON u.id = s.user_id
        ORDER BY s.created_at DESC
        """
    )


def create_seller_account(data):
    return register_user(
        data.get("name"),
        data.get("email"),
        data.get("password"),
        data.get("phone"),
        "SELLER",
        data.get("companyName") or data.get("name"),
        data.get("address"),
        data.get("gstNumber"),
    )


def delete_seller_account(seller_id):
    seller = fetch_one("SELECT user_id FROM sellers WHERE id = %s", (seller_id,))
    if seller:
        execute("DELETE FROM users WHERE id = %s", (seller["user_id"],))


def list_orders_for_admin():
    return fetch_all("SELECT * FROM vw_order_summary ORDER BY created_at DESC")


def list_order_items(order_id):
    return fetch_all(
        """
        SELECT oi.id, oi.quantity, oi.unit_price, oi.total_price, p.id AS product_id, p.name AS product_name
        FROM order_items oi
        JOIN products p ON p.id = oi.product_id
        WHERE oi.order_id = %s
        ORDER BY oi.id
        """,
        (order_id,),
    )


def update_order_status(order_id, status):
    execute("UPDATE orders SET status = %s WHERE id = %s", (status, order_id))


def list_notifications():
    return fetch_all("SELECT * FROM notifications ORDER BY created_at DESC LIMIT 100")


def mark_notifications_read():
    execute("UPDATE notifications SET is_read = 1 WHERE role_target IN ('ADMIN', 'ALL')")


def supply_options():
    return fetch_all("SELECT * FROM vw_available_supplier_inventory ORDER BY product_name, seller_name")


def create_supply_request(admin_user_id, seller_product_id, quantity, notes=""):
    add_procurement_item(admin_user_id, seller_product_id, quantity, notes)
    submit_procurement(admin_user_id)


def procurement_cart(admin_user_id):
    cart = fetch_one(
        """
        SELECT id, status, notes, created_at
        FROM admin_procurement_carts
        WHERE admin_user_id = %s AND status = 'DRAFT'
        ORDER BY id DESC LIMIT 1
        """,
        (admin_user_id,),
    )
    if not cart:
        return None, []
    items = fetch_all(
        """
        SELECT pci.id, pci.quantity, pci.price_per_unit, pci.total_value,
               spi.seller_name, spi.product_name, spi.available_stock, spi.seller_product_id
        FROM admin_procurement_cart_items pci
        JOIN vw_available_supplier_inventory spi ON spi.seller_product_id = pci.seller_product_id
        WHERE pci.cart_id = %s
        ORDER BY pci.id DESC
        """,
        (cart["id"],),
    )
    return cart, items


def add_procurement_item(admin_user_id, seller_product_id, quantity, notes):
    return call_procedure("sp_add_procurement_cart_item", [admin_user_id, seller_product_id, quantity, notes, 0])


def update_procurement_item(item_id, quantity):
    execute("UPDATE admin_procurement_cart_items SET quantity = %s WHERE id = %s", (quantity, item_id))


def remove_procurement_item(item_id):
    execute("DELETE FROM admin_procurement_cart_items WHERE id = %s", (item_id,))


def submit_procurement(admin_user_id):
    return call_procedure("sp_submit_procurement_cart", [admin_user_id, 0])


def list_supply_requests_admin():
    return fetch_all("SELECT * FROM vw_supply_request_admin ORDER BY created_at DESC")


def seller_dashboard_data(seller_id):
    summary = fetch_one(
        """
        SELECT
            (SELECT COUNT(*) FROM seller_products WHERE seller_id = %s AND is_active = 1) AS total_products,
            (SELECT COUNT(*) FROM seller_products WHERE seller_id = %s AND is_active = 1 AND stock_quantity < 20) AS low_stock,
            (SELECT COUNT(*) FROM supply_requests WHERE seller_id = %s AND status = 'PENDING') AS pending_requests,
            (SELECT COUNT(*) FROM supply_requests WHERE seller_id = %s AND status = 'APPROVED') AS approved_requests
        """,
        (seller_id, seller_id, seller_id, seller_id),
    )
    recent_requests = fetch_all(
        """
        SELECT * FROM vw_supply_request_seller
        WHERE seller_id = %s
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (seller_id,),
    )
    return summary, recent_requests


def seller_products(seller_id):
    return fetch_all(
        """
        SELECT sp.*, c.name AS category_name
        FROM seller_products sp
        LEFT JOIN categories c ON c.id = sp.category_id
        WHERE seller_id = %s AND is_active = 1
        ORDER BY sp.name
        """,
        (seller_id,),
    )


def create_seller_product(seller_id, data):
    return execute(
        """
        INSERT INTO seller_products(seller_id, name, description, category_id, brand, model_number, price, stock_quantity, min_stock_threshold)
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            seller_id,
            data.get("name"),
            data.get("description"),
            data.get("category_id"),
            data.get("brand"),
            data.get("model_number"),
            data.get("price"),
            data.get("stock_quantity", 0),
            data.get("min_stock_threshold", 20),
        ),
    )


def update_seller_product(seller_id, product_id, data):
    execute(
        """
        UPDATE seller_products
        SET name=%s, description=%s, category_id=%s, brand=%s, model_number=%s, price=%s, stock_quantity=%s, min_stock_threshold=%s
        WHERE id=%s AND seller_id=%s
        """,
        (
            data.get("name"),
            data.get("description"),
            data.get("category_id"),
            data.get("brand"),
            data.get("model_number"),
            data.get("price"),
            data.get("stock_quantity", 0),
            data.get("min_stock_threshold", 20),
            product_id,
            seller_id,
        ),
    )


def archive_seller_product(seller_id, product_id):
    execute("UPDATE seller_products SET is_active = 0 WHERE id = %s AND seller_id = %s", (product_id, seller_id))


def list_seller_requests(seller_id):
    return fetch_all(
        """
        SELECT * FROM vw_supply_request_seller
        WHERE seller_id = %s
        ORDER BY created_at DESC
        """,
        (seller_id,),
    )


def respond_supply_request(request_id, seller_id, status, remarks):
    return call_procedure("sp_respond_supply_request", [request_id, seller_id, status, remarks])


def store_products():
    return fetch_all(
        """
        SELECT * FROM vw_store_products
        WHERE stock_quantity > 0
        ORDER BY name
        """
    )


def user_cart(user_id):
    return fetch_all(
        """
        SELECT ci.id, ci.quantity, p.id AS product_id, p.name, p.brand, p.price, c.name AS category_name,
               (ci.quantity * p.price) AS total_price
        FROM cart_items ci
        JOIN products p ON p.id = ci.product_id
        LEFT JOIN categories c ON c.id = p.category_id
        WHERE ci.user_id = %s
        ORDER BY ci.id DESC
        """,
        (user_id,),
    )


def add_to_cart(user_id, product_id, quantity):
    return call_procedure("sp_add_to_user_cart", [user_id, product_id, quantity, 0])


def update_cart_item(user_id, item_id, quantity):
    execute("UPDATE cart_items SET quantity = %s WHERE id = %s AND user_id = %s", (quantity, item_id, user_id))


def remove_cart_item(user_id, item_id):
    execute("DELETE FROM cart_items WHERE id = %s AND user_id = %s", (item_id, user_id))


def clear_cart(user_id):
    execute("DELETE FROM cart_items WHERE user_id = %s", (user_id,))


def cart_count(user_id):
    row = fetch_one("SELECT COALESCE(SUM(quantity), 0) AS count FROM cart_items WHERE user_id = %s", (user_id,))
    return int(row["count"]) if row else 0


def place_order(user_id, shipping_address, notes):
    return call_procedure("sp_place_order", [user_id, shipping_address, notes, 0])


def user_orders(user_id):
    return fetch_all(
        """
        SELECT * FROM vw_order_summary
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,),
    )
