from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Supplier
from app.extensions import db

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    suppliers = Supplier.query.paginate(page=page, per_page=10)
    return render_template('suppliers/list.html', suppliers=suppliers)

@suppliers_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        supplier = Supplier(
            name=request.form.get('name'),
            contact_info=request.form.get('contact_info'),
            email=request.form.get('email'),
            phone=request.form.get('phone')
        )
        db.session.add(supplier)
        db.session.commit()
        flash('Fornecedor criado com sucesso', 'success')
        return redirect(url_for('suppliers.list'))
    return render_template('suppliers/form.html', supplier=None)

@suppliers_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    supplier = Supplier.query.get_or_404(id)
    if request.method == 'POST':
        supplier.name = request.form.get('name')
        supplier.contact_info = request.form.get('contact_info')
        supplier.email = request.form.get('email')
        supplier.phone = request.form.get('phone')
        db.session.commit()
        flash('Fornecedor atualizado com sucesso', 'success')
        return redirect(url_for('suppliers.list'))
    return render_template('suppliers/form.html', supplier=supplier)

@suppliers_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    supplier = Supplier.query.get_or_404(id)
    db.session.delete(supplier)
    db.session.commit()
    flash('Fornecedor deletado com sucesso', 'success')
    return redirect(url_for('suppliers.list'))
