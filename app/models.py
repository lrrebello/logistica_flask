from datetime import datetime, date, time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.extensions import db

# ==================== USUÁRIOS ====================

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    open_id = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(100))
    email = db.Column(db.String(320), unique=True)
    login_method = db.Column(db.String(64))
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(20), default='user', nullable=False)  # admin, user, driver, commercial
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_signed_in = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ==================== FORNECEDORES E PRODUTOS ====================

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nif = db.Column(db.String(9))
    contact_person = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    products = db.relationship('Product', backref='supplier', lazy=True)


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    unit = db.Column(db.String(20), default='kg', nullable=False)  # kg, un, lt, cx
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    stock = db.relationship('Stock', backref='product', lazy=True, uselist=False)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)


class Stock(db.Model):
    __tablename__ = 'stock'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    reserved_quantity = db.Column(db.Numeric(12, 2), default=0)
    minimum_level = db.Column(db.Numeric(12, 2), default=0)
    maximum_level = db.Column(db.Numeric(12, 2))
    location = db.Column(db.String(50))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity


# ==================== CLIENTES E ENDEREÇOS ====================

class StopTimeConfig(db.Model):
    __tablename__ = 'stop_time_configs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # Supermercado, Padaria, Hotel, etc
    description = db.Column(db.String(200))
    base_time = db.Column(db.Integer, default=15)  # minutos
    unloading_time_per_unit = db.Column(db.Integer, default=2)  # minutos por unidade
    payment_time = db.Column(db.Integer, default=5)
    documentation_time = db.Column(db.Integer, default=3)
    setup_time = db.Column(db.Integer, default=5)  # manobra/estacionamento
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def total_time(self):
        return self.base_time + self.payment_time + self.documentation_time + self.setup_time


class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    nif = db.Column(db.String(9), unique=True)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    stop_time_config_id = db.Column(db.Integer, db.ForeignKey('stop_time_configs.id'))
    custom_stop_time = db.Column(db.Integer, nullable=True)
    average_pallets = db.Column(db.Integer, default=1)
    needs_delivery_ramp = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    addresses = db.relationship('Address', backref='client', lazy=True, cascade="all, delete-orphan")
    orders = db.relationship('Order', backref='client', lazy=True)
    stop_time_config = db.relationship('StopTimeConfig', foreign_keys=[stop_time_config_id])


class Address(db.Model):
    __tablename__ = 'addresses'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    street = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(10), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    is_headquarters = db.Column(db.Boolean, default=False)
    is_delivery_point = db.Column(db.Boolean, default=True)
    delivery_instructions = db.Column(db.Text)
    time_window_start = db.Column(db.Time)
    time_window_end = db.Column(db.Time)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# ==================== VEÍCULOS ====================

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True)
    plate = db.Column(db.String(10), unique=True, nullable=False)
    model = db.Column(db.String(50))
    brand = db.Column(db.String(50))
    type = db.Column(db.String(20), nullable=False)  # van, truck, trailer
    max_weight = db.Column(db.Numeric(10, 2))  # kg
    max_volume = db.Column(db.Numeric(10, 2))  # m³
    max_height = db.Column(db.Numeric(10, 2), nullable=True)  # m
    max_axle_load = db.Column(db.Numeric(5, 2), nullable=True)  # toneladas por eixo
    length = db.Column(db.Numeric(5, 2), nullable=True)  # metros
    width = db.Column(db.Numeric(5, 2), nullable=True)  # metros
    hazmat = db.Column(db.Boolean, default=False)
    cargo_type = db.Column(db.String(50))  # general, refrigerated, hazardous
    fuel_type = db.Column(db.String(20))
    status = db.Column(db.String(20), default='available')  # available, in_use, maintenance
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


# ==================== MOTORISTAS ====================

class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    license_number = db.Column(db.String(20), unique=True, nullable=False)
    license_expiry = db.Column(db.Date, nullable=True)
    license_category = db.Column(db.String(10))
    phone = db.Column(db.String(20), nullable=True)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='active')
    max_driving_hours_per_day = db.Column(db.Integer, default=9)
    max_driving_hours_per_week = db.Column(db.Integer, default=56)
    max_work_hours_per_day = db.Column(db.Integer, default=10)
    required_rest_after_4h30 = db.Column(db.Integer, default=45)
    required_daily_rest = db.Column(db.Integer, default=11)
    avoid_tolls = db.Column(db.Boolean, default=False)
    avoid_highways = db.Column(db.Boolean, default=False)
    prefer_scenic = db.Column(db.Boolean, default=False)
    max_speed = db.Column(db.Integer, default=120)
    preferred_start_time = db.Column(db.Time)
    preferred_end_time = db.Column(db.Time)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    user = db.relationship('User', backref='driver_profile')


