# 🛍️ E-Commerce Churn Prediction & RFM Analysis

**Projet Final - MSc2 Manager Data Marketing**
Algo & Bases de Données | INSEEC Lyon | 2026

---

## 📋 Contexte

Ce projet implémente un **pipeline data marketing complet** pour identifier et réengager les clients à risque de churn dans une boutique e-commerce.

### Problématique métier
**"Comment identifier et prioriser les clients à risque de churn pour optimiser les actions de rétention ?"**

- Analyser le comportement d'achat (Recency, Frequency, Monetary)
- Segmenter les clients en groupes actionables
- Détecter les clients inactifs
- Fournir un dashboard interactif pour le suivi en temps réel

---

## 🏗️ Architecture technique

### 1️⃣ **Base de données SQL** (`schema.sql`)

#### Modèle relationnel (3+ tables + M2M)
```
┌─────────────┐       ┌──────────┐
│  CUSTOMERS  │────1:N│  ORDERS  │
└─────────────┘       └──────────┘
                            │
                            │1:N
                            ▼
                    ┌─────────────────┐
                    │  ORDER_ITEMS    │ (M2M)
                    └─────────────────┘
                            │
                            │N:M
                            ▼
                      ┌──────────┐
                      │ PRODUCTS │
                      └──────────┘

┌──────────────────────┐
│ CUSTOMER_SEGMENTS    │ (enrichis par pipeline)
└──────────────────────┘
```

#### Contraintes
- ✅ FOREIGN KEY sur customer_id, order_id, product_id
- ✅ NOT NULL sur colonnes essentielles
- ✅ UNIQUE sur email et product_name
- ✅ CHECK sur price > 0, quantity > 0

#### Vues (3)
1. `vw_customer_rfm` : RFM par client
2. `vw_product_stats` : Stats produits
3. `vw_category_performance` : Performance par catégorie

#### Fonctions (2)
1. `fn_calculate_rfm_score()` : Calcul score RFM pondéré (0-100)
2. `fn_get_segment()` : Classification en segment

#### Procédure stockée (1)
- `sp_update_customer_segments()` : Mise à jour batch de tous les segments

#### Requêtes SQL (6+)
1. Clients par ville avec montant moyen → WHERE, GROUP BY, HAVING, ORDER BY, LIMIT
2. Top 10 clients par CA → HAVING, ORDER BY, LIMIT
3. Ventes mensuelles par catégorie → **CTE**
4. Détail commandes → **Jointure 3+ tables**
5. Clients sans commande depuis 6 mois → **Sous-requête**
6. Clients avec achat > moyenne → **Sous-requête corellée**

---

### 2️⃣ **Pipeline Python** (`rfm_pipeline.py`)

**Algorithme RFM appliqué au marketing :**

```python
RFM Score = (R_score × 8) + (F_score × 6) + (M_score × 6)
            └─ 40% ─────┘   └─ 30% ──┘    └─ 30% ──┘

Segmentation :
- Champion  (80-100) : Top clients, très loyaux
- Loyal     (60-79)  : Bons clients réguliers
- Potential (40-59)  : Clients à cultiver
- At Risk   (<40)    : À risque, action requise

Détection Churn :
- High   : Recency > 180j
- Medium : Recency 90-180j OU Frequency = 0
- Low    : Recency < 90j ET Frequency > 0
```

#### Étapes
1. **Connexion MySQL** : Charger clients + historique commandes
2. **Calcul RFM** :
   - Recency : jours depuis dernière commande
   - Frequency : nombre total de commandes
   - Monetary : total dépensé
3. **Scoring** : Scores 1-5 par composant (quintiles)
4. **Segmentation** : Classification en 4 segments
5. **Détection churn** : 3 niveaux de risque
6. **Enrichissement API** : Géolocalisation (OpenStreetMap/Nominatim)
7. **Stockage BD** : Insertion en table `customer_segments`

---

### 3️⃣ **Dashboard interactif** (`dashboard.py`)

**Plotly Dash**

#### KPIs (3+)
- 📊 Nombre total de clients
- 💰 CA moyen par client
- ⚠️ % clients à risque (churn)
- 📈 Nombre de commandes

#### Graphiques (2+)
- 📊 Distribution des segments (Pie chart)
- 📈 Distribution des scores RFM (Histogram)
- 🗺️ Heatmap Recency vs Monetary
- 🏙️ Clients par catégorie de ville

#### Filtres interactifs
- **Dropdown** : Sélectionner segment ou risque churn
- **Slider** : Filtrer par score RFM minimum
- **Callbacks** : Mise à jour dynamique des graphiques

