-- Smart Recipe 数据库初始化脚本 (MySQL版本)
-- 支持多地区部署

-- 设置字符集
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- 用户表
CREATE TABLE users (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    password_hash VARCHAR(255),
    avatar_url TEXT,
    bio TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    open_id VARCHAR(255) UNIQUE COMMENT 'The user''s unique identifier',
    height DECIMAL(5, 2) COMMENT 'The height of the user, (unit: cm)',
    weight DECIMAL(5, 2) COMMENT 'The weight of the user, (unit: kg)',
    user_type INT COMMENT 'User Stage: 1-Prepare for pregnancy, 2-Pregnant(1-Early/2-Mid/3-Late), 3-Lactation, 4-male, 6-Puerperium',
    is_paid BOOLEAN DEFAULT FALSE COMMENT 'is paid user or not',
    region VARCHAR(10) NOT NULL COMMENT 'china 或 us',
    language VARCHAR(10) DEFAULT 'zh-CN',
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户偏好设置表
CREATE TABLE user_preferences (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) UNIQUE NOT NULL,
    dietary_restrictions JSON COMMENT 'User dietary restrictions',
    allergies JSON COMMENT 'User allergens/intolerances/contraindications, stores an array of allergen names',
    cooking_level VARCHAR(20) DEFAULT 'beginner',
    preferred_cuisines JSON COMMENT 'Cuisine preference, stores an array of cuisine IDs',
    exercise_level INT DEFAULT 1 COMMENT 'Exercise level: 0-no, 1-Light, 2-Moderate, 3-Heavy',
    eating_habit INT DEFAULT 0 COMMENT 'User''s eating habits: 0-normal, 1-Vegan, 2-Ovo vegetarian, 3-lacto vegetarian, 4-Ovo lacto, 5-Semi vegetarian, 6-Flexitarian, 7-Halal',
    staple_food_preference INT DEFAULT 0 COMMENT 'Staple food preference: 0-normal, 1-wheaten food, 2-Rice',
    flavour_preference JSON COMMENT 'Taste preference, stores an array of flavour IDs',
    cooking_type_preference JSON COMMENT 'Cooking type preference, stores an array of cooking type IDs',
    preferred_season INT COMMENT 'The current season: 1-spring, 2-summer, 3-autumn, 4-winter',
    gene_params JSON COMMENT 'Gene params: { "nutrient_list": [], "requirement_list": [] }',
    notification_settings JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 食谱表
CREATE TABLE recipes (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    instructions JSON NOT NULL,
    ingredients JSON NOT NULL,
    cooking_time INT COMMENT '分钟',
    prep_time INT COMMENT '分钟',
    servings INT DEFAULT 1,
    difficulty VARCHAR(20) DEFAULT 'easy',
    cuisine_type VARCHAR(50),
    tags JSON,
    nutrition_info JSON,
    image_urls JSON,
    video_url TEXT,
    is_public BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    rating DECIMAL(2,1) DEFAULT 0.0,
    rating_count INT DEFAULT 0,
    view_count INT DEFAULT 0,
    region VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 食谱评分表
CREATE TABLE recipe_ratings (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    recipe_id CHAR(36) NOT NULL,
    user_id CHAR(36) NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_recipe_user (recipe_id, user_id),
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 收藏表
CREATE TABLE favorites (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    recipe_id CHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_recipe (user_id, recipe_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 购物清单表
CREATE TABLE shopping_lists (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    items JSON,
    is_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 菜谱分类表
CREATE TABLE categories (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    description TEXT,
    icon_url TEXT,
    color VARCHAR(7) COMMENT 'hex color',
    parent_id CHAR(36),
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    region VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 食谱分类关联表
CREATE TABLE recipe_categories (
    recipe_id CHAR(36) NOT NULL,
    category_id CHAR(36) NOT NULL,
    PRIMARY KEY (recipe_id, category_id),
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户关注表
CREATE TABLE user_follows (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    follower_id CHAR(36) NOT NULL,
    following_id CHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_follow (follower_id, following_id),
    FOREIGN KEY (follower_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (following_id) REFERENCES users(id) ON DELETE CASCADE,
    CHECK (follower_id != following_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 通知表
CREATE TABLE notifications (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    data JSON,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户会话表
CREATE TABLE user_sessions (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    user_id CHAR(36) NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    device_info JSON,
    ip_address VARCHAR(45),
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建索引
CREATE INDEX idx_users_region ON users(region);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_open_id ON users(open_id);

CREATE INDEX idx_recipes_region ON recipes(region);
CREATE INDEX idx_recipes_user_id ON recipes(user_id);
CREATE INDEX idx_recipes_title ON recipes(title);
CREATE INDEX idx_recipes_cuisine_type ON recipes(cuisine_type);
CREATE INDEX idx_recipes_difficulty ON recipes(difficulty);
CREATE INDEX idx_recipes_is_public ON recipes(is_public);
CREATE INDEX idx_recipes_is_featured ON recipes(is_featured);
CREATE INDEX idx_recipes_rating ON recipes(rating);
CREATE INDEX idx_recipes_created_at ON recipes(created_at);

CREATE INDEX idx_recipe_ratings_recipe_id ON recipe_ratings(recipe_id);
CREATE INDEX idx_recipe_ratings_user_id ON recipe_ratings(user_id);

CREATE INDEX idx_favorites_user_id ON favorites(user_id);
CREATE INDEX idx_favorites_recipe_id ON favorites(recipe_id);

CREATE INDEX idx_categories_region ON categories(region);
CREATE INDEX idx_categories_parent_id ON categories(parent_id);
CREATE INDEX idx_categories_sort_order ON categories(sort_order);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_token_hash ON user_sessions(token_hash);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

-- 创建触发器：自动更新食谱评分
DELIMITER $$

CREATE TRIGGER update_recipe_rating_after_insert
    AFTER INSERT ON recipe_ratings
    FOR EACH ROW
BEGIN
    UPDATE recipes SET 
        rating = (
            SELECT ROUND(AVG(rating), 1) 
            FROM recipe_ratings 
            WHERE recipe_id = NEW.recipe_id
        ),
        rating_count = (
            SELECT COUNT(*) 
            FROM recipe_ratings 
            WHERE recipe_id = NEW.recipe_id
        )
    WHERE id = NEW.recipe_id;
END$$

CREATE TRIGGER update_recipe_rating_after_update
    AFTER UPDATE ON recipe_ratings
    FOR EACH ROW
BEGIN
    UPDATE recipes SET 
        rating = (
            SELECT ROUND(AVG(rating), 1) 
            FROM recipe_ratings 
            WHERE recipe_id = NEW.recipe_id
        ),
        rating_count = (
            SELECT COUNT(*) 
            FROM recipe_ratings 
            WHERE recipe_id = NEW.recipe_id
        )
    WHERE id = NEW.recipe_id;
END$$

CREATE TRIGGER update_recipe_rating_after_delete
    AFTER DELETE ON recipe_ratings
    FOR EACH ROW
BEGIN
    UPDATE recipes SET 
        rating = COALESCE((
            SELECT ROUND(AVG(rating), 1) 
            FROM recipe_ratings 
            WHERE recipe_id = OLD.recipe_id
        ), 0.0),
        rating_count = (
            SELECT COUNT(*) 
            FROM recipe_ratings 
            WHERE recipe_id = OLD.recipe_id
        )
    WHERE id = OLD.recipe_id;
END$$

DELIMITER ; 