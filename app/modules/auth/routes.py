from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.extensions import db
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('core.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_signed_in = datetime.utcnow()
            db.session.commit()
            return redirect(url_for('core.dashboard'))
        else:
            flash('Email ou senha inválidos', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('core.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if User.query.filter_by(email=email).first():
            flash('Email já registrado', 'danger')
            return redirect(url_for('auth.register'))
        
        if password != password_confirm:
            flash('Senhas não conferem', 'danger')
            return redirect(url_for('auth.register'))
        
        user = User(
            open_id=email,
            name=name,
            email=email,
            role='user',
            login_method='local'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registro realizado com sucesso! Faça login', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')
