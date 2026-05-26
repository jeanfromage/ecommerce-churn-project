# 🎤 GUIDE DE PRÉSENTATION - 28 Mai 2026

**Durée totale : 5-7 minutes**  
**Modalité : Présentation en distanciel + partage écran dashboard**

---

## 📋 SCRIPT DE PRÉSENTATION

### **[00:00] INTRO & CONTEXTE** (30 secondes)

*Bonjour, je présente mon projet final pour l'UE Algo & BDD.*

**Slide/Titre à montrer :**
```
E-Commerce Churn Prediction & RFM Analysis
Segmentation clients et détection du risque de churn
```

*Le contexte : On a une boutique e-commerce avec 120 clients, 500 commandes. 
L'objectif est de répondre à cette question métier importante :
"Comment identifier et prioriser les clients à risque de churn pour optimiser la rétention ?"*

---

### **[00:30] PROBLÉMATIQUE MÉTIER** (1 minute)

*Pourquoi c'est important ?*

1. **Le contexte**
   - 120 clients, variés en comportement
   - Certains achètent régulièrement, d'autres se sont arrêtés
   - Comment les traiter différemment ?

2. **Les questions opérationnelles**
   - Qui sont nos meilleurs clients ? → Marque loyale
   - Qui risque de partir ? → Action de rétention urgente
   - Qui peut avoir du potentiel ? → Cultiver
   - Qui est inactif depuis longtemps ? → Re-engagement

3. **La solution : Segmentation RFM**
   - **R**ecency : Quand ont-ils acheté ? (0-365 jours)
   - **F**requency : Combien de fois ? (0-20+ commandes)
   - **M**onetary : Combien dépensé ? (€0 à €10k)
   - → Score combiné pour chaque client

*Résultat : 4 segments actionnables + 3 niveaux de churn risk*

---

### **[01:30] ARCHITECTURE TECHNIQUE** (1 minute 30)

#### **A. Base de données** (45 sec)

*Montrer le schéma :*

```
CUSTOMERS (120)
    ↓ 1:N
ORDERS (500)
    ↓ 1:N
ORDER_ITEMS (M2M entre Orders et Products)
    ↑ N:M
PRODUCTS (35)

↓

CUSTOMER_SEGMENTS (enrichis par pipeline)
```

*Points clés :*
- 5 tables, relations FK et M2M
- Contraintes (NOT NULL, UNIQUE, CHECK)
- 3 VUES pour simplifier les requêtes
- 2 FONCTIONS pour le calcul RFM
- 1 PROCÉDURE pour mise à jour batch

*Les requêtes SQL :*
- WHERE, GROUP BY, HAVING, ORDER BY, LIMIT
- Jointures 3+ tables
- CTE (Common Table Expression)
- Sous-requêtes

#### **B. Pipeline Python** (45 sec)

*Montrer le flux :*

```
MySQL [raw data]
    ↓
RFM Pipeline
├─ Calcul RFM
├─ Scoring (0-100)
├─ Segmentation (4 groupes)
├─ Détection churn (3 niveaux)
├─ API enrichissement (Nominatim/OpenStreetMap)
    ↓
customer_segments [enrichis]
```

*Technologies :*
- MySQL connector
- Pandas (manipulation data)
- Requests (API Nominatim)
- NumPy (calculs)

---

### **[03:00] DÉMO DASHBOARD** (2-3 minutes)

*Partager votre écran*

#### **Étape 1 : Vue d'ensemble** (30 sec)
```
Montrer la page d'accueil du dashboard :
- 4 KPIs en haut : 👥 Total clients | 💰 CA moyen | ⚠️ % Churn | 📈 Commandes
- 4 graphiques : Distribution segments | Histogram RFM | Churn | Scatter
```

*Discours :*
"Ici on voit les statistiques globales. On a 120 clients, un CA moyen de 2914€, 
25% des clients sont à risque churn élevé. Les segments sont bien distribués."

#### **Étape 2 : Filtrage par segment Champions** (45 sec)
```
Cliquer sur dropdown "Segment" → "Champions"
```

*Discours :*
"Regardez comment les graphiques changent. Je filtre sur Champions seulement. 
On voit 15 clients, beaucoup de fréquence, CA élevé, tous 'Low' churn risk.
Ce sont nos meilleurs clients, à protéger absolument."

#### **Étape 3 : Filtrage par churn High** (45 sec)
```
Reset segment → "Tous"
Cliquer sur dropdown "Churn" → "High"
```

*Discours :*
"Maintenant je regarde les clients à risque HIGH churn. C'est 30 clients 
inactifs depuis 180+ jours. Score RFM bas. Ce sont nos priorités de re-engagement.
On pourrait déclencher des campagnes email ciblées pour eux."

#### **Étape 4 : Filtre slider RFM** (30 sec)
```
Bouger le slider RFM vers 80+
```

*Discours :*
"Avec le slider, je sélectionne les clients avec score RFM > 80 (Champion level).
On voit juste 15 clients de haute valeur."

---

### **[06:00] CODE INTÉRESSANT** (1 minute)

*Partager le code source via terminal ou éditeur*

#### **Option A : Fonction RFM**
```sql
FUNCTION fn_calculate_rfm_score(p_recency, p_frequency, p_monetary)
```

