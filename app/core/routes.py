from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Supplier, Product, Client, Order, Stock
from app.extensions import db

core_bp = Blueprint('core', __name__)

@core_bp.route('/')
@core_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role not in ['admin', 'user']:
        flash('Acesso negado', 'danger')
        return redirect(url_for('auth.logout'))
    
    stats = {
        'total_suppliers': Supplier.query.count(),
        'total_products': Product.query.count(),
        'total_clients': Client.query.count(),
        'total_orders': Order.query.count(),
        'pending_orders': Order.query.filter_by(status='pending').count(),
        'in_transit_orders': Order.query.filter_by(status='in_transit').count(),
        'delivered_orders': Order.query.filter_by(status='delivered').count(),
        'critical_stock': db.session.query(Stock).filter(Stock.quantity <= Stock.minimum_level).count(),
    }
    
    return render_template('dashboard.html', stats=stats)
