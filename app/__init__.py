from flask import Flask
from app.config import Config
from app.extensions import db, login_manager

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)

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