# ==================== PEDIDOS ====================

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, confirmed, in_transit, delivered, cancelled
    priority = db.Column(db.String(10), default='normal')  # normal, high, urgent
    total_amount = db.Column(db.Numeric(12, 2), default=0.0, nullable=False)
    notes = db.Column(db.Text)
    internal_notes = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    delivered_at = db.Column(db.DateTime)
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    route_waypoints = db.relationship('RouteWaypoint', backref='order', lazy=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id])


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(12, 2), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(12, 2), nullable=False, default=0.0)
    
    def calculate_total(self):
        self.total_price = self.quantity * self.unit_price


# ==================== ROTAS ====================

class Route(db.Model):
    __tablename__ = 'routes'
    id = db.Column(db.Integer, primary_key=True)
    route_number = db.Column(db.String(20), unique=True, nullable=False)
    route_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    route_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed, cancelled
    estimated_clients_count = db.Column(db.Integer)
    actual_clients_count = db.Column(db.Integer)
    region = db.Column(db.String(50))
    total_distance = db.Column(db.Numeric(10, 2))
    total_estimated_duration = db.Column(db.Integer)
    total_actual_duration = db.Column(db.Integer)
    total_toll_cost = db.Column(db.Numeric(10, 2))
    total_fuel_cost = db.Column(db.Numeric(10, 2))
    optimization_method = db.Column(db.String(20))
    optimization_score = db.Column(db.Float)
    was_optimized = db.Column(db.Boolean, default=False)
    last_optimization_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    # Relacionamentos
    driver = db.relationship('Driver', backref='routes')
    vehicle = db.relationship('Vehicle', backref='routes')
    waypoints = db.relationship('RouteWaypoint', backref='route', lazy=True, 
                                cascade='all, delete-orphan', 
                                order_by='RouteWaypoint.sequence_order')
    created_by = db.relationship('User', foreign_keys=[created_by_id])


class RouteWaypoint(db.Model):
    __tablename__ = 'route_waypoints'
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)  # Pode ser nulo para pontos de início/fim
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False)
    sequence_order = db.Column(db.Integer, nullable=False)
    original_sequence_order = db.Column(db.Integer)
    is_optimized = db.Column(db.Boolean, default=False)
    optimized_by = db.Column(db.String(50))
    estimated_travel_time = db.Column(db.Integer)
    actual_travel_time = db.Column(db.Integer)
    estimated_arrival = db.Column(db.DateTime)
    actual_arrival = db.Column(db.DateTime)
    departure_time = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')
    notes = db.Column(db.Text)
    delivered_at = db.Column(db.DateTime, nullable=True)
    proof_of_delivery = db.Column(db.String(255))
    driving_time_until_rest = db.Column(db.Integer)
    required_rest_minutes = db.Column(db.Integer)
    is_rest_stop = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    address = db.relationship('Address')


# ==================== LOGS E SUPORTE ====================

class RouteOptimizationLog(db.Model):
    __tablename__ = 'route_optimization_logs'
    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    optimization_date = db.Column(db.DateTime, default=datetime.utcnow)
    algorithm_used = db.Column(db.String(50))
    original_sequence = db.Column(db.Text)
    optimized_sequence = db.Column(db.Text)
    estimated_savings_km = db.Column(db.Numeric(10, 2))
    estimated_savings_time = db.Column(db.Integer)
    applied_manually = db.Column(db.Boolean, default=False)
    applied_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes = db.Column(db.Text)
    
    route = db.relationship('Route', backref='optimization_logs')
    applied_by = db.relationship('User', foreign_keys=[applied_by_id])


class DriverDailyLog(db.Model):
    __tablename__ = 'driver_daily_logs'
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_driving_minutes = db.Column(db.Integer, default=0)
    total_rest_minutes = db.Column(db.Integer, default=0)
    total_work_minutes = db.Column(db.Integer, default=0)
    violations = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    driver = db.relationship('Driver', backref='daily_logs')


class DeliveryZone(db.Model):
    __tablename__ = 'delivery_zones'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    postal_codes = db.Column(db.Text)
    default_vehicle_type = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Holiday(db.Model):
    __tablename__ = 'holidays'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, unique=True)
    name = db.Column(db.String(100))
    affects_delivery = db.Column(db.Boolean, default=True)