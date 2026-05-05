import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, make_response, current_app
from flask_login import login_required, current_user
from app.models import Route, RouteWaypoint, Driver, Vehicle, Order, Address
from app.extensions import db
from datetime import datetime, date
import uuid
import requests
import json
import urllib.parse

routes_bp = Blueprint('routes', __name__)

def calculate_stop_time(waypoint):
    """Calcula tempo total de parada em minutos baseado no tipo de cliente"""
    
    # Tempo base padrão
    base_time = 15
    
    if waypoint.order and waypoint.order.client:
        # Verificar configuração customizada
        if waypoint.order.client.custom_stop_time:
            return waypoint.order.client.custom_stop_time
        
        # Buscar configuração por tipo de estabelecimento
        if waypoint.order.client.stop_time_config:
            config = waypoint.order.client.stop_time_config
            # Calcular tempo baseado na quantidade de produtos
            total_units = sum(item.quantity for item in waypoint.order.items) if waypoint.order.items else 1
            unloading_time = min(config.unloading_time_per_unit * total_units, 30)  # max 30 min descarga
            return config.base_time + unloading_time + config.payment_time + config.documentation_time + config.setup_time
    
    # Estimar baseado na prioridade
    if waypoint.order and waypoint.order.priority == 'urgent':
        return base_time - 5  # Urgentes são mais rápidos
    
    return base_time

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
    
    # Buscar endereços disponíveis para pontos fixos
    available_addresses = Address.query.filter_by(is_delivery_point=True).all()
    
    # TODOS os pedidos pendentes ou confirmados que NÃO estão em nenhuma rota
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
                # Filtrar apenas waypoints com pedido (ignorar início/fim fixos)
                deliveries = [wp for wp in route.waypoints if wp.order_id]
                # Ordenar por prioridade
                deliveries.sort(key=lambda w: (
                    0 if w.order.priority == 'urgent' else 1 if w.order.priority == 'high' else 2,
                    w.address.city if w.address else ''
                ))
                # Manter pontos fixos (início/fim)
                new_sequence = []
                for wp in route.waypoints:
                    if not wp.order_id:
                        new_sequence.append(wp)
                new_sequence.extend(deliveries)
                for seq, wp in enumerate(new_sequence, 1):
                    wp.sequence_order = seq
                    if wp.order_id:
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
                created_by_id=current_user.id,
                start_address_id=request.form.get('start_address_id') or None,
                end_address_id=request.form.get('end_address_id') or None
            )
            db.session.add(route)
            db.session.flush()
            
            # Contar quantos waypoints vamos adicionar
            waypoint_count = 0
            
            # Adicionar ponto de partida fixo (se existir)
            if route.start_address_id:
                start_wp = RouteWaypoint(
                    route_id=route.id,
                    order_id=None,
                    address_id=route.start_address_id,
                    sequence_order=1,
                    status='pending',
                    notes='Ponto de partida (carga)'
                )
                db.session.add(start_wp)
                waypoint_count += 1
            
            # Adicionar pedidos selecionados
            waypoints_order = request.form.get('waypoints_order', '')
            if waypoints_order:
                order_ids = [oid.strip() for oid in waypoints_order.split(',') if oid.strip()]
                start_seq = waypoint_count + 1
                for seq, order_id in enumerate(order_ids, start_seq):
                    try:
                        order_id_int = int(order_id)
                        order = Order.query.get(order_id_int)
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
                            waypoint_count += 1
                    except (ValueError, TypeError):
                        continue
            
            # Adicionar ponto de retorno fixo (se existir)
            if route.end_address_id:
                end_seq = waypoint_count + 1
                end_wp = RouteWaypoint(
                    route_id=route.id,
                    order_id=None,
                    address_id=route.end_address_id,
                    sequence_order=end_seq,
                    status='pending',
                    notes='Ponto de retorno (descarga)'
                )
                db.session.add(end_wp)
            
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
                         route=None,
                         available_addresses=available_addresses)

