from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Client, Address, StopTimeConfig
from app.extensions import db
import re

clients_bp = Blueprint('clients', __name__)


def validar_nif(nif):
    """Valida NIF português (9 dígitos, sem espaços ou caracteres especiais)"""
    if not nif:
        return None
    # Remover espaços, pontos, hífens
    nif_limpo = re.sub(r'[^0-9]', '', str(nif))
    if len(nif_limpo) == 9 and nif_limpo.isdigit():
        return nif_limpo
    return None

@clients_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    clients = Client.query.paginate(page=page, per_page=10)
    return render_template('clients/list.html', clients=clients)


@clients_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    stop_time_configs = StopTimeConfig.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        # Validar NIF
        nif_raw = request.form.get('nif')
        nif_validado = validar_nif(nif_raw)
        
        if nif_raw and not nif_validado:
            flash('NIF inválido. Deve conter 9 dígitos.', 'danger')
            return render_template('clients/form.html', 
                                 client=None, 
                                 address=None,
                                 stop_time_configs=stop_time_configs,
                                 form_data=request.form)
        
        client = Client(
            name=request.form.get('name'),
            nif=nif_validado,
            email=request.form.get('email') or None,
            phone=request.form.get('phone') or None,
            stop_time_config_id=request.form.get('stop_time_config_id') or None,
            custom_stop_time=request.form.get('custom_stop_time') or None,
            average_pallets=request.form.get('average_pallets', 1),
            needs_delivery_ramp=True if request.form.get('needs_delivery_ramp') else False
        )
        db.session.add(client)
        db.session.flush()
        
        address = Address(
            client_id=client.id,
            street=request.form.get('street'),
            city=request.form.get('city'),
            postal_code=request.form.get('postal_code'),
            latitude=request.form.get('latitude') or None,
            longitude=request.form.get('longitude') or None,
            is_headquarters=True if request.form.get('is_headquarters') else False,
            is_delivery_point=True if request.form.get('is_delivery_point') else False,
            delivery_instructions=request.form.get('delivery_instructions'),
            time_window_start=request.form.get('time_window_start') or None,
            time_window_end=request.form.get('time_window_end') or None
        )
        db.session.add(address)
        
        db.session.commit()
        flash('Cliente criado com sucesso', 'success')
        return redirect(url_for('clients.list'))
    
    return render_template('clients/form.html', 
                         client=None, 
                         address=None,
                         stop_time_configs=stop_time_configs)


@clients_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    client = Client.query.get_or_404(id)
    stop_time_configs = StopTimeConfig.query.filter_by(is_active=True).all()
    
    # Buscar o endereço principal (primeiro endereço)
    address = client.addresses[0] if client.addresses else None
    
    if request.method == 'POST':
        # ==================== ATUALIZAR CLIENTE ====================
        client.name = request.form.get('name')
        client.nif = request.form.get('nif')
        client.email = request.form.get('email')
        client.phone = request.form.get('phone')
        client.stop_time_config_id = request.form.get('stop_time_config_id') or None
        client.custom_stop_time = request.form.get('custom_stop_time') or None
        client.average_pallets = request.form.get('average_pallets', 1)
        client.needs_delivery_ramp = True if request.form.get('needs_delivery_ramp') else False
        
        # ==================== ATUALIZAR OU CRIAR ENDEREÇO PRINCIPAL ====================
        if address:
            # Atualizar endereço existente
            address.street = request.form.get('street')
            address.city = request.form.get('city')
            address.postal_code = request.form.get('postal_code')
            address.latitude = request.form.get('latitude') or None
            address.longitude = request.form.get('longitude') or None
            address.is_headquarters = True if request.form.get('is_headquarters') else False
            address.is_delivery_point = True if request.form.get('is_delivery_point') else False
            address.delivery_instructions = request.form.get('delivery_instructions')
            address.time_window_start = request.form.get('time_window_start') or None
            address.time_window_end = request.form.get('time_window_end') or None
        else:
            # Criar novo endereço
            address = Address(
                client_id=client.id,
                street=request.form.get('street'),
                city=request.form.get('city'),
                postal_code=request.form.get('postal_code'),
                latitude=request.form.get('latitude') or None,
                longitude=request.form.get('longitude') or None,
                is_headquarters=True if request.form.get('is_headquarters') else False,
                is_delivery_point=True if request.form.get('is_delivery_point') else False,
                delivery_instructions=request.form.get('delivery_instructions'),
                time_window_start=request.form.get('time_window_start') or None,
                time_window_end=request.form.get('time_window_end') or None
            )
            db.session.add(address)
        
        db.session.commit()
        flash('Cliente atualizado com sucesso', 'success')
        return redirect(url_for('clients.list'))
    
    return render_template('clients/form.html', client=client, address=address, stop_time_configs=stop_time_configs)


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
            is_delivery_point=True if request.form.get('is_delivery_point') else False,
            delivery_instructions=request.form.get('delivery_instructions'),
            time_window_start=request.form.get('time_window_start') if request.form.get('time_window_start') else None,
            time_window_end=request.form.get('time_window_end') if request.form.get('time_window_end') else None
        )
        db.session.add(address)
        db.session.commit()
        flash('Endereço adicionado com sucesso', 'success')
        return redirect(url_for('clients.edit', id=client.id))
    return render_template('clients/address_form.html', client=client, address=None)


@clients_bp.route('/address/<int:address_id>/delete', methods=['POST'])
@login_required
def address_delete(address_id):
    address = Address.query.get_or_404(address_id)
    client_id = address.client_id
    db.session.delete(address)
    db.session.commit()
    flash('Endereço removido com sucesso', 'success')
    return redirect(url_for('clients.edit', id=client_id))


@clients_bp.route('/address/<int:address_id>/edit', methods=['GET', 'POST'])
@login_required
def address_edit(address_id):
    address = Address.query.get_or_404(address_id)
    client = address.client
    if request.method == 'POST':
        address.street = request.form.get('street')
        address.city = request.form.get('city')
        address.postal_code = request.form.get('postal_code')
        address.latitude = request.form.get('latitude') or None
        address.longitude = request.form.get('longitude') or None
        address.is_headquarters = True if request.form.get('is_headquarters') else False
        address.is_delivery_point = True if request.form.get('is_delivery_point') else False
        address.delivery_instructions = request.form.get('delivery_instructions')
        address.time_window_start = request.form.get('time_window_start') or None
        address.time_window_end = request.form.get('time_window_end') or None
        db.session.commit()
        flash('Endereço atualizado com sucesso', 'success')
        return redirect(url_for('clients.edit', id=client.id))
    return render_template('clients/address_form.html', client=client, address=address)