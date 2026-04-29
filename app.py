from datetime import datetime
from functools import wraps

from flask import Flask, jsonify, redirect, request, send_from_directory, session

from app.config import Config
from app.services import (
    add_to_cart,
    admin_analytics_data,
    admin_dashboard_data,
    archive_seller_product,
    cart_count,
    clear_cart,
    create_admin_product,
    create_category,
    create_seller_account,
    create_seller_product,
    create_supply_request,
    delete_admin_product,
    delete_category,
    delete_seller_account,
    get_user_by_id,
    list_admin_products,
    list_categories,
    list_notifications,
    list_order_items,
    list_orders_for_admin,
    list_seller_requests,
    list_sellers,
    list_supply_requests_admin,
    list_users,
    login_user,
    low_stock_products,
    mark_notifications_read,
    place_order,
    procurement_cart,
    register_user,
    remove_cart_item,
    remove_procurement_item,
    respond_supply_request,
    seller_products,
    store_products,
    submit_procurement,
    supply_options,
    update_admin_product,
    update_cart_item,
    update_category,
    update_order_status,
    update_procurement_item,
    update_seller_product,
    user_cart,
    user_orders,
)


app = Flask(__name__, static_folder="frontend", static_url_path="")
app.secret_key = Config.SECRET_KEY


def ok(data=None, message="OK", **extra):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return jsonify(payload)


def fail(message, status=400):
    return jsonify({"success": False, "message": message}), status


def current_user():
    user = session.get("user")
    if not user:
        return None
    return get_user_by_id(user["id"])