@routes_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    route = Route.query.get_or_404(id)
    drivers = Driver.query.filter_by(status='active').all()
    vehicles = Vehicle.query.filter_by(status='available').all()
    
    # Buscar endereços disponíveis para pontos fixos
    available_addresses = Address.query.filter_by(is_delivery_point=True).all()
    
    # Pedidos disponíveis:
    # 1. Pedidos pendentes/confirmados que NÃO estão em nenhuma rota
    # 2. Pedidos que já estão nesta rota (para poder ver/adicionar mais)
    orders = Order.query.filter(
        Order.status.in_(['pending', 'confirmed']),
        (~Order.route_waypoints.any()) | 
        (Order.route_waypoints.any(RouteWaypoint.route_id == id))
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
                    # Verificar se pedido já está noutra rota
                    existing = RouteWaypoint.query.filter(
                        RouteWaypoint.order_id == order.id,
                        RouteWaypoint.route_id != route.id
                    ).first()
                    if existing:
                        flash(f'⚠️ Pedido #{order.order_number} já está na rota {existing.route.route_number}', 'warning')
                        continue
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
            # Filtrar apenas waypoints com pedido (ignorar pontos fixos)
            deliveries = [wp for wp in route.waypoints if wp.order_id]
            # Ordenar por prioridade e cidade
            deliveries.sort(key=lambda w: (
                0 if w.order.priority == 'urgent' else 1 if w.order.priority == 'high' else 2,
                w.address.city if w.address else ''
            ))
            # Manter pontos fixos (início/fim)
            new_sequence = []
            for wp in route.waypoints:
                if not wp.order_id:
                    new_sequence.append(wp)
            new_sequence.extend(deliveries)
            for seq, wp in enumerate(new_sequence, 1):
                wp.sequence_order = seq
                if wp.order_id:
                    wp.is_optimized = True
                    wp.optimized_by = 'ai'
            route.was_optimized = True
            route.last_optimization_date = datetime.utcnow()
            route.optimization_method = 'ai_basic'
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
            
            # Atualizar pontos fixos
            new_start_id = request.form.get('start_address_id') or None
            new_end_id = request.form.get('end_address_id') or None
            
            # Se os pontos fixos mudaram, recriar waypoints fixos
            if route.start_address_id != new_start_id or route.end_address_id != new_end_id:
                # Remover waypoints fixos antigos
                for wp in route.waypoints:
                    if not wp.order_id:
                        db.session.delete(wp)
                
                route.start_address_id = new_start_id
                route.end_address_id = new_end_id
                db.session.flush()
                
                # Recriar pontos fixos na ordem correta
                new_sequence = []
                if route.start_address_id:
                    start_wp = RouteWaypoint(
                        route_id=route.id,
                        order_id=None,
                        address_id=route.start_address_id,
                        sequence_order=1,
                        status='pending',
                        notes='Ponto de partida'
                    )
                    db.session.add(start_wp)
                    new_sequence.append(start_wp)
                
                # Adicionar entregas existentes
                deliveries = [wp for wp in route.waypoints if wp.order_id]
                for wp in deliveries:
                    new_sequence.append(wp)
                
                if route.end_address_id and route.end_address_id != route.start_address_id:
                    end_wp = RouteWaypoint(
                        route_id=route.id,
                        order_id=None,
                        address_id=route.end_address_id,
                        sequence_order=len(new_sequence) + 1,
                        status='pending',
                        notes='Ponto de retorno'
                    )
                    db.session.add(end_wp)
                    new_sequence.append(end_wp)
                
                # Reordenar sequência
                for seq, wp in enumerate(new_sequence, 1):
                    wp.sequence_order = seq
            else:
                route.start_address_id = new_start_id
                route.end_address_id = new_end_id
            
            db.session.commit()
            flash('Rota atualizada com sucesso!', 'success')
            return redirect(url_for('routes.list'))
    
    waypoints = route.waypoints
    return render_template('routes/form.html', 
                         route=route,
                         drivers=drivers, 
                         vehicles=vehicles,
                         orders=orders,
                         waypoints=waypoints,
                         available_addresses=available_addresses)

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

@routes_bp.route('/<int:id>')
@login_required
def view(id):
    """Visualizar detalhes da rota com todas as entregas"""
    route = Route.query.get_or_404(id)
    waypoints = route.waypoints  # Já ordenados pela sequence_order
    
    # Calcular estatísticas da rota
    total_orders = len(waypoints)
    total_estimated_time = sum(w.estimated_travel_time or 0 for w in waypoints)
    
    return render_template('routes/view.html', 
                         route=route, 
                         waypoints=waypoints,
                         total_orders=total_orders,
                         total_estimated_time=total_estimated_time)

@routes_bp.route('/<int:id>/reorder', methods=['POST'])
@login_required
def reorder_waypoints(id):
    """Reordenar waypoints da rota via drag-and-drop"""
    route = Route.query.get_or_404(id)
    data = request.get_json()
    order = data.get('order', [])
    
    # Criar um dicionário para mapear order_id para waypoint
    waypoint_map = {wp.order_id: wp for wp in route.waypoints if wp.order_id}
    
    for seq, order_id in enumerate(order, 1):
        if order_id in waypoint_map:
            waypoint = waypoint_map[order_id]
            waypoint.sequence_order = seq
            waypoint.is_optimized = False
            waypoint.optimized_by = 'manual'
    
    route.was_optimized = False
    db.session.commit()
    
    return jsonify({'success': True})

@routes_bp.route('/<int:route_id>/remove/<int:order_id>', methods=['POST'])
@login_required
def remove_waypoint(route_id, order_id):
    """Remover um waypoint da rota"""
    waypoint = RouteWaypoint.query.filter_by(route_id=route_id, order_id=order_id).first()
    if waypoint:
        order = Order.query.get(order_id)
        order.status = 'pending'
        db.session.delete(waypoint)
        
        # Reordenar os waypoints restantes
        waypoints = RouteWaypoint.query.filter_by(route_id=route_id).order_by(RouteWaypoint.sequence_order).all()
        for seq, wp in enumerate(waypoints, 1):
            wp.sequence_order = seq
        
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'error': 'Waypoint not found'}), 404

