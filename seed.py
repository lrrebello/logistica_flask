#!/usr/bin/env python3
"""
Seed para popular o banco de dados com dados iniciais para produção
Execute com: python seed_producao.py
"""

from app import create_app
from app.extensions import db
from app.models import (
    User, Supplier, Product, Stock, Client, Address, 
    Vehicle, Driver, Order, OrderItem, Route, RouteWaypoint,
    StopTimeConfig, DeliveryZone, Holiday
)
from datetime import datetime, date, time
import random

def seed_producao():
    app = create_app()
    with app.app_context():
        print("🌱 A criar dados iniciais para produção...")
        
        # ==================== USUÁRIOS ====================
        print("👤 Criando usuários...")
        
        # Usuário Admin
        admin = User.query.filter_by(email='admin@logistica.pt').first()
        if not admin:
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
            print("  ✅ Admin criado: admin@logistica.pt / admin123")
        
        # Usuário Comercial
        comercial = User.query.filter_by(email='comercial@logistica.pt').first()
        if not comercial:
            comercial = User(
                open_id='comercial',
                name='João Comercial',
                email='comercial@logistica.pt',
                role='user',
                login_method='local',
                is_active=True
            )
            comercial.set_password('comercial123')
            db.session.add(comercial)
            print("  ✅ Comercial criado: comercial@logistica.pt / comercial123")
        
        # Usuário Motorista 1
        motorista1 = User.query.filter_by(email='motorista1@logistica.pt').first()
        if not motorista1:
            motorista1 = User(
                open_id='motorista1',
                name='António Santos',
                email='motorista1@logistica.pt',
                role='driver',
                login_method='local',
                is_active=True
            )
            motorista1.set_password('motorista123')
            db.session.add(motorista1)
            print("  ✅ Motorista 1 criado: motorista1@logistica.pt / motorista123")
        
        # Usuário Motorista 2
        motorista2 = User.query.filter_by(email='motorista2@logistica.pt').first()
        if not motorista2:
            motorista2 = User(
                open_id='motorista2',
                name='José Ferreira',
                email='motorista2@logistica.pt',
                role='driver',
                login_method='local',
                is_active=True
            )
            motorista2.set_password('motorista123')
            db.session.add(motorista2)
            print("  ✅ Motorista 2 criado: motorista2@logistica.pt / motorista123")
        
        db.session.commit()
        
        # ==================== CONFIGURAÇÕES DE TEMPO ====================
        print("⏱️ Configurando tempos de parada...")
        
        stop_configs = [
            {'name': 'Supermercado', 'base_time': 20, 'unloading_time_per_unit': 3, 'payment_time': 8, 'documentation_time': 5, 'setup_time': 10},
            {'name': 'Padaria/Pequeno Comércio', 'base_time': 10, 'unloading_time_per_unit': 1, 'payment_time': 3, 'documentation_time': 2, 'setup_time': 5},
            {'name': 'Hotel/Restaurante', 'base_time': 15, 'unloading_time_per_unit': 2, 'payment_time': 5, 'documentation_time': 3, 'setup_time': 8},
            {'name': 'Indústria', 'base_time': 30, 'unloading_time_per_unit': 5, 'payment_time': 10, 'documentation_time': 10, 'setup_time': 15},
            {'name': 'Farmácia', 'base_time': 8, 'unloading_time_per_unit': 1, 'payment_time': 2, 'documentation_time': 2, 'setup_time': 5},
            {'name': 'Escola/Hospital', 'base_time': 25, 'unloading_time_per_unit': 3, 'payment_time': 5, 'documentation_time': 8, 'setup_time': 10},
        ]
        
        for data in stop_configs:
            existing = StopTimeConfig.query.filter_by(name=data['name']).first()
            if not existing:
                config = StopTimeConfig(**data)
                db.session.add(config)
                print(f"  ✅ {data['name']} criado")
        
        db.session.commit()
        
        # ==================== VEÍCULOS ====================
        print("🚚 Criando veículos...")
        
        vehicles = [
            {'plate': 'AA-01-AA', 'model': 'Sprinter', 'brand': 'Mercedes', 'type': 'van', 'max_weight': 3500, 'max_height': 2.2, 'length': 5.9, 'status': 'available'},
            {'plate': 'BB-02-BB', 'model': 'Daily', 'brand': 'Iveco', 'type': 'truck', 'max_weight': 7000, 'max_height': 3.0, 'length': 7.2, 'status': 'available'},
            {'plate': 'CC-03-CC', 'model': 'Transit', 'brand': 'Ford', 'type': 'van', 'max_weight': 4000, 'max_height': 2.5, 'length': 6.0, 'status': 'available'},
        ]
        
        for data in vehicles:
            existing = Vehicle.query.filter_by(plate=data['plate']).first()
            if not existing:
                vehicle = Vehicle(**data)
                db.session.add(vehicle)
                print(f"  ✅ {data['plate']} - {data['model']} criado")
        
        db.session.commit()
        
        # ==================== MOTORISTAS ====================
        print("👨‍✈️ Criando motoristas...")
        
        drivers = [
            {'user_id': motorista1.id, 'name': 'António Santos', 'license_number': 'PT-1234567', 'license_expiry': date(2028, 12, 31), 'license_category': 'C', 'phone': '912345678', 'status': 'active'},
            {'user_id': motorista2.id, 'name': 'José Ferreira', 'license_number': 'PT-7654321', 'license_expiry': date(2027, 6, 30), 'license_category': 'C', 'phone': '923456789', 'status': 'active'},
        ]
        
        for data in drivers:
            existing = Driver.query.filter_by(license_number=data['license_number']).first()
            if not existing:
                driver = Driver(**data)
                db.session.add(driver)
                print(f"  ✅ {data['name']} criado")
        
        db.session.commit()
        
        # ==================== CLIENTES EXEMPLO ====================
        print("🏢 Criando clientes exemplo...")
        
        clientes = [
            {'name': 'Supermercado Modelo', 'nif': '501234567', 'email': 'compras@modelo.pt', 'phone': '213456789'},
            {'name': 'Padaria Central', 'nif': '502345678', 'email': 'padaria@central.pt', 'phone': '213456790'},
            {'name': 'Hotel Portugal', 'nif': '503456789', 'email': 'compras@hotelportugal.pt', 'phone': '213456791'},
        ]
        
        for data in clientes:
            existing = Client.query.filter_by(nif=data['nif']).first()
            if not existing:
                client = Client(**data)
                db.session.add(client)
                print(f"  ✅ {data['name']} criado")
        
        db.session.commit()
        
        # ==================== FERIADOS PORTUGAL ====================
        print("📅 Criando feriados...")
        
        feriados = [
            {'date': date(2026, 1, 1), 'name': 'Ano Novo'},
            {'date': date(2026, 4, 5), 'name': 'Páscoa'},
            {'date': date(2026, 4, 25), 'name': 'Dia da Liberdade'},
            {'date': date(2026, 5, 1), 'name': 'Dia do Trabalhador'},
            {'date': date(2026, 6, 10), 'name': 'Dia de Portugal'},
            {'date': date(2026, 8, 15), 'name': 'Assunção de Nossa Senhora'},
            {'date': date(2026, 10, 5), 'name': 'Implantação da República'},
            {'date': date(2026, 11, 1), 'name': 'Dia de Todos os Santos'},
            {'date': date(2026, 12, 1), 'name': 'Restauração da Independência'},
            {'date': date(2026, 12, 8), 'name': 'Imaculada Conceição'},
            {'date': date(2026, 12, 25), 'name': 'Natal'},
        ]
        
        for data in feriados:
            existing = Holiday.query.filter_by(date=data['date']).first()
            if not existing:
                holiday = Holiday(**data)
                db.session.add(holiday)
        
        db.session.commit()
        print(f"  ✅ {len(feriados)} feriados criados")
        
        # ==================== ZONAS DE ENTREGA ====================
        print("🗺️ Criando zonas de entrega...")
        
        zonas = [
            {'name': 'Grande Lisboa', 'description': 'Lisboa e arredores', 'postal_codes': '1000-1999', 'default_vehicle_type': 'van'},
            {'name': 'Grande Porto', 'description': 'Porto e arredores', 'postal_codes': '4000-4999', 'default_vehicle_type': 'van'},
            {'name': 'Centro', 'description': 'Região Centro', 'postal_codes': '3000-3999', 'default_vehicle_type': 'truck'},
        ]
        
        for data in zonas:
            existing = DeliveryZone.query.filter_by(name=data['name']).first()
            if not existing:
                zone = DeliveryZone(**data)
                db.session.add(zone)
                print(f"  ✅ {data['name']} criada")
        
        db.session.commit()
        
        print("\n" + "="*50)
        print("🎉 SEED CONCLUÍDO COM SUCESSO!")
        print("="*50)
        print("\n📋 Credenciais de acesso:")
        print("   Admin:     admin@logistica.pt / admin123")
        print("   Comercial: comercial@logistica.pt / comercial123")
        print("   Motorista: motorista1@logistica.pt / motorista123")
        print("   Motorista: motorista2@logistica.pt / motorista123")
        print("\n🚚 Veículos criados:")
        print("   AA-01-AA - Mercedes Sprinter (Van)")
        print("   BB-02-BB - Iveco Daily (Camião)")
        print("   CC-03-CC - Ford Transit (Van)")
        print("\n👨‍✈️ Motoristas:")
        print("   António Santos (PT-1234567)")
        print("   José Ferreira (PT-7654321)")
        print("\n🏢 Clientes exemplo:")
        for c in clientes:
            print(f"   {c['name']}")
        print("="*50)

if __name__ == '__main__':
    seed_producao()