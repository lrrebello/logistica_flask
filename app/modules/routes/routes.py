from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Route, RouteWaypoint, Driver, Vehicle, Order, Address
from app.extensions import db
from datetime import datetime, date
import uuid

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
    # Buscar pedidos pendentes (não atribuídos a nenhuma rota confirmada)
    orders = Order.query.filter(
        Order.status.in_(['pending', 'confirmed']),
        ~Order.route_waypoints.any()
    ).all()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Adicionar waypoints à rota
        if action == 'add':
            order_ids = request.form.get('add_waypoints', '').split(',')
            route_id = request.args.get('id')
            if route_id:
                route = Route.query.get(route_id)
                for seq, order_id in enumerate(order_ids, 1):
                    if order_id:
                        order = Order.query.get(order_id)
                        if order and order.address_id:
                            waypoint = RouteWaypoint(
                                route_id=route.id,
                                order_id=order.id,
                                address_id=order.address_id,
                                sequence_order=len(route.waypoints) + seq,
                                status='pending'
                            )
                            db.session.add(waypoint)
                            order.status = 'confirmed'
                db.session.commit()
            return redirect(url_for('routes.edit', id=route_id))
        
        # Remover waypoint
        elif action == 'remove':
            order_id = request.form.get('remove_waypoint')
            route_id = request.args.get('id')
            if route_id and order_id:
                waypoint = RouteWaypoint.query.filter_by(route_id=route_id, order_id=order_id).first()
                if waypoint:
                    order = Order.query.get(order_id)
                    order.status = 'pending'
                    db.session.delete(waypoint)
                    # Reordenar sequência
                    waypoints = RouteWaypoint.query.filter_by(route_id=route_id).order_by(RouteWaypoint.sequence_order).all()
                    for seq, wp in enumerate(waypoints, 1):
                        wp.sequence_order = seq
                    db.session.commit()
            return redirect(url_for('routes.edit', id=route_id))
        
        # Otimizar rota
        elif action == 'optimize':
            route_id = request.args.get('id')
            if route_id:
                route = Route.query.get(route_id)
                waypoints = list(route.waypoints)
                # Algoritmo simples: ordenar por prioridade e cidade
                waypoints.sort(key=lambda w: (
                    0 if w.order.priority == 'urgent' else 1 if w.order.priority == 'high' else 2,
                    w.address.city
                ))
                for seq, wp in enumerate(waypoints, 1):
                    wp.sequence_order = seq
                    wp.is_optimized = True
                    wp.optimized_by = 'ai'
                route.was_optimized = True
                route.last_optimization_date = datetime.utcnow()
                route.optimization_method = 'ai_basic'
                db.session.commit()
            return redirect(url_for('routes.edit', id=route_id))
        
        # Criar nova rota
        else:
            # Gerar route_number se não foi enviado
            route_number = request.form.get('route_number')
            if not route_number:
                # Gerar número automático: ROTA + data + sequência
                today = date.today().strftime('%Y%m%d')
                last_route = Route.query.order_by(Route.id.desc()).first()
                next_num = (last_route.id + 1) if last_route else 1
                route_number = f"ROTA-{today}-{next_num:03d}"
            
            route = Route(
                route_number=route_number,
                route_name=request.form.get('route_name'),
                description=request.form.get('description'),
                region=request.form.get('region'),
                driver_id=request.form.get('driver_id'),
                vehicle_id=request.form.get('vehicle_id'),
                route_date=datetime.strptime(request.form.get('route_date'), '%Y-%m-%d').date(),
                status='planned',
                notes=request.form.get('notes'),
                created_by_id=current_user.id
            )
            db.session.add(route)
            db.session.flush()
            
            # Adicionar pedidos selecionados
            waypoints_order = request.form.get('waypoints_order', '')
            if waypoints_order:
                order_ids = waypoints_order.split(',')
                for seq, order_id in enumerate(order_ids, 1):
                    if order_id:
                        order = Order.query.get(order_id)
                        if order and order.address_id:
                            waypoint = RouteWaypoint(
                                route_id=route.id,
                                order_id=order.id,
                                address_id=order.address_id,
                                sequence_order=seq,
                                status='pending'
                            )
                            db.session.add(waypoint)
                            order.status = 'confirmed'
            
            db.session.commit()
            flash('Rota criada com sucesso!', 'success')
            return redirect(url_for('routes.list'))
    
    # GET - mostrar formulário
    waypoints = []
    return render_template('routes/form.html', 
                         drivers=drivers, 
                         vehicles=vehicles, 
                         orders=orders,
                         waypoints=waypoints,
                         route=None)