@routes_bp.route('/<int:id>/optimize', methods=['POST'])
@login_required
def optimize_route(id):
    """Otimização com análise de viabilidade de horários"""
    route = Route.query.get_or_404(id)
    
    import math
    from datetime import datetime, timedelta
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371
        if not lat1 or not lon1 or not lat2 or not lon2:
            return 30
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
    
    def calculate_travel_time(origin, destination):
        """Estima tempo de viagem em minutos"""
        if not origin or not destination:
            return 30
        if not hasattr(origin, 'address') or not origin.address:
            return 30
        if not destination.address:
            return 30
        
        # Calcular distância em km
        distance = haversine_distance(
            origin.address.latitude,
            origin.address.longitude,
            destination.address.latitude,
            destination.address.longitude
        )
        
        # Estimar tempo: 60 km/h em média
        return int((distance / 60) * 60)  # Converter para minutos
    
    deliveries = [wp for wp in route.waypoints if wp.order_id]
    
    if not deliveries:
        return jsonify({'success': False, 'message': 'Nenhuma entrega para otimizar'})
    
    # Ordenar por prioridade
    deliveries.sort(key=lambda w: (
        0 if w.order.priority == 'urgent' else 1 if w.order.priority == 'high' else 2,
        w.address.city if w.address else ''
    ))
    
    # Atualizar sequência
    start_seq = 1
    for wp in route.waypoints:
        if not wp.order_id:
            start_seq += 1
    
    for seq, wp in enumerate(deliveries, start_seq):
        wp.sequence_order = seq
        wp.is_optimized = True
        wp.optimized_by = 'ai'
    
    route.was_optimized = True
    route.last_optimization_date = datetime.utcnow()
    route.optimization_method = 'ai_priority'
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Rota otimizada com sucesso!'})

