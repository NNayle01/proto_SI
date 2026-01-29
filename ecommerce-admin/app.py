#!/usr/bin/env python3
"""
Interface d'administration pour Le Verger du Coin
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_admin_ici'

# Configuration de la base de données Dolibarr
DB_CONFIG = {
    'host': 'db',
    'port': 3306,
    'user': 'dolibarr',
    'password': 'dolibarrpass',
    'database': 'dolibarr'
}

def get_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Erreur DB: {e}")
        return None

# Authentification
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            flash('Connexion réussie !', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Identifiants incorrects', 'danger')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('admin_login'))

def admin_required(f):
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Vous devez être connecté', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return wrapper

# Tableau de bord
@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

# Produits
@app.route('/admin/products')
@admin_required
def admin_products():
    conn = get_db()
    if not conn:
        flash('Erreur de connexion à la base de données', 'danger')
        return redirect(url_for('admin_login'))
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT p.rowid, p.ref, p.label, p.description, p.price, 
                   COALESCE(ps.reel, 0) as stock
            FROM llx_product p
            LEFT JOIN llx_product_stock ps ON p.rowid = ps.fk_product
            ORDER BY p.label
        """)
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('admin/products.html', products=products)
    except Exception as e:
        flash(f'Erreur: {e}', 'danger')
        return redirect(url_for('admin_dashboard'))

# Mise à jour de stock (corrigée pour accepter POST)
@app.route('/admin/stock/update', methods=['POST'])
@admin_required
def update_stock():
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'DB connection failed'})
    
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        new_stock = data.get('stock')
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE llx_product_stock SET reel = %s WHERE fk_product = %s
        """, (new_stock, product_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Stock mis à jour'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
