from flask import Flask
from app.config import Config
from app.extensions import db, login_manager

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)

    # Context processor para disponibilizar menu em todos os templates
    @app.context_processor
    def inject_menu():
        from flask_login import current_user
        menu_items = []
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                menu_items = [
                    {'url': 'core.dashboard', 'icon': 'bi bi-speedometer2', 'name': 'Dashboard'},
                    {'url': 'suppliers.list', 'icon': 'bi bi-building', 'name': 'Fornecedores'},
                    {'url': 'products.list', 'icon': 'bi bi-box-seam', 'name': 'Produtos'},
                    {'url': 'stock.list', 'icon': 'bi bi-pie-chart', 'name': 'Estoque'},
                    {'url': 'clients.list', 'icon': 'bi bi-people', 'name': 'Clientes'},
                    {'url': 'orders.list', 'icon': 'bi bi-cart-check', 'name': 'Pedidos'},
                    {'url': 'routes.list', 'icon': 'bi bi-map', 'name': 'Rotas'},
                    {'url': 'vehicles.list', 'icon': 'bi bi-truck', 'name': 'Veículos'},
                    {'url': 'drivers.list', 'icon': 'bi bi-person-badge', 'name': 'Motoristas'},
                ]
            elif current_user.role == 'user':
                menu_items = [
                    {'url': 'core.dashboard', 'icon': 'bi bi-speedometer2', 'name': 'Dashboard'},
                    {'url': 'clients.list', 'icon': 'bi bi-people', 'name': 'Clientes'},
                    {'url': 'orders.list', 'icon': 'bi bi-cart-check', 'name': 'Pedidos'},
                    {'url': 'routes.list', 'icon': 'bi bi-map', 'name': 'Rotas'},
                ]
            elif current_user.role == 'driver':
                menu_items = [
                    {'url': 'core.dashboard', 'icon': 'bi bi-speedometer2', 'name': 'Dashboard'},
                    {'url': 'routes.list', 'icon': 'bi bi-map', 'name': 'Minhas Rotas'},
                ]
        return {'menu_items': menu_items}
    
    # Registrar Blueprints
    from app.modules.auth.routes import auth_bp
    from app.modules.clients.routes import clients_bp
    from app.modules.suppliers.routes import suppliers_bp
    from app.modules.products.routes import products_bp
    from app.modules.stock.routes import stock_bp
    from app.modules.orders.routes import orders_bp
    from app.modules.routes.routes import routes_bp
    from app.modules.vehicles.routes import vehicles_bp
    from app.modules.drivers.routes import drivers_bp
    from app.core.routes import core_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(clients_bp, url_prefix='/clients')
    app.register_blueprint(suppliers_bp, url_prefix='/suppliers')
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(stock_bp, url_prefix='/stock')
    app.register_blueprint(orders_bp, url_prefix='/orders')
    app.register_blueprint(routes_bp, url_prefix='/routes')
    app.register_blueprint(vehicles_bp, url_prefix='/vehicles')
    app.register_blueprint(drivers_bp, url_prefix='/drivers')
    app.register_blueprint(core_bp)

    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))