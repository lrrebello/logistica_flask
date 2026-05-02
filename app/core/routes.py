from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Supplier, Product, Client, Order, Stock
from app.extensions import db

core_bp = Blueprint('core', __name__)

# Menu items por role
MENU_ITEMS = {
    'admin': [
        {'url': 'core.dashboard', 'icon': 'bi bi-speedometer2', 'name': 'Dashboard', 'endpoint': 'core.dashboard'},
        {'url': 'suppliers.list', 'icon': 'bi bi-building', 'name': 'Fornecedores', 'endpoint': 'suppliers'},
        {'url': 'products.list', 'icon': 'bi bi-box-seam', 'name': 'Produtos', 'endpoint': 'products'},
        {'url': 'stock.list', 'icon': 'bi bi-pie-chart', 'name': 'Estoque', 'endpoint': 'stock'},
        {'url': 'clients.list', 'icon': 'bi bi-people', 'name': 'Clientes', 'endpoint': 'clients'},
        {'url': 'orders.list', 'icon': 'bi bi-cart-check', 'name': 'Pedidos', 'endpoint': 'orders'},
        {'url': 'routes.list', 'icon': 'bi bi-map', 'name': 'Rotas', 'endpoint': 'routes'},
        {'url': 'vehicles.list', 'icon': 'bi bi-truck', 'name': 'Veículos', 'endpoint': 'vehicles'},
        {'url': 'drivers.list', 'icon': 'bi bi-person-badge', 'name': 'Motoristas', 'endpoint': 'drivers'},
    ],
    'user': [
        {'url': 'core.dashboard', 'icon': 'bi bi-speedometer2', 'name': 'Dashboard', 'endpoint': 'core.dashboard'},
        {'url': 'clients.list', 'icon': 'bi bi-people', 'name': 'Clientes', 'endpoint': 'clients'},
        {'url': 'orders.list', 'icon': 'bi bi-cart-check', 'name': 'Pedidos', 'endpoint': 'orders'},
        {'url': 'routes.list', 'icon': 'bi bi-map', 'name': 'Rotas', 'endpoint': 'routes'},
    ],
    'driver': [
        {'url': 'core.dashboard', 'icon': 'bi bi-speedometer2', 'name': 'Dashboard', 'endpoint': 'core.dashboard'},
        {'url': 'routes.list', 'icon': 'bi bi-map', 'name': 'Minhas Rotas', 'endpoint': 'routes'},
        {'url': 'routes.navigate_driver', 'icon': 'bi bi-compass', 'name': 'Navegar', 'endpoint': 'routes.navigate_driver'},
    ],
}

@core_bp.route('/')
@core_bp.route('/dashboard')
@login_required
def dashboard():
    # Permissões baseadas no role
    if current_user.role == 'admin':
        stats = {
            'total_suppliers': Supplier.query.count(),
            'total_products': Product.query.count(),
            'total_clients': Client.query.count(),
            'total_orders': Order.query.count(),
            'pending_orders': Order.query.filter_by(status='pending').count(),
            'in_transit_orders': Order.query.filter_by(status='confirmed').count(),
            'delivered_orders': Order.query.filter_by(status='delivered').count(),
            'critical_stock': db.session.query(Stock).filter(Stock.quantity <= Stock.minimum_level).count(),
        }
    elif current_user.role == 'user':
        stats = {
            'total_clients': Client.query.count(),
            'total_orders': Order.query.count(),
            'pending_orders': Order.query.filter_by(status='pending').count(),
            'total_routes': Route.query.count(),
        }
    else:  # driver
        # Motorista vê apenas rotas atribuídas a ele
        from app.models import Route
        driver_routes = Route.query.filter_by(driver_id=current_user.driver_profile.id if current_user.driver_profile else 0).count() if current_user.driver_profile else 0
        stats = {
            'my_routes': driver_routes,
            'today_routes': Route.query.filter_by(driver_id=current_user.driver_profile.id if current_user.driver_profile else 0, route_date=date.today()).count() if current_user.driver_profile else 0,
            'completed_today': Route.query.filter_by(driver_id=current_user.driver_profile.id if current_user.driver_profile else 0, status='completed').count() if current_user.driver_profile else 0,
        }
    
    return render_template('dashboard.html', stats=stats)