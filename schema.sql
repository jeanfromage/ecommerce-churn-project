-- =====================================================
-- PROJET FINAL : E-COMMERCE CHURN PREDICTION
-- Algo & Bases de Données - MSc2 Manager Data Marketing
-- =====================================================

-- DROP DATABASE IF EXISTS ecommerce_churn;
-- CREATE DATABASE ecommerce_churn;
-- USE ecommerce_churn;

-- =====================================================
-- 1. CRÉATION DES TABLES
-- =====================================================

-- Table CUSTOMERS
CREATE TABLE IF NOT EXISTS customers (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    signup_date DATE NOT NULL,
    city VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_email CHECK (email LIKE '%@%')
);

-- Table PRODUCTS
CREATE TABLE IF NOT EXISTS products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT check_price CHECK (price > 0)
);

-- Table ORDERS
CREATE TABLE IF NOT EXISTS orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    order_date DATE NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    CONSTRAINT check_amount CHECK (total_amount >= 0)
);

-- Table ORDER_ITEMS (jointure M2M entre ORDERS et PRODUCTS)
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE,
    CONSTRAINT check_quantity CHECK (quantity > 0),
    CONSTRAINT check_unit_price CHECK (unit_price > 0)
);

-- Table CUSTOMER_SEGMENTS (enrichissée par le pipeline Python)
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
);

-- =====================================================
-- 2. INDEXES
-- =====================================================

