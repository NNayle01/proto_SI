from flask import Flask, render_template, request, jsonify
import mysql.connector

app = Flask(__name__)
app.secret_key = 'test'

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

@app.route('/')
def index():
    return "Admin Interface - Accueil"

@app.route('/products')
def products():
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
