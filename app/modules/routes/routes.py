import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import Route, RouteWaypoint, Driver, Vehicle, Order, Address
from app.extensions import db
from datetime import datetime, date
import uuid

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
        
        lat1 = origin.address.latitude
        lon1 = origin.address.longitude
        lat2 = destination.address.latitude
        lon2 = destination.address.longitude
        
        if not lat1 or not lon1 or not lat2 or not lon2:
            return 30
        
        dist = haversine_distance(lat1, lon1, lat2, lon2)
        # Velocidade média: 40 km/h em zona urbana, 80 em autoestrada
        speed = 50 if 'autoestrada' in str(origin.address.city).lower() else 40
        return max(5, int((dist / speed) * 60))
    
    # Separar pontos
    start_point = None
    end_point = None
    deliveries = []
    
    for wp in route.waypoints:
        if wp.order_id is None:
            if start_point is None:
                start_point = wp
            else:
                end_point = wp
        else:
            deliveries.append(wp)
    
    if len(deliveries) <= 1:
        return jsonify({'success': False, 'message': 'Não há entregas suficientes'})
    
    # Hora de início (08:00 padrão, mas pode vir do motorista)
    start_time = datetime.now().replace(hour=8, minute=0, second=0, microsecond=0)
    current_time = start_time
    current_pos = start_point
    
    results = []
    time_buffer = 0  # Buffer para imprevistos
    
    for wp in deliveries:
        travel_time = calculate_travel_time(current_pos, wp)
        arrival_time = current_time + timedelta(minutes=travel_time + time_buffer)
        
        # Tempo de serviço (20 min padrão)
        service_time = 20
        
        # Analisar janela de horário
        window_start = None
        window_end = None
        has_reabertura = False
        reabertura_time = None
        is_feasible = True
        status = "ok"
        message = ""
        
        if wp.address and wp.address.time_window_start and wp.address.time_window_end:
            window_start = datetime.now().replace(
                hour=wp.address.time_window_start.hour,
                minute=wp.address.time_window_start.minute
            )
            window_end = datetime.now().replace(
                hour=wp.address.time_window_end.hour,
                minute=wp.address.time_window_end.minute
            )
            
            # Se a janela já passou hoje
            if window_end < datetime.now():
                # Verificar se há reabertura (exemplo: 14:00-15:00)
                # Por enquanto, consideramos reabertura em 50 min (como no seed)
                if wp.notes and "Reabertura" in wp.notes:
                    has_reabertura = True
                    # Extrair minutos da reabertura da nota
                    import re
                    match = re.search(r'(\d+)\s*min', wp.notes)
                    if match:
                        reabertura_min = int(match.group(1))
                        reabertura_time = datetime.now() + timedelta(minutes=reabertura_min)
                        is_feasible = True
                        status = "reabertura"
                        message = f"Janela fechada. Reabertura às {reabertura_time.strftime('%H:%M')}"
                    else:
                        is_feasible = False
                        status = "impossivel"
                        message = "Janela de entrega já fechada sem previsão de reabertura"
                else:
                    is_feasible = False
                    status = "impossivel"
                    message = "Janela de entrega já fechada para hoje"
            
            # Se ainda não passou, verificar se chegamos a tempo
            elif arrival_time > window_end:
                # Vamos chegar atrasado
                time_diff = (arrival_time - window_end).seconds / 60
                if wp.order.priority == 'urgent' and time_diff <= 30:
                    status = "atraso_leve"
                    message = f"Atraso estimado de {int(time_diff)} min"
                elif wp.order.priority == 'urgent':
                    status = "atraso_grave"
                    message = f"Atraso significativo de {int(time_diff)} min"
                else:
                    is_feasible = False
                    status = "impossivel"
                    message = f"Não será possível chegar a tempo (atraso de {int(time_diff)} min)"
            
            # Chegamos dentro da janela
            else:
                status = "ok"
                message = f"Chegada prevista: {arrival_time.strftime('%H:%M')} (janela: {window_start.strftime('%H:%M')}-{window_end.strftime('%H:%M')})"
        
        # Calcular urgência (quanto maior, mais prioritário)
        urgency = 0
        if wp.order.priority == 'urgent':
            urgency = 100
        elif wp.order.priority == 'high':
            urgency = 60
        else:
            urgency = 30
        
        # Penalizar quem está perdendo prazo
        if status == "atraso_leve":
            urgency += 150
        elif status == "atraso_grave":
            urgency += 300
        elif status == "reabertura":
            urgency += 80
        elif status == "impossivel":
            urgency = 1000  # Prioridade máxima para avisar
        
        results.append({
            'waypoint': wp,
            'arrival_time': arrival_time,
            'urgency': urgency,
            'status': status,
            'message': message,
            'is_feasible': is_feasible,
            'service_time': service_time,
            'travel_time': travel_time
        })
        
        # Atualizar para próxima iteração (apenas se for viável continuar)
        if is_feasible:
            current_time = arrival_time + timedelta(minutes=service_time)
            current_pos = wp
        else:
            # Não avança para os próximos se este é impossível
            # Isso ajuda a identificar o ponto de falha
            pass
    
    # Separar por status
    impossible = [r for r in results if not r['is_feasible']]
    reabertura = [r for r in results if r['status'] == 'reabertura']
    atrasados = [r for r in results if r['status'] in ['atraso_leve', 'atraso_grave']]
    ok = [r for r in results if r['status'] == 'ok']
    
    # Ordenar para otimização
    if impossible:
        # Se há entregas impossíveis, colocar no início para avisar
        results.sort(key=lambda r: (
            -r['urgency'],  # Urgência inversa
            r['arrival_time']
        ))
    else:
        # Ordenar normal: urgência > tempo de chegada
        results.sort(key=lambda r: (
            -r['urgency'],
            r['arrival_time']
        ))
    
    # Montar sequência final
    new_sequence = []
    if start_point:
        new_sequence.append(start_point)
    
    for r in results:
        new_sequence.append(r['waypoint'])
    
    if end_point:
        new_sequence.append(end_point)
    
    # Aplicar ordem
    for seq, wp in enumerate(new_sequence, 1):
        wp.sequence_order = seq
        if wp.order_id:
            wp.is_optimized = True
            wp.optimized_by = 'ai_timewindow'
            # Salvar informações de viabilidade na nota
            for r in results:
                if r['waypoint'].id == wp.id:
                    if r['status'] != 'ok':
                        wp.notes = f"[VIABILIDADE] {r['message']}"
                    break
    
    route.was_optimized = True
    route.last_optimization_date = datetime.utcnow()
    route.optimization_method = 'time_window'
    
    db.session.commit()
    
    # Gerar relatório completo
    report = []
    if impossible:
        report.append(f"❌ ENTREGAS IMPOSSÍVEIS: {len(impossible)}")
        for r in impossible:
            report.append(f"   - #{r['waypoint'].order.order_number}: {r['message']}")
    
    if reabertura:
        report.append(f"⚠️ ENTREGAS COM REABERTURA: {len(reabertura)}")
        for r in reabertura:
            report.append(f"   - #{r['waypoint'].order.order_number}: {r['message']}")
    
    if atrasados:
        report.append(f"⚠️ ENTREGAS COM ATRASO: {len(atrasados)}")
        for r in atrasados:
            report.append(f"   - #{r['waypoint'].order.order_number}: {r['message']}")
    
    report.append(f"✅ ENTREGAS OK: {len(ok)}")
    
    return jsonify({
        'success': True,
        'message': "\n".join(report),
        'details': {
            'total_entregas': len(deliveries),
            'impossiveis': len(impossible),
            'reabertura': len(reabertura),
            'atrasados': len(atrasados),
            'ok': len(ok)
        }
    })

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
    
    # Adicionar pontos da rota (se tiver a geometria salva)
    # Por enquanto, adicionar waypoints
    for wp in waypoints:
        if wp.address.latitude and wp.address.longitude:
            gpx += f'''            <trkpt lat="{wp.address.latitude}" lon="{wp.address.longitude}">
                <name>Parada {wp.sequence_order} - Pedido {wp.order.order_number}</name>
                <desc>{wp.address.street}, {wp.address.city}</desc>
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
        <Placemark>
            <name>Percurso</name>
            <styleUrl>#routeLine</styleUrl>
            <LineString>
                <coordinates>
'''
    
    for wp in waypoints:
        if wp.address.latitude and wp.address.longitude:
            kml += f'                    {wp.address.longitude},{wp.address.latitude}\n'
    
    kml += '''                </coordinates>
            </LineString>
        </Placemark>
'''
    
    for wp in waypoints:
        if wp.address.latitude and wp.address.longitude:
            kml += f'''
        <Placemark>
            <name>Parada {wp.sequence_order} - {wp.order.client.name}</name>
            <description>{wp.address.street}, {wp.address.city}</description>
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
    
    # Construir URLs para navegação
    google_maps_urls = []
    waze_urls = []
    
    for i, wp in enumerate(waypoints, 1):
        if wp.address.latitude and wp.address.longitude:
            lat = wp.address.latitude
            lng = wp.address.longitude
            google_maps_urls.append({
                'order': i,
                'url': f'https://www.google.com/maps/dir/?api=1&destination={lat},{lng}',
                'client': wp.order.client.name,
                'address': f'{wp.address.street}, {wp.address.city}'
            })
            waze_urls.append({
                'order': i,
                'url': f'https://www.waze.com/ul?ll={lat},{lng}&navigate=yes',
                'client': wp.order.client.name,
                'address': f'{wp.address.street}, {wp.address.city}'
            })
    
    return render_template('routes/navigate.html', 
                         route=route, 
                         google_urls=google_maps_urls,
                         waze_urls=waze_urls)