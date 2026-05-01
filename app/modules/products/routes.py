from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Product, Supplier, Stock
from app.extensions import db

products_bp = Blueprint('products', __name__)

@products_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    products = Product.query.paginate(page=page, per_page=10)
    return render_template('products/list.html', products=products)

@products_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    suppliers = Supplier.query.all()
    if request.method == 'POST':
        product = Product(
            name=request.form.get('name'),
            description=request.form.get('description'),
            price=request.form.get('price'),
            unit=request.form.get('unit', 'kg'),
            supplier_id=request.form.get('supplier_id') or None
        )
        db.session.add(product)
        db.session.flush()
        
        stock = Stock(
            product_id=product.id,
            quantity=0,
            minimum_level=request.form.get('minimum_level', 0)
        )
        db.session.add(stock)
        db.session.commit()
        
        flash('Produto criado com sucesso', 'success')
        return redirect(url_for('products.list'))
    return render_template('products/form.html', product=None, suppliers=suppliers)

@products_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    product = Product.query.get_or_404(id)
    suppliers = Supplier.query.all()
    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = request.form.get('price')
        product.unit = request.form.get('unit', 'kg')
        product.supplier_id = request.form.get('supplier_id') or None
        
        if product.stock:
            product.stock.minimum_level = request.form.get('minimum_level', 0)
        
        db.session.commit()
        flash('Produto atualizado com sucesso', 'success')
        return redirect(url_for('products.list'))
    return render_template('products/form.html', product=product, suppliers=suppliers)

@products_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Produto deletado com sucesso', 'success')
    return redirect(url_for('products.list'))
