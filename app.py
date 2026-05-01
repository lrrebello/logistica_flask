import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Supplier, Product, Client, Address, Stock, Vehicle, Driver, Order, OrderItem
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== AUTENTICAÇÃO ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_signed_in = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou senha inválidos', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if User.query.filter_by(email=email).first():
            flash('Email já registrado', 'danger')
            return redirect(url_for('register'))
        
        if password != password_confirm:
            flash('Senhas não conferem', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            open_id=email,
            name=name,
            email=email,
            role='user',
            login_method='local'
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registro realizado com sucesso! Faça login', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# ==================== DASHBOARD ====================

@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role not in ['admin', 'user']:
        flash('Acesso negado', 'danger')
        return redirect(url_for('logout'))
    
    # Estatísticas
    total_suppliers = Supplier.query.count()
    total_products = Product.query.count()
    total_clients = Client.query.count()
    total_orders = Order.query.count()
    
    # Pedidos por status
    pending_orders = Order.query.filter_by(status='pending').count()
    in_transit_orders = Order.query.filter_by(status='in_transit').count()
    delivered_orders = Order.query.filter_by(status='delivered').count()
    
    # Stock crítico
    critical_stock = db.session.query(Stock).filter(
        Stock.quantity <= Stock.minimum_level
    ).count()
    
    stats = {
        'total_suppliers': total_suppliers,
        'total_products': total_products,
        'total_clients': total_clients,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'in_transit_orders': in_transit_orders,
        'delivered_orders': delivered_orders,
        'critical_stock': critical_stock,
    }
    
    return render_template('dashboard.html', stats=stats)

# ==================== FORNECEDORES ====================

@app.route('/suppliers')
@login_required
def suppliers_list():
    page = request.args.get('page', 1, type=int)
    suppliers = Supplier.query.paginate(page=page, per_page=10)
    return render_template('suppliers/list.html', suppliers=suppliers)

@app.route('/suppliers/new', methods=['GET', 'POST'])
@login_required
def suppliers_new():
    if request.method == 'POST':
        supplier = Supplier(
            name=request.form.get('name'),
            contact_info=request.form.get('contact_info'),
            email=request.form.get('email'),
            phone=request.form.get('phone')
        )
        db.session.add(supplier)
        db.session.commit()
        flash('Fornecedor criado com sucesso', 'success')
        return redirect(url_for('suppliers_list'))
    
    return render_template('suppliers/form.html', supplier=None)

@app.route('/suppliers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def suppliers_edit(id):
    supplier = Supplier.query.get_or_404(id)
    
    if request.method == 'POST':
        supplier.name = request.form.get('name')
        supplier.contact_info = request.form.get('contact_info')
        supplier.email = request.form.get('email')
        supplier.phone = request.form.get('phone')
        db.session.commit()
        flash('Fornecedor atualizado com sucesso', 'success')
        return redirect(url_for('suppliers_list'))
    
    return render_template('suppliers/form.html', supplier=supplier)

@app.route('/suppliers/<int:id>/delete', methods=['POST'])
@login_required
def suppliers_delete(id):
    supplier = Supplier.query.get_or_404(id)
    db.session.delete(supplier)
    db.session.commit()
    flash('Fornecedor deletado com sucesso', 'success')
    return redirect(url_for('suppliers_list'))

# ==================== PRODUTOS ====================

@app.route('/products')
@login_required
def products_list():
    page = request.args.get('page', 1, type=int)
    products = Product.query.paginate(page=page, per_page=10)
    return render_template('products/list.html', products=products)

@app.route('/products/new', methods=['GET', 'POST'])
@login_required
def products_new():
    suppliers = Supplier.query.all()
    
    if request.method == 'POST':
        product = Product(
            name=request.form.get('name'),
            description=request.form.get('description'),
            price=request.form.get('price'),
            unit=request.form.get('unit', 'kg'),
            supplier_id=request.form.get('supplier_id') or None
        )
        db.session.add(product)
        db.session.flush()
        
        # Criar stock
        stock = Stock(
            product_id=product.id,
            quantity=0,
            minimum_level=request.form.get('minimum_level', 0)
        )
        db.session.add(stock)
        db.session.commit()
        
        flash('Produto criado com sucesso', 'success')
        return redirect(url_for('products_list'))
    
    return render_template('products/form.html', product=None, suppliers=suppliers)

@app.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def products_edit(id):
    product = Product.query.get_or_404(id)
    suppliers = Supplier.query.all()
    
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = request.form.get('price')
        product.unit = request.form.get('unit', 'kg')
        product.supplier_id = request.form.get('supplier_id') or None
        
        if product.stock:
            product.stock.minimum_level = request.form.get('minimum_level', 0)
        
        db.session.commit()
        flash('Produto atualizado com sucesso', 'success')
        return redirect(url_for('products_list'))
    
    return render_template('products/form.html', product=product, suppliers=suppliers)

@app.route('/products/<int:id>/delete', methods=['POST'])
@login_required
def products_delete(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Produto deletado com sucesso', 'success')
    return redirect(url_for('products_list'))

# ==================== CLIENTES ====================

@app.route('/clients')
@login_required
def clients_list():
    page = request.args.get('page', 1, type=int)
    clients = Client.query.paginate(page=page, per_page=10)
    return render_template('clients/list.html', clients=clients)

@app.route('/clients/new', methods=['GET', 'POST'])
@login_required
def clients_new():
    if request.method == 'POST':
        client = Client(
            name=request.form.get('name'),
            tax_id=request.form.get('tax_id'),
            email=request.form.get('email'),
            phone=request.form.get('phone')
        )
        db.session.add(client)
        db.session.commit()
        flash('Cliente criado com sucesso', 'success')
        return redirect(url_for('clients_list'))
    
    return render_template('clients/form.html', client=None)

@app.route('/clients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def clients_edit(id):
    client = Client.query.get_or_404(id)
    
    if request.method == 'POST':
        client.name = request.form.get('name')
        client.tax_id = request.form.get('tax_id')
        client.email = request.form.get('email')
        client.phone = request.form.get('phone')
        db.session.commit()
        flash('Cliente atualizado com sucesso', 'success')
        return redirect(url_for('clients_list'))
    
    return render_template('clients/form.html', client=client)

@app.route('/clients/<int:id>/delete', methods=['POST'])
@login_required
def clients_delete(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash('Cliente deletado com sucesso', 'success')
    return redirect(url_for('clients_list'))

# ==================== ENDEREÇOS ====================

@app.route('/clients/<int:client_id>/addresses')
@login_required
def addresses_list(client_id):
    client = Client.query.get_or_404(client_id)
    return render_template('addresses/list.html', client=client)

@app.route('/clients/<int:client_id>/addresses/new', methods=['GET', 'POST'])
@login_required
def addresses_new(client_id):
    client = Client.query.get_or_404(client_id)
    
    if request.method == 'POST':
        address = Address(
            client_id=client_id,
            street=request.form.get('street'),
            city=request.form.get('city'),
            postal_code=request.form.get('postal_code'),
            latitude=request.form.get('latitude'),
            longitude=request.form.get('longitude'),
            is_headquarters=request.form.get('is_headquarters') == 'on'
        )
        db.session.add(address)
        db.session.commit()
        flash('Endereço criado com sucesso', 'success')
        return redirect(url_for('addresses_list', client_id=client_id))
    
    return render_template('addresses/form.html', client=client, address=None)

@app.route('/addresses/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def addresses_edit(id):
    address = Address.query.get_or_404(id)
    
    if request.method == 'POST':
        address.street = request.form.get('street')
        address.city = request.form.get('city')
        address.postal_code = request.form.get('postal_code')
        address.latitude = request.form.get('latitude')
        address.longitude = request.form.get('longitude')
        address.is_headquarters = request.form.get('is_headquarters') == 'on'
        db.session.commit()
        flash('Endereço atualizado com sucesso', 'success')
        return redirect(url_for('addresses_list', client_id=address.client_id))
    
    return render_template('addresses/form.html', client=address.client, address=address)

@app.route('/addresses/<int:id>/delete', methods=['POST'])
@login_required
def addresses_delete(id):
    address = Address.query.get_or_404(id)
    client_id = address.client_id
    db.session.delete(address)
    db.session.commit()
    flash('Endereço deletado com sucesso', 'success')
    return redirect(url_for('addresses_list', client_id=client_id))

# ==================== STOCK ====================

@app.route('/stock')
@login_required
def stock_list():
    page = request.args.get('page', 1, type=int)
    stock = db.session.query(Stock).join(Product).paginate(page=page, per_page=10)
    return render_template('stock/list.html', stock=stock)

@app.route('/stock/<int:id>/update', methods=['POST'])
@login_required
def stock_update(id):
    stock = Stock.query.get_or_404(id)
    stock.quantity = request.form.get('quantity')
    stock.minimum_level = request.form.get('minimum_level')
    stock.last_updated = datetime.utcnow()
    db.session.commit()
    flash('Stock atualizado com sucesso', 'success')
    return redirect(url_for('stock_list'))

# ==================== PEDIDOS ====================

@app.route('/orders')
@login_required
def orders_list():
    page = request.args.get('page', 1, type=int)
    orders = Order.query.paginate(page=page, per_page=10)
    return render_template('orders/list.html', orders=orders)

@app.route('/orders/new', methods=['GET', 'POST'])
@login_required
def orders_new():
    clients = Client.query.all()
    products = Product.query.all()
    
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        address_id = request.form.get('address_id')
        notes = request.form.get('notes')
        
        order = Order(
            order_number=f"PED-{datetime.utcnow().timestamp()}",
            client_id=client_id,
            address_id=address_id,
            status='pending',
            notes=notes
        )
        db.session.add(order)
        db.session.flush()
        
        # Adicionar itens do pedido
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        prices = request.form.getlist('price[]')
        
        total = 0
        for product_id, quantity, price in zip(product_ids, quantities, prices):
            if product_id and quantity and price:
                subtotal = float(quantity) * float(price)
                item = OrderItem(
                    order_id=order.id,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=price,
                    subtotal=subtotal
                )
                db.session.add(item)
                total += subtotal
        
        order.total_amount = total
        db.session.commit()
        
        flash('Pedido criado com sucesso', 'success')
        return redirect(url_for('orders_list'))
    
    return render_template('orders/form.html', clients=clients, products=products, order=None)

@app.route('/orders/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def orders_edit(id):
    order = Order.query.get_or_404(id)
    
    if request.method == 'POST':
        order.status = request.form.get('status')
        order.notes = request.form.get('notes')
        db.session.commit()
        flash('Pedido atualizado com sucesso', 'success')
        return redirect(url_for('orders_list'))
    
    return render_template('orders/edit.html', order=order)

# ==================== FROTA ====================

@app.route('/vehicles')
@login_required
def vehicles_list():
    page = request.args.get('page', 1, type=int)
    vehicles = Vehicle.query.paginate(page=page, per_page=10)
    return render_template('vehicles/list.html', vehicles=vehicles)

@app.route('/vehicles/new', methods=['GET', 'POST'])
@login_required
def vehicles_new():
    if request.method == 'POST':
        vehicle = Vehicle(
            plate=request.form.get('plate'),
            model=request.form.get('model'),
            type=request.form.get('type'),
            max_weight=request.form.get('max_weight'),
            max_height=request.form.get('max_height'),
            status='available'
        )
        db.session.add(vehicle)
        db.session.commit()
        flash('Veículo criado com sucesso', 'success')
        return redirect(url_for('vehicles_list'))
    
    return render_template('vehicles/form.html', vehicle=None)

@app.route('/drivers')
@login_required
def drivers_list():
    page = request.args.get('page', 1, type=int)
    drivers = Driver.query.paginate(page=page, per_page=10)
    return render_template('drivers/list.html', drivers=drivers)

@app.route('/drivers/new', methods=['GET', 'POST'])
@login_required
def drivers_new():
    if request.method == 'POST':
        driver = Driver(
            name=request.form.get('name'),
            license_number=request.form.get('license_number'),
            license_expiry=request.form.get('license_expiry'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            emergency_contact=request.form.get('emergency_contact'),
            hire_date=request.form.get('hire_date'),
            status='active'
        )
        db.session.add(driver)
        db.session.commit()
        flash('Motorista criado com sucesso', 'success')
        return redirect(url_for('drivers_list'))
    
    return render_template('drivers/form.html', driver=None)

# ==================== ERRO 404 ====================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

# ==================== INICIALIZAR ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