@routes_bp.route('/<int:id>/map')
@login_required
def view_map(id):
    """Visualizar rota no mapa com Geoapify"""
    route = Route.query.get_or_404(id)
    waypoints = route.waypoints
    
    # Converter waypoints para dicionário serializável em JSON
    waypoints_data = []
    for wp in waypoints:
        # Verificar se tem coordenadas
        lat = None
        lng = None
        if wp.address and wp.address.latitude and wp.address.longitude:
            lat = float(wp.address.latitude)
            lng = float(wp.address.longitude)
        
        waypoints_data.append({
            'order_id': wp.order_id,
            'sequence_order': wp.sequence_order,
            'latitude': lat,
            'longitude': lng,
            'address': {
                'street': wp.address.street if wp.address else '',
                'city': wp.address.city if wp.address else '',
                'postal_code': wp.address.postal_code if wp.address else '',
                'delivery_instructions': wp.address.delivery_instructions if wp.address else ''
            },
            'order': {
                'order_number': wp.order.order_number if wp.order else '',
                'priority': wp.order.priority if wp.order else 'normal',
                'client_name': wp.order.client.name if wp.order and wp.order.client else ''
            }
        })
    
    geoapify_api_key = os.environ.get('GEOAPIFY_API_KEY', '')
    
    return render_template('routes/map.html', 
                         route=route, 
                         waypoints=waypoints_data,
                         geoapify_api_key=geoapify_api_key)

@routes_bp.route('/<int:id>/export/gpx')
@login_required
def export_gpx(id):
    """Exportar rota no formato GPX para GPS Garmin/TomTom"""
    from flask import make_response
    route = Route.query.get_or_404(id)
    waypoints = route.waypoints
    
    # Construir XML GPX
    gpx = f'''<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Logistica Irmãos Monteiro" xmlns="http://www.topografix.com/GPX/1/1">
    <metadata>
        <name>Rota {route.route_number} - {route.route_date}</name>
        <desc>{route.route_name or 'Rota de entrega'}</desc>
    </metadata>
    <trk>
        <name>Rota {route.route_number}</name>
        <trkseg>
'''
    
    # Adicionar pontos da rota - APENAS com coordenadas
    for wp in waypoints:
        if wp.address and wp.address.latitude and wp.address.longitude:
            if wp.order:
                # Ponto com pedido
                name = f"Parada {wp.sequence_order} - Pedido {wp.order.order_number} - {wp.order.client.name}"
                desc = f"{wp.address.street}, {wp.address.city}"
            else:
                # Ponto de início/fim
                name = f"Parada {wp.sequence_order} - Centralrest (Fábrica)"
                desc = f"{wp.address.street}, {wp.address.city}"
            
            gpx += f'''            <trkpt lat="{wp.address.latitude}" lon="{wp.address.longitude}">
                <name>{name}</name>
                <desc>{desc}</desc>
            </trkpt>
'''
    
    gpx += '''        </trkseg>
    </trk>
</gpx>'''
    
    response = make_response(gpx)
    response.headers['Content-Type'] = 'application/gpx+xml'
    response.headers['Content-Disposition'] = f'attachment; filename=rota_{route.route_number}_{route.route_date}.gpx'
    return response

@routes_bp.route('/<int:id>/export/kml')
@login_required
def export_kml(id):
    """Exportar rota no formato KML para Google Earth/My Maps"""
    from flask import make_response
    route = Route.query.get_or_404(id)
    waypoints = route.waypoints
    
    kml = f'''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>Rota {route.route_number}</name>
        <description>{route.route_name or 'Rota de entrega'}</description>
        <Style id="routeLine">
            <LineStyle>
                <color>ff0066cc</color>
                <width>4</width>
            </LineStyle>
        </Style>
        <Style id="waypointIcon">
            <IconStyle>
                <color>ff10b981</color>
                <scale>0.8</scale>
                <Icon>
                    <href>http://maps.google.com/mapfiles/kml/pushpin/red-pushpin.png</href>
                </Icon>
            </IconStyle>
        </Style>
        <Placemark>
            <name>Percurso</name>
            <styleUrl>#routeLine</styleUrl>
            <LineString>
                <coordinates>
'''
    
    for wp in waypoints:
        if wp.address and wp.address.latitude and wp.address.longitude:
            kml += f'                    {wp.address.longitude},{wp.address.latitude}\n'
    
    kml += '''                </coordinates>
            </LineString>
        </Placemark>
'''
    
    for wp in waypoints:
        if wp.address and wp.address.latitude and wp.address.longitude:
            if wp.order:
                name = f"Parada {wp.sequence_order} - {wp.order.client.name} (Pedido #{wp.order.order_number})"
                desc = f"{wp.address.street}, {wp.address.city}"
            else:
                name = f"Parada {wp.sequence_order} - Centralrest (Fábrica)"
                desc = f"{wp.address.street}, {wp.address.city}"
            
            kml += f'''
        <Placemark>
            <name>{name}</name>
            <description>{desc}</description>
            <styleUrl>#waypointIcon</styleUrl>
            <Point>
                <coordinates>{wp.address.longitude},{wp.address.latitude}</coordinates>
            </Point>
        </Placemark>
'''
    
    kml += '''    </Document>
</kml>'''
    
    response = make_response(kml)
    response.headers['Content-Type'] = 'application/vnd.google-earth.kml+xml'
    response.headers['Content-Disposition'] = f'attachment; filename=rota_{route.route_number}_{route.route_date}.kml'
    return response

