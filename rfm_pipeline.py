"""
Pipeline RFM : Recency, Frequency, Monetary Analysis
Segmente les clients et détecte le churn
"""

import mysql.connector
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv
import json

# Charger configuration
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'ecommerce_churn')
}

# =====================================================
# 1. CONNEXION À LA BASE
# =====================================================

def connect_db():
    """Connecter à MySQL"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        print(f"✗ Erreur connexion MySQL: {err}")
        raise

def load_customer_data(conn):
    """Charger données clients et commandes"""
    query = """
    SELECT 
        c.customer_id,
        c.first_name,
        c.last_name,
        c.email,
        c.city,
        c.signup_date,
        COALESCE(COUNT(DISTINCT o.order_id), 0) AS frequency,
        COALESCE(SUM(o.total_amount), 0) AS monetary,
        COALESCE(MAX(o.order_date), c.signup_date) AS last_order_date
    FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id
    GROUP BY c.customer_id
    """
    
    df = pd.read_sql(query, conn)
    df['last_order_date'] = pd.to_datetime(df['last_order_date'])
    return df

# =====================================================
# 2. CALCUL RFM
# =====================================================

def calculate_rfm(df):
    """Calculer Recency, Frequency, Monetary"""
    
    # Recency : jours depuis dernière commande
    today = datetime.now().date()
    df['recency'] = (today - df['last_order_date'].dt.date).dt.days
    
    # Frequency : déjà dans les données
    df['frequency'] = df['frequency'].astype(int)
    
    # Monetary : déjà dans les données
    df['monetary'] = df['monetary'].round(2)
    
    return df

def score_rfm_components(df):
    """Scorer chaque composant (1-5)"""
    
    # Recency : moins c'est élevé, mieux c'est (inversé)
    df['r_score'] = pd.qcut(df['recency'], q=5, labels=[5, 4, 3, 2, 1], duplicates='drop')
    df['r_score'] = df['r_score'].astype(int)
    
    # Frequency : plus c'est élevé, mieux c'est
    df['f_score'] = pd.qcut(df['frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
    df['f_score'] = df['f_score'].astype(int)
    
    # Monetary : plus c'est élevé, mieux c'est
    df['m_score'] = pd.qcut(df['monetary'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
    df['m_score'] = df['m_score'].astype(int)
    
    return df

def calculate_overall_rfm_score(df):
    """Calculer score RFM global (0-100)"""
    # Pondération : R(40%) + F(30%) + M(30%)
    df['rfm_score'] = (
        df['r_score'] * 8 +      # 5 * 8 = 40 points max
        df['f_score'] * 6 +      # 5 * 6 = 30 points max
        df['m_score'] * 6        # 5 * 6 = 30 points max
    )
    
    return df

def segment_customers(df):
    """Segmenter les clients en 4 groupes"""
    def get_segment(score):
        if score >= 80:
            return 'Champion'
        elif score >= 60:
            return 'Loyal'
        elif score >= 40:
            return 'Potential'
        else:
            return 'At Risk'
    
    df['segment'] = df['rfm_score'].apply(get_segment)
    return df

def detect_churn_risk(df):
    """Détecter risque de churn"""
    def get_churn_risk(recency, frequency):
        if recency > 180:
            return 'High'
        elif recency > 90:
            return 'Medium'
        elif frequency == 0:
            return 'Medium'
        else:
            return 'Low'
    
    df['churn_risk'] = df.apply(
        lambda row: get_churn_risk(row['recency'], row['frequency']),
        axis=1
    )
    
    return df

# =====================================================
# 3. ENRICHISSEMENT VIA API
# =====================================================

def enrich_with_coordinates(df):
    """Ajouter coordonnées GPS via API Nominatim (OpenStreetMap)"""
    
    print("\n🌐 Enrichissement par géolocalisation...")
    
    coordinates = {}
    unique_cities = df['city'].dropna().unique()
    
    for city in unique_cities:
        try:
            # API Nominatim gratuite (OpenStreetMap)
            response = requests.get(
                'https://nominatim.openstreetmap.org/search',
                params={
                    'q': f"{city}, France",
                    'format': 'json',
                    'limit': 1
                },
                timeout=5,
                headers={'User-Agent': 'ecommerce-rfm-analysis'}
            )
            
            if response.status_code == 200 and response.json():
                data = response.json()[0]
                coordinates[city] = {
                    'lat': float(data['lat']),
                    'lon': float(data['lon'])
                }
                print(f"  ✓ {city}: ({coordinates[city]['lat']:.2f}, {coordinates[city]['lon']:.2f})")
            else:
                print(f"  ⚠ {city}: Non trouvée")
        except Exception as e:
            print(f"  ✗ {city}: Erreur API - {str(e)[:50]}")
    
    # Ajouter les colonnes
    df['latitude'] = df['city'].map(lambda x: coordinates.get(x, {}).get('lat', None))
    df['longitude'] = df['city'].map(lambda x: coordinates.get(x, {}).get('lon', None))
    
    return df

# =====================================================
# 4. INSERTION EN BASE
# =====================================================

def save_segments_to_db(conn, df):
    """Insérer les segments dans customer_segments"""
    
    cursor = conn.cursor()
    
    insert_sql = """
    INSERT INTO customer_segments 
        (customer_id, rfm_score, segment_name, recency_days, frequency, monetary_value, churn_risk)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        rfm_score = VALUES(rfm_score),
        segment_name = VALUES(segment_name),
        recency_days = VALUES(recency_days),
        frequency = VALUES(frequency),
        monetary_value = VALUES(monetary_value),
        churn_risk = VALUES(churn_risk),
        last_updated = CURRENT_TIMESTAMP
    """
    
    data = [
        (
            int(row['customer_id']),
            int(row['rfm_score']),
            row['segment'],
            int(row['recency']),
            int(row['frequency']),
            float(row['monetary']),
            row['churn_risk']
        )
        for _, row in df.iterrows()
    ]
    
    cursor.executemany(insert_sql, data)
    conn.commit()
    cursor.close()
    
    print(f"\n✓ {len(data)} segments insérés/mis à jour en base")

# =====================================================
# 5. STATISTIQUES
# =====================================================

def print_statistics(df):
    """Afficher statistiques"""
    print("\n" + "="*60)
    print("📊 STATISTIQUES RFM")
    print("="*60)
    
    print(f"\n📈 Scores RFM:")
    print(f"  • Moyenne: {df['rfm_score'].mean():.1f}")
    print(f"  • Médiane: {df['rfm_score'].median():.1f}")
    print(f"  • Min-Max: {df['rfm_score'].min():.0f} - {df['rfm_score'].max():.0f}")
    
    print(f"\n👥 Distribution par segment:")
    seg_dist = df['segment'].value_counts()
    for segment, count in seg_dist.items():
        pct = (count / len(df)) * 100
        print(f"  • {segment}: {count} clients ({pct:.1f}%)")
    
    print(f"\n⚠️  Risque de churn:")
    churn_dist = df['churn_risk'].value_counts()
    for risk, count in churn_dist.items():
        pct = (count / len(df)) * 100
        print(f"  • {risk}: {count} clients ({pct:.1f}%)")
    
    print(f"\n💰 Données de base:")
    print(f"  • Recency moyenne: {df['recency'].mean():.0f} jours")
    print(f"  • Frequency moyenne: {df['frequency'].mean():.1f} commandes")
    print(f"  • Monetary moyenne: €{df['monetary'].mean():.2f}")
    print(f"  • CA total: €{df['monetary'].sum():.2f}")
    
    print("\n" + "="*60)

def export_results(df):
    """Exporter résultats"""
    
    # Sauvegarder en CSV
    output_file = '/home/claude/ecommerce-churn-project/rfm_results.csv'
    df_export = df[[
        'customer_id', 'first_name', 'last_name', 'email', 'city',
        'recency', 'frequency', 'monetary',
        'rfm_score', 'segment', 'churn_risk'
    ]].sort_values('rfm_score', ascending=False)
    
    df_export.to_csv(output_file, index=False)
    print(f"\n✓ Résultats exportés: {output_file}")
    
    return df_export

# =====================================================
# 6. MAIN
# =====================================================

def main():
    """Pipeline RFM complet"""
    
    print("="*60)
    print("🚀 PIPELINE RFM - SEGMENTATION CLIENT")
    print("="*60)
    
    # Connexion
    print("\n[1] Connexion à la base...")
    conn = connect_db()
    print("✓ Connecté")
    
    # Charger données
    print("\n[2] Chargement des données...")
    df = load_customer_data(conn)
    print(f"✓ {len(df)} clients chargés")
    
    # Calculer RFM
    print("\n[3] Calcul RFM...")
    df = calculate_rfm(df)
    df = score_rfm_components(df)
    df = calculate_overall_rfm_score(df)
    print("✓ RFM calculé")
    
    # Segmentation
    print("\n[4] Segmentation et détection churn...")
    df = segment_customers(df)
    df = detect_churn_risk(df)
    print("✓ Segmentation complète")
    
    # Enrichissement API
    print("\n[5] Enrichissement géolocalisation...")
    try:
        df = enrich_with_coordinates(df)
        print("✓ Données enrichies")
    except Exception as e:
        print(f"⚠ API indisponible: {e}")
    
    # Sauvegarder en base
    print("\n[6] Insertion en base de données...")
    save_segments_to_db(conn, df)
    
    # Stats et export
    print_statistics(df)
    export_results(df)
    
    # Fermer connexion
    conn.close()
    print("\n✅ Pipeline terminé !")

if __name__ == '__main__':
    main()
