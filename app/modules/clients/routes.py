from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Client, Address
from app.extensions import db

clients_bp = Blueprint('clients', __name__)

@clients_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    clients = Client.query.paginate(page=page, per_page=10)
    return render_template('clients/list.html', clients=clients)

@clients_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        client = Client(
            name=request.form.get('name'),
            tax_id=request.form.get('tax_id'),
            email=request.form.get('email'),
            phone=request.form.get('phone')
        )
        db.session.add(client)
        db.session.commit()
        flash('Cliente criado com sucesso', 'success')
        return redirect(url_for('clients.list'))
    return render_template('clients/form.html', client=None)

@clients_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    client = Client.query.get_or_404(id)
    if request.method == 'POST':
        client.name = request.form.get('name')
        client.tax_id = request.form.get('tax_id')
        client.email = request.form.get('email')
        client.phone = request.form.get('phone')
        db.session.commit()
        flash('Cliente atualizado com sucesso', 'success')
        return redirect(url_for('clients.list'))
    return render_template('clients/form.html', client=client)

@clients_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash('Cliente deletado com sucesso', 'success')
    return redirect(url_for('clients.list'))

# Endereços do Cliente (Sede e Descarga)
@clients_bp.route('/<int:client_id>/addresses/new', methods=['GET', 'POST'])
@login_required
def address_new(client_id):
    client = Client.query.get_or_404(client_id)
    if request.method == 'POST':
        address = Address(
            client_id=client.id,
            street=request.form.get('street'),
            city=request.form.get('city'),
            postal_code=request.form.get('postal_code'),
            latitude=request.form.get('latitude'),
            longitude=request.form.get('longitude'),
            is_headquarters=True if request.form.get('is_headquarters') else False,
            is_delivery_point=True if request.form.get('is_delivery_point') else False
        )
        db.session.add(address)
        db.session.commit()
        flash('Endereço adicionado com sucesso', 'success')
        return redirect(url_for('clients.edit', id=client.id))
    return render_template('clients/address_form.html', client=client, address=None)
