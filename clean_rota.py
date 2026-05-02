# cleanup_orphans.py
from app import create_app
from app.extensions import db
from app.models import Order, RouteWaypoint

def cleanup_orphans():
    app = create_app()
    with app.app_context():
        # Encontrar pedidos que estão 'confirmed' mas não têm waypoint
        orphan_orders = Order.query.filter(
            Order.status == 'confirmed',
            ~Order.route_waypoints.any()
        ).all()
        
        print(f"Encontrados {len(orphan_orders)} pedidos órfãos")
        
        for order in orphan_orders:
            order.status = 'pending'
            print(f"  ↳ Pedido #{order.order_number} voltou para 'pending'")
        
        db.session.commit()
        print("✅ Limpeza concluída!")

if __name__ == '__main__':
    cleanup_orphans()