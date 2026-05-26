#!/bin/bash
# =====================================================
# QUICK START - E-COMMERCE CHURN PROJECT
# Copy-paste à exécuter dans votre terminal
# =====================================================

echo "🚀 Quick Start - E-Commerce Churn Project"
echo "=========================================="

# 1️⃣ CLONE
echo ""
echo "[1] Clone le repo..."
# git clone https://github.com/YOUR_USERNAME/ecommerce-churn-project.git
# cd ecommerce-churn-project

# 2️⃣ VENV
echo ""
echo "[2] Création environnement virtuel..."
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# Ou sur Windows:
# venv\Scripts\activate

# 3️⃣ DEPENDENCIES
echo ""
echo "[3] Installation dépendances..."
pip install --upgrade pip
pip install -r requirements.txt

# 4️⃣ CONFIG
echo ""
echo "[4] Configuration MySQL..."
echo "    Éditer .env avec vos paramètres:"
echo "    - DB_HOST: localhost"
echo "    - DB_USER: root"
echo "    - DB_PASSWORD: votre_mot_de_passe"
cp .env.example .env
# nano .env  # Éditer le fichier

# 5️⃣ DATA GENERATION
echo ""
echo "[5] Génération des données..."
python generate_data.py
echo "    ✓ 120 clients, 35 produits, 500 commandes, 1510 items"

# 6️⃣ LOAD DATA
echo ""
echo "[6] Chargement en MySQL..."
python load_data.py
echo "    ✓ Base créée, tables créées, données chargées"

# 7️⃣ RFM PIPELINE
echo ""
echo "[7] Calcul RFM et segmentation..."
python rfm_pipeline.py
echo "    ✓ Segments calculés, API enrichissement, résultats en BD"

# 8️⃣ DASHBOARD
echo ""
echo "[8] Lancement du dashboard..."
echo "    → http://localhost:8050"
echo "    (Appuyez sur Ctrl+C pour arrêter)"
python dashboard.py

echo ""
echo "✅ Projet prêt !"
