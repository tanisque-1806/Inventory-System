# Inventory DBMS

Inventory DBMS is a standalone Python + MySQL warehouse system for electrical inventory management. It keeps the same business roles as your earlier project, but it is not connected to the Java project and runs independently with its own backend, frontend, and database.

## Business Description

This project manages an electric warehouse where:
- `Admin` is the warehouse owner
- `Seller` is the supplier
- `User` is the small dealer

The warehouse can sell items to dealers, request stock from suppliers, and keep stock movement synchronized directly through DBMS logic.

## DBMS-First Features

- User cart and order placement using stored procedures
- Product stock auto-updated after orders through trigger logic
- Admin notification created automatically whenever any item drops below `20`
- Seller inventory handled separately in `seller_products`
- Admin procurement cart where admin can review and edit supplier order lines before submission
- Seller receives admin requests and can approve or reject them
- On supplier approval:
  - supplier stock decreases
  - admin warehouse stock increases
- Reporting views for low stock, admin inventory, store products, supplier inventory, and order summaries

## Project Structure

```text
inventory-dbms/
  app.py
  requirements.txt
  .env.example
  app/
    __init__.py
    auth.py
    config.py
    db.py
    routes/
      auth.py
      admin.py
      seller.py
      user.py
  database/
    schema.sql
```

## Main Database Objects

### Views
- `vw_admin_inventory`
- `vw_store_products`
- `vw_low_stock_alerts`
- `vw_available_supplier_inventory`
- `vw_supply_request_admin`
- `vw_supply_request_seller`
- `vw_order_summary`

### Procedures
- `sp_add_to_user_cart`
- `sp_place_order`
- `sp_add_procurement_cart_item`
- `sp_submit_procurement_cart`
- `sp_respond_supply_request`

### Triggers
- `trg_order_item_reduce_stock`
- `trg_notify_low_stock_after_product_update`
- `trg_notify_low_stock_after_seller_update`

## Setup

### 1. Create virtual environment

```powershell
cd C:\Users\98har\Desktop\inventory-dbms
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` and update MySQL settings.

### 3. Create database

```powershell
mysql -u root -p < database\schema.sql
```

This creates the `inventory_py` database and seeds default users.

### 4. Run Streamlit Frontend

```powershell
inventory\Scripts\streamlit run streamlit_app.py
```

App runs at:
- [http://localhost:8501](http://localhost:8501)

The Streamlit app now provides:
- Admin panel
- Seller panel
- User/dealer panel
- Login and registration
- Product, category, cart, order, procurement, supply request, and notification flows

## Default Accounts

These rows are seeded in SQL:

- Admin: `admin@inventory.com`
- Seller: `seller@inventory.com`
- User: `user@inventory.com`

Seeded passwords:
- Admin: `admin123`
- Seller: `seller123`
- User: `user123`

## Important Flow

1. Seller adds inventory in `seller_products`
2. Admin sees available supplier inventory through `vw_available_supplier_inventory`
3. Admin builds a procurement cart
4. Admin edits cart lines if needed
5. Admin submits the cart
6. Seller receives pending requests
7. Seller approves or rejects
8. If approved, the DB procedure updates seller stock and admin stock
9. If any stock drops below `20`, admin gets a notification automatically

## Next Suggested Step

This project now includes a Streamlit frontend so the main workflows can be used from one Python app instead of separate HTML pages.
