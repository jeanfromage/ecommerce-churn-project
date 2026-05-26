"""
Script de chargement des données dans MySQL
Crée la BD, les tables, et insère les données JSON
"""

import mysql.connector
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

# Configuration MySQL
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'ecommerce_churn')
}

def load_json_file(filename):
    """Charger un fichier JSON"""
    filepath = f'/home/claude/ecommerce-churn-project/{filename}'
    with open(filepath, 'r') as f:
        return json.load(f)

def create_database(cursor):
    """Créer la base de données"""
    try:
        cursor.execute("DROP DATABASE IF EXISTS ecommerce_churn")
        cursor.execute("CREATE DATABASE ecommerce_churn")
        print("✓ Base de données créée")
    except mysql.connector.Error as err:
        print(f"✗ Erreur création BD: {err}")
        raise

def setup_schema(cursor):
    """Exécuter le script SQL pour créer les tables"""
    with open('/home/claude/ecommerce-churn-project/schema.sql', 'r') as f:
        schema_content = f.read()
    
    # Diviser par ;;
    statements = [s.strip() for s in schema_content.split(';') if s.strip()]
    
    for i, statement in enumerate(statements):
        if statement and not statement.startswith('--'):
            try:
                cursor.execute(statement)
                print(f"✓ Requête {i+1} exécutée")
            except mysql.connector.Error as err:
                if "already exists" in str(err) or "Duplicate" in str(err):
                    print(f"  ℹ Requête {i+1} (ignorée: existe déjà)")
                else:
                    print(f"⚠ Erreur requête {i+1}: {err}")
    
    print("✓ Schéma créé")

def insert_customers(cursor, customers):
    """Insérer les clients"""
    sql = """
    INSERT INTO customers (first_name, last_name, email, signup_date, city)
    VALUES (%s, %s, %s, %s, %s)
    """
    
    data = [
        (c['first_name'], c['last_name'], c['email'], c['signup_date'], c['city'])
        for c in customers
    ]
    
    cursor.executemany(sql, data)
    print(f"✓ {len(customers)} clients insérés")

def insert_products(cursor, products):
    """Insérer les produits"""
    sql = """
    INSERT INTO products (product_name, category, price)
    VALUES (%s, %s, %s)
    """
    
    data = [
        (p['product_name'], p['category'], p['price'])
        for p in products
    ]
    
    cursor.executemany(sql, data)
    print(f"✓ {len(products)} produits insérés")

def insert_orders(cursor, orders):
    """Insérer les commandes"""
    sql = """
    INSERT INTO orders (customer_id, order_date, total_amount)
    VALUES (%s, %s, %s)
    """
    
    data = [
        (o['customer_id'], o['order_date'], o['total_amount'])
        for o in orders
    ]
    
    cursor.executemany(sql, data)
    print(f"✓ {len(orders)} commandes insérées")

def insert_order_items(cursor, order_items):
    """Insérer les items de commande"""
    sql = """
    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
    VALUES (%s, %s, %s, %s)
    """
    
    data = [
        (oi['order_id'], oi['product_id'], oi['quantity'], oi['unit_price'])
        for oi in order_items
    ]
    
    cursor.executemany(sql, data)
    print(f"✓ {len(order_items)} items insérés")

def main():
    """Orchestration principale"""
    print("=" * 50)
    print("🚀 Chargement des données dans MySQL")
    print("=" * 50 + "\n")
    
    # Connexion sans base
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()
        
        # Créer la base
        print("[1] Création de la base de données...")
        create_database(cursor)
        conn.commit()
        cursor.close()
        conn.close()
        
        # Reconnexion avec la base
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Charger les données
        print("\n[2] Chargement des données...")
        customers = load_json_file('customers.json')
        products = load_json_file('products.json')
        orders = load_json_file('orders.json')
        order_items = load_json_file('order_items.json')
        
        # Créer le schéma
        print("\n[3] Création du schéma...")
        setup_schema(cursor)
        conn.commit()
        
        # Insérer les données
        print("\n[4] Insertion des données...")
        insert_customers(cursor, customers)
        insert_products(cursor, products)
        insert_orders(cursor, orders)
        insert_order_items(cursor, order_items)
        conn.commit()
        
        # Vérification
        print("\n[5] Vérification...")
        cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM customers) as customers,
                (SELECT COUNT(*) FROM products) as products,
                (SELECT COUNT(*) FROM orders) as orders,
                (SELECT COUNT(*) FROM order_items) as order_items
        """)
        result = cursor.fetchone()
        print(f"✓ Customers: {result[0]}, Products: {result[1]}, Orders: {result[2]}, Items: {result[3]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Chargement terminé avec succès !")
        
    except mysql.connector.Error as err:
        print(f"\n✗ Erreur MySQL: {err}")
        print("\n⚠️  Assurez-vous que:")
        print("  1. MySQL est en cours d'exécution")
        print("  2. Les variables .env sont correctes (DB_HOST, DB_USER, DB_PASSWORD)")
        print("  3. L'utilisateur MySQL a les droits CREATE DATABASE")
        raise

if __name__ == '__main__':
    main()
