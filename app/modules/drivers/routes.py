from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Driver, User
from app.extensions import db
from datetime import datetime

drivers_bp = Blueprint('drivers', __name__)

@drivers_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    drivers = Driver.query.paginate(page=page, per_page=10)
    return render_template('drivers/list.html', drivers=drivers)

@drivers_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    # Buscar usuários que ainda não são motoristas e têm role 'driver' ou 'user'
    existing_driver_user_ids = [d.user_id for d in Driver.query.all() if d.user_id]
    available_users = User.query.filter(~User.id.in_(existing_driver_user_ids)).all()
    
    if request.method == 'POST':
        driver = Driver(
            user_id=request.form.get('user_id') or None,
            name=request.form.get('name'),
            license_number=request.form.get('license_number'),
            license_expiry=datetime.strptime(request.form.get('license_expiry'), '%Y-%m-%d').date() if request.form.get('license_expiry') else None,
            phone=request.form.get('phone'),
            status='active'
        )
        db.session.add(driver)
        db.session.commit()
        flash('Motorista cadastrado com sucesso', 'success')
        return redirect(url_for('drivers.list'))
    return render_template('drivers/form.html', driver=None, users=available_users)

@drivers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    driver = Driver.query.get_or_404(id)
    if request.method == 'POST':
        driver.name = request.form.get('name')
        driver.license_number = request.form.get('license_number')
        driver.phone = request.form.get('phone')
        driver.status = request.form.get('status')
        db.session.commit()
        flash('Motorista atualizado com sucesso', 'success')
        return redirect(url_for('drivers.list'))
    return render_template('drivers/form.html', driver=driver)
