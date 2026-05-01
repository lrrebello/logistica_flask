from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Vehicle
from app.extensions import db

vehicles_bp = Blueprint('vehicles', __name__)

@vehicles_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    vehicles = Vehicle.query.paginate(page=page, per_page=10)
    return render_template('vehicles/list.html', vehicles=vehicles)

@vehicles_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        vehicle = Vehicle(
            plate=request.form.get('plate'),
            model=request.form.get('model'),
            type=request.form.get('type'),
            max_weight=request.form.get('max_weight'),
            max_height=request.form.get('max_height'),
            status='available'
        )
        db.session.add(vehicle)
        db.session.commit()
        flash('Veículo cadastrado com sucesso', 'success')
        return redirect(url_for('vehicles.list'))
    return render_template('vehicles/form.html', vehicle=None)

@vehicles_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    vehicle = Vehicle.query.get_or_404(id)
    if request.method == 'POST':
        vehicle.plate = request.form.get('plate')
        vehicle.model = request.form.get('model')
        vehicle.type = request.form.get('type')
        vehicle.max_weight = request.form.get('max_weight')
        vehicle.max_height = request.form.get('max_height')
        vehicle.status = request.form.get('status')
        db.session.commit()
        flash('Veículo atualizado com sucesso', 'success')
        return redirect(url_for('vehicles.list'))
    return render_template('vehicles/form.html', vehicle=vehicle)
