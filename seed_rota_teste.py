#!/usr/bin/env python3
"""
Seed para criar uma rota de teste realista
"""

from app import create_app
from app.extensions import db
from app.models import (
    Client, Address, Product, Order, OrderItem, 
    Vehicle, Driver, Route, RouteWaypoint, StopTimeConfig
)
from datetime import datetime, date, time
import random
import time as time_module

def limpar_dados_antigos():
    """Remove rotas de teste e pedidos associados"""
    print("🗑️ A limpar dados antigos...")
    
    # Apagar waypoints de rotas de teste
    RouteWaypoint.query.filter(
        RouteWaypoint.route.has(Route.route_number.like('TEST-%'))
    ).delete(synchronize_session=False)
    
    # Apagar rotas de teste
    Route.query.filter(Route.route_number.like('TEST-%')).delete(synchronize_session=False)
    
    # Apagar itens de pedidos de teste
    OrderItem.query.filter(
        OrderItem.order.has(Order.order_number.like('TEST-%'))
    ).delete(synchronize_session=False)
    
    # Apagar pedidos de teste
    Order.query.filter(Order.order_number.like('TEST-%')).delete(synchronize_session=False)
    
    db.session.commit()
    print("✅ Dados antigos removidos")

def get_or_create_client(nif, defaults):
    client = Client.query.filter_by(nif=nif).first()
    if not client:
        client = Client(**defaults)
        db.session.add(client)
        db.session.flush()
    return client

def get_or_create_address(client_id, defaults):
    address = Address.query.filter_by(client_id=client_id, street=defaults.get('street')).first()
    if not address:
        address = Address(client_id=client_id, **defaults)
        db.session.add(address)
        db.session.flush()
    return address

def get_or_create_stop_config(name, defaults):
    config = StopTimeConfig.query.filter_by(name=name).first()
    if not config:
        config = StopTimeConfig(**defaults)
        db.session.add(config)
        db.session.flush()
    return config

