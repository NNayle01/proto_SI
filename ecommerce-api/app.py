from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import mysql.connector
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration de la base de données
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'db'),
    'user': os.getenv('DB_USER', 'dolibarr'),
    'password': os.getenv('DB_PASSWORD', 'dolibarrpass'),
    'database': os.getenv('DB_NAME', 'dolibarr'),
    'port': 3306
}

# Configuration de l'API Dolibarr
DOLIBARR_API_URL = os.getenv('DOLIBARR_API_URL', 'http://dolibarr:80')
DOLIBARR_API_KEY = os.getenv('DOLIBARR_API_KEY', 'dev_api_key_2026')

def get_dolibarr_headers():
    headers = {'Content-Type': 'application/json'}
    if DOLIBARR_API_KEY and DOLIBARR_API_KEY != 'your_dolibarr_api_key':
        headers['DOLAPIKEY'] = DOLIBARR_API_KEY
    return headers

def get_db_connection():
    """Établit une connexion à la base de données"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"Erreur de connexion à la base de données: {err}")
        return None

@app.route('/api/products', methods=['GET'])
def get_products():
    """Récupère les produits depuis Dolibarr ou directement depuis la base de données"""
    try:
        # Récupérer les paramètres de filtre
        search_query = request.args.get('search', '')
        season = request.args.get('season', '')
        category = request.args.get('category', '')
        
        # D'abord essayer via l'API Dolibarr
        url = f"{DOLIBARR_API_URL}/api/index.php/products"
        headers = get_dolibarr_headers()
        response = requests.get(url, headers=headers)
        
        # Si la réponse est réussie, retourner les données
        if response.status_code == 200:
            products = response.json()
            
            # Ajouter les champs season et category aux produits
            for product in products:
                # Déterminer la saison en fonction du nom du produit
                if 'Hiver' in product.get('label', ''):
                    product['season'] = 'Hiver'
                elif 'Printemps' in product.get('label', ''):
                    product['season'] = 'Printemps'
                elif 'Été' in product.get('label', ''):
                    product['season'] = 'Été'
                elif 'Automne' in product.get('label', ''):
                    product['season'] = 'Automne'
                else:
                    product['season'] = 'Inconnu'
                
                # Déterminer la catégorie en fonction du nom du produit
                if 'Fruits' in product.get('label', ''):
                    product['category'] = 'Fruits'
                elif 'Légumes' in product.get('label', ''):
                    product['category'] = 'Légumes'
                elif 'Produits Transformés' in product.get('label', ''):
                    product['category'] = 'Produits Transformés'
                else:
                    product['category'] = 'Inconnu'
                
                print(f"Produit: {product.get('label')}, Saison: {product.get('season')}, Catégorie: {product.get('category')}")
            
            # Appliquer les filtres si nécessaire
            if search_query or season or category:
                filtered_products = []
                for product in products:
                    # Filtrer par recherche
                    if search_query:
                        search_match = (
                            search_query.lower() in product.get('label', '').lower() or
                            search_query.lower() in product.get('description', '').lower() or
                            search_query.lower() in product.get('ref', '').lower()
                        )
                        if not search_match:
                            continue
                    
                    # Filtrer par saison (si disponible dans les données)
                    if season and product.get('season') != season:
                        continue
                    
                    # Filtrer par catégorie (si disponible dans les données)
                    if category and product.get('category') != category:
                        continue
                    
                    filtered_products.append(product)
                
                return jsonify(filtered_products)
            else:
                return jsonify(products)
        else:
            # Si l'API Dolibarr nécessite une authentification, essayer sans clé API
            print(f"Première tentative échouée avec statut {response.status_code}, tentative sans clé API...")
            headers_no_key = {'Content-Type': 'application/json'}
            response_no_key = requests.get(url, headers=headers_no_key)
            
            if response_no_key.status_code == 200:
                products = response_no_key.json()
                
                # Appliquer les filtres si nécessaire
                if search_query or season or category:
                    filtered_products = []
                    for product in products:
                        # Filtrer par recherche
                        if search_query:
                            search_match = (
                                search_query.lower() in product.get('label', '').lower() or
                                search_query.lower() in product.get('description', '').lower() or
                                search_query.lower() in product.get('ref', '').lower()
                            )
                            if not search_match:
                                continue
                        
                        # Filtrer par saison (si disponible dans les données)
                        if season and product.get('season') != season:
                            continue
                        
                        # Filtrer par catégorie (si disponible dans les données)
                        if category and product.get('category') != category:
                            continue
                        
                        filtered_products.append(product)
                    
                    return jsonify(filtered_products)
                else:
                    return jsonify(products)
            else:
                print(f"Deuxième tentative échouée avec statut {response_no_key.status_code}")
                print(f"Erreur API Dolibarr: {response_no_key.text}")
                
                # Si l'API Dolibarr échoue, essayer de lire directement depuis la base de données
                print("Tentative de lecture directe depuis la base de données...")
                conn = get_db_connection()
                if conn:
                    try:
                        cursor = conn.cursor(dictionary=True)
                        
                        # Construire la requête SQL avec les filtres
                        query = """
                            SELECT rowid as id, ref, label as name, description, price, 
                                   CASE 
                                       WHEN label LIKE '%Hiver%' THEN 'Hiver'
                                       WHEN label LIKE '%Printemps%' THEN 'Printemps'
                                       WHEN label LIKE '%Été%' THEN 'Été'
                                       WHEN label LIKE '%Automne%' THEN 'Automne'
                                       ELSE 'Inconnu'
                                   END as season,
                                   CASE 
                                       WHEN label LIKE '%Fruits%' THEN 'Fruits'
                                       WHEN label LIKE '%Légumes%' THEN 'Légumes'
                                       WHEN label LIKE '%Produits Transformés%' THEN 'Produits Transformés'
                                       ELSE 'Inconnu'
                                   END as category
                            FROM llx_product 
                            WHERE entity = 1
                        """
                        
                        params = []
                        conditions = []
                        
                        # Ajouter les conditions de filtre
                        if search_query:
                            conditions.append("(label LIKE %s OR description LIKE %s OR ref LIKE %s)")
                            params.extend([f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'])
                        
                        if season:
                            conditions.append("""( 
                                label LIKE %s OR 
                                label LIKE %s OR 
                                label LIKE %s OR 
                                label LIKE %s 
                            )""")
                            params.extend([f'%Hiver%', f'%Printemps%', f'%Été%', f'%Automne%'])
                        
                        if category:
                            conditions.append("""( 
                                label LIKE %s OR 
                                label LIKE %s OR 
                                label LIKE %s 
                            )""")
                            params.extend([f'%Fruits%', f'%Légumes%', f'%Produits Transformés%'])
                        
                        # Ajouter les conditions à la requête
                        if conditions:
                            query += " AND " + " AND ".join(conditions)
                        
                        cursor.execute(query, params)
                        products = cursor.fetchall()
                        cursor.close()
                        conn.close()
                        
                        if products:
                            print(f"Succès : {len(products)} produits récupérés depuis la base de données")
                            return jsonify(products)
                        else:
                            print("Aucun produit trouvé dans la base de données")
                            return jsonify([])
                    except Exception as db_error:
                        print(f"Erreur de base de données: {db_error}")
                        return jsonify({'error': f'Erreur de base de données: {str(db_error)}'}), 500
                else:
                    print("Impossible de se connecter à la base de données")
                    return jsonify({'error': 'Impossible de se connecter à la base de données'}), 500
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération des produits: {e}")
        return jsonify({'error': f'Erreur de connexion: {str(e)}'}), 500

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Crée une commande dans Dolibarr"""
    try:
        order_data = request.json
        url = f"{DOLIBARR_API_URL}/api/index.php/orders"
        headers = get_dolibarr_headers()
        response = requests.post(url, json=order_data, headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la création de la commande: {e}")
        return jsonify({'error': 'Erreur lors de la création de la commande'}), 500

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Récupère la liste des clients depuis la base de données"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Impossible de se connecter à la base de données'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Récupérer les clients particuliers
        query = """
        SELECT 
            u.rowid as id, 
            CONCAT(u.firstname, ' ', u.lastname) as name, 
            u.email, 
            u.user_mobile as phone, 
            u.datec as since
        FROM llx_user u
        WHERE u.rowid > 1 AND u.fk_soc = 2
        ORDER BY u.lastname, u.firstname
        """
        
        cursor.execute(query)
        customers = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(customers)
        
    except Exception as e:
        print(f"Erreur lors de la récupération des clients: {e}")
        return jsonify({'error': f'Erreur lors de la récupération des clients: {str(e)}'}), 500

@app.route('/api/customers', methods=['POST'])
def create_customer():
    """Crée un client dans Dolibarr"""
    try:
        customer_data = request.json
        url = f"{DOLIBARR_API_URL}/api/index.php/thirdparties"
        headers = get_dolibarr_headers()
        response = requests.post(url, json=customer_data, headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la création du client: {e}")
        return jsonify({'error': 'Erreur lors de la création du client'}), 500

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Récupère un produit spécifique depuis Dolibarr ou la base de données"""
    try:
        # D'abord essayer via l'API Dolibarr
        url = f"{DOLIBARR_API_URL}/api/index.php/products/{product_id}"
        headers = get_dolibarr_headers()
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            # Si l'API Dolibarr échoue, essayer de lire directement depuis la base de données
            print(f"API Dolibarr échouée pour le produit {product_id}, lecture directe depuis la base de données...")
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT rowid as id, ref, label as name, description, price FROM llx_product WHERE rowid = %s", (product_id,))
                    product = cursor.fetchone()
                    cursor.close()
                    conn.close()
                    
                    if product:
                        print(f"Succès : Produit {product_id} récupéré depuis la base de données")
                        return jsonify(product)
                    else:
                        print(f"Produit {product_id} non trouvé dans la base de données")
                        return jsonify({'error': 'Produit non trouvé'}), 404
                except Exception as db_error:
                    print(f"Erreur de base de données pour le produit {product_id}: {db_error}")
                    return jsonify({'error': f'Erreur de base de données: {str(db_error)}'}), 500
            else:
                print(f"Impossible de se connecter à la base de données pour le produit {product_id}")
                return jsonify({'error': 'Impossible de se connecter à la base de données'}), 500
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération du produit {product_id}: {e}")
        return jsonify({'error': f'Erreur de connexion: {str(e)}'}), 500

@app.route('/api/stock/<int:product_id>', methods=['GET'])
def get_product_stock(product_id):
    """Récupère le stock d'un produit depuis la base de données"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Impossible de se connecter à la base de données'}), 500
        
        cursor = conn.cursor(dictionary=True)
        query = """
        SELECT p.rowid, p.ref, p.label, p.price, 
               SUM(ps.reel) as stock
        FROM llx_product as p
        LEFT JOIN llx_product_stock as ps ON p.rowid = ps.fk_product
        WHERE p.rowid = %s
        GROUP BY p.rowid, p.ref, p.label, p.price
        """
        cursor.execute(query, (product_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Produit non trouvé'}), 404
            
    except Exception as e:
        print(f"Erreur lors de la récupération du stock: {e}")
        return jsonify({'error': 'Erreur lors de la récupération du stock'}), 500

@app.route('/api/stock/<int:product_id>', methods=['PUT'])
def update_product_stock(product_id):
    """Met à jour le stock d'un produit dans la base de données"""
    try:
        data = request.get_json()
        stock_quantity = data.get('stock')
        
        if stock_quantity is None:
            return jsonify({'error': 'Quantité de stock manquante'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Impossible de se connecter à la base de données'}), 500
        
        cursor = conn.cursor()
        
        # Vérifier si le produit existe
        cursor.execute("SELECT rowid FROM llx_product WHERE rowid = %s", (product_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Produit non trouvé'}), 404
        
        # Vérifier si une entrée de stock existe déjà
        cursor.execute("SELECT rowid FROM llx_product_stock WHERE fk_product = %s", (product_id,))
        stock_entry = cursor.fetchone()
        
        if stock_entry:
            # Mettre à jour le stock existant
            cursor.execute("""
                UPDATE llx_product_stock 
                SET reel = %s, tms = NOW()
                WHERE fk_product = %s
            """, (stock_quantity, product_id))
        else:
            # Créer une nouvelle entrée de stock (utiliser l'entrepôt par défaut avec rowid=1)
            cursor.execute("""
                INSERT INTO llx_product_stock (fk_product, fk_entrepot, reel, tms)
                VALUES (%s, 1, %s, NOW())
            """, (product_id, stock_quantity))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Stock mis à jour avec succès'})
        
    except Exception as e:
        print(f"Erreur lors de la mise à jour du stock: {e}")
        return jsonify({'error': f'Erreur lors de la mise à jour du stock: {str(e)}'}), 500

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Récupère la liste des commandes depuis la base de données"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Impossible de se connecter à la base de données'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Récupérer les commandes avec les détails des clients
        query = """
        SELECT 
            c.rowid as id, 
            c.ref, 
            s.nom as customer_name, 
            c.date_commande as date, 
            c.fk_statut as status, 
            c.total_ttc as total
        FROM llx_commande c
        JOIN llx_societe s ON c.fk_soc = s.rowid
        ORDER BY c.date_commande DESC
        """
        
        cursor.execute(query)
        orders = cursor.fetchall()
        
        # Pour chaque commande, récupérer les détails
        for order in orders:
            cursor.execute("""
                SELECT 
                    cd.fk_product as product_id, 
                    p.label as product_name, 
                    cd.qty as quantity, 
                    cd.total_ttc as total
                FROM llx_commandedet cd
                JOIN llx_product p ON cd.fk_product = p.rowid
                WHERE cd.fk_commande = %s
            """, (order['id'],))
            
            order['items'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(orders)
        
    except Exception as e:
        print(f"Erreur lors de la récupération des commandes: {e}")
        return jsonify({'error': f'Erreur lors de la récupération des commandes: {str(e)}'}), 500

@app.route('/api/financial', methods=['GET'])
def get_financial():
    """Récupère les données financières depuis la base de données"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Impossible de se connecter à la base de données'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Récupérer les transactions financières
        query = """
        SELECT 
            rowid as id, 
            label, 
            amount, 
            datev as date,
            CASE WHEN amount > 0 THEN 'revenue' ELSE 'expense' END as type
        FROM llx_bank
        ORDER BY datev DESC
        """
        
        cursor.execute(query)
        transactions = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(transactions)
        
    except Exception as e:
        print(f"Erreur lors de la récupération des données financières: {e}")
        return jsonify({'error': f'Erreur lors de la récupération des données financières: {str(e)}'}), 500

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Récupère les détails d'une commande spécifique"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Impossible de se connecter à la base de données'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Récupérer la commande
        query = """
        SELECT 
            c.rowid as id, 
            c.ref, 
            s.nom as customer_name, 
            c.date_commande as date, 
            c.fk_statut as status, 
            c.total_ttc as total
        FROM llx_commande c
        JOIN llx_societe s ON c.fk_soc = s.rowid
        WHERE c.rowid = %s
        """
        
        cursor.execute(query, (order_id,))
        order = cursor.fetchone()
        
        if not order:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Commande non trouvée'}), 404
        
        # Récupérer les détails de la commande
        query = """
        SELECT 
            cd.fk_product as product_id, 
            p.label as product_name, 
            cd.qty as quantity, 
            cd.total_ttc as total
        FROM llx_commandedet cd
        JOIN llx_product p ON cd.fk_product = p.rowid
        WHERE cd.fk_commande = %s
        """
        
        cursor.execute(query, (order_id,))
        order['items'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify(order)
        
    except Exception as e:
        print(f"Erreur lors de la récupération de la commande {order_id}: {e}")
        return jsonify({'error': f'Erreur lors de la récupération de la commande: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
