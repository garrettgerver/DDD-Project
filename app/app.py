from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import psycopg2
import psycopg2.extras
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'shopapp_secret_key_2024'

# ── DB connection ────────────────────────────────────────────────────────────
def get_db():
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', 5432),
        dbname=os.environ.get('DB_NAME', 'shopdb'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', ''),
        cursor_factory=psycopg2.extras.RealDictCursor
    )

def query(sql, params=(), fetchone=False, fetchall=False, commit=False):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    result = None
    if fetchone:
        result = cur.fetchone()
    elif fetchall:
        result = cur.fetchall()
    if commit:
        conn.commit()
    cur.close()
    conn.close()
    return result

# ── Auth helpers ─────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*a, **kw)
    return dec

def staff_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if session.get('role') != 'staff':
            flash('Staff access required.', 'error')
            return redirect(url_for('index'))
        return f(*a, **kw)
    return dec

def customer_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if session.get('role') != 'customer':
            flash('Customer access required.', 'error')
            return redirect(url_for('index'))
        return f(*a, **kw)
    return dec

# ── Cart helper ───────────────────────────────────────────────────────────────
def get_cart():
    return session.get('cart', {})

def save_cart(cart):
    session['cart'] = cart
    session.modified = True

def cart_count():
    return sum(get_cart().values())

app.jinja_env.globals['cart_count'] = cart_count

