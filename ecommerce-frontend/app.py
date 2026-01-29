from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
import requests
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_ici'

# Configuration de l'API backend
API_URL = os.getenv('API_URL', 'http://ecommerce_api:5000')

# Route pour la page d'accueil
@app.route('/')
def home():
    """Page d'accueil avec la liste des produits"""
    try:
        # Récupérer les paramètres de filtre
        search_query = request.args.get('search', '')
        season = request.args.get('season', '')
        category = request.args.get('category', '')
        
        print(f"Paramètres de filtre - Recherche: {search_query}, Saison: {season}, Catégorie: {category}")
        
        # Construire l'URL de l'API avec les paramètres de filtre
        api_url = f'{API_URL}/api/products'
        params = {}
        if search_query:
            params['search'] = search_query
        if season:
            params['season'] = season
        if category:
            params['category'] = category
        
        print(f"URL de l'API: {api_url}")
        print(f"Paramètres: {params}")
        
        response = requests.get(api_url, params=params)
        print(f"Statut de la réponse: {response.status_code}")
        print(f"Contenu de la réponse: {response.text[:200]}")
        
        if response.status_code == 200:
            products = response.json()
            print(f"Nombre de produits retournés: {len(products)}")
            return render_template('home.html', products=products)
        else:
            return render_template('home.html', products=[], error='Impossible de charger les produits')
    except Exception as e:
        print(f"Erreur lors de la récupération des produits: {e}")
        return render_template('home.html', products=[], error='Erreur de connexion au serveur')

# Route pour la page "Notre Histoire"
@app.route('/about')
def about():
    return render_template('about.html')

# Route pour la page "Nos Marchés"
@app.route('/markets')
def markets():
    return render_template('markets.html')

# Route pour la page "Produits de Saison"
@app.route('/seasonal')
def seasonal():
    return render_template('seasonal.html')

# Route pour la page produit
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Page de détails d'un produit"""
    try:
        product_response = requests.get(f'{API_URL}/api/products/{product_id}')
        stock_response = requests.get(f'{API_URL}/api/stock/{product_id}')
        
        if product_response.status_code == 200:
            product = product_response.json()
            stock = stock_response.json().get('stock', 0) if stock_response.status_code == 200 else 0
            return render_template('product.html', product=product, stock=stock)
        else:
            return render_template('error.html', message='Produit non trouvé'), 404
    except Exception as e:
        print(f"Erreur lors de la récupération du produit: {e}")
        return render_template('error.html', message='Erreur de connexion au serveur'), 500

# Route pour ajouter au panier
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    """Ajoute un produit au panier"""
    product_id = str(request.form.get('product_id'))  # Convert to string for consistent session keys
    quantity = int(request.form.get('quantity', 1))
    
    if 'cart' not in session:
        session['cart'] = {}
    
    if product_id in session['cart']:
        session['cart'][product_id] += quantity
    else:
        session['cart'][product_id] = quantity
    
    # Mark session as modified to ensure it saves
    session.modified = True
    
    # Debug: afficher le contenu du panier
    print(f"Produit ajouté au panier: {product_id}, Quantité: {quantity}")
    print(f"Contenu du panier: {session['cart']}")
    
    return redirect(url_for('view_cart'))

# Route pour voir le panier
@app.route('/cart')
def view_cart():
    """Affiche le contenu du panier"""
    cart = session.get('cart', {})
    
    if not cart:
        return render_template('cart.html', cart={}, total=0)
    
    products = []
    total = 0
    
    for product_id, quantity in cart.items():
        try:
            response = requests.get(f'{API_URL}/api/products/{product_id}')
            if response.status_code == 200:
                product = response.json()
                # Ensure the product ID is preserved for cart operations
                product['id'] = str(product.get('id', product_id))
                product['quantity'] = quantity
                product['subtotal'] = product.get('price', 0) * quantity
                products.append(product)
                total += product['subtotal']
        except Exception as e:
            print(f"Erreur lors de la récupération du produit {product_id}: {e}")
    
    return render_template('cart.html', cart=products, total=total)