---

## 🚀 Installation & Démarrage

### Prérequis
- Python 3.8+
- MySQL 5.7+ ou MariaDB
- pip

### 1. Cloner le repo
```bash
git clone https://github.com/YOUR_USERNAME/ecommerce-churn-project.git
cd ecommerce-churn-project
```

### 2. Créer l'environnement
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Installer dépendances
```bash
pip install -r requirements.txt
```

### 4. Configurer MySQL
```bash
cp .env.example .env
# Éditer .env avec vos paramètres MySQL
nano .env
```

Contenu `.env` :
```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=ecommerce_churn
```

### 5. Générer les données
```bash
python generate_data.py
```
Output : 120 clients, 35 produits, 500 commandes, 1510 items

### 6. Charger en base
```bash
python load_data.py
```
Crée la BD et les tables automatiquement.

### 7. Lancer le pipeline RFM
```bash
python rfm_pipeline.py
```
Calcule les segments et les insère en base.

### 8. Lancer le dashboard
```bash
python dashboard.py
```
Ouvrir http://localhost:8050 dans le navigateur.

---

## 📁 Structure du projet

```
ecommerce-churn-project/
├── README.md                      # Ce fichier
├── .env.example                   # Variables d'environnement (template)
├── .gitignore                     # Fichiers à ignorer
│
├── 1_DATA/
│   ├── generate_data.py          # Génération données réalistes
│   ├── customers.json            # Données clients
│   ├── products.json             # Données produits
│   ├── orders.json               # Données commandes
│   └── order_items.json          # Données items
│
├── 2_DATABASE/
│   ├── schema.sql                # Schéma BD complète (tables, vues, fonctions, procédures)
│   └── load_data.py              # Script de chargement MySQL
│
├── 3_PIPELINE/
│   ├── rfm_pipeline.py           # Pipeline RFM (calcul, segmentation, API enrichissement)
│   └── rfm_results.csv           # Résultats exportés
│
├── 4_DASHBOARD/
│   ├── dashboard.py              # Application Plotly Dash
│   └── screenshots/              # Captures d'écran
│
├── requirements.txt              # Dépendances Python
└── docs/
    ├── SCHEMA_DIAGRAM.png        # Diagramme entités-relations
    └── SQL_QUERIES.md            # Requêtes principales documentées
```

---

## 📊 Schéma de la base

```sql
CUSTOMERS
  ├─ customer_id (PK)
  ├─ first_name, last_name
  ├─ email (UNIQUE)
  ├─ signup_date (DATE)
  ├─ city
  └─ created_at (TIMESTAMP)

ORDERS
  ├─ order_id (PK)
  ├─ customer_id (FK → CUSTOMERS)
  ├─ order_date (DATE)
  ├─ total_amount (DECIMAL)
  └─ created_at (TIMESTAMP)

ORDER_ITEMS (M2M ORDERS ↔ PRODUCTS)
  ├─ order_item_id (PK)
  ├─ order_id (FK → ORDERS)
  ├─ product_id (FK → PRODUCTS)
  ├─ quantity (INT)
  ├─ unit_price (DECIMAL)
  └─ created_at (TIMESTAMP)

PRODUCTS
  ├─ product_id (PK)
  ├─ product_name (VARCHAR, UNIQUE)
  ├─ category (VARCHAR)
  ├─ price (DECIMAL)
  └─ created_at (TIMESTAMP)

CUSTOMER_SEGMENTS (enrichis par pipeline)
  ├─ segment_id (PK)
  ├─ customer_id (FK → CUSTOMERS, UNIQUE)
  ├─ rfm_score (INT 0-100)
  ├─ segment_name (VARCHAR)
  ├─ recency_days, frequency, monetary_value
  ├─ churn_risk (VARCHAR)
  └─ last_updated (TIMESTAMP)
```

---

## 🔍 Requêtes SQL principales

### Q1 : Top clients par CA
```sql
SELECT customer_id, CONCAT(first_name, ' ', last_name) as name, 
       COUNT(order_id) as nb_orders, SUM(total_amount) as total_spent
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id
HAVING SUM(total_amount) > 1000
ORDER BY total_spent DESC LIMIT 10;
```

### Q2 : Clients à risque (inactifs)
```sql
SELECT c.customer_id, c.email,
       MAX(o.order_date) as last_order,
       DATEDIFF(CURDATE(), MAX(o.order_date)) as days_inactive
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id
HAVING days_inactive > 180 OR COUNT(o.order_id) = 0
ORDER BY days_inactive DESC;
```