CREATE INDEX idx_customer_signup ON customers(signup_date);
CREATE INDEX idx_order_date ON orders(order_date);
CREATE INDEX idx_order_customer ON orders(customer_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- =====================================================
-- 3. VUES (CREATE VIEW)
-- =====================================================

-- Vue 1 : RFM par client (Recency, Frequency, Monetary)
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
GROUP BY c.customer_id, c.first_name, c.last_name, c.email;

-- Vue 2 : Statistiques produits
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
GROUP BY p.product_id, p.product_name, p.category, p.price;

-- Vue 3 : Performance par catégorie
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
GROUP BY p.category;

-- =====================================================
-- 4. FONCTIONS
-- =====================================================

-- Fonction : Calculer le RFM score (0-100)
DELIMITER //
CREATE OR REPLACE FUNCTION fn_calculate_rfm_score(
    p_recency INT,
    p_frequency INT,
    p_monetary DECIMAL(10, 2)
) RETURNS INT DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_score INT;
    DECLARE v_max_monetary DECIMAL(10, 2);
    
    -- Récupérer le montant max pour normaliser
    SELECT MAX(monetary_value) INTO v_max_monetary FROM vw_customer_rfm;
    
    -- Calcul du score : R (40%) + F (30%) + M (30%)
    SET v_score = ROUND(
        (100 - LEAST(p_recency, 365) / 365 * 100) * 0.4 +  -- Recency inversée
        LEAST(p_frequency, 20) / 20 * 100 * 0.3 +            -- Frequency normalisée
        (p_monetary / GREATEST(v_max_monetary, 1)) * 100 * 0.3 -- Monetary normalisé
    );
    
    RETURN GREATEST(0, LEAST(100, v_score));
END//
DELIMITER ;

-- Fonction : Déterminer segment client
DELIMITER //
CREATE OR REPLACE FUNCTION fn_get_segment(p_score INT) RETURNS VARCHAR(20) DETERMINISTIC
BEGIN
    IF p_score >= 80 THEN
        RETURN 'Champion';
    ELSEIF p_score >= 60 THEN
        RETURN 'Loyal';
    ELSEIF p_score >= 40 THEN
        RETURN 'Potential';
    ELSE
        RETURN 'At Risk';
    END IF;
END//
DELIMITER ;

-- =====================================================
-- 5. PROCÉDURES STOCKÉES
-- =====================================================

-- Procédure : Mettre à jour tous les segments clients
DELIMITER //
CREATE OR REPLACE PROCEDURE sp_update_customer_segments()
BEGIN
    DECLARE v_done INT DEFAULT 0;
    DECLARE v_customer_id INT;
    DECLARE v_recency INT;
    DECLARE v_frequency INT;
    DECLARE v_monetary DECIMAL(10, 2);
    DECLARE v_rfm_score INT;
    DECLARE v_segment VARCHAR(20);
    
    DECLARE cur CURSOR FOR 
        SELECT 
            customer_id,
            recency_days,
            frequency,
            monetary_value
        FROM vw_customer_rfm;
    
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;
    
    OPEN cur;
    
    read_loop: LOOP
        FETCH cur INTO v_customer_id, v_recency, v_frequency, v_monetary;
        
        IF v_done THEN
            LEAVE read_loop;
        END IF;
        
        SET v_rfm_score = fn_calculate_rfm_score(v_recency, v_frequency, v_monetary);
        SET v_segment = fn_get_segment(v_rfm_score);
        
        INSERT INTO customer_segments 
            (customer_id, rfm_score, segment_name, recency_days, frequency, monetary_value, churn_risk)
        VALUES 
            (v_customer_id, v_rfm_score, v_segment, v_recency, v_frequency, v_monetary,
             IF(v_recency > 180, 'High', IF(v_recency > 90, 'Medium', 'Low')))
        ON DUPLICATE KEY UPDATE 
            rfm_score = v_rfm_score,
            segment_name = v_segment,
            recency_days = v_recency,
            frequency = v_frequency,
            monetary_value = v_monetary,
            churn_risk = IF(v_recency > 180, 'High', IF(v_recency > 90, 'Medium', 'Low')),
            last_updated = CURRENT_TIMESTAMP;
    
    END LOOP;
    
    CLOSE cur;
END//
DELIMITER ;

-- =====================================================
-- 6. REQUÊTES SELECT PRINCIPALES
-- =====================================================

-- Q1 : Clients par ville avec montant moyen (WHERE, GROUP BY, ORDER BY)
SELECT 
    c.city,
    COUNT(c.customer_id) AS nb_customers,
    ROUND(AVG(o.total_amount), 2) AS avg_order_value,
    ROUND(SUM(o.total_amount), 2) AS total_revenue
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
WHERE c.city IS NOT NULL
GROUP BY c.city
HAVING COUNT(c.customer_id) >= 3
ORDER BY total_revenue DESC
LIMIT 10;

-- Q2 : Top 10 clients par CA (HAVING, ORDER BY, LIMIT)
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    c.email,
    COUNT(o.order_id) AS nb_orders,
    ROUND(SUM(o.total_amount), 2) AS total_spent
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name, c.email
HAVING SUM(o.total_amount) > 1000
ORDER BY total_spent DESC
LIMIT 10;

-- Q3 : Ventes mensuelles par catégorie (CTE - Common Table Expression)
WITH monthly_sales AS (
    SELECT 
        DATE_TRUNC(o.order_date, MONTH) AS month,
        p.category,
        ROUND(SUM(oi.quantity * oi.unit_price), 2) AS monthly_revenue
    FROM orders o
    INNER JOIN order_items oi ON o.order_id = oi.order_id
    INNER JOIN products p ON oi.product_id = p.product_id
    GROUP BY DATE_TRUNC(o.order_date, MONTH), p.category
)
SELECT 
    month,
    category,
    monthly_revenue
FROM monthly_sales
WHERE monthly_revenue > 0
ORDER BY month DESC, monthly_revenue DESC;

-- Q4 : Jointure 3+ tables - Détail commandes avec client et produit
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    o.order_id,
    o.order_date,
    p.product_name,
    p.category,
    oi.quantity,
    oi.unit_price,
    ROUND(oi.quantity * oi.unit_price, 2) AS line_total
FROM customers c
INNER JOIN orders o ON c.customer_id = o.customer_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p ON oi.product_id = p.product_id
WHERE o.order_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY o.order_date DESC, o.order_id;

-- Q5 : Sous-requête - Clients sans commande depuis 6 mois
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    c.email,
    c.signup_date,
    (SELECT MAX(order_date) FROM orders WHERE customer_id = c.customer_id) AS last_order_date,
    DATEDIFF(CURDATE(), (SELECT MAX(order_date) FROM orders WHERE customer_id = c.customer_id)) AS days_since_last_order
FROM customers c
WHERE (SELECT MAX(order_date) FROM orders WHERE customer_id = c.customer_id) < DATE_SUB(CURDATE(), INTERVAL 180 DAY)
   OR (SELECT COUNT(*) FROM orders WHERE customer_id = c.customer_id) = 0
ORDER BY last_order_date ASC;

-- Q6 : Sous-requête corellée - Clients avec achat > moyenne
SELECT 
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    ROUND(SUM(o.total_amount), 2) AS customer_total,
    (SELECT ROUND(AVG(total_amount), 2) FROM orders) AS overall_avg_order,
    ROUND(
        SUM(o.total_amount) - (SELECT AVG(total_amount) FROM orders) * COUNT(o.order_id), 
        2
    ) AS surplus_vs_avg
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.first_name, c.last_name
HAVING SUM(o.total_amount) > (SELECT AVG(total_amount) FROM orders)
ORDER BY customer_total DESC;

-- =====================================================
-- 7. UTILITAIRES
-- =====================================================

-- Compter les enregistrements
SELECT 
    'customers' AS table_name,
    COUNT(*) AS row_count
FROM customers
UNION ALL
SELECT 'products', COUNT(*) FROM products
UNION ALL
SELECT 'orders', COUNT(*) FROM orders
UNION ALL
SELECT 'order_items', COUNT(*) FROM order_items
UNION ALL
SELECT 'customer_segments', COUNT(*) FROM customer_segments;

-- =====================================================
-- 8. EXEMPLE D'INSERTION DE DONNÉES (via CSV/JSON après)
-- =====================================================

-- Note: Les données seront insérées via le script Python
-- INSERT INTO customers (first_name, last_name, email, signup_date, city) VALUES (...);
-- INSERT INTO products (product_name, category, price) VALUES (...);
-- INSERT INTO orders (customer_id, order_date, total_amount) VALUES (...);
-- INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (...);
