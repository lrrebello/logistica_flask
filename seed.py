#!/usr/bin/env python3
"""
Script para popular o banco de dados com dados de teste para Portugal
Execute com: python seed.py
"""

from app import create_app
from app.extensions import db
from app.models import (
    User, Supplier, Product, Stock, Client, Address, 
    Vehicle, Driver, Order, OrderItem, Route, RouteWaypoint,
    DeliveryZone, Holiday
)
from datetime import datetime, date, time, timedelta
import uuid

def seed_database():
    app = create_app()
    with app.app_context():
        print("🔄 Recriando banco de dados...")
        db.drop_all()
        db.create_all()
        
        print("👤 Criando usuários...")
        
        # Admin
        admin = User(
            open_id='admin',
            name='Administrador',
            email='admin@logistica.pt',
            role='admin',
            login_method='local',
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Utilizador comercial
        commercial = User(
            open_id='comercial',
            name='João Silva',
            email='comercial@logistica.pt',
            role='user',
            login_method='local',
            is_active=True
        )
        commercial.set_password('comercial123')
        db.session.add(commercial)
        
        # Motorista 1
        driver_user = User(
            open_id='motorista1',
            name='António Santos',
            email='motorista@logistica.pt',
            role='driver',
            login_method='local',
            is_active=True
        )
        driver_user.set_password('motorista123')
        db.session.add(driver_user)
        
        db.session.commit()
        print("✅ Usuários criados")
        
        print("🏢 Criando fornecedores...")
        
        suppliers = [
            Supplier(name='Frutas do Algarve', nif='501234567', contact_person='Manuel Costa', 
                    email='manuel@frutasalgarve.pt', phone='289123456', address='Estrada Nacional 125, Faro'),
            Supplier(name='Carnes Transmontanas', nif='502345678', contact_person='Ricardo Pereira',
                    email='ricardo@carnestm.pt', phone='276123456', address='Zona Industrial, Bragança'),
            Supplier(name='Padaria Central', nif='503456789', contact_person='Isabel Ferreira',
                    email='isabel@padariacentral.pt', phone='213456789', address='Rua Augusta, Lisboa'),
            Supplier(name='Bebidas do Norte', nif='504567890', contact_person='Carlos Mendes',
                    email='carlos@bebidasnorte.pt', phone='253123456', address='Av. da Liberdade, Porto')
        ]
        
        for supplier in suppliers:
            db.session.add(supplier)
        
        db.session.commit()
        print(f"✅ {len(suppliers)} fornecedores criados")
        
        print("📦 Criando produtos...")
        
        products = [
            Product(sku='FRU-001', name='Laranja Algarvia', description='Laranjas frescas do Algarve', 
                   price=1.50, unit='kg', supplier_id=suppliers[0].id),
            Product(sku='FRU-002', name='Maçã Bravo', description='Maçã Bravo de Esmolfe', 
                   price=2.20, unit='kg', supplier_id=suppliers[0].id),
            Product(sku='CAR-001', name='Bife da Vazia', description='Carne maturada 21 dias', 
                   price=18.90, unit='kg', supplier_id=suppliers[1].id),
            Product(sku='CAR-002', name='Frango Caseiro', description='Frango de produção caseira', 
                   price=7.50, unit='kg', supplier_id=suppliers[1].id),
            Product(sku='PAD-001', name='Pão Alentejano', description='Pão tradicional alentejano', 
                   price=2.80, unit='un', supplier_id=suppliers[2].id),
            Product(sku='BEB-001', name='Vinho do Porto', description='Vinho do Porto 10 anos', 
                   price=25.00, unit='garrafa', supplier_id=suppliers[3].id),
        ]
        
        for product in products:
            db.session.add(product)
        
        db.session.commit()
        
        # Adicionar stock
        for product in products:
            stock = Stock(
                product_id=product.id,
                quantity=1000,
                minimum_level=100,
                maximum_level=2000,
                location=f'ZONA-{product.id}'
            )
            db.session.add(stock)
        
        db.session.commit()
        print(f"✅ {len(products)} produtos criados")
        
        print("👥 Criando clientes...")
        
        clients = [
            Client(name='Continente Modelo', nif='501234568', email='compras@continente.pt', phone='213456789'),
            Client(name='Pingo Doce', nif='502345679', email='compras@pingodoce.pt', phone='213456790'),
            Client(name='Lidl Portugal', nif='503456780', email='compras@lidl.pt', phone='213456791'),
            Client(name='Auchan', nif='504567891', email='compras@auchan.pt', phone='213456792'),
        ]
        
        for client in clients:
            db.session.add(client)
        
        db.session.commit()
        
        # Adicionar endereços
        addresses = [
            Address(client_id=clients[0].id, street='Av. João XXI, 50', city='Lisboa', 
                   postal_code='1000-300', latitude=38.7369, longitude=-9.1427, 
                   is_headquarters=True, is_delivery_point=True),
            Address(client_id=clients[1].id, street='Rua de Santa Catarina, 200', city='Porto', 
                   postal_code='4000-450', latitude=41.1496, longitude=-8.6060, 
                   is_headquarters=True, is_delivery_point=True),
            Address(client_id=clients[2].id, street='Estrada Nacional 10', city='Alverca', 
                   postal_code='2615-001', latitude=38.8919, longitude=-9.0398, 
                   is_headquarters=True, is_delivery_point=True),
            Address(client_id=clients[3].id, street='Av. D. João II, 50', city='Lisboa', 
                   postal_code='1990-095', latitude=38.7690, longitude=-9.0945, 
                   is_headquarters=True, is_delivery_point=True),
        ]
        
        for address in addresses:
            db.session.add(address)
        
        db.session.commit()
        print(f"✅ {len(clients)} clientes criados")
        
        print("🚚 Criando veículos...")
        
        vehicles = [
            Vehicle(plate='AA-01-AA', model='Sprinter', brand='Mercedes', type='van',
                   max_weight=2000, max_volume=12, max_height=2.0, fuel_type='diesel', status='available'),
            Vehicle(plate='BB-02-BB', model='Daily', brand='Iveco', type='truck',
                   max_weight=3500, max_volume=20, max_height=2.5, fuel_type='diesel', status='available'),
            Vehicle(plate='CC-03-CC', model='Transit', brand='Ford', type='van',
                   max_weight=1500, max_volume=10, max_height=1.9, fuel_type='diesel', status='available'),
        ]
        
        for vehicle in vehicles:
            db.session.add(vehicle)
        
        db.session.commit()
        print(f"✅ {len(vehicles)} veículos criados")
        
        print("👨‍✈️ Criando motoristas...")
        
        drivers = [
            Driver(user_id=driver_user.id, name='António Santos', license_number='PT-1234567',
                  license_expiry=date(2028, 12, 31), license_category='C', phone='912345678',
                  emergency_contact='Maria Santos', emergency_phone='962345678', status='active',
                  preferred_start_time=time(8, 0), preferred_end_time=time(18, 0)),
            Driver(name='José Ferreira', license_number='PT-7654321',
                  license_expiry=date(2027, 6, 30), license_category='B', phone='923456789',
                  emergency_contact='Ana Ferreira', emergency_phone='963456789', status='active'),
        ]
        
        for driver in drivers:
            db.session.add(driver)
        
        db.session.commit()
        print(f"✅ {len(drivers)} motoristas criados")
        
        print("📝 Criando pedidos...")
        
        orders = []
        for i, client in enumerate(clients):
            order = Order(
                order_number=f'ORD-{datetime.now().strftime("%Y%m%d")}-{i+1:03d}',
                client_id=client.id,
                address_id=client.addresses[0].id if client.addresses else None,
                status='confirmed',
                priority='normal',
                notes=f'Pedido de teste {i+1}',
                created_by_id=admin.id
            )
            db.session.add(order)
            orders.append(order)
        
        db.session.commit()
        
        # Adicionar itens aos pedidos
        for order in orders:
            items = [
                OrderItem(order_id=order.id, product_id=products[0].id, quantity=100, 
                         unit_price=products[0].price, total_price=100 * products[0].price),
                OrderItem(order_id=order.id, product_id=products[1].id, quantity=50,
                         unit_price=products[1].price, total_price=50 * products[1].price),
            ]
            total = 0
            for item in items:
                db.session.add(item)
                total += item.total_price
            order.total_amount = total
        
        db.session.commit()
        print(f"✅ {len(orders)} pedidos criados")
        
        print("🗺️ Criando rotas...")
        
        # Criar uma rota para teste
        route = Route(
            route_number=f'ROT-{datetime.now().strftime("%Y%m%d")}-001',
            driver_id=drivers[0].id,
            vehicle_id=vehicles[0].id,
            route_date=date.today() + timedelta(days=1),
            status='planned',
            optimization_method='manual',
            created_by_id=admin.id
        )
        db.session.add(route)
        db.session.commit()
        
        # Adicionar waypoints à rota
        for idx, order in enumerate(orders[:3]):
            waypoint = RouteWaypoint(
                route_id=route.id,
                order_id=order.id,
                address_id=order.address_id,
                sequence_order=idx + 1,
                original_sequence_order=idx + 1,
                status='pending',
                estimated_travel_time=30
            )
            db.session.add(waypoint)
        
        db.session.commit()
        print(f"✅ Rota criada com {len(orders[:3])} paradas")
        
        print("🗺️ Criando zonas de entrega...")
        
        zones = [
            DeliveryZone(name='Zona Sul', description='Lisboa e arredores', 
                        postal_codes='1000-1999, 2000-2999', default_vehicle_type='van'),
            DeliveryZone(name='Zona Norte', description='Porto e arredores',
                        postal_codes='4000-4999, 5000-5999', default_vehicle_type='truck'),
        ]
        
        for zone in zones:
            db.session.add(zone)
        
        db.session.commit()
        
        print("📅 Criando feriados...")
        
        holidays = [
            Holiday(date=date(2026, 1, 1), name='Ano Novo', affects_delivery=True),
            Holiday(date=date(2026, 4, 5), name='Páscoa', affects_delivery=True),
            Holiday(date=date(2026, 4, 25), name='Dia da Liberdade', affects_delivery=True),
            Holiday(date=date(2026, 5, 1), name='Dia do Trabalhador', affects_delivery=True),
            Holiday(date=date(2026, 6, 10), name='Dia de Portugal', affects_delivery=True),
            Holiday(date=date(2026, 8, 15), name='Assunção de Nossa Senhora', affects_delivery=True),
            Holiday(date=date(2026, 10, 5), name='Implantação da República', affects_delivery=True),
            Holiday(date=date(2026, 11, 1), name='Dia de Todos os Santos', affects_delivery=True),
            Holiday(date=date(2026, 12, 1), name='Restauração da Independência', affects_delivery=True),
            Holiday(date=date(2026, 12, 8), name='Imaculada Conceição', affects_delivery=True),
            Holiday(date=date(2026, 12, 25), name='Natal', affects_delivery=True),
        ]
        
        for holiday in holidays:
            db.session.add(holiday)
        
        db.session.commit()
        
        print("\n" + "="*50)
        print("🎉 BANCO DE DADOS CRIADO COM SUCESSO!")
        print("="*50)
        print("\n📋 Credenciais de acesso:")
        print("   Admin:     admin@logistica.pt / admin123")
        print("   Comercial: comercial@logistica.pt / comercial123")
        print("   Motorista: motorista@logistica.pt / motorista123")
        print("\n📊 Resumo:")
        print(f"   - {len(users)} utilizadores")
        print(f"   - {len(suppliers)} fornecedores")
        print(f"   - {len(products)} produtos")
        print(f"   - {len(clients)} clientes")
        print(f"   - {len(vehicles)} veículos")
        print(f"   - {len(drivers)} motoristas")
        print(f"   - {len(orders)} pedidos")
        print(f"   - 1 rota com {len(orders[:3])} paradas")
        print(f"   - {len(zones)} zonas de entrega")
        print(f"   - {len(holidays)} feriados")
        print("="*50)

if __name__ == '__main__':
    seed_database()