*Explication :*
"Voilà comment on calcule le score RFM. C'est une pondération :
- Recency (40%) : plus c'est récent, mieux c'est
- Frequency (30%) : plus d'achats, mieux c'est
- Monetary (30%) : plus on dépense, mieux c'est
Score final : 0 à 100"

#### **Option B : Procédure stockée**
```sql
PROCEDURE sp_update_customer_segments
```

*Explication :*
"Cette procédure calcule tous les segments d'un coup. 
Elle boucle sur tous les clients, applique la fonction de score,
puis classe en Champion/Loyal/Potential/At Risk.
Très utile pour mettre à jour batch."

#### **Option C : Pipeline RFM en Python**
```python
def calculate_rfm(df):
    # Recency: days since last order
    df['recency'] = (today - df['last_order_date']).days
    
    # Frequency: already in data
    df['frequency'] = df['frequency'].astype(int)
    
    # Monetary: already in data
    df['monetary'] = df['monetary'].round(2)
```

*Explication :*
"Côté Python, c'est simple : on charge les clients et commandes,
on calcule R/F/M, on score avec pandas, on segmente, et on réinsère en base."

---

### **[07:00] CONCLUSION** (30 secondes)

*Récapitulatif :*

✅ **Problématique** : Identifier clients à risque → Actions de rétention ciblées
✅ **Solution** : RFM segmentation (4 groupes) + churn detection (3 niveaux)
✅ **Technos** : MySQL + Python + Plotly Dash
✅ **Résultats** : Dashboard actionable, 120 clients segmentés
✅ **Portfolio** : Code clean, documenté, versionné GitHub

*Merci !*

---

## 🎯 POINTS CLÉS À RETENIR

| Aspect | À montrer |
|--------|-----------|
| **Problématique** | "Identifier clients à risque pour la rétention" |
| **Données** | "120 clients, 500 commandes, 2 ans d'historique" |
| **Algo** | "RFM segmentation : 4 groupes + churn detection" |
| **BD** | "5 tables, vues, fonctions, procédures" |
| **Code** | "Python pipeline + Plotly dashboard" |
| **Résultat** | "Dashboard interactif, filtres, KPIs temps réel" |

---

## 📊 STATISTIQUES À MENTIONNER

```
👥 Clients par segment:
   • Champions    : 15% (CA €43K)
   • Loyal        : 25% (CA €72K)
   • Potential    : 35% (CA €89K)
   • At Risk      : 25% (CA €29K)

⚠️ Churn risk:
   • High         : 25% (inactifs 180+j)
   • Medium       : 35% (inactifs 90-180j)
   • Low          : 40% (actifs)

💰 Valeur client:
   • CA total     : €349K
   • CA moyen     : €2,914
   • CA médian    : €2,100
```

---

## ⏱️ TIMING DÉTAILLÉ

```
[0:00-0:30] Intro contexte
[0:30-1:30] Problématique métier + RFM
[1:30-3:00] Architecture technique (BD + Pipeline)
[3:00-6:00] Démo dashboard avec filtres
[6:00-7:00] Code intéressant
[7:00-7:30] Conclusion + Q&A
─────────────────
Total: 7:30 minutes
```

---

## 🚨 ASTUCES PRÉSENTATION

1. **Si l'API échoue** : "L'API Nominatim gère gracieusement. Sans API, les données restent valides."

2. **Si la démo plante** : "Le code est testé localement. Je peux montrer les fichiers sources."

3. **Si question sur le choix RFM** : "RFM est le standard du marketing analytique. C'est simple, efficace, et prouvé."

4. **Si question sur le score** : "La pondération 40-30-30 est issue d'une analyse, mais elle est configurable."

5. **Si question cahier des charges** : "Checklist complète en GitHub. J'ai 100% des 4 parties."

---

## 💡 QUESTIONS ANTICIPÉES & RÉPONSES

**Q: Pourquoi RFM et pas ML ?**
A: RFM est plus simple, interprétable, et suffisant pour le marketing. ML serait overkill ici.

**Q: Comment vous gérez les données manquantes ?**
A: Données synthétiques donc nickel. En production, fillna avec valeurs par défaut.

**Q: L'API Nominatim est lente ?**
A: Oui, c'est volontaire pour montrer l'enrichissement. En prod, on utiliserait une DB GéoDB.

**Q: Vous avez testé en production ?**
A: Code local testé. Le setup est dans le README, avec variables .env.

**Q: Comment vous aviez le temps pour tout ça ?**
A: Structure clear, génération données auto, pipeline réutilisable. 4h classe + perso.

---

## 🎬 SCÉNARIOS DE DÉMO

### **Scénario 1 : Rapide** (2 min)
1. Vue globale dashboard
2. Filtrer Champions
3. Afficher statistiques

### **Scénario 2 : Moyen** (3 min)
1. Vue globale
2. Filtrer Champions
3. Filtrer High churn
4. Montrer table détail

### **Scénario 3 : Complet** (4 min)
1. Vue globale + KPIs
2. Filtrer par segment
3. Filtrer par churn
4. Filtrer par score slider
5. Montrer graphiques individuels
6. Ouvrir table détail

---

## 📸 CAPTURES D'ÉCRAN À PRÉPARER

1. Dashboard overview (non filtré)
2. Dashboard filtré Champions
3. Dashboard filtré High churn
4. Schema.sql dans éditeur
5. rfm_pipeline.py code intéressant
6. GitHub repo front page

---

**🎯 Bonne présentation ! Confiance et clarté ! 🚀**