def require_login(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return fail("Unauthorized", 401)
            if roles and user["role"] not in roles:
                return fail("Forbidden", 403)
            request.current_user = user
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def serialize_product(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row.get("description"),
        "brand": row.get("brand"),
        "modelNumber": row.get("model_number"),
        "price": row.get("price"),
        "stockQuantity": row.get("stock_quantity"),
        "minStockThreshold": row.get("min_stock_threshold"),
        "active": bool(row.get("is_active", True)),
        "createdAt": row.get("created_at"),
        "updatedAt": row.get("updated_at"),
        "category": {"id": row.get("category_id"), "name": row.get("category_name")} if row.get("category_name") or row.get("category_id") else None,
    }


def serialize_category(row):
    return {"id": row["id"], "name": row["name"], "description": row.get("description")}


def serialize_user(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "phone": row.get("phone"),
        "role": row.get("role"),
        "active": bool(row.get("is_active", True)),
        "createdAt": row.get("created_at"),
    }


def serialize_seller(row):
    return {
        "id": row["id"],
        "companyName": row.get("company_name"),
        "phone": row.get("phone"),
        "address": row.get("address"),
        "gstNumber": row.get("gst_number"),
        "active": bool(row.get("is_active", True)),
        "createdAt": row.get("created_at"),
        "user": {"name": row.get("owner_name"), "email": row.get("owner_email")},
    }


def serialize_order(row):
    return {
        "id": row["id"],
        "finalAmount": row.get("total_amount"),
        "status": row.get("status"),
        "shippingAddress": row.get("shipping_address"),
        "notes": row.get("notes"),
        "createdAt": row.get("created_at"),
        "updatedAt": row.get("updated_at"),
        "user": {"id": row.get("user_id"), "name": row.get("customer_name"), "email": row.get("email")},
        "orderItems": row.get("orderItems", []),
    }


def serialize_supply(row):
    return {
        "id": row["id"],
        "sellerId": row.get("seller_id"),
        "productName": row.get("product_name"),
        "quantity": row.get("quantity"),
        "pricePerUnit": row.get("price_per_unit"),
        "status": row.get("status"),
        "notes": row.get("admin_notes"),
        "adminRemarks": row.get("seller_remarks"),
        "createdAt": row.get("created_at"),
        "sellerName": row.get("seller_name"),
        "seller": {
            "id": row.get("seller_id"),
            "companyName": row.get("seller_name"),
            "user": {"name": row.get("seller_name")},
        },
    }


def serialize_notification(row):
    return {
        "id": row["id"],
        "message": row.get("message"),
        "type": row.get("type"),
        "read": bool(row.get("is_read")),
        "createdAt": row.get("created_at"),
    }


def serialize_cart_item(row):
    return {
        "id": row["id"],
        "quantity": row.get("quantity", 0),
        "totalPrice": row.get("total_price"),
        "product": {
            "id": row.get("product_id"),
            "name": row.get("name"),
            "brand": row.get("brand"),
            "price": row.get("price"),
            "category": {"name": row.get("category_name")} if row.get("category_name") else None,
        },
    }


@app.get("/")
def root():
    return redirect("/login.html")


@app.get("/<path:path>")
def static_proxy(path):
    return send_from_directory(app.static_folder, path)


@app.post("/api/auth/login")
def login():
    body = request.get_json(force=True)
    user = login_user(body.get("email"), body.get("password"))
    if not user:
        return fail("Invalid email or password", 401)
    session["user"] = {"id": user["id"], "role": user["role"]}
    return jsonify(
        {
            "token": f"session-{user['id']}",
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
        }
    )


@app.post("/api/auth/register")
def register():
    body = request.get_json(force=True)
    register_user(body.get("name"), body.get("email"), body.get("password"), body.get("phone"), "USER")
    return ok(message="Registered successfully")


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return ok(message="Logged out")


@app.get("/api/categories")
@require_login("ADMIN", "SELLER", "USER")
def categories():
    return ok([serialize_category(row) for row in list_categories()])


@app.get("/api/products")
@require_login("ADMIN", "USER")
def products():
    return ok([serialize_product(row) for row in store_products()])


@app.get("/api/cart")
@require_login("USER", "ADMIN")
def cart():
    return ok([serialize_cart_item(row) for row in user_cart(request.current_user["id"])])


@app.get("/api/cart/count")
@require_login("USER", "ADMIN")
def cart_count_route():
    return ok(cart_count(request.current_user["id"]))


@app.post("/api/cart")
@require_login("USER", "ADMIN")
def add_cart():
    body = request.get_json(force=True)
    add_to_cart(request.current_user["id"], body.get("productId"), body.get("quantity"))
    return ok(message="Added to cart")


@app.put("/api/cart/<int:item_id>")
@require_login("USER", "ADMIN")
def update_cart(item_id):
    body = request.get_json(force=True)
    update_cart_item(request.current_user["id"], item_id, body.get("quantity"))
    return ok(message="Cart updated")


@app.delete("/api/cart/<int:item_id>")
@require_login("USER", "ADMIN")
def delete_cart_item(item_id):
    remove_cart_item(request.current_user["id"], item_id)
    return ok(message="Cart item removed")


@app.delete("/api/cart")
@require_login("USER", "ADMIN")
def clear_cart_route():
    clear_cart(request.current_user["id"])
    return ok(message="Cart cleared")


@app.post("/api/orders")
@require_login("USER", "ADMIN")
def create_order():
    body = request.get_json(force=True)
    result, payload = place_order(request.current_user["id"], body.get("shippingAddress"), body.get("notes"))
    order_id = payload[0].get("order_id") if payload and payload[0].get("order_id") else result[3]
    return ok(message=payload[0]["message"] if payload else "Order placed", orderId=order_id)


@app.get("/api/orders")
@require_login("USER", "ADMIN")
def orders():
    orders_list = []
    for row in user_orders(request.current_user["id"]):
        row["orderItems"] = [
            {
                "id": item["id"],
                "quantity": item["quantity"],
                "unitPrice": item["unit_price"],
                "totalPrice": item["total_price"],
                "product": {"id": item["product_id"], "name": item["product_name"]},
            }
            for item in list_order_items(row["id"])
        ]
        orders_list.append(serialize_order(row))
    return ok(orders_list)


@app.get("/api/admin/dashboard")
@require_login("ADMIN")
def admin_dashboard():
    summary, low_stock = admin_dashboard_data()
    monthly, _ = admin_analytics_data()
    current_month = datetime.now().strftime("%Y-%m")
    revenue_this_month = next((row["revenue"] for row in monthly if row["month_key"] == current_month), 0)
    orders_this_month = next((row["order_count"] for row in monthly if row["month_key"] == current_month), 0)
    return ok(
        {
            "totalRevenue": sum(float(row.get("revenue") or 0) for row in monthly),
            "revenueThisMonth": revenue_this_month,
            "ordersThisMonth": orders_this_month,
            "totalOrders": summary["orders"],
            "totalProducts": summary["products"],
            "lowStockCount": len(low_stock),
            "totalUsers": summary["users"],
            "totalSellers": summary["sellers"],
            "unreadNotifications": summary["unread_notifications"],
        }
    )


@app.get("/api/admin/analytics/monthly/<int:year>")
@require_login("ADMIN")
def admin_monthly(year):
    monthly, _ = admin_analytics_data()
    filtered = [row for row in monthly if str(row["month_key"]).startswith(str(year))]
    return ok({"labels": [row["month_label"] for row in filtered], "revenue": [row["revenue"] for row in filtered]})


@app.get("/api/admin/analytics/top-products")
@require_login("ADMIN")
def admin_top_products():
    _, top_products = admin_analytics_data()
    return ok([{"productName": row["product_name"], "totalQuantitySold": row["total_quantity"], "totalRevenue": row["total_revenue"]} for row in top_products])


@app.get("/api/admin/products")
@require_login("ADMIN")
def admin_products():
    return ok([serialize_product(row) for row in list_admin_products()])


@app.get("/api/admin/products/low-stock")
@require_login("ADMIN")
def admin_low_stock():
    return ok([serialize_product(row) for row in low_stock_products()])


@app.get("/api/admin/products/supply-options")
@require_login("ADMIN")
def admin_supply_options():
    options = []
    for row in supply_options():
        options.append(
            {
                "sellerProductId": row["seller_product_id"],
                "sellerId": row["seller_id"],
                "sellerName": row["seller_name"],
                "productName": row["product_name"],
                "availableStock": row["available_stock"],
                "pricePerUnit": row["price_per_unit"],
                "categoryName": row.get("category_name"),
            }
        )
    return ok(options)


@app.post("/api/admin/products")
@require_login("ADMIN")
def admin_product_create():
    body = request.get_json(force=True)
    create_admin_product(
        {
            "name": body.get("name"),
            "description": body.get("description"),
            "category_id": body.get("categoryId"),
            "brand": body.get("brand"),
            "model_number": body.get("modelNumber"),
            "price": body.get("price"),
            "stock_quantity": body.get("stockQuantity"),
            "min_stock_threshold": body.get("minStockThreshold"),
        }
    )
    return ok(message="Product created")


@app.put("/api/admin/products/<int:product_id>")
@require_login("ADMIN")
def admin_product_update(product_id):
    body = request.get_json(force=True)
    update_admin_product(
        product_id,
        {
            "name": body.get("name"),
            "description": body.get("description"),
            "category_id": body.get("categoryId"),
            "brand": body.get("brand"),
            "model_number": body.get("modelNumber"),
            "price": body.get("price"),
            "stock_quantity": body.get("stockQuantity"),
            "min_stock_threshold": body.get("minStockThreshold"),
        },
    )
    return ok(message="Product updated")


@app.delete("/api/admin/products/<int:product_id>")
@require_login("ADMIN")
def admin_product_delete(product_id):
    delete_admin_product(product_id)
    return ok(message="Product deleted")


@app.get("/api/admin/categories")
@require_login("ADMIN")
def admin_categories():
    return ok([serialize_category(row) for row in list_categories()])


@app.post("/api/admin/categories")
@require_login("ADMIN")
def admin_category_create():
    body = request.get_json(force=True)
    create_category(body.get("name"), body.get("description"))
    return ok(message="Category created")


@app.put("/api/admin/categories/<int:category_id>")
@require_login("ADMIN")
def admin_category_update(category_id):
    body = request.get_json(force=True)
    update_category(category_id, body.get("name"), body.get("description"))
    return ok(message="Category updated")


@app.delete("/api/admin/categories/<int:category_id>")
@require_login("ADMIN")
def admin_category_delete(category_id):
    delete_category(category_id)
    return ok(message="Category deleted")


@app.get("/api/admin/users")
@require_login("ADMIN")
def admin_users():
    return ok([serialize_user(row) for row in list_users()])


@app.get("/api/admin/sellers")
@require_login("ADMIN")
def admin_sellers():
    return ok([serialize_seller(row) for row in list_sellers()])


@app.post("/api/admin/sellers")
@require_login("ADMIN")
def admin_seller_create():
    body = request.get_json(force=True)
    create_seller_account(body)
    return ok(message="Seller created")


@app.delete("/api/admin/sellers/<int:seller_id>")
@require_login("ADMIN")
def admin_seller_delete(seller_id):
    delete_seller_account(seller_id)
    return ok(message="Seller deactivated")


@app.get("/api/admin/orders")
@require_login("ADMIN")
def admin_orders():
    orders = []
    for row in list_orders_for_admin():
        row["orderItems"] = [
            {
                "id": item["id"],
                "quantity": item["quantity"],
                "unitPrice": item["unit_price"],
                "totalPrice": item["total_price"],
                "product": {"id": item["product_id"], "name": item["product_name"]},
            }
            for item in list_order_items(row["id"])
        ]
        orders.append(serialize_order(row))
    return ok(orders)


@app.put("/api/admin/orders/<int:order_id>/status")
@require_login("ADMIN")
def admin_order_status(order_id):
    body = request.get_json(force=True)
    update_order_status(order_id, body.get("status"))
    return ok(message="Order status updated")


@app.get("/api/admin/supply-requests")
@require_login("ADMIN")
def admin_supply_requests():
    return ok([serialize_supply(row) for row in list_supply_requests_admin()])


@app.post("/api/admin/supply-requests")
@require_login("ADMIN")
def admin_supply_request_create():
    body = request.get_json(force=True)
    create_supply_request(request.current_user["id"], body.get("sellerProductId"), body.get("quantity"), body.get("notes"))
    return ok(message="Supply request created")


@app.get("/api/admin/notifications")
@require_login("ADMIN")
def admin_notifications():
    notifications = [serialize_notification(row) for row in list_notifications()]
    unread = sum(1 for row in notifications if not row["read"])
    return ok({"notifications": notifications, "unreadCount": unread})


@app.put("/api/admin/notifications/mark-read")
@require_login("ADMIN")
def admin_notifications_mark_read():
    mark_notifications_read()
    return ok(message="Notifications marked as read")


@app.get("/api/seller/products")
@require_login("SELLER")
def seller_products_route():
    return ok([
        {
            "id": row["id"],
            "name": row["name"],
            "description": row.get("description"),
            "brand": row.get("brand"),
            "modelNumber": row.get("model_number"),
            "price": row.get("price"),
            "stockQuantity": row.get("stock_quantity"),
            "minStockThreshold": row.get("min_stock_threshold"),
            "category": {"id": row.get("category_id"), "name": row.get("category_name")} if row.get("category_id") else None,
        }
        for row in seller_products(request.current_user["seller_id"])
    ])


@app.post("/api/seller/products")
@require_login("SELLER")
def seller_product_create():
    body = request.get_json(force=True)
    create_seller_product(
        request.current_user["seller_id"],
        {
            "name": body.get("name"),
            "description": body.get("description"),
            "category_id": body.get("categoryId"),
            "brand": body.get("brand"),
            "model_number": body.get("modelNumber"),
            "price": body.get("price"),
            "stock_quantity": body.get("stockQuantity"),
            "min_stock_threshold": body.get("minStockThreshold"),
        },
    )
    return ok(message="Seller product created")


@app.put("/api/seller/products/<int:product_id>")
@require_login("SELLER")
def seller_product_update(product_id):
    body = request.get_json(force=True)
    update_seller_product(
        request.current_user["seller_id"],
        product_id,
        {
            "name": body.get("name"),
            "description": body.get("description"),
            "category_id": body.get("categoryId"),
            "brand": body.get("brand"),
            "model_number": body.get("modelNumber"),
            "price": body.get("price"),
            "stock_quantity": body.get("stockQuantity"),
            "min_stock_threshold": body.get("minStockThreshold"),
        },
    )
    return ok(message="Seller product updated")


@app.delete("/api/seller/products/<int:product_id>")
@require_login("SELLER")
def seller_product_delete(product_id):
    archive_seller_product(request.current_user["seller_id"], product_id)
    return ok(message="Seller product deleted")


@app.get("/api/seller/supply-requests")
@require_login("SELLER")
def seller_supply_requests():
    return ok([serialize_supply(row) for row in list_seller_requests(request.current_user["seller_id"])])


@app.put("/api/seller/supply-requests/<int:request_id>")
@require_login("SELLER")
def seller_supply_request_update(request_id):
    body = request.get_json(force=True)
    respond_supply_request(request_id, request.current_user["seller_id"], body.get("status"), body.get("remarks"))
    return ok(message="Supply request updated")


@app.get("/api/health")
def health():
    return ok({"status": "ok"})


@app.errorhandler(Exception)
def handle_error(error):
    return fail(str(error), 500)


if __name__ == "__main__":
    app.run(debug=True, port=8501)
