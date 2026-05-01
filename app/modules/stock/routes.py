from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models import Stock, Product
from app.extensions import db
from datetime import datetime

stock_bp = Blueprint('stock', __name__)

@stock_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    stocks = Stock.query.paginate(page=page, per_page=10)
    return render_template('stock/list.html', stocks=stocks)

@stock_bp.route('/<int:id>/update', methods=['GET', 'POST'])
@login_required
def update(id):
    stock = Stock.query.get_or_404(id)
    if request.method == 'POST':
        stock.quantity = request.form.get('quantity')
        stock.minimum_level = request.form.get('minimum_level')
        stock.last_updated = datetime.utcnow()
        db.session.commit()
        flash('Estoque atualizado com sucesso', 'success')
        return redirect(url_for('stock.list'))
    return render_template('stock/form.html', stock=stock)
