# Smart Recipe - 多平台多地区应用

一个支持 iOS/Android 移动端和 Web 前端的智能食谱应用，同时支持中国和美国两个地区版本。

## 项目架构

```
smart-recipe/
├── mobile/                    # 移动端应用
│   ├── ios/                   # iOS应用 (Swift/SwiftUI)
│   ├── android/               # Android应用 (Kotlin)
│   └── shared/                # 移动端共享代码和资源
├── web/                       # Web前端 (React/Vue)
├── backend/                   # Python 3.12 后端服务
├── database/                  # 数据库配置和迁移
├── shared/                    # 跨平台共享资源
│   ├── assets/                # 图片、图标等静态资源
│   ├── translations/          # 国际化翻译文件
│   └── configs/               # 共享配置
├── configs/                   # 环境和地区配置
│   ├── china/                 # 中国版本配置
│   ├── us/                    # 美国版本配置
│   └── common/                # 通用配置
├── scripts/                   # 构建和部署脚本
├── docs/                      # 项目文档
└── .github/                   # CI/CD 配置
```

## 技术栈

### 移动端
- **iOS**: Swift, SwiftUI
- **Android**: Kotlin, Jetpack Compose
- **共享逻辑**: 可考虑使用 Kotlin Multiplatform

### Web前端
- **框架**: React 18+ / Vue 3+
- **状态管理**: Redux Toolkit / Pinia
- **UI库**: Material-UI / Ant Design
- **构建工具**: Vite

### 后端
- **语言**: Python 3.12
- **框架**: FastAPI
- **数据库**: PostgreSQL (主库) + Redis (缓存)
- **认证**: JWT + OAuth2
- **API文档**: OpenAPI/Swagger

### 基础设施
- **容器化**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack

## 多地区支持

### 配置差异
- 服务器地址和CDN
- 第三方服务集成（支付、地图、推送等）
- 合规要求
- UI/UX 本地化

### 国际化
- 多语言支持 (zh-CN, en-US)
- 时区和日期格式
- 货币和数字格式
- 文化适应性设计

## 快速开始

```bash
# 克隆项目
git clone <repository-url>
cd smart-recipe

# 启动开发环境
make dev-up

# 构建所有平台
make build-all

# 部署到特定地区
make deploy-china
make deploy-us
```

## 开发指南

详细的开发指南请参考 [docs/development.md](docs/development.md)

## 部署指南

详细的部署指南请参考 [docs/deployment.md](docs/deployment.md) 