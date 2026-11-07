-- ============================================================================
-- AI-DRIVEN PERSONALIZED PREVENTIVE HEALTHCARE AND NUTRITION MANAGEMENT SYSTEM
-- Relational Database Schema (MySQL 8.0+ / InnoDB Engine)
-- Character Set: utf8mb4 | Collation: utf8mb4_unicode_ci
-- ============================================================================

CREATE DATABASE IF NOT EXISTS health_portal_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE health_portal_db;

-- ----------------------------------------------------------------------------
-- 1. USERS & PROFILES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('user', 'admin') DEFAULT 'user' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_profiles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    age INT NULL,
    gender ENUM('male', 'female', 'other') NULL,
    height_cm FLOAT NULL,
    weight_kg FLOAT NULL,
    bmi FLOAT NULL,
    activity_level VARCHAR(30) DEFAULT 'sedentary',
    dietary_preference VARCHAR(30) DEFAULT 'vegetarian',
    regional_preference VARCHAR(30) DEFAULT 'south_indian',
    budget_preference VARCHAR(20) DEFAULT 'medium',
    food_allergies TEXT NULL,
    dietary_restrictions TEXT NULL,
    existing_conditions TEXT NULL,
    data_sharing_consent BOOLEAN DEFAULT TRUE NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_profile_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS admin_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 2. NUTRITION CORE & FOOD DATABASE
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS food_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    description VARCHAR(255) NULL,
    regional_origin VARCHAR(50) DEFAULT 'pan_india'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS food_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT NOT NULL,
    food_name VARCHAR(120) NOT NULL,
    native_name VARCHAR(120) NULL,
    serving_unit VARCHAR(50) DEFAULT '100g' NOT NULL,
    serving_size_grams FLOAT DEFAULT 100.0 NOT NULL,
    calories FLOAT NOT NULL,
    protein_g FLOAT DEFAULT 0.0 NOT NULL,
    carbs_g FLOAT DEFAULT 0.0 NOT NULL,
    fat_g FLOAT DEFAULT 0.0 NOT NULL,
    fiber_g FLOAT DEFAULT 0.0 NOT NULL,
    sugar_g FLOAT DEFAULT 0.0 NOT NULL,
    sodium_mg FLOAT DEFAULT 0.0 NOT NULL,
    potassium_mg FLOAT DEFAULT 0.0 NOT NULL,
    regional_tag VARCHAR(50) DEFAULT 'south_indian',
    is_vegetarian BOOLEAN DEFAULT TRUE NOT NULL,
    is_vegan BOOLEAN DEFAULT FALSE NOT NULL,
    allergen_tags VARCHAR(255) DEFAULT '',
    is_verified BOOLEAN DEFAULT TRUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_food_category FOREIGN KEY (category_id) REFERENCES food_categories(id),
    INDEX idx_food_name (food_name),
    INDEX idx_regional_tag (regional_tag)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS meal_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(40) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS food_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    food_item_id INT NOT NULL,
    meal_type_id INT NOT NULL,
    log_date DATE NOT NULL,
    quantity_multiplier FLOAT DEFAULT 1.0 NOT NULL,
    calculated_calories FLOAT NOT NULL,
    calculated_protein FLOAT NOT NULL,
    calculated_carbs FLOAT NOT NULL,
    calculated_fat FLOAT NOT NULL,
    logged_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_foodlog_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_foodlog_item FOREIGN KEY (food_item_id) REFERENCES food_items(id) ON DELETE RESTRICT,
    CONSTRAINT fk_foodlog_meal FOREIGN KEY (meal_type_id) REFERENCES meal_types(id),
    INDEX idx_user_date (user_id, log_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS nutrition_targets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    target_calories FLOAT DEFAULT 2000.0 NOT NULL,
    target_protein_g FLOAT DEFAULT 60.0 NOT NULL,
    target_carbs_g FLOAT DEFAULT 250.0 NOT NULL,
    target_fats_g FLOAT DEFAULT 65.0 NOT NULL,
    target_fiber_g FLOAT DEFAULT 30.0 NOT NULL,
    target_water_ml FLOAT DEFAULT 2500.0 NOT NULL,
    is_custom BOOLEAN DEFAULT FALSE NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_targets_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS recommendations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    food_item_id INT NOT NULL,
    recommendation_date DATE NOT NULL,
    meal_time VARCHAR(30) DEFAULT 'lunch',
    match_score FLOAT DEFAULT 0.0,
    recommendation_reason VARCHAR(255) NOT NULL,
    clinical_justification TEXT NULL,
    is_accepted BOOLEAN DEFAULT FALSE,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_reco_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_reco_food FOREIGN KEY (food_item_id) REFERENCES food_items(id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 3. ACTIVITY & LIFESTYLE TRACKING
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    log_date DATE NOT NULL,
    step_count INT DEFAULT 0 NOT NULL,
    distance_km FLOAT DEFAULT 0.0 NOT NULL,
    calories_burned FLOAT DEFAULT 0.0 NOT NULL,
    logged_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_activity_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_user_activity_date (user_id, log_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS water_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    log_date DATE NOT NULL,
    amount_ml INT DEFAULT 0 NOT NULL,
    logged_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_water_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_water_date (user_id, log_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS sleep_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    log_date DATE NOT NULL,
    sleep_hours FLOAT DEFAULT 7.0 NOT NULL,
    sleep_quality_score INT DEFAULT 75 NOT NULL,
    logged_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_sleep_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uq_user_sleep_date (user_id, log_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS exercise_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    log_date DATE NOT NULL,
    exercise_type VARCHAR(50) NOT NULL,
    duration_minutes INT NOT NULL,
    estimated_calories_burned FLOAT DEFAULT 0.0 NOT NULL,
    logged_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_exercise_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_exercise_date (user_id, log_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_goals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    goal_type VARCHAR(50) DEFAULT 'maintenance' NOT NULL,
    target_weight_kg FLOAT NULL,
    target_date DATE NULL,
    status VARCHAR(20) DEFAULT 'active' NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_goal_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 4. MACHINE LEARNING & HEALTH ASSESSMENTS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS health_assessments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    assessment_type VARCHAR(50) NOT NULL,
    input_payload TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_assess_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ml_prediction_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    assessment_id INT NOT NULL UNIQUE,
    user_id INT NOT NULL,
    condition_name VARCHAR(50) NOT NULL,
    risk_score FLOAT NOT NULL,
    risk_category VARCHAR(30) NOT NULL,
    top_contributing_features TEXT NOT NULL,
    model_version VARCHAR(30) DEFAULT '1.0.0' NOT NULL,
    clinical_disclaimer TEXT NOT NULL,
    evaluated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_pred_assessment FOREIGN KEY (assessment_id) REFERENCES health_assessments(id) ON DELETE CASCADE,
    CONSTRAINT fk_pred_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------------------
-- 5. GENERATIVE AI & EDUCATIONAL AWARENESS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    sender ENUM('user', 'assistant') NOT NULL,
    message TEXT NOT NULL,
    context_used TEXT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_chat_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_chat (user_id, timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS health_articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    author_admin_id INT NULL,
    title VARCHAR(200) NOT NULL,
    slug VARCHAR(220) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    summary VARCHAR(350) NOT NULL,
    content_markdown TEXT NOT NULL,
    academic_citations TEXT NULL,
    read_time_minutes INT DEFAULT 5 NOT NULL,
    published_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_article_admin FOREIGN KEY (author_admin_id) REFERENCES admin_users(id) ON DELETE SET NULL,
    INDEX idx_article_category (category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS article_bookmarks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    article_id INT NOT NULL,
    bookmarked_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT fk_bm_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_bm_article FOREIGN KEY (article_id) REFERENCES health_articles(id) ON DELETE CASCADE,
    UNIQUE KEY uq_user_article_bookmark (user_id, article_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
