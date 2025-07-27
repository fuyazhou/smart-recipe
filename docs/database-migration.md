# 数据库迁移说明 - PostgreSQL 到 MySQL

## 迁移概述

项目已成功从 PostgreSQL 迁移到 MySQL 8.0，以下是主要变更内容：

## 主要变更

### 1. 数据库服务
- **原来**: PostgreSQL 15
- **现在**: MySQL 8.0
- **驱动**: 从 `asyncpg` 改为 `aiomysql` 和 `PyMySQL`

### 2. 数据类型映射

| PostgreSQL | MySQL | 说明 |
|------------|-------|------|
| UUID | CHAR(36) | 使用字符串存储UUID |
| JSONB | JSON | MySQL原生JSON类型 |
| TIMESTAMP WITH TIME ZONE | TIMESTAMP | MySQL时间戳 |
| BOOLEAN | BOOLEAN | 保持不变 |
| INET | VARCHAR(45) | IP地址存储 |

### 3. 语法变更

#### 索引
```sql
-- PostgreSQL (GIN索引)
CREATE INDEX idx_recipes_title_trgm ON recipes USING gin (title gin_trgm_ops);

-- MySQL (普通索引)
CREATE INDEX idx_recipes_title ON recipes(title);
```

#### 约束
```sql
-- PostgreSQL
UNIQUE(recipe_id, user_id)

-- MySQL  
UNIQUE KEY unique_recipe_user (recipe_id, user_id)
```

#### 触发器
```sql
-- PostgreSQL (函数 + 触发器)
CREATE OR REPLACE FUNCTION update_recipe_rating()
RETURNS TRIGGER AS $$
BEGIN
    -- 逻辑
END;
$$ language 'plpgsql';

-- MySQL (直接触发器)
DELIMITER $$
CREATE TRIGGER update_recipe_rating_after_insert
    AFTER INSERT ON recipe_ratings
    FOR EACH ROW
BEGIN
    -- 逻辑
END$$
DELIMITER ;
```

### 4. 配置变更

#### Docker Compose
```yaml
# PostgreSQL
postgres:
  image: postgres:15
  environment:
    POSTGRES_DB: smart_recipe
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres

# MySQL
mysql:
  image: mysql:8.0
  environment:
    MYSQL_DATABASE: smart_recipe
    MYSQL_USER: smartrecipe
    MYSQL_PASSWORD: smartrecipe
    MYSQL_ROOT_PASSWORD: root
  command: --default-authentication-plugin=mysql_native_password --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
```

#### 连接字符串
```python
# PostgreSQL
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/smart_recipe"

# MySQL
DATABASE_URL = "mysql://smartrecipe:smartrecipe@localhost:3306/smart_recipe"
```

### 5. 代码变更

#### SQLAlchemy 模型
```python
# PostgreSQL
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

# MySQL
id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
```

#### JSON 字段默认值
```python
# PostgreSQL
preferences = Column(JSON, default=[])

# MySQL  
preferences = Column(JSON, default=lambda: [])
```

## 新增用户字段

根据业务需求，新增了以下用户相关字段：

### users 表新增字段
- `open_id`: 用户唯一标识符
- `height`: 身高 (cm)
- `weight`: 体重 (kg) 
- `user_type`: 用户阶段 (备孕/孕期/哺乳期等)
- `is_paid`: 是否付费用户

### user_preferences 表新增字段
- `exercise_level`: 运动等级 (0-3)
- `eating_habit`: 饮食习惯 (0-7)
- `staple_food_preference`: 主食偏好 (0-2)
- `flavour_preference`: 口味偏好
- `cooking_type_preference`: 烹饪方式偏好
- `preferred_season`: 当前季节
- `gene_params`: 基因参数 (营养需求)

## 迁移验证

### 1. 数据库连接测试
```bash
cd backend
PYTHONPATH=. python -c "from app.config.settings import settings; print(f'Database URL: {settings.DATABASE_URL}')"
```

### 2. 启动服务测试
```bash
# 启动MySQL
docker compose up -d mysql

# 检查服务状态
docker compose ps

# 查看日志
docker compose logs mysql
```

### 3. API测试
```bash
# 启动后端服务
cd backend
PYTHONPATH=. python app/main.py

# 访问API文档
open http://localhost:8000/docs
```

## 常用命令

### 数据库操作
```bash
# 重置数据库
make db-reset

# 运行迁移
make db-migrate

# 填充测试数据
make db-seed
```

### 开发环境
```bash
# 启动所有服务
make dev-up

# 停止所有服务
make dev-down

# 清理环境
make clean
```

## 注意事项

1. **字符集**: 确保使用 `utf8mb4` 字符集，支持完整的Unicode字符集
2. **JSON字段**: MySQL 8.0的JSON字段性能良好，但语法与PostgreSQL略有不同
3. **UUID**: 使用字符串存储，需要在应用层生成UUID
4. **时区**: MySQL的TIMESTAMP字段默认使用系统时区，需要在连接时指定时区
5. **索引**: 移除了PostgreSQL特有的GIN索引，使用标准B-tree索引

## 性能优化建议

1. **连接池**: 配置合适的连接池大小
2. **索引**: 根据查询模式添加必要的复合索引  
3. **分区**: 对于大表考虑分区策略
4. **缓存**: 充分利用Redis缓存减少数据库压力
5. **读写分离**: 生产环境可考虑主从复制 