def seed_rota_teste():
    app = create_app()
    with app.app_context():
        print("🔄 A criar rota de teste...")
        
        # Limpar dados antigos primeiro
        limpar_dados_antigos()
        
        # ==================== CONFIGURAÇÕES DE TEMPO ====================
        configs = [
            {'name': 'Supermercado', 'base_time': 20, 'unloading_time_per_unit': 3, 'payment_time': 8, 'documentation_time': 5, 'setup_time': 10},
            {'name': 'Padaria/Pequeno Comércio', 'base_time': 10, 'unloading_time_per_unit': 1, 'payment_time': 3, 'documentation_time': 2, 'setup_time': 5},
            {'name': 'Hotel/Restaurante', 'base_time': 15, 'unloading_time_per_unit': 2, 'payment_time': 5, 'documentation_time': 3, 'setup_time': 8},
            {'name': 'Indústria', 'base_time': 30, 'unloading_time_per_unit': 5, 'payment_time': 10, 'documentation_time': 10, 'setup_time': 15},
        ]
        
        for data in configs:
            get_or_create_stop_config(data['name'], data)
        
        # ==================== CLIENTES ====================
        centralrest = get_or_create_client('500000001', {
            'name': 'Centralrest - Fábrica Ílhavo', 'nif': '500000001',
            'email': 'logistica@centralrest.pt', 'phone': '234123456', 'is_active': True
        })
        
        centralrest_addr = get_or_create_address(centralrest.id, {
            'street': 'Zona Industrial de Ílhavo, Lote 42', 'city': 'Ílhavo',
            'postal_code': '3830-000', 'latitude': 40.6167, 'longitude': -8.6667,
            'is_headquarters': True, 'is_delivery_point': False
        })
        
        # Clientes
        client_ilhavo1 = get_or_create_client('501234567', {'name': 'Supermercado Sol Nascente', 'nif': '501234567', 'email': 'compras@sol.pt', 'phone': '234567890', 'is_active': True})
        client_ilhavo2 = get_or_create_client('502345678', {'name': 'Padaria Central Ílhavo', 'nif': '502345678', 'email': 'padaria@central.pt', 'phone': '234567891', 'is_active': True})
        client_vagos1 = get_or_create_client('503456789', {'name': 'Mercearia do Largo', 'nif': '503456789', 'email': 'mercearia@largo.pt', 'phone': '234567892', 'is_active': True})
        client_vagos2 = get_or_create_client('504567890', {'name': 'Talho Vagos', 'nif': '504567890', 'email': 'talho@vagos.pt', 'phone': '234567893', 'is_active': True})
        client_vagos3 = get_or_create_client('505678901', {'name': 'Café Central Vagos', 'nif': '505678901', 'email': 'cafe@central.pt', 'phone': '234567894', 'is_active': True})
        client_aveiro1 = get_or_create_client('506789012', {'name': 'Continente Aveiro', 'nif': '506789012', 'email': 'compras@continente.pt', 'phone': '234567895', 'is_active': True})
        client_aveiro2 = get_or_create_client('507890123', {'name': 'Pingo Doce Aveiro', 'nif': '507890123', 'email': 'compras@pingodoce.pt', 'phone': '234567896', 'is_active': True})
        client_aveiro3 = get_or_create_client('508901234', {'name': 'Lidl Aveiro', 'nif': '508901234', 'email': 'compras@lidl.pt', 'phone': '234567897', 'is_active': True})
        client_aveiro4 = get_or_create_client('509012345', {'name': 'Restaurante O Telheiro', 'nif': '509012345', 'email': 'telheiro@rest.pt', 'phone': '234567898', 'is_active': True})
        client_aveiro5 = get_or_create_client('510123456', {'name': 'Hotel Moliceiro', 'nif': '510123456', 'email': 'compras@hotelmoliceiro.pt', 'phone': '234567899', 'is_active': True})
        
        # Associar configurações de tempo
        supermercado = StopTimeConfig.query.filter_by(name='Supermercado').first()
        padaria = StopTimeConfig.query.filter_by(name='Padaria/Pequeno Comércio').first()
        hotel = StopTimeConfig.query.filter_by(name='Hotel/Restaurante').first()
        industria = StopTimeConfig.query.filter_by(name='Indústria').first()
        
        client_ilhavo1.stop_time_config_id = supermercado.id if supermercado else None
        client_aveiro1.stop_time_config_id = supermercado.id if supermercado else None
        client_aveiro2.stop_time_config_id = supermercado.id if supermercado else None
        client_aveiro3.stop_time_config_id = supermercado.id if supermercado else None
        client_ilhavo2.stop_time_config_id = padaria.id if padaria else None
        client_vagos1.stop_time_config_id = padaria.id if padaria else None
        client_vagos2.stop_time_config_id = padaria.id if padaria else None
        client_vagos3.stop_time_config_id = padaria.id if padaria else None
        client_aveiro5.stop_time_config_id = hotel.id if hotel else None
        client_aveiro4.stop_time_config_id = industria.id if industria else None
        
        # ==================== ENDEREÇOS ====================
        addr_ilhavo1 = get_or_create_address(client_ilhavo1.id, {'street': 'Rua dos Bombeiros, 10', 'city': 'Ílhavo', 'postal_code': '3830-123', 'latitude': 40.6160, 'longitude': -8.6700, 'is_delivery_point': True, 'time_window_start': time(9,0), 'time_window_end': time(12,0)})
        addr_ilhavo2 = get_or_create_address(client_ilhavo2.id, {'street': 'Largo da República, 5', 'city': 'Ílhavo', 'postal_code': '3830-124', 'latitude': 40.6180, 'longitude': -8.6650, 'is_delivery_point': True})
        addr_vagos1 = get_or_create_address(client_vagos1.id, {'street': 'Rua Principal, 20', 'city': 'Vagos', 'postal_code': '3840-125', 'latitude': 40.5500, 'longitude': -8.6800, 'is_delivery_point': True})
        addr_vagos2 = get_or_create_address(client_vagos2.id, {'street': 'Avenida da Liberdade, 8', 'city': 'Vagos', 'postal_code': '3840-126', 'latitude': 40.5530, 'longitude': -8.6830, 'is_delivery_point': True})
        addr_vagos3 = get_or_create_address(client_vagos3.id, {'street': 'Praça do Município, 3', 'city': 'Vagos', 'postal_code': '3840-127', 'latitude': 40.5560, 'longitude': -8.6780, 'is_delivery_point': True})
        addr_aveiro1 = get_or_create_address(client_aveiro1.id, {'street': 'Rua do Comércio, 50', 'city': 'Aveiro', 'postal_code': '3800-200', 'latitude': 40.6443, 'longitude': -8.6455, 'is_delivery_point': True, 'time_window_start': time(14,0), 'time_window_end': time(18,0)})
        addr_aveiro2 = get_or_create_address(client_aveiro2.id, {'street': 'Avenida Lourenço Peixinho, 100', 'city': 'Aveiro', 'postal_code': '3800-168', 'latitude': 40.6419, 'longitude': -8.6515, 'is_delivery_point': True})
        addr_aveiro3 = get_or_create_address(client_aveiro3.id, {'street': 'Rua de Viseu, 25', 'city': 'Aveiro', 'postal_code': '3810-228', 'latitude': 40.6387, 'longitude': -8.6573, 'is_delivery_point': True})
        addr_aveiro4 = get_or_create_address(client_aveiro4.id, {'street': 'Rua das Salineiras, 15', 'city': 'Ílhavo', 'postal_code': '3830-399', 'latitude': 40.6075, 'longitude': -8.6867, 'is_delivery_point': True})
        addr_aveiro5 = get_or_create_address(client_aveiro5.id, {'street': 'Rua João Mendonça, 10', 'city': 'Aveiro', 'postal_code': '3800-200', 'latitude': 40.6326, 'longitude': -8.6459, 'is_delivery_point': True, 'time_window_start': time(8,0), 'time_window_end': time(10,0)})
        
        # ==================== PRODUTOS ====================
        produtos = []
        for sku, name, price in [('P001', 'Produto A', 10.0), ('P002', 'Produto B', 20.0), ('P003', 'Produto C', 15.0)]:
            prod = Product.query.filter_by(sku=sku).first()
            if not prod:
                prod = Product(sku=sku, name=name, price=price, unit='un')
                db.session.add(prod)
                db.session.flush()
            produtos.append(prod)
        
        # ==================== PEDIDOS (com timestamp único) ====================
        pedidos = []
        timestamp = int(time_module.time())
        
        pedidos_data = [
            (client_ilhavo1, addr_ilhavo1, 'normal'),
            (client_ilhavo2, addr_ilhavo2, 'high'),
            (client_ilhavo2, addr_ilhavo2, 'normal'),
            (client_vagos1, addr_vagos1, 'normal'),
            (client_vagos2, addr_vagos2, 'normal'),
            (client_vagos3, addr_vagos3, 'normal'),
            (client_vagos1, addr_vagos1, 'normal'),
            (client_aveiro1, addr_aveiro1, 'high'),
            (client_aveiro2, addr_aveiro2, 'normal'),
            (client_aveiro3, addr_aveiro3, 'normal'),
            (client_aveiro4, addr_aveiro4, 'normal'),
            (client_aveiro5, addr_aveiro5, 'urgent'),
            (client_aveiro5, addr_aveiro5, 'normal')
        ]
        
        for i, (client, addr, priority) in enumerate(pedidos_data, start=1):
            pedido = Order(
                order_number=f"TST{timestamp}{i:03d}",  # Ex: TST1734567890001
                client_id=client.id,
                address_id=addr.id,
                status='pending',
                priority=priority
            )
            db.session.add(pedido)
            pedidos.append(pedido)
        
        db.session.flush()
        
        # Itens dos pedidos
        for pedido in pedidos:
            prod = random.choice(produtos)
            qtd = random.randint(1, 10)
            item = OrderItem(order_id=pedido.id, product_id=prod.id, quantity=qtd, unit_price=prod.price, total_price=qtd * prod.price)
            db.session.add(item)
            pedido.total_amount = (pedido.total_amount or 0) + item.total_price
        
        # ==================== VEÍCULO E MOTORISTA ====================
        vehicle = Vehicle.query.filter_by(plate='AA-12-34').first()
        if not vehicle:
            vehicle = Vehicle(plate='AA-12-34', model='Sprinter', brand='Mercedes', type='van', max_weight=3500, status='available')
            db.session.add(vehicle)
            db.session.flush()
        
        driver = Driver.query.filter_by(license_number='PT-9876543').first()
        if not driver:
            driver = Driver(name='João Motorista', license_number='PT-9876543', phone='912345678', status='active')
            db.session.add(driver)
            db.session.flush()
        
        # ==================== ROTA ====================
        waypoints_raw = [(centralrest_addr.id, None, 'Centralrest (Início)')]
        
        pedidos_shuffled = list(pedidos)
        random.shuffle(pedidos_shuffled)
        
        for p in pedidos_shuffled:
            waypoints_raw.append((p.address_id, p.id, p.client.name))
        
        waypoints_raw.append((centralrest_addr.id, None, 'Centralrest (Fim)'))
        
        route = Route(
            route_number=f"TST{timestamp}",
            route_name='Rota de Teste - Centro/Norte',
            description='Rota com clientes em Ílhavo, Vagos e Aveiro (ordem aleatória)',
            region='Centro',
            driver_id=driver.id,
            vehicle_id=vehicle.id,
            route_date=date.today(),
            status='planned',
            notes='Rota criada para teste de funcionalidades',
            created_by_id=1
        )
        db.session.add(route)
        db.session.flush()
        
        # Waypoints
        hotel_pedido = pedidos[11] if len(pedidos) > 11 else None
        for seq, (addr_id, order_id, _) in enumerate(waypoints_raw, start=1):
            notes = None
            if order_id and hotel_pedido and order_id == hotel_pedido.id:
                notes = "Restrição crítica: janela de entrega já fechada (08:00-10:00). Reabertura prevista em 50 minutos."
            
            waypoint = RouteWaypoint(
                route_id=route.id,
                order_id=order_id,
                address_id=addr_id,
                sequence_order=seq,
                status='pending',
                estimated_travel_time=random.randint(15, 45),
                notes=notes
            )
            db.session.add(waypoint)
        
        db.session.commit()
        
        print(f"\n✅ Rota de teste criada com sucesso!")
        print(f"   Número da rota: {route.route_number}")
        print(f"   Total de paradas: {len(waypoints_raw)}")
        print(f"   Pedidos incluídos: {len(pedidos)}")
        print("\n🔔 Acesse a rota pelo menu Rotas e utilize o mapa!")
        print("   Use o botão 'Otimizar' para reordenar logicamente as entregas.\n")

if __name__ == '__main__':
    seed_rota_teste()