# Route pour mettre à jour le panier
@app.route('/update_cart', methods=['POST'])
def update_cart():
    """Met à jour les quantités dans le panier"""
    product_id = str(request.form.get('product_id'))  # Convert to string for consistent session keys
    new_quantity = int(request.form.get('quantity', 0))
    
    # Debug: afficher les informations
    print(f"Mise à jour du panier: Produit {product_id}, Nouvelle quantité: {new_quantity}")
    
    if new_quantity <= 0:
        if 'cart' in session and product_id in session['cart']:
            del session['cart'][product_id]
            session.modified = True
            print(f"Produit {product_id} supprimé du panier")
    else:
        if 'cart' in session:
            session['cart'][product_id] = new_quantity
            session.modified = True
            print(f"Quantité mise à jour: {new_quantity}")
    
    print(f"Contenu final du panier: {session.get('cart', {})}")
    
    return redirect(url_for('view_cart'))

# Route pour supprimer un produit du panier
@app.route('/remove_from_cart/<product_id>')
def remove_from_cart(product_id):
    """Supprime un produit du panier"""
    product_id = str(product_id)  # Convert to string for consistent session keys
    if 'cart' in session and product_id in session['cart']:
        del session['cart'][product_id]
        session.modified = True
        print(f"Produit {product_id} supprimé du panier")
    
    print(f"Contenu du panier après suppression: {session.get('cart', {})}")
    
    return redirect(url_for('view_cart'))

