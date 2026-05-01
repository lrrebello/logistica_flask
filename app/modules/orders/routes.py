from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Order, OrderItem, Client, Product, Address
from app.extensions import db
import uuid

orders_bp = Blueprint('orders', __name__)

@orders_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    orders = Order.query.paginate(page=page, per_page=10)
    return render_template('orders/list.html', orders=orders)

@orders_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    clients = Client.query.all()
    products = Product.query.all()
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        # Buscar o endereço de descarga padrão do cliente
        address = Address.query.filter_by(client_id=client_id, is_delivery_point=True).first()
        if not address:
            address = Address.query.filter_by(client_id=client_id).first()
            
        if not address:
            flash('Cliente não possui endereço cadastrado', 'danger')
            return redirect(url_for('orders.new'))

        order = Order(
            order_number=str(uuid.uuid4())[:8].upper(),
            client_id=client_id,
            address_id=address.id,
            status='pending',
            notes=request.form.get('notes')
        )
        db.session.add(order)
        db.session.commit()
        flash('Pedido criado com sucesso', 'success')
        return redirect(url_for('orders.list'))
    return render_template('orders/form.html', clients=clients, products=products)

@orders_bp.route('/<int:id>/status', methods=['POST'])
@login_required
def update_status(id):
    order = Order.query.get_or_404(id)
    order.status = request.form.get('status')
    db.session.commit()
    flash('Status do pedido atualizado', 'success')
    return redirect(url_for('orders.list'))
