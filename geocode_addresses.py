# geocode_addresses.py
from app import create_app
from app.extensions import db
from app.models import Address
import requests
import os
from dotenv import load_dotenv

load_dotenv()

GEOAPIFY_API_KEY = os.getenv('GEOAPIFY_API_KEY')

def geocode_addresses():
    app = create_app()
    with app.app_context():
        addresses = Address.query.filter(
            (Address.latitude == None) | (Address.longitude == None)
        ).all()
        
        for address in addresses:
            addr_str = f"{address.street}, {address.city}, Portugal"
            url = f"https://api.geoapify.com/v1/geocode/search?text={addr_str}&apiKey={GEOAPIFY_API_KEY}"
            
            try:
                response = requests.get(url)
                data = response.json()
                
                if data['features']:
                    coords = data['features'][0]['geometry']['coordinates']
                    address.longitude = coords[0]
                    address.latitude = coords[1]
                    print(f"✅ Geocodificado: {addr_str} -> {coords[1]}, {coords[0]}")
                else:
                    print(f"❌ Não encontrado: {addr_str}")
                    
            except Exception as e:
                print(f"Erro ao geocodificar {addr_str}: {e}")
        
        db.session.commit()
        print("Geocodificação concluída!")

if __name__ == '__main__':
    geocode_addresses()