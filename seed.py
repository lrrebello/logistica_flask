#!/usr/bin/env python3
"""
Script para popular o banco de dados com dados de teste
Execute com: python seed.py
"""

from app import app, db
from models import User, Supplier, Product, Stock, Client, Address, Vehicle, Driver, Order, OrderItem
from datetime import datetime, date, timedelta

def seed_database():
    with app.app_context():
        # Limpar dados existentes (opcional)
        print("🔄 Limpando dados existentes...")
        db.drop_all()
        db.create_all()
        
        # ==================== CRIAR USUÁRIOS ====================
        print("👤 Criando usuários...")
        
        admin = User(
            open_id='admin_user',
            name='Administrador',
            email='admin@logistica.com',
            role='admin',
            login_method='local'
        )
        admin.set_password('admin')
        db.session.add(admin)
        
        user = User(
            open_id='user_user',
            name='Usuário Teste',
            email='user@logistica.com',
            role='user',
            login_method='local'
        )
        user.set_password('user')
        db.session.add(user)
        
        driver = User(
            open_id='driver_user',
            name='Motorista Teste',
            email='driver@logistica.com',
            role='driver',
            login_method='local'
        )
        driver.set_password('driver')
        db.session.add(driver)
        
        db.session.commit()
        print("✅ Usuários criados")
        
        # ==================== CRIAR FORNECEDORES ====================
        print("🏢 Criando fornecedores...")
        
        suppliers_data = [
            {
                'name': 'Fornecedor A',
                'contact_info': 'João Silva',
                'email': 'joao@fornecedora.com',
                'phone': '(11) 98765-4321'
            },
            {
                'name': 'Fornecedor B',
                'contact_info': 'Maria Santos',
                'email': 'maria@fornecedorb.com',
                'phone': '(11) 99876-5432'
            },
            {
                'name': 'Fornecedor C',
                'contact_info': 'Pedro Costa',
                'email': 'pedro@fornecedorc.com',
                'phone': '(11) 97654-3210'
            }
        ]
        
        suppliers = []
        for data in suppliers_data:
            supplier = Supplier(**data)
            db.session.add(supplier)
            suppliers.append(supplier)
        
        db.session.commit()
        print(f"✅ {len(suppliers)} fornecedores criados")
        
        # ==================== CRIAR PRODUTOS ====================
        print("📦 Criando produtos...")
        
        products_data = [
            {'name': 'Arroz Integral 5kg', 'description': 'Arroz integral de qualidade premium', 'price': '25.50', 'unit': 'kg', 'supplier_id': suppliers[0].id},
            {'name': 'Feijão Carioca 2kg', 'description': 'Feijão carioca selecionado', 'price': '15.00', 'unit': 'kg', 'supplier_id': suppliers[0].id},
            {'name': 'Macarrão Integral 500g', 'description': 'Macarrão integral tipo penne', 'price': '8.50', 'unit': 'un', 'supplier_id': suppliers[1].id},
            {'name': 'Azeite Extra Virgem 500ml', 'description': 'Azeite importado extra virgem', 'price': '45.00', 'unit': 'un', 'supplier_id': suppliers[1].id},
            {'name': 'Sal Refinado 1kg', 'description': 'Sal refinado iodado', 'price': '3.50', 'unit': 'kg', 'supplier_id': suppliers[2].id},
            {'name': 'Açúcar Cristal 2kg', 'description': 'Açúcar cristal refinado', 'price': '12.00', 'unit': 'kg', 'supplier_id': suppliers[2].id},
        ]
        
        products = []
        for data in products_data:
            product = Product(**data)
            db.session.add(product)
            products.append(product)
        
        db.session.commit()
        print(f"✅ {len(products)} produtos criados")
        
        # ==================== CRIAR STOCK ====================
        print("📊 Criando stock...")
        
        for product in products:
            stock = Stock(
                product_id=product.id,
                quantity=100,
                minimum_level=20
            )
            db.session.add(stock)
        
        db.session.commit()
        print(f"✅ Stock criado para {len(products)} produtos")
        
        # ==================== CRIAR CLIENTES ====================
        print("👥 Criando clientes...")
        
        clients_data = [
            {'name': 'Supermercado Central', 'tax_id': '12.345.678/0001-90', 'email': 'compras@central.com.br', 'phone': '(11) 3333-4444'},
            {'name': 'Mercearia do Bairro', 'tax_id': '98.765.432/0001-10', 'email': 'vendas@mercearia.com.br', 'phone': '(11) 4444-5555'},
            {'name': 'Restaurante Sabor', 'tax_id': '55.555.555/0001-88', 'email': 'pedidos@sabor.com.br', 'phone': '(11) 5555-6666'},
        ]
        
        clients = []
        for data in clients_data:
            client = Client(**data)
            db.session.add(client)
            clients.append(client)
        
        db.session.commit()
        print(f"✅ {len(clients)} clientes criados")
        
        # ==================== CRIAR ENDEREÇOS ====================
        print("📍 Criando endereços...")
        
        addresses_data = [
            {'client_id': clients[0].id, 'street': 'Rua A, 100', 'city': 'São Paulo', 'postal_code': '01000-000', 'latitude': -23.5505, 'longitude': -46.6333, 'is_headquarters': True},
            {'client_id': clients[1].id, 'street': 'Rua B, 200', 'city': 'São Paulo', 'postal_code': '02000-000', 'latitude': -23.5500, 'longitude': -46.6300, 'is_headquarters': True},
            {'client_id': clients[2].id, 'street': 'Rua C, 300', 'city': 'São Paulo', 'postal_code': '03000-000', 'latitude': -23.5510, 'longitude': -46.6350, 'is_headquarters': True},
        ]
        
        addresses = []
        for data in addresses_data:
            address = Address(**data)
            db.session.add(address)
            addresses.append(address)
        
        db.session.commit()
        print(f"✅ {len(addresses)} endereços criados")
        
        # ==================== CRIAR VEÍCULOS ====================
        print("🚚 Criando veículos...")
        
        vehicles_data = [
            {'plate': 'ABC-1234', 'model': 'Volkswagen Delivery', 'type': 'light', 'max_weight': '1500', 'max_height': '2.0', 'status': 'available'},
            {'plate': 'DEF-5678', 'model': 'Iveco Daily', 'type': 'medium', 'max_weight': '3500', 'max_height': '2.5', 'status': 'available'},
            {'plate': 'GHI-9012', 'model': 'Scania P310', 'type': 'heavy', 'max_weight': '10000', 'max_height': '3.0', 'status': 'available'},
        ]
        
        vehicles = []
        for data in vehicles_data:
            vehicle = Vehicle(**data)
            db.session.add(vehicle)
            vehicles.append(vehicle)
        
        db.session.commit()
        print(f"✅ {len(vehicles)} veículos criados")
        
        # ==================== CRIAR MOTORISTAS ====================
        print("👨‍✈️ Criando motoristas...")
        
        drivers_data = [
            {
                'user_id': driver.id,
                'name': 'Carlos Silva',
                'license_number': '12345678901',
                'license_expiry': date.today() + timedelta(days=365),
                'phone': '(11) 99999-1111',
                'address': 'Rua X, 123 - São Paulo',
                'emergency_contact': '(11) 99999-2222',
                'hire_date': date.today() - timedelta(days=365),
                'status': 'active'
            },
            {
                'user_id': None,
                'name': 'João Santos',
                'license_number': '98765432109',
                'license_expiry': date.today() + timedelta(days=180),
                'phone': '(11) 99999-3333',
                'address': 'Rua Y, 456 - São Paulo',
                'emergency_contact': '(11) 99999-4444',
                'hire_date': date.today() - timedelta(days=180),
                'status': 'active'
            },
        ]
        
        drivers_list = []
        for data in drivers_data:
            drv = Driver(**data)
            db.session.add(drv)
            drivers_list.append(drv)
        
        db.session.commit()
        print(f"✅ {len(drivers_list)} motoristas criados")
        
        # ==================== CRIAR PEDIDOS ====================
        print("📋 Criando pedidos...")
        
        orders_data = [
            {
                'order_number': f'PED-{datetime.now().timestamp()}',
                'client_id': clients[0].id,
                'address_id': addresses[0].id,
                'status': 'pending',
                'notes': 'Entrega prioritária',
                'total_amount': '100.00'
            },
            {
                'order_number': f'PED-{datetime.now().timestamp() + 1}',
                'client_id': clients[1].id,
                'address_id': addresses[1].id,
                'status': 'confirmed',
                'notes': 'Entrega normal',
                'total_amount': '250.50'
            },
            {
                'order_number': f'PED-{datetime.now().timestamp() + 2}',
                'client_id': clients[2].id,
                'address_id': addresses[2].id,
                'status': 'in_transit',
                'notes': 'Em rota de entrega',
                'total_amount': '450.00'
            },
        ]
        
        orders_list = []
        for data in orders_data:
            order = Order(**data)
            db.session.add(order)
            orders_list.append(order)
        
        db.session.commit()
        print(f"✅ {len(orders_list)} pedidos criados")
        
        # ==================== CRIAR ITENS DE PEDIDOS ====================
        print("📦 Criando itens de pedidos...")
        
        order_items_count = 0
        for i, order in enumerate(orders_list):
            for j in range(2):
                product = products[i * 2 + j]
                item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=10,
                    unit_price=float(product.price),
                    subtotal=float(product.price) * 10
                )
                db.session.add(item)
                order_items_count += 1
        
        db.session.commit()
        print(f"✅ {order_items_count} itens de pedidos criados")
        
        # ==================== RESUMO ====================
        print("\n" + "="*50)
        print("✅ BANCO DE DADOS POPULADO COM SUCESSO!")
        print("="*50)
        print("\n📝 Credenciais de teste:\n")
        print("Admin:")
        print("  Email: admin@logistica.com")
        print("  Senha: admin")
        print("\nUsuário:")
        print("  Email: user@logistica.com")
        print("  Senha: user")
        print("\nMotorista:")
        print("  Email: driver@logistica.com")
        print("  Senha: driver")
        print("\n" + "="*50 + "\n")

if __name__ == '__main__':
    seed_database()