@routes_bp.route('/<int:id>/navigate')
@login_required
def navigate(id):
    """Página com links para navegação em apps de GPS"""
    route = Route.query.get_or_404(id)
    waypoints = route.waypoints
    
    # Construir URLs para navegação individual
    google_maps_urls = []
    waze_urls = []
    
    # Construir URL do Google Maps com TODAS as paradas (rota completa)
    google_waypoints = []
    
    for i, wp in enumerate(waypoints, 1):
        # Verificar se tem coordenadas para a rota completa
        if wp.address and wp.address.latitude and wp.address.longitude:
            google_waypoints.append({
                'lat': wp.address.latitude,
                'lng': wp.address.longitude,
                'order': i
            })
        
        # Verificar se tem pedido para navegação individual
        if wp.order and wp.order.client and wp.address:
            if wp.address.latitude and wp.address.longitude:
                lat = wp.address.latitude
                lng = wp.address.longitude
                google_maps_urls.append({
                    'order': i,
                    'url': f'https://www.google.com/maps/dir/?api=1&destination={lat},{lng}',
                    'client': wp.order.client.name,
                    'address': f'{wp.address.street}, {wp.address.city}',
                    'order_number': wp.order.order_number,
                    'type': 'delivery'
                })
                waze_urls.append({
                    'order': i,
                    'url': f'https://www.waze.com/ul?ll={lat},{lng}&navigate=yes',
                    'client': wp.order.client.name,
                    'address': f'{wp.address.street}, {wp.address.city}',
                    'order_number': wp.order.order_number,
                    'type': 'delivery'
                })
            else:
                google_maps_urls.append({
                    'order': i,
                    'url': '#',
                    'client': wp.order.client.name,
                    'address': f'{wp.address.street}, {wp.address.city} (sem coordenadas)',
                    'order_number': wp.order.order_number,
                    'type': 'delivery',
                    'no_coords': True
                })
                waze_urls.append({
                    'order': i,
                    'url': '#',
                    'client': wp.order.client.name,
                    'address': f'{wp.address.street}, {wp.address.city} (sem coordenadas)',
                    'order_number': wp.order.order_number,
                    'type': 'delivery',
                    'no_coords': True
                })
        else:
            # Ponto de início/fim
            if wp.address:
                google_maps_urls.append({
                    'order': i,
                    'url': f'https://www.google.com/maps/dir/?api=1&destination={wp.address.latitude},{wp.address.longitude}' if wp.address.latitude else '#',
                    'client': 'Centralrest - Fábrica',
                    'address': f'{wp.address.street}, {wp.address.city}',
                    'order_number': 'PONTO DE PARTIDA',
                    'type': 'start_end'
                })
                waze_urls.append({
                    'order': i,
                    'url': f'https://www.waze.com/ul?ll={wp.address.latitude},{wp.address.longitude}&navigate=yes' if wp.address.latitude else '#',
                    'client': 'Centralrest - Fábrica',
                    'address': f'{wp.address.street}, {wp.address.city}',
                    'order_number': 'PONTO DE RETORNO',
                    'type': 'start_end'
                })
    
    return render_template('routes/navigate.html', 
                         route=route, 
                         google_maps_urls=google_maps_urls,
                         waze_urls=waze_urls,
                         google_waypoints=google_waypoints)
