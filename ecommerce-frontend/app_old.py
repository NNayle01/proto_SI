from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)
app.secret_key = 'votre_cle_secrete_ici'  # Changez cela en production

# Configuration de l'API backend
API_URL = os.getenv('API_URL', 'http://ecommerce_api:5000')

# Route pour la page d'accueil
@app.route('/')
def home():
    """Page d'accueil avec la liste des produits"""
    try:
        response = requests.get(f'{API_URL}/api/products')
        if response.status_code == 200:
            products = response.json()
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

# Route pour l'interface d'administration
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

def admin_required(f):
    """Décorateur pour les routes admin"""
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Vous devez être connecté pour accéder à cette page', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return wrapper

# Tableau de bord admin
@app.route('/admin')
@admin_required
def admin_dashboard():
    """Tableau de bord admin"""
    return render_template('admin/dashboard.html')

# Route pour la page produit
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Page de détails d'un produit"""
    try:
        # Récupérer les détails du produit
        product_response = requests.get(f'{API_URL}/api/products/{product_id}')
        
        # Récupérer le stock
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
    product_id = request.form.get('product_id')
    quantity = int(request.form.get('quantity', 1))
    
    # Initialiser le panier dans la session si nécessaire
    if 'cart' not in session:
        session['cart'] = {}
    
    # Ajouter ou mettre à jour le produit dans le panier
    if product_id in session['cart']:
        session['cart'][product_id] += quantity
    else:
        session['cart'][product_id] = quantity
    
    return redirect(url_for('view_cart'))

# Route pour voir le panier
@app.route('/cart')
def view_cart():
    """Affiche le contenu du panier"""
    cart = session.get('cart', {})
    
    if not cart:
        return render_template('cart.html', cart={}, total=0)
    
    # Récupérer les détails des produits dans le panier
    products = []
    total = 0
    
    for product_id, quantity in cart.items():
        try:
            response = requests.get(f'{API_URL}/api/products/{product_id}')
            if response.status_code == 200:
                product = response.json()
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
    product_id = request.form.get('product_id')
    new_quantity = int(request.form.get('quantity', 0))
    
    if new_quantity <= 0:
        # Supprimer le produit si la quantité est 0 ou négative
        if 'cart' in session and product_id in session['cart']:
            del session['cart'][product_id]
    else:
        # Mettre à jour la quantité
        if 'cart' in session:
            session['cart'][product_id] = new_quantity
    
    return redirect(url_for('view_cart'))

# Route pour supprimer un produit du panier
@app.route('/remove_from_cart/<product_id>')
def remove_from_cart(product_id):
    """Supprime un produit du panier"""
    if 'cart' in session and product_id in session['cart']:
        del session['cart'][product_id]
    
    return redirect(url_for('view_cart'))

# Route pour le checkout
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Checkout"""
    # Votre code de checkout existant
    pass

# Routes admin pour la gestion des produits
@app.route('/admin/products')
@admin_required
def admin_products():
    """Liste des produits dans l'admin"""
    try:
        response = requests.get(f'{API_URL}/api/products')
        if response.status_code == 200:
            products = response.json()
            return render_template('admin/products.html', products=products)
        else:
            flash('Impossible de charger les produits', 'danger')
            return redirect(url_for('admin_dashboard'))
    except Exception as e:
        flash(f'Erreur: {e}', 'danger')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/stock/update', methods=['POST'])
@admin_required
def update_stock():
    """Mettre à jour le stock"""
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        new_stock = data.get('stock')
        
        # Appeler l'API pour mettre à jour le stock
        response = requests.post(
            f'{API_URL}/api/stock/update',
            json={'product_id': product_id, 'stock': new_stock}
        )
        
        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Stock mis à jour'})
        else:
            return jsonify({'success': False, 'error': response.text})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Route pour le checkout
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
                'status': 'draft'  # ou 'validated' selon votre workflow
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)