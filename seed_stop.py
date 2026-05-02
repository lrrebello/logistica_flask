# seed_stop_config.py
from app import create_app
from app.extensions import db
from app.models import StopTimeConfig, Client

def seed_stop_time_configs():
    app = create_app()
    with app.app_context():
        # Criar configurações
        configs = [
            {'name': 'Supermercado', 'base_time': 20, 'unloading_time': 8, 'payment_time': 5, 'documentation_time': 5},
            {'name': 'Padaria/Pequeno Comércio', 'base_time': 10, 'unloading_time': 3, 'payment_time': 3, 'documentation_time': 2},
            {'name': 'Hotel/Restaurante', 'base_time': 15, 'unloading_time': 5, 'payment_time': 4, 'documentation_time': 3},
            {'name': 'Indústria', 'base_time': 30, 'unloading_time': 10, 'payment_time': 8, 'documentation_time': 7},
            {'name': 'Farmácia', 'base_time': 8, 'unloading_time': 2, 'payment_time': 2, 'documentation_time': 2},
            {'name': 'Escola/Hospital', 'base_time': 25, 'unloading_time': 5, 'payment_time': 5, 'documentation_time': 5},
        ]
        
        for data in configs:
            existing = StopTimeConfig.query.filter_by(name=data['name']).first()
            if not existing:
                config = StopTimeConfig(**data)
                db.session.add(config)
                print(f"✅ Criado: {data['name']}")
        
        db.session.commit()
        
        # Associar clientes existentes (opcional)
        config_map = {
            'Supermercado': ['Supermercado Sol Nascente', 'Continente Aveiro', 'Pingo Doce Aveiro', 'Lidl Aveiro'],
            'Padaria/Pequeno Comércio': ['Padaria Central Ílhavo', 'Mercearia do Largo', 'Café Central Vagos'],
            'Hotel/Restaurante': ['Hotel Moliceiro', 'Restaurante O Telheiro'],
            'Indústria': ['Centralrest - Fábrica Ílhavo', 'Talho Vagos']
        }
        
        for config_name, client_names in config_map.items():
            config = StopTimeConfig.query.filter_by(name=config_name).first()
            if config:
                for client_name in client_names:
                    client = Client.query.filter_by(name=client_name).first()
                    if client and not client.stop_time_config_id:
                        client.stop_time_config_id = config.id
                        print(f"  ↳ Associado {client_name} → {config_name}")
        
        db.session.commit()
        print("\n✅ Configurações de tempo de parada criadas com sucesso!")

if __name__ == '__main__':
    seed_stop_time_configs()