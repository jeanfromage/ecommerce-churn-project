-- =====================================================
-- REQUÊTES DE TEST & EXPLORATION
-- Exécuter après le chargement des données + pipeline RFM
-- =====================================================

-- 1️⃣ Vue du résumé RFM (utilise la vue)
SELECT * FROM vw_customer_rfm LIMIT 20;

-- 2️⃣ Distribution par segment
SELECT 
    segment_name,
    COUNT(*) as nb_clients,
    ROUND(COUNT(*) * 100 / (SELECT COUNT(*) FROM customer_segments), 2) as pct,
    ROUND(AVG(rfm_score), 1) as avg_rfm_score,
    ROUND(AVG(monetary_value), 2) as avg_monetary
FROM customer_segments
GROUP BY segment_name
ORDER BY avg_rfm_score DESC;

-- 3️⃣ Clients à risque élevé (High churn)
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
    c.email,
    cs.rfm_score,
    cs.churn_risk,
    cs.recency_days,
    cs.frequency,
    cs.monetary_value
FROM customer_segments cs
JOIN customers c ON cs.customer_id = c.customer_id
WHERE cs.churn_risk = 'High'
ORDER BY cs.rfm_score ASC
LIMIT 30;

-- 4️⃣ Top 15 Champions
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
    c.email,
    c.city,
    cs.rfm_score,
    cs.segment_name,
    cs.recency_days,
    cs.frequency,
    cs.monetary_value
FROM customer_segments cs
JOIN customers c ON cs.customer_id = c.customer_id
WHERE cs.segment_name = 'Champion'
ORDER BY cs.rfm_score DESC
LIMIT 15;

-- 5️⃣ CA par segment
SELECT 
    cs.segment_name,
    COUNT(DISTINCT cs.customer_id) as nb_clients,
    ROUND(SUM(cs.monetary_value), 2) as total_revenue,
    ROUND(AVG(cs.monetary_value), 2) as avg_revenue,
    ROUND(SUM(cs.monetary_value) * 100 / (SELECT SUM(monetary_value) FROM customer_segments), 2) as revenue_pct
FROM customer_segments cs
GROUP BY cs.segment_name
ORDER BY total_revenue DESC;

-- 6️⃣ Clients sans commande depuis 90 jours
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
    c.email,
    cs.recency_days,
    cs.rfm_score,
    cs.churn_risk,
    (SELECT COUNT(*) FROM orders WHERE customer_id = c.customer_id) as total_orders
FROM customer_segments cs
JOIN customers c ON cs.customer_id = c.customer_id
WHERE cs.recency_days > 90
ORDER BY cs.recency_days DESC;

-- 7️⃣ Distribution géographique par segment
SELECT 
    c.city,
    cs.segment_name,
    COUNT(*) as nb_clients,
    ROUND(AVG(cs.rfm_score), 1) as avg_score
FROM customer_segments cs
JOIN customers c ON cs.customer_id = c.customer_id
WHERE c.city IS NOT NULL
GROUP BY c.city, cs.segment_name
ORDER BY c.city, cs.segment_name;

-- 8️⃣ Vérification intégrité données
SELECT 
    'Customers' as table_name,
    COUNT(*) as record_count,
    COUNT(DISTINCT customer_id) as unique_ids
FROM customers
UNION ALL
SELECT 
    'Orders',
    COUNT(*),
    COUNT(DISTINCT order_id)
FROM orders
UNION ALL
SELECT 
    'Order Items',
    COUNT(*),
    COUNT(DISTINCT order_item_id)
FROM order_items
UNION ALL
SELECT 
    'Products',
    COUNT(*),
    COUNT(DISTINCT product_id)
FROM products
UNION ALL
SELECT 
    'Customer Segments',
    COUNT(*),
    COUNT(DISTINCT customer_id)
FROM customer_segments;

-- 9️⃣ Clients qui N'ONT PAS de segment (pas encore calculé)
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
    c.email,
    (SELECT COUNT(*) FROM orders WHERE customer_id = c.customer_id) as total_orders
FROM customers c
LEFT JOIN customer_segments cs ON c.customer_id = cs.customer_id
WHERE cs.customer_id IS NULL;

-- 🔟 Produits les plus vendus
SELECT 
    p.product_name,
    p.category,
    COUNT(DISTINCT oi.order_id) as times_ordered,
    SUM(oi.quantity) as total_qty,
    ROUND(SUM(oi.quantity * oi.unit_price), 2) as total_revenue
FROM products p
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_revenue DESC;

-- 1️⃣1️⃣ Performance catégories (utilise la vue)
SELECT * FROM vw_category_performance ORDER BY total_revenue DESC;

-- 1️⃣2️⃣ Clients actifs ce mois-ci
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
    COUNT(DISTINCT o.order_id) as orders_this_month,
    ROUND(SUM(o.total_amount), 2) as spending_this_month
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE MONTH(o.order_date) = MONTH(CURDATE())
  AND YEAR(o.order_date) = YEAR(CURDATE())
GROUP BY c.customer_id, c.first_name, c.last_name
ORDER BY spending_this_month DESC;

-- 1️⃣3️⃣ Appel procédure stockée (mettre à jour segments)
CALL sp_update_customer_segments();

-- 1️⃣4️⃣ Test fonction RFM score
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) as customer_name,
    cs.recency_days,
    cs.frequency,
    cs.monetary_value,
    fn_calculate_rfm_score(cs.recency_days, cs.frequency, cs.monetary_value) as calculated_score,
    cs.rfm_score as stored_score
FROM customer_segments cs
JOIN customers c ON cs.customer_id = c.customer_id
LIMIT 10;

-- 1️⃣5️⃣ Test fonction segment
SELECT 
    rfm_score,
    fn_get_segment(rfm_score) as segment,
    COUNT(*) as nb_clients
FROM customer_segments
GROUP BY rfm_score
ORDER BY rfm_score DESC;
