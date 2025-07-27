# Smart Recipe 开发指南

## 项目概述

Smart Recipe 是一个支持多平台（iOS/Android/Web）和多地区（中国/美国）的智能食谱应用。

## 技术架构

### 后端架构
- **框架**: FastAPI (Python 3.12)
- **数据库**: PostgreSQL + Redis
- **认证**: JWT + OAuth2
- **API文档**: OpenAPI/Swagger

### 前端架构
- **Web**: React 18 + TypeScript + Vite
- **iOS**: Swift + SwiftUI
- **Android**: Kotlin + Jetpack Compose

### 基础设施
- **容器化**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **部署**: Kubernetes

## 开发环境设置

### 1. 环境要求

**必须:**
- Docker Desktop
- Git
- Python 3.12+
- Node.js 18+

**可选 (移动端开发):**
- Xcode 15+ (iOS开发)
- Android Studio (Android开发)

### 2. 快速启动

```bash
# 克隆项目
git clone <repository-url>
cd smart-recipe

# 启动开发环境
make dev-up

# 访问应用
# Web前端: http://localhost:3000
# 后端API: http://localhost:8000
# API文档: http://localhost:8000/docs
```

### 3. 环境变量配置

复制环境变量模板:
```bash
cp .env.example .env
```

根据需要修改配置，特别是:
- `REGION`: 设置为 `china` 或 `us`
- 数据库连接信息
- 第三方服务API密钥

## 开发流程

### 1. 分支管理

- `main`: 生产环境分支
- `develop`: 开发环境分支
- `feature/*`: 功能开发分支
- `hotfix/*`: 紧急修复分支

### 2. 代码规范

**Python (后端)**
```bash
# 代码格式化
black app/
isort app/

# 代码检查
flake8 app/

# 运行测试
pytest
```

**TypeScript (Web前端)**
```bash
# 代码格式化
npm run format

# 代码检查
npm run lint

# 运行测试
npm test
```

### 3. 提交规范

使用 Conventional Commits 格式:
```
feat: 添加新功能
fix: 修复bug
docs: 更新文档
style: 代码格式修改
refactor: 代码重构
test: 添加测试
chore: 构建过程或辅助工具的变动
```

## 数据库开发

### 1. 迁移管理

```bash
# 创建新的迁移
cd backend
alembic revision --autogenerate -m "添加用户表"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 2. 测试数据

```bash
# 填充测试数据
python scripts/seed_data.py
```

## API开发

### 1. 新增API端点

1. 在 `backend/app/routers/` 中创建路由文件
2. 定义Pydantic模型用于请求/响应
3. 实现业务逻辑
4. 添加单元测试
5. 更新API文档

### 2. API版本管理

使用URL路径进行版本控制:
```
/api/v1/users
/api/v2/users
```

## 前端开发

### 1. 组件开发

```tsx
// 功能组件模板
import React from 'react';
import { useTranslation } from 'react-i18next';

interface Props {
  // 定义属性类型
}

const Component: React.FC<Props> = ({ }) => {
  const { t } = useTranslation();
  
  return (
    <div>
      {/* JSX内容 */}
    </div>
  );
};

export default Component;
```

### 2. 状态管理

使用Redux Toolkit进行状态管理:
```typescript
// 创建slice
import { createSlice } from '@reduxjs/toolkit';

const slice = createSlice({
  name: 'feature',
  initialState,
  reducers: {
    // reducer 函数
  },
});
```

### 3. 国际化

```typescript
// 使用翻译
import { useTranslation } from 'react-i18next';

const { t } = useTranslation();
return <div>{t('common.save')}</div>;
```

## 移动端开发

### 1. iOS开发

```bash
# 安装依赖
cd mobile/ios
pod install

# 设置地区环境变量
export REGION=china  # 或 us

# 构建项目
xcodebuild -workspace SmartRecipe.xcworkspace \
  -scheme SmartRecipe \
  -configuration Debug build
```

### 2. Android开发

```bash
# 构建不同地区版本
cd mobile/android
./gradlew assembleChinaDebug    # 中国版本
./gradlew assembleUsDebug       # 美国版本
```

## 多地区支持

### 1. 配置差异

每个地区都有独立的配置文件:
- `configs/china/` - 中国配置
- `configs/us/` - 美国配置

### 2. 第三方服务集成

**中国地区:**
- 支付: 微信支付、支付宝
- 地图: 高德地图
- 推送: 个推
- 统计: 友盟

**美国地区:**
- 支付: Stripe、Apple Pay、Google Pay
- 地图: Google Maps
- 推送: Firebase
- 统计: Firebase Analytics

### 3. 构建不同版本

```bash
# 构建中国版本
REGION=china make build-all

# 构建美国版本
REGION=us make build-all
```

## 测试

### 1. 单元测试

```bash
# 后端测试
cd backend
pytest tests/

# 前端测试
cd web
npm test
```

### 2. 集成测试

```bash
# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 运行集成测试
pytest tests/integration/
```

### 3. E2E测试

```bash
# Web E2E测试
cd web
npm run test:e2e

# 移动端UI测试
# iOS: 使用XCUITest
# Android: 使用Espresso
```

## 部署

### 1. 本地部署

```bash
# 部署到本地Kubernetes
make deploy-local
```

### 2. 生产部署

```bash
# 部署到中国环境
make deploy-china

# 部署到美国环境
make deploy-us
```

## 故障排除

### 1. 常见问题

**Docker容器启动失败**
```bash
# 检查日志
docker-compose logs <service-name>

# 重新构建
docker-compose build --no-cache
```

**数据库连接失败**
```bash
# 检查数据库状态
docker-compose ps postgres

# 重置数据库
docker-compose down -v
docker-compose up postgres -d
```

### 2. 性能调优

**数据库优化**
- 添加必要的索引
- 使用数据库连接池
- 实施查询缓存

**API优化**
- 使用Redis缓存
- 实施分页
- 压缩响应数据

## 监控和日志

### 1. 应用监控

- **指标收集**: Prometheus
- **可视化**: Grafana  
- **告警**: AlertManager

### 2. 日志管理

- **收集**: Filebeat
- **处理**: Logstash
- **存储**: Elasticsearch
- **查询**: Kibana

## 安全注意事项

### 1. 认证和授权

- 使用强密码策略
- 实施双因素认证
- 定期轮换JWT密钥

### 2. 数据保护

- 加密敏感数据
- 使用HTTPS
- 实施CORS策略
- 输入验证和消毒

### 3. 漏洞管理

- 定期更新依赖包
- 进行安全扫描
- 实施安全头部

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码并推送
4. 创建Pull Request
5. 等待代码审查

## 获取帮助

- 查看项目Wiki
- 搜索现有Issues
- 创建新的Issue
- 联系团队成员 