# Route pour le checkout
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Page de checkout et création de la commande"""
    if request.method == 'POST':
        # Récupérer les informations du client
        customer_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'address': request.form.get('address'),
            'phone': request.form.get('phone')
        }
        
        # Créer le client dans Dolibarr
        try:
            customer_response = requests.post(f'{API_URL}/api/customers', json=customer_data)
            if customer_response.status_code != 200:
                return render_template('checkout.html', error='Erreur lors de la création du client')
                
            customer = customer_response.json()
            customer_id = customer.get('id')
            
            # Créer la commande
            cart = session.get('cart', {})
            if not cart:
                return render_template('checkout.html', error='Votre panier est vide')
            
            # Préparer les données de la commande
            order_items = []
            for product_id, quantity in cart.items():
                order_items.append({
                    'product_id': product_id,
                    'quantity': quantity
                })
            
            order_data = {
                'customer_id': customer_id,
                'items': order_items,
                'status': 'draft'
            }
            
            # Créer la commande dans Dolibarr
            order_response = requests.post(f'{API_URL}/api/orders', json=order_data)
            
            if order_response.status_code == 200:
                # Vider le panier après la commande
                session.pop('cart', None)
                return render_template('order_confirmation.html', order=order_response.json())
            else:
                return render_template('checkout.html', error='Erreur lors de la création de la commande')
                
        except Exception as e:
            print(f"Erreur lors du checkout: {e}")
            return render_template('checkout.html', error='Erreur de connexion au serveur')
    
    # Si GET, afficher le formulaire de checkout
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('home'))
    
    return render_template('checkout.html')

@app.route('/demo_end')
def demo_end():
    """Page Fin de DEMO"""
    return render_template('demo_end.html')

# Routes d'administration
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Page de connexion admin"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Vérification simple (à améliorer en production)
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            flash('Connexion admin réussie !', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Identifiants incorrects', 'danger')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    """Déconnexion admin"""
    session.pop('admin_logged_in', None)
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('home'))

@app.route('/admin')
def admin_dashboard():
    """Tableau de bord admin"""
    return render_template('admin/dashboard.html')

@app.route('/admin/products')
def admin_products():
    """Gestion des produits admin"""
    try:
        response = requests.get(f'{API_URL}/api/products')
        if response.status_code == 200:
            products = response.json()
            return render_template('admin/products.html', products=products)
        else:
            return render_template('admin/products.html', products=[], error='Impossible de charger les produits')
    except Exception as e:
        print(f"Erreur lors de la récupération des produits: {e}")
        return render_template('admin/products.html', products=[], error='Erreur de connexion au serveur')

@app.route('/admin/stock')
def admin_stock():
    """Gestion des stocks admin"""
    try:
        # Récupérer les produits avec leurs stocks
        products_response = requests.get(f'{API_URL}/api/products')
        
        if products_response.status_code == 200:
            products = products_response.json()
            
            # Pour chaque produit, récupérer son stock
            for product in products:
                stock_response = requests.get(f'{API_URL}/api/stock/{product["id"]}')
                if stock_response.status_code == 200:
                    product['stock'] = stock_response.json().get('stock', 0)
                else:
                    product['stock'] = 0
            
            return render_template('admin/stock.html', products=products)
        else:
            return render_template('admin/stock.html', products=[], error='Impossible de charger les produits et stocks')
    except Exception as e:
        print(f"Erreur lors de la récupération des stocks: {e}")
        return render_template('admin/stock.html', products=[], error='Erreur de connexion au serveur')

@app.route('/admin/stock/export')
def export_stock():
    """Export des stocks en CSV"""
    try:
        # Récupérer les produits avec leurs stocks
        products_response = requests.get(f'{API_URL}/api/products')
        
        if products_response.status_code == 200:
            products = products_response.json()
            
            # Pour chaque produit, récupérer son stock
            stock_data = []
            for product in products:
                stock_response = requests.get(f'{API_URL}/api/stock/{product["id"]}')
                if stock_response.status_code == 200:
                    stock = stock_response.json().get('stock', 0)
                else:
                    stock = 0
                
                stock_data.append({
                    'id': product['id'],
                    'name': product['name'],
                    'price': product['price'],
                    'stock': stock
                })
            
            # Créer un fichier CSV
            import csv
            from io import StringIO
            
            si = StringIO()
            cw = csv.writer(si)
            cw.writerow(['ID', 'Nom', 'Prix', 'Stock'])
            
            for item in stock_data:
                cw.writerow([item['id'], item['name'], item['price'], item['stock']])
            
            output = si.getvalue()
            
            return Response(
                output,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment;filename=stock_export.csv'}
            )
        else:
            flash('Impossible de charger les données de stock pour l\'export', 'danger')
            return redirect(url_for('admin_stock'))
    except Exception as e:
        print(f"Erreur lors de l'export des stocks: {e}")
        flash('Erreur lors de l\'export des stocks', 'danger')
        return redirect(url_for('admin_stock'))

@app.route('/admin/stock/import', methods=['POST'])
def import_stock():
    """Import des stocks depuis un fichier CSV"""
    if 'file' not in request.files:
        flash('Aucun fichier sélectionné', 'danger')
        return redirect(url_for('admin_stock'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('Aucun fichier sélectionné', 'danger')
        return redirect(url_for('admin_stock'))
    
    if file and file.filename.endswith('.csv'):
        try:
            import csv
            from io import StringIO
            
            stream = StringIO(file.stream.read().decode("UTF8"))
            csv_input = csv.reader(stream)
            
            # Sauter l'en-tête
            next(csv_input)
            
            updated_count = 0
            
            for row in csv_input:
                if len(row) >= 4:
                    product_id = row[0]
                    stock_quantity = row[3]
                    
                    # Mettre à jour le stock via l'API
                    stock_data = {'stock': int(stock_quantity)}
                    update_response = requests.put(f'{API_URL}/api/stock/{product_id}', json=stock_data)
                    
                    if update_response.status_code == 200:
                        updated_count += 1
            
            flash(f'Import terminé ! {updated_count} produits mis à jour', 'success')
            return redirect(url_for('admin_stock'))
            
        except Exception as e:
            print(f"Erreur lors de l'import des stocks: {e}")
            flash('Erreur lors de l\'import des stocks', 'danger')
            return redirect(url_for('admin_stock'))
    else:
        flash('Veuillez sélectionner un fichier CSV valide', 'danger')
        return redirect(url_for('admin_stock'))

@app.route('/admin/stock/update/<int:product_id>', methods=['POST'])
def update_stock(product_id):
    """Mise à jour individuelle du stock d'un produit"""
    try:
        data = request.get_json()
        stock_quantity = data.get('stock')
        
        if stock_quantity is None:
            return jsonify({'success': False, 'error': 'Quantité de stock manquante'}), 400
        
        # Mettre à jour le stock via l'API
        stock_data = {'stock': int(stock_quantity)}
        update_response = requests.put(f'{API_URL}/api/stock/{product_id}', json=stock_data)
        
        if update_response.status_code == 200:
            return jsonify({'success': True, 'message': 'Stock mis à jour avec succès'})
        else:
            return jsonify({'success': False, 'error': 'Erreur lors de la mise à jour du stock'}), 500
            
    except Exception as e:
        print(f"Erreur lors de la mise à jour du stock: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/orders')
def admin_orders():
    """Gestion des commandes admin"""
    try:
        # Récupérer les commandes depuis l'API
        orders_response = requests.get(f'{API_URL}/api/orders')
        
        if orders_response.status_code == 200:
            orders = orders_response.json()
            return render_template('admin/orders.html', orders=orders)
        else:
            return render_template('admin/orders.html', orders=[], error='Impossible de charger les commandes')
    except Exception as e:
        print(f"Erreur lors de la récupération des commandes: {e}")
        return render_template('admin/orders.html', orders=[], error='Erreur de connexion au serveur')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