### Q3 : Ventes par catégorie (CTE)
```sql
WITH monthly_sales AS (
  SELECT DATE_TRUNC(o.order_date, MONTH) as month,
         p.category,
         SUM(oi.quantity * oi.unit_price) as revenue
  FROM orders o
  JOIN order_items oi ON o.order_id = oi.order_id
  JOIN products p ON oi.product_id = p.product_id
  GROUP BY DATE_TRUNC(o.order_date, MONTH), p.category
)
SELECT * FROM monthly_sales WHERE revenue > 0
ORDER BY month DESC;
```

---

## 🎯 Résultats attendus

### Données
- ✅ 120 clients
- ✅ 35 produits (5 catégories)
- ✅ 500 commandes
- ✅ 1510 items commandés

### Segments
- ✅ Champions : ~15% (clients fidèles, CA élevé)
- ✅ Loyal : ~25% (bons clients réguliers)
- ✅ Potential : ~35% (à cultiver)
- ✅ At Risk : ~25% (inactifs, action requise)

### Dashboard
- ✅ KPIs en temps réel
- ✅ Filtres interactifs
- ✅ Graphiques dynamiques
- ✅ Exportable en image

---

## 📚 Technologies utilisées

| Catégorie | Outils |
|-----------|--------|
| **Base de données** | MySQL, SQL |
| **Python** | Pandas, NumPy, Requests |
| **Dashboard** | Plotly, Dash |
| **Versioning** | Git, GitHub |
| **Enrichissement** | OpenStreetMap API (Nominatim) |

---

## ⚠️ Points clés du cahier des charges

### ☑️ Partie 1 : Modélisation BDD
- [x] Schéma sur dbdiagram.io (3+ tables avec relations)
- [x] 1 relation many-to-many (ORDER_ITEMS)
- [x] Fichier SQL complet (create + insert)
- [x] FOREIGN KEY et NOT NULL/UNIQUE
- [x] 6 requêtes SELECT différentes (WHERE, GROUP BY, HAVING, ORDER BY, LIMIT)
- [x] Jointure 3+ tables
- [x] CTE + sous-requête
- [x] Créer VIEW (3 vues)
- [x] Fonctions et procédure stockée

### ☑️ Partie 2 : Pipeline Python
- [x] Connexion MySQL
- [x] Manipulation Pandas
- [x] Appel API externe (Nominatim)
- [x] Algorithme RFM appliqué
- [x] Insertion résultats en table MySQL
- [x] Code commenté avec fonctions

### ☑️ Partie 3 : Dashboard Plotly
- [x] Dashboard fonctionnel
- [x] 3+ KPIs
- [x] 2+ graphiques
- [x] Filtre interactif (dropdown, slider)
- [x] Callback pour mise à jour

### ☑️ Partie 4 : Documentation
- [x] README complet
- [x] Schéma diagram
- [x] Présentation prête

---

## 🎤 Présentation (28 mai 2026)

Points à couvrir :
1. **Problématique métier** : Identification et rétention des clients à risque
2. **Schéma BD** : Architecture relationnelle, choix de modélisation
3. **Pipeline RFM** : Calcul des segments, enrichissement API
4. **Dashboard** : Démo en direct, interactions
5. **Code intéressant** : Procédure stockée ou fonction Python

---

## 📝 Livrables

✅ Repo GitHub public (lien à envoyer sur Discord avant le 28/05)
✅ Données réalistes (120 clients, 500+ commandes)
✅ Schema.sql complet
✅ Pipeline RFM fonctionnel
✅ Dashboard interactif
✅ README documenté
✅ Code clean et versionné (pas de .env en commit)

---

## 🙋 FAQ

**Q: Puis-je utiliser d'autres données ?**
A: Oui, Kaggle ou data.gouv.fr sont acceptés. Respectez minimum 30 lignes par table.

**Q: Comment masquer mon mot de passe MySQL ?**
A: Utilisez un fichier `.env` et ajoutez-le à `.gitignore`.

**Q: L'API Nominatim est trop lente ?**
A: Le pipeline gère gracieusement. Vous pouvez générer des coordonnées mockées.

**Q: Je dois vraiment avoir une procédure stockée ?**
A: Oui, c'est une exigence du cahier des charges.

---

## 📞 Auteur

**Rostom** | INSEEC MSc2 Manager Data Marketing | 2026

---

## 📄 Licence

MIT License - Libre d'utilisation pour fins éducatives

---

**Dernière mise à jour** : Mai 2026
**Status** : ✅ Prêt pour présentation