@routes_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    route = Route.query.get_or_404(id)
    drivers = Driver.query.filter_by(status='active').all()
    vehicles = Vehicle.query.filter_by(status='available').all()
    
    # Pedidos disponíveis (não atribuídos a esta rota)
    orders = Order.query.filter(
        Order.status.in_(['pending', 'confirmed']),
        ~Order.route_waypoints.any(RouteWaypoint.route_id != id)
    ).all()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Adicionar waypoints
        if action == 'add':
            order_ids = request.form.get('add_waypoints', '').split(',')
            current_seq = len(route.waypoints)
            for seq, order_id in enumerate(order_ids, current_seq + 1):
                if order_id:
                    order = Order.query.get(order_id)
                    if order and order.address_id:
                        waypoint = RouteWaypoint(
                            route_id=route.id,
                            order_id=order.id,
                            address_id=order.address_id,
                            sequence_order=seq,
                            status='pending'
                        )
                        db.session.add(waypoint)
                        order.status = 'confirmed'
            db.session.commit()
            return redirect(url_for('routes.edit', id=id))
        
        # Remover waypoint
        elif action == 'remove':
            order_id = request.form.get('remove_waypoint')
            if order_id:
                waypoint = RouteWaypoint.query.filter_by(route_id=id, order_id=order_id).first()
                if waypoint:
                    order = Order.query.get(order_id)
                    order.status = 'pending'
                    db.session.delete(waypoint)
                    # Reordenar
                    waypoints = RouteWaypoint.query.filter_by(route_id=id).order_by(RouteWaypoint.sequence_order).all()
                    for seq, wp in enumerate(waypoints, 1):
                        wp.sequence_order = seq
                    db.session.commit()
            return redirect(url_for('routes.edit', id=id))
        
        # Otimizar
        elif action == 'optimize':
            route = Route.query.get(id)
            waypoints = list(route.waypoints)
            waypoints.sort(key=lambda w: (w.address.city, w.order.priority))
            for seq, wp in enumerate(waypoints, 1):
                wp.sequence_order = seq
                wp.is_optimized = True
                wp.optimized_by = 'ai'
            route.was_optimized = True
            route.last_optimization_date = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('routes.edit', id=id))
        
        # Atualizar dados da rota
        else:
            route.route_number = request.form.get('route_number')
            route.route_name = request.form.get('route_name')
            route.description = request.form.get('description')
            route.region = request.form.get('region')
            route.driver_id = request.form.get('driver_id')
            route.vehicle_id = request.form.get('vehicle_id')
            route.route_date = datetime.strptime(request.form.get('route_date'), '%Y-%m-%d').date()
            route.notes = request.form.get('notes')
            db.session.commit()
            flash('Rota atualizada com sucesso!', 'success')
            return redirect(url_for('routes.list'))
    
    waypoints = route.waypoints
    return render_template('routes/form.html', 
                         route=route,
                         drivers=drivers, 
                         vehicles=vehicles,
                         orders=orders,
                         waypoints=waypoints)

@routes_bp.route('/<int:id>/complete', methods=['POST'])
@login_required
def complete(id):
    route = Route.query.get_or_404(id)
    route.status = 'completed'
    for waypoint in route.waypoints:
        waypoint.status = 'completed'
        if waypoint.order:
            waypoint.order.status = 'delivered'
            waypoint.order.delivered_at = datetime.utcnow()
    db.session.commit()
    flash('Rota finalizada com sucesso!', 'success')
    return redirect(url_for('routes.list'))

@routes_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    route = Route.query.get_or_404(id)
    # Liberar os pedidos antes de deletar
    for waypoint in route.waypoints:
        if waypoint.order:
            waypoint.order.status = 'pending'
    db.session.delete(route)
    db.session.commit()
    flash('Rota removida com sucesso!', 'success')
    return redirect(url_for('routes.list'))