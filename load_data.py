"""
Script de chargement des données dans MySQL
Crée la BD, les tables, et insère les données JSON
"""

import mysql.connector
import json
import os
from dotenv import load_dotenv

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
    with open(filename, 'r') as f:
        return json.load(f)

def create_tables(cursor):
    """Créer les tables une par une"""

    # Table CUSTOMERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INT PRIMARY KEY AUTO_INCREMENT,
        first_name VARCHAR(50) NOT NULL,
        last_name VARCHAR(50) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        signup_date DATE NOT NULL,
        city VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("✓ Table customers créée")

    # Table PRODUCTS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        product_id INT PRIMARY KEY AUTO_INCREMENT,
        product_name VARCHAR(100) NOT NULL,
        category VARCHAR(50) NOT NULL,
        price DECIMAL(10, 2) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("✓ Table products créée")

    # Table ORDERS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INT PRIMARY KEY AUTO_INCREMENT,
        customer_id INT NOT NULL,
        order_date DATE NOT NULL,
        total_amount DECIMAL(10, 2) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
    )
    """)
    print("✓ Table orders créée")

    # Table ORDER_ITEMS (M2M)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        order_item_id INT PRIMARY KEY AUTO_INCREMENT,
        order_id INT NOT NULL,
        product_id INT NOT NULL,
        quantity INT NOT NULL,
        unit_price DECIMAL(10, 2) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
    )
    """)
    print("✓ Table order_items créée")

    # Table CUSTOMER_SEGMENTS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customer_segments (
        segment_id INT PRIMARY KEY AUTO_INCREMENT,
        customer_id INT NOT NULL UNIQUE,
        rfm_score INT,
        segment_name VARCHAR(50),
        recency_days INT,
        frequency INT,
        monetary_value DECIMAL(10, 2),
        churn_risk VARCHAR(20),
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
    )
    """)
    print("✓ Table customer_segments créée")

    # Index
    try:
        cursor.execute("CREATE INDEX idx_order_customer ON orders(customer_id)")
        cursor.execute("CREATE INDEX idx_order_date ON orders(order_date)")
        cursor.execute("CREATE INDEX idx_order_items_order ON order_items(order_id)")
        cursor.execute("CREATE INDEX idx_order_items_product ON order_items(product_id)")
        print("✓ Index créés")
    except:
        print("  ℹ Index déjà existants")

    # Vue 1 : RFM par client
    cursor.execute("""
    CREATE OR REPLACE VIEW vw_customer_rfm AS
    SELECT 
        c.customer_id,
        c.first_name,
        c.last_name,
        c.email,
        DATEDIFF(CURDATE(), MAX(o.order_date)) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        COALESCE(SUM(o.total_amount), 0) AS monetary_value,
        MIN(o.order_date) AS first_order_date,
        MAX(o.order_date) AS last_order_date
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id, c.first_name, c.last_name, c.email
    """)
    print("✓ Vue vw_customer_rfm créée")

    # Vue 2 : Stats produits
    cursor.execute("""
    CREATE OR REPLACE VIEW vw_product_stats AS
    SELECT 
        p.product_id,
        p.product_name,
        p.category,
        p.price,
        COUNT(DISTINCT oi.order_id) AS times_ordered,
        SUM(oi.quantity) AS total_quantity_sold,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue
    FROM products p
    LEFT JOIN order_items oi ON p.product_id = oi.product_id
    GROUP BY p.product_id, p.product_name, p.category, p.price
    """)
    print("✓ Vue vw_product_stats créée")

    # Vue 3 : Performance par catégorie
    cursor.execute("""
    CREATE OR REPLACE VIEW vw_category_performance AS
    SELECT 
        p.category,
        COUNT(DISTINCT p.product_id) AS nb_products,
        COUNT(DISTINCT oi.order_id) AS nb_orders,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS total_revenue,
        ROUND(AVG(p.price), 2) AS avg_price,
        ROUND(SUM(oi.quantity), 0) AS total_items_sold
    FROM products p
    LEFT JOIN order_items oi ON p.product_id = oi.product_id
    GROUP BY p.category
    """)
    print("✓ Vue vw_category_performance créée")

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

    try:
        # Connexion sans base
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor = conn.cursor()

        # Créer la base
        print("[1] Création de la base de données...")
        cursor.execute("DROP DATABASE IF EXISTS ecommerce_churn")
        cursor.execute("CREATE DATABASE ecommerce_churn")
        print("✓ Base de données créée")
        conn.commit()
        cursor.close()
        conn.close()

        # Reconnexion avec la base
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Créer les tables
        print("\n[2] Création des tables...")
        create_tables(cursor)
        conn.commit()

        # Charger les données JSON
        print("\n[3] Chargement des données JSON...")
        customers = load_json_file('customers.json')
        products = load_json_file('products.json')
        orders = load_json_file('orders.json')
        order_items = load_json_file('order_items.json')

        # Insérer les données
        print("\n[4] Insertion des données...")
        insert_customers(cursor, customers)
        insert_products(cursor, products)
        insert_orders(cursor, orders)
        insert_order_items(cursor, order_items)
        conn.commit()

        # Vérification
        print("\n[5] Vérification...")
        cursor.execute("SELECT COUNT(*) FROM customers")
        c = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM products")
        p = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM orders")
        o = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM order_items")
        oi = cursor.fetchone()[0]
        print(f"✓ Customers: {c}, Products: {p}, Orders: {o}, Items: {oi}")

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
