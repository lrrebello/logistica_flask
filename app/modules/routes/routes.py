from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Route, RouteWaypoint, Driver, Vehicle, Order, Address
from app.extensions import db
from datetime import datetime

routes_bp = Blueprint('routes', __name__)

@routes_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    routes = Route.query.paginate(page=page, per_page=10)
    return render_template('routes/list.html', routes=routes)

@routes_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    drivers = Driver.query.filter_by(status='active').all()
    vehicles = Vehicle.query.filter_by(status='available').all()
    orders = Order.query.filter_by(status='pending').all()
    
    if request.method == 'POST':
        route = Route(
            driver_id=request.form.get('driver_id'),
            vehicle_id=request.form.get('vehicle_id'),
            route_date=datetime.strptime(request.form.get('route_date'), '%Y-%m-%d').date(),
            status='planned'
        )
        db.session.add(route)
        db.session.flush()
        
        # Adicionar pedidos selecionados como waypoints
        selected_orders = request.form.getlist('orders')
        for i, order_id in enumerate(selected_orders):
            order = Order.query.get(order_id)
            # O endereço de descarga já está no pedido
            waypoint = RouteWaypoint(
                route_id=route.id,
                order_id=order.id,
                address_id=order.address_id,
                sequence_order=i + 1,
                status='pending'
            )
            db.session.add(waypoint)
            order.status = 'confirmed'
            
        db.session.commit()
        flash('Rota criada com sucesso', 'success')
        return redirect(url_for('routes.list'))
        
    return render_template('routes/form.html', drivers=drivers, vehicles=vehicles, orders=orders)

@routes_bp.route('/<int:id>/complete', methods=['POST'])
@login_required
def complete(id):
    route = Route.query.get_or_404(id)
    route.status = 'completed'
    for waypoint in route.waypoints:
        waypoint.status = 'completed'
        if waypoint.order:
            waypoint.order.status = 'delivered'
    db.session.commit()
    flash('Rota finalizada com sucesso', 'success')
    return redirect(url_for('routes.list'))
