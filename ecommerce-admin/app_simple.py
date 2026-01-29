#!/usr/bin/env python3
"""
Interface d'administration simplifiée pour Le Verger du Coin
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_admin'

# Configuration de la base de données
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

# Routes simplifiées
@app.route('/admin')
def admin_index():
    return "Interface d'administration - Accueil"

@app.route('/admin/products')
def admin_products():
    conn = get_db()
    if not conn:
        return "Erreur de connexion à la base de données"
    
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT rowid, ref, label, price FROM llx_product LIMIT 10")
        products = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(products)
    except Exception as e:
        return f"Erreur: {e}"

@app.route('/admin/stock/update', methods=['POST'])
def update_stock():
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'error': 'DB connection failed'})
    
    try:
        product_id = request.json.get('product_id')
        new_stock = request.json.get('stock')
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE llx_product_stock SET reel = %s WHERE fk_product = %s
        """, (new_stock, product_id))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Stock updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
