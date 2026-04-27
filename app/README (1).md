# ShopApp — CS4092 Online Shopping Application

A full-featured online shopping application built with Python (Flask) and PostgreSQL.

## Project Structure

```
shop_app/
├── app.py              # Main Flask application (all routes & logic)
├── seed_db.py          # Database seed script (sample data)
├── requirements.txt    # Python dependencies
└── templates/
    ├── base.html                  # Base layout + nav
    ├── index.html                 # Home page
    ├── login.html                 # Login
    ├── register.html              # Customer registration
    ├── products.html              # Product catalog with search/filter
    ├── product_detail.html        # Single product view + add to cart
    ├── cart.html                  # Shopping cart
    ├── checkout.html              # Checkout + delivery/payment
    ├── orders.html                # Customer order history
    ├── order_detail.html          # Single order view
    ├── account.html               # Customer account (addresses + cards)
    ├── staff_products.html        # Staff: product list
    ├── staff_product_form.html    # Staff: add/edit product
    ├── staff_stock.html           # Staff: stock management
    ├── staff_customers.html       # Staff: customer list
    └── staff_customer_detail.html # Staff: customer + order management
```

## Setup

### 1. Create PostgreSQL database

```bash
psql -U postgres
CREATE DATABASE shopdb;
\q
```

### 2. Run the schema SQL

```bash
psql -U postgres -d shopdb -f DDDProject_RelationalSchema.sql
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure database connection (optional)

Set environment variables if your PostgreSQL credentials differ:

```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=shopdb
export DB_USER=postgres
export DB_PASSWORD=yourpassword
```

### 5. Seed sample data (optional but recommended)

```bash
python seed_db.py
```

### 6. Run the application

```bash
python app.py
```

Open http://localhost:5000 in your browser.

## Default Login IDs

After seeding:
- **Staff login**: role=staff, ID=1 (Alice Manager)
- **Customer login**: role=customer, ID=1 (Bob Smith)

## Features Implemented

### Customer
- Register a new account (receives a customer ID)
- Login by role + ID
- Browse & search products (by name, category)
- View product detail with stock availability per warehouse
- Shopping cart (add, update quantity, remove)
- Checkout with delivery type selection (standard $5.99 / express $14.99)
- Select payment method (credit card) at checkout
- View order history and order details
- Manage addresses (add, edit, delete)
- Manage credit cards (add, edit, delete)

### Staff
- Login by role + ID
- Add, edit, delete products and prices
- View and add stock to warehouses
- View all customers and their account balances
- View customer orders
- Update order status (issued → sent → received)

### Database Features Used
- Full relational schema with all tables
- ENUM types: order_status, delivery_type
- CHECK constraints on price, quantity, dates
- UNIQUE constraint on stock(product_id, warehouse_id)
- ON CONFLICT upsert for stock updates
- Customer balance tracking
- Stock reduction on order placement