# ═══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    products = query('SELECT * FROM product ORDER BY product_id LIMIT 12', fetchall=True)
    categories = query('SELECT DISTINCT category FROM product WHERE category IS NOT NULL ORDER BY category', fetchall=True)
    return render_template('index.html', products=products, categories=categories)

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form['role']
        uid  = request.form.get('id', '').strip()
        if not uid.isdigit():
            flash('Please enter a valid numeric ID.', 'error')
            return render_template('login.html')
        uid = int(uid)
        if role == 'customer':
            row = query('SELECT * FROM customer WHERE customer_id=%s', (uid,), fetchone=True)
            if row:
                session['user'] = dict(row)
                session['role'] = 'customer'
                return redirect(url_for('index'))
        elif role == 'staff':
            row = query('SELECT * FROM staff_member WHERE staff_id=%s', (uid,), fetchone=True)
            if row:
                session['user'] = dict(row)
                session['role'] = 'staff'
                return redirect(url_for('index'))
        flash('User not found.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash('Name is required.', 'error')
            return render_template('register.html')
        row = query('INSERT INTO customer (name) VALUES (%s) RETURNING customer_id, name, balance',
                    (name,), fetchone=True, commit=True)
        flash(f'Account created! Your customer ID is {row["customer_id"]}. Use it to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# ── Products ──────────────────────────────────────────────────────────────────
@app.route('/products')
def products():
    cat = request.args.get('category', '')
    q   = request.args.get('q', '')
    sql = 'SELECT * FROM product WHERE 1=1'
    params = []
    if cat:
        sql += ' AND category=%s'; params.append(cat)
    if q:
        sql += ' AND (name ILIKE %s OR description ILIKE %s)'; params += [f'%{q}%', f'%{q}%']
    sql += ' ORDER BY name'
    prods = query(sql, params, fetchall=True)
    cats  = query('SELECT DISTINCT category FROM product WHERE category IS NOT NULL ORDER BY category', fetchall=True)
    return render_template('products.html', products=prods, categories=cats, selected_cat=cat, q=q)

@app.route('/product/<int:pid>')
def product_detail(pid):
    p = query('SELECT * FROM product WHERE product_id=%s', (pid,), fetchone=True)
    if not p:
        flash('Product not found.', 'error')
        return redirect(url_for('products'))
    stock = query('''SELECT s.qnum, w.address FROM stock s
                     JOIN warehouse w ON w.warehouse_id=s.warehouse_id
                     WHERE s.product_id=%s''', (pid,), fetchall=True)
    total_stock = sum(r['qnum'] for r in stock) if stock else 0
    return render_template('product_detail.html', product=p, stock=stock, total_stock=total_stock)

# ── Staff: product CRUD ───────────────────────────────────────────────────────
@app.route('/staff/products')
@login_required
@staff_required
def staff_products():
    prods = query('SELECT * FROM product ORDER BY product_id', fetchall=True)
    return render_template('staff_products.html', products=prods)

@app.route('/staff/products/add', methods=['GET', 'POST'])
@login_required
@staff_required
def staff_add_product():
    if request.method == 'POST':
        f = request.form
        query('''INSERT INTO product (name,category,price,type,brand,size,description)
                 VALUES (%s,%s,%s,%s,%s,%s,%s)''',
              (f['name'], f.get('category'), float(f['price']),
               f.get('type'), f.get('brand'), f.get('size'), f.get('description')),
              commit=True)
        flash('Product added.', 'success')
        return redirect(url_for('staff_products'))
    return render_template('staff_product_form.html', product=None)

@app.route('/staff/products/<int:pid>/edit', methods=['GET', 'POST'])
@login_required
@staff_required
def staff_edit_product(pid):
    p = query('SELECT * FROM product WHERE product_id=%s', (pid,), fetchone=True)
    if request.method == 'POST':
        f = request.form
        query('''UPDATE product SET name=%s,category=%s,price=%s,type=%s,brand=%s,size=%s,description=%s
                 WHERE product_id=%s''',
              (f['name'], f.get('category'), float(f['price']),
               f.get('type'), f.get('brand'), f.get('size'), f.get('description'), pid),
              commit=True)
        flash('Product updated.', 'success')
        return redirect(url_for('staff_products'))
    return render_template('staff_product_form.html', product=p)

@app.route('/staff/products/<int:pid>/delete', methods=['POST'])
@login_required
@staff_required
def staff_delete_product(pid):
    query('DELETE FROM product WHERE product_id=%s', (pid,), commit=True)
    flash('Product deleted.', 'success')
    return redirect(url_for('staff_products'))

# ── Staff: stock management ───────────────────────────────────────────────────
@app.route('/staff/stock')
@login_required
@staff_required
def staff_stock():
    stock = query('''SELECT s.*, p.name AS product_name, w.address AS warehouse_address
                     FROM stock s
                     JOIN product p ON p.product_id=s.product_id
                     JOIN warehouse w ON w.warehouse_id=s.warehouse_id
                     ORDER BY p.name''', fetchall=True)
    products   = query('SELECT product_id, name FROM product ORDER BY name', fetchall=True)
    warehouses = query('SELECT warehouse_id, address FROM warehouse ORDER BY address', fetchall=True)
    return render_template('staff_stock.html', stock=stock, products=products, warehouses=warehouses)

@app.route('/staff/stock/add', methods=['POST'])
@login_required
@staff_required
def staff_add_stock():
    pid = int(request.form['product_id'])
    wid = int(request.form['warehouse_id'])
    qty = int(request.form['quantity'])
    query('''INSERT INTO stock (product_id, warehouse_id, qnum) VALUES (%s,%s,%s)
             ON CONFLICT (product_id, warehouse_id) DO UPDATE SET qnum = stock.qnum + EXCLUDED.qnum''',
          (pid, wid, qty), commit=True)
    flash('Stock updated.', 'success')
    return redirect(url_for('staff_stock'))

# ── Staff: customer info ──────────────────────────────────────────────────────
@app.route('/staff/customers')
@login_required
@staff_required
def staff_customers():
    customers = query('SELECT * FROM customer ORDER BY customer_id', fetchall=True)
    return render_template('staff_customers.html', customers=customers)

@app.route('/staff/customers/<int:cid>')
@login_required
@staff_required
def staff_customer_detail(cid):
    c      = query('SELECT * FROM customer WHERE customer_id=%s', (cid,), fetchone=True)
    orders = query('''SELECT o.*, dp.type AS delivery_type, dp.price AS delivery_price, dp.delivery_date
                      FROM "order" o
                      LEFT JOIN delivery_plan dp ON dp.order_id=o.order_id
                      WHERE o.customer_id=%s ORDER BY o.order_id DESC''', (cid,), fetchall=True)
    return render_template('staff_customer_detail.html', customer=c, orders=orders)

@app.route('/staff/orders/<int:oid>/status', methods=['POST'])
@login_required
@staff_required
def staff_update_order_status(oid):
    status = request.form['status']
    query('UPDATE "order" SET status=%s WHERE order_id=%s', (status, oid), commit=True)
    flash('Order status updated.', 'success')
    return redirect(request.referrer or url_for('staff_customers'))

# ── Cart ──────────────────────────────────────────────────────────────────────
@app.route('/cart')
@login_required
@customer_required
def cart():
    cart = get_cart()
    items = []
    total = 0
    for pid_str, qty in cart.items():
        p = query('SELECT * FROM product WHERE product_id=%s', (int(pid_str),), fetchone=True)
        if p:
            subtotal = float(p['price']) * qty
            total += subtotal
            items.append({'product': p, 'qty': qty, 'subtotal': subtotal})
    return render_template('cart.html', items=items, total=total)

@app.route('/cart/add/<int:pid>', methods=['POST'])
@login_required
@customer_required
def cart_add(pid):
    qty  = int(request.form.get('qty', 1))
    cart = get_cart()
    cart[str(pid)] = cart.get(str(pid), 0) + qty
    save_cart(cart)
    flash('Added to cart.', 'success')
    return redirect(request.referrer or url_for('products'))

@app.route('/cart/update/<int:pid>', methods=['POST'])
@login_required
@customer_required
def cart_update(pid):
    qty  = int(request.form.get('qty', 0))
    cart = get_cart()
    if qty <= 0:
        cart.pop(str(pid), None)
    else:
        cart[str(pid)] = qty
    save_cart(cart)
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:pid>', methods=['POST'])
@login_required
@customer_required
def cart_remove(pid):
    cart = get_cart()
    cart.pop(str(pid), None)
    save_cart(cart)
    return redirect(url_for('cart'))

# ── Checkout / Orders ────────────────────────────────────────────────────────
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
@customer_required
def checkout():
    cid   = session['user']['customer_id']
    cards = query('SELECT * FROM credit_card WHERE customer_id=%s', (cid,), fetchall=True)
    cart  = get_cart()
    if not cart:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('cart'))

    items = []
    subtotal = 0
    for pid_str, qty in cart.items():
        p = query('SELECT * FROM product WHERE product_id=%s', (int(pid_str),), fetchone=True)
        if p:
            s = float(p['price']) * qty
            subtotal += s
            items.append({'product': p, 'qty': qty, 'subtotal': s})

    if request.method == 'POST':
        delivery_type  = request.form.get('delivery_type', 'standard')
        delivery_price = 5.99 if delivery_type == 'standard' else 14.99
        card_id        = request.form.get('card_id')

        conn = get_db()
        cur  = conn.cursor()
        try:
            # Create order
            cur.execute('INSERT INTO "order" (customer_id) VALUES (%s) RETURNING order_id', (cid,))
            oid = cur.fetchone()['order_id']
            # Order contents
            for pid_str, qty in cart.items():
                cur.execute('INSERT INTO order_content (order_id,product_id,quantity) VALUES (%s,%s,%s)',
                            (oid, int(pid_str), qty))
                # Reduce stock (bonus: availability check)
                cur.execute('''UPDATE stock SET qnum = qnum - %s
                               WHERE product_id=%s AND qnum >= %s''', (qty, int(pid_str), qty))
            # Delivery plan
            cur.execute('''INSERT INTO delivery_plan (order_id,type,price)
                           VALUES (%s,%s,%s)''', (oid, delivery_type, delivery_price))
            # Update balance
            total = subtotal + delivery_price
            cur.execute('UPDATE customer SET balance = balance + %s WHERE customer_id=%s', (total, cid))
            conn.commit()
            save_cart({})
            session['user']['balance'] = float(session['user'].get('balance', 0)) + total
            flash(f'Order #{oid} placed successfully!', 'success')
            return redirect(url_for('orders'))
        except Exception as e:
            conn.rollback()
            flash(f'Order failed: {e}', 'error')
        finally:
            cur.close(); conn.close()

    return render_template('checkout.html', items=items, subtotal=subtotal, cards=cards)

@app.route('/orders')
@login_required
@customer_required
def orders():
    cid    = session['user']['customer_id']
    orders = query('''SELECT o.*, dp.type AS delivery_type, dp.price AS delivery_price,
                             dp.delivery_date, dp.ship_date
                      FROM "order" o
                      LEFT JOIN delivery_plan dp ON dp.order_id=o.order_id
                      WHERE o.customer_id=%s ORDER BY o.order_id DESC''', (cid,), fetchall=True)
    return render_template('orders.html', orders=orders)

@app.route('/orders/<int:oid>')
@login_required
@customer_required
def order_detail(oid):
    cid   = session['user']['customer_id']
    order = query('SELECT * FROM "order" WHERE order_id=%s AND customer_id=%s', (oid, cid), fetchone=True)
    if not order:
        flash('Order not found.', 'error')
        return redirect(url_for('orders'))
    items = query('''SELECT oc.quantity, p.name, p.price, oc.quantity*p.price AS subtotal
                     FROM order_content oc JOIN product p ON p.product_id=oc.product_id
                     WHERE oc.order_id=%s''', (oid,), fetchall=True)
    dp    = query('SELECT * FROM delivery_plan WHERE order_id=%s', (oid,), fetchone=True)
    return render_template('order_detail.html', order=order, items=items, dp=dp)

# ── Account ───────────────────────────────────────────────────────────────────
@app.route('/account')
@login_required
@customer_required
def account():
    cid      = session['user']['customer_id']
    customer = query('SELECT * FROM customer WHERE customer_id=%s', (cid,), fetchone=True)
    addresses= query('SELECT * FROM customer_address WHERE customer_id=%s', (cid,), fetchall=True)
    cards    = query('SELECT * FROM credit_card WHERE customer_id=%s', (cid,), fetchall=True)
    return render_template('account.html', customer=customer, addresses=addresses, cards=cards)

# addresses
@app.route('/account/address/add', methods=['POST'])
@login_required
@customer_required
def add_address():
    cid = session['user']['customer_id']
    query('INSERT INTO customer_address (customer_id,address) VALUES (%s,%s)',
          (cid, request.form['address']), commit=True)
    flash('Address added.', 'success')
    return redirect(url_for('account'))

@app.route('/account/address/<int:aid>/edit', methods=['POST'])
@login_required
@customer_required
def edit_address(aid):
    cid = session['user']['customer_id']
    query('UPDATE customer_address SET address=%s WHERE id=%s AND customer_id=%s',
          (request.form['address'], aid, cid), commit=True)
    flash('Address updated.', 'success')
    return redirect(url_for('account'))

@app.route('/account/address/<int:aid>/delete', methods=['POST'])
@login_required
@customer_required
def delete_address(aid):
    cid = session['user']['customer_id']
    query('DELETE FROM customer_address WHERE id=%s AND customer_id=%s', (aid, cid), commit=True)
    flash('Address removed.', 'success')
    return redirect(url_for('account'))

# credit cards
@app.route('/account/card/add', methods=['POST'])
@login_required
@customer_required
def add_card():
    cid = session['user']['customer_id']
    query('INSERT INTO credit_card (customer_id,number,address) VALUES (%s,%s,%s)',
          (cid, request.form['number'], request.form['address']), commit=True)
    flash('Card added.', 'success')
    return redirect(url_for('account'))

@app.route('/account/card/<int:crd>/edit', methods=['POST'])
@login_required
@customer_required
def edit_card(crd):
    cid = session['user']['customer_id']
    query('UPDATE credit_card SET number=%s, address=%s WHERE card_id=%s AND customer_id=%s',
          (request.form['number'], request.form['address'], crd, cid), commit=True)
    flash('Card updated.', 'success')
    return redirect(url_for('account'))

@app.route('/account/card/<int:crd>/delete', methods=['POST'])
@login_required
@customer_required
def delete_card(crd):
    cid = session['user']['customer_id']
    query('DELETE FROM credit_card WHERE card_id=%s AND customer_id=%s', (crd, cid), commit=True)
    flash('Card removed.', 'success')
    return redirect(url_for('account'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
