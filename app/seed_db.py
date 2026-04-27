"""
seed_db.py — Run this once to populate your database with sample data.
Usage: python seed_db.py
"""
import psycopg2
import os

conn = psycopg2.connect(
    host=os.environ.get('DB_HOST', 'localhost'),
    port=os.environ.get('DB_PORT', 5432),
    dbname=os.environ.get('DB_NAME', 'shopdb'),
    user=os.environ.get('DB_USER', 'postgres'),
    password=os.environ.get('DB_PASSWORD', ''),
)
cur = conn.cursor()

# Warehouses
cur.execute("INSERT INTO warehouse (address) VALUES ('123 North Ave, Chicago, IL') ON CONFLICT DO NOTHING")
cur.execute("INSERT INTO warehouse (address) VALUES ('456 South Blvd, Los Angeles, CA') ON CONFLICT DO NOTHING")

# Staff
cur.execute("""
    INSERT INTO staff_member (name, address, salary, job_title)
    VALUES ('Alice Manager', '789 Admin Rd', 75000, 'Store Manager')
    ON CONFLICT DO NOTHING
""")

# Customers
cur.execute("INSERT INTO customer (name) VALUES ('Bob Smith') ON CONFLICT DO NOTHING")
cur.execute("INSERT INTO customer (name) VALUES ('Carol Jones') ON CONFLICT DO NOTHING")

# Products
products = [
    ('Running Shoes', 'Apparel', 89.99, 'Footwear', 'Nike', '10', 'Lightweight and comfortable running shoes.'),
    ('Winter Jacket', 'Apparel', 149.99, 'Outerwear', 'Patagonia', 'L', 'Warm insulated jacket for cold weather.'),
    ('Organic Apples', 'Food', 4.99, 'Fruit', 'FreshFarm', '1lb bag', 'Crisp organic apples from local farms.'),
    ('Coffee Beans', 'Food', 14.99, 'Beverage', 'BlueBottle', '12oz', 'Single-origin medium roast coffee.'),
    ('Wireless Headphones', 'Electronics', 199.99, 'Audio', 'Sony', None, 'Noise-cancelling over-ear headphones.'),
    ('Yoga Mat', 'Sports', 39.99, 'Fitness', 'Manduka', '6mm', 'Non-slip premium yoga mat.'),
    ('Desk Lamp', 'Home', 49.99, 'Lighting', 'BenQ', None, 'Adjustable LED desk lamp with USB charging.'),
    ('Notebook', 'Stationery', 9.99, 'Writing', 'Leuchtturm', 'A5', 'Hardcover dotted notebook.'),
]
for p in products:
    cur.execute("""
        INSERT INTO product (name, category, price, type, brand, size, description)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT DO NOTHING
    """, p)

conn.commit()

# Stock: put products in warehouses
cur.execute("SELECT product_id FROM product ORDER BY product_id")
pids = [r[0] for r in cur.fetchall()]
cur.execute("SELECT warehouse_id FROM warehouse ORDER BY warehouse_id LIMIT 2")
wids = [r[0] for r in cur.fetchall()]

for i, pid in enumerate(pids):
    wid = wids[i % len(wids)]
    cur.execute("""
        INSERT INTO stock (product_id, warehouse_id, qnum)
        VALUES (%s, %s, %s)
        ON CONFLICT (product_id, warehouse_id) DO UPDATE SET qnum = EXCLUDED.qnum
    """, (pid, wid, 50))

# Add address + card for first customer
cur.execute("SELECT customer_id FROM customer ORDER BY customer_id LIMIT 1")
cid = cur.fetchone()[0]
cur.execute("INSERT INTO customer_address (customer_id, address) VALUES (%s, '100 Home St, Cincinnati, OH') ON CONFLICT DO NOTHING", (cid,))
cur.execute("INSERT INTO credit_card (customer_id, number, address) VALUES (%s, '4111111111111111', '100 Home St, Cincinnati, OH') ON CONFLICT DO NOTHING", (cid,))

conn.commit()
cur.close()
conn.close()
print("✓ Database seeded successfully!")
print("\nSample login credentials:")
print("  Staff  → role: staff,    ID: 1")
print("  Customer → role: customer, ID: 1")
