"""
Générateur de données réalistes pour e-commerce
Crée : customers, products, orders, order_items
"""

import random
import json
from datetime import datetime, timedelta
import pandas as pd

# ==================== CONFIGURATION ====================

NB_CUSTOMERS = 120
NB_PRODUCTS = 40
NB_ORDERS = 500

CITIES = ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice', 'Nantes', 'Strasbourg', 
          'Bordeaux', 'Lille', 'Rennes', 'Reims', 'Le Havre', 'Saint-Étienne', 'Toulon']

CATEGORIES = ['Électronique', 'Vêtements', 'Maison', 'Sports', 'Beauté']

FIRST_NAMES = ['Alice', 'Bob', 'Clara', 'David', 'Emma', 'François', 'Gérard', 'Hélène',
               'Isabelle', 'Jean', 'Karine', 'Luc', 'Marie', 'Nicolas', 'Olivier', 'Patricia',
               'Quentin', 'Raphaël', 'Sophie', 'Thomas', 'Université', 'Victor', 'Wenya', 'Xavier',
               'Yannick', 'Zoé']

LAST_NAMES = ['Dupont', 'Martin', 'Bernard', 'Thomas', 'Robert', 'Petit', 'Durand', 'Lefevre',
              'Moreau', 'Simon', 'Laurent', 'Lefebvre', 'Michel', 'Garcia', 'David', 'Bertrand',
              'Roux', 'Vincent', 'Fournier', 'Morel']

# ==================== FUNCTIONS ====================

def generate_customers(n=NB_CUSTOMERS):
    """Générer liste de clients"""
    customers = []
    base_date = datetime.now() - timedelta(days=730)  # 2 ans en arrière
    
    for i in range(1, n + 1):
        signup_date = base_date + timedelta(days=random.randint(0, 730))
        customer = {
            'customer_id': i,
            'first_name': random.choice(FIRST_NAMES),
            'last_name': random.choice(LAST_NAMES),
            'email': f"customer_{i}@ecommerce.fr",
            'signup_date': signup_date.strftime('%Y-%m-%d'),
            'city': random.choice(CITIES)
        }
        customers.append(customer)
    
    return customers

def generate_products(n=NB_PRODUCTS):
    """Générer liste de produits"""
    products = []
    
    product_names = {
        'Électronique': ['Casque Bluetooth', 'Batterie externe', 'Câble USB-C', 'Souris sans fil', 
                        'Clavier mécanique', 'Webcam HD', 'Adaptateur HDMI'],
        'Vêtements': ['T-shirt coton', 'Jean classique', 'Hoodie', 'Chaussettes', 'Bonnet', 
                     'Écharpe', 'Veste imperméable'],
        'Maison': ['Lampe de bureau', 'Coussin', 'Tapis', 'Tableau', 'Étagère', 'Miroir', 
                  'Cadre photo'],
        'Sports': ['Tapis de yoga', 'Bouteille réutilisable', 'Gants de sport', 'Bande élastique',
                  'Corde à sauter', 'Balle de fitness', 'Bandeau'],
        'Beauté': ['Crème hydratante', 'Savon naturel', 'Shampooing', 'Masque facial', 
                  'Déodorant', 'Brosse à dents', 'Gel douche']
    }
    
    product_id = 1
    for category in CATEGORIES:
        for name in product_names[category]:
            price = round(random.uniform(10, 200), 2)
            product = {
                'product_id': product_id,
                'product_name': name,
                'category': category,
                'price': price
            }
            products.append(product)
            product_id += 1
    
    return products

def generate_orders(customers, n=NB_ORDERS):
    """Générer commandes avec distribution réaliste"""
    orders = []
    base_date = datetime.now() - timedelta(days=730)
    
    for order_id in range(1, n + 1):
        # Certains clients commandent plus souvent
        customer = random.choice(customers)
        order_date = base_date + timedelta(days=random.randint(0, 730))
        
        order = {
            'order_id': order_id,
            'customer_id': customer['customer_id'],
            'order_date': order_date.strftime('%Y-%m-%d'),
            'total_amount': 0  # Calculé avec les items
        }
        orders.append(order)
    
    return orders

def generate_order_items(orders, products, orders_per_item_range=(1, 5)):
    """Générer items de commande"""
    order_items = []
    item_id = 1
    
    for order in orders:
        nb_items = random.randint(*orders_per_item_range)
        
        for _ in range(nb_items):
            product = random.choice(products)
            quantity = random.randint(1, 3)
            unit_price = product['price']
            
            item = {
                'order_item_id': item_id,
                'order_id': order['order_id'],
                'product_id': product['product_id'],
                'quantity': quantity,
                'unit_price': unit_price
            }
            order_items.append(item)
            
            # Mettre à jour total_amount
            order['total_amount'] += quantity * unit_price
            item_id += 1
    
    return order_items

def export_to_json(data, filename):
    """Exporter données en JSON"""
    with open(f'/home/claude/ecommerce-churn-project/{filename}', 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✓ {filename} généré ({len(data)} entrées)")

def export_to_csv(data, filename):
    """Exporter données en CSV"""
    df = pd.DataFrame(data)
    df.to_csv(f'/home/claude/ecommerce-churn-project/{filename}', index=False)
    print(f"✓ {filename} généré ({len(data)} entrées)")

# ==================== MAIN ====================

if __name__ == '__main__':
    print("🚀 Génération de données e-commerce...\n")
    
    # Générer
    customers = generate_customers(NB_CUSTOMERS)
    products = generate_products(NB_PRODUCTS)
    orders = generate_orders(customers, NB_ORDERS)
    order_items = generate_order_items(orders, products)
    
    # Arrondir total_amount à 2 décimales
    for order in orders:
        order['total_amount'] = round(order['total_amount'], 2)
    
    # Exporter
    export_to_json(customers, 'customers.json')
    export_to_json(products, 'products.json')
    export_to_json(orders, 'orders.json')
    export_to_json(order_items, 'order_items.json')
    
    export_to_csv(customers, 'customers.csv')
    export_to_csv(products, 'products.csv')
    export_to_csv(orders, 'orders.csv')
    export_to_csv(order_items, 'order_items.csv')
    
    # Stats
    print(f"\n📊 Résumé :")
    print(f"   • {len(customers)} clients")
    print(f"   • {len(products)} produits")
    print(f"   • {len(orders)} commandes")
    print(f"   • {len(order_items)} items commandés")
    print(f"   • Montant total: €{sum(o['total_amount'] for o in orders):.2f}")
    print(f"\n✅ Données générées avec succès !")
