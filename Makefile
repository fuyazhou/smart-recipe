# Smart Recipe - Makefile

.PHONY: help dev-up dev-down build-all test clean deploy-china deploy-us

# 默认目标
help:
	@echo "Smart Recipe - 多平台应用构建系统"
	@echo ""
	@echo "可用命令:"
	@echo "  dev-up       启动开发环境"
	@echo "  dev-down     停止开发环境"
	@echo "  build-all    构建所有平台"
	@echo "  test         运行所有测试"
	@echo "  clean        清理构建文件"
	@echo "  deploy-china 部署到中国环境"
	@echo "  deploy-us    部署到美国环境"

# 开发环境
dev-up:
	@echo "启动开发环境..."
	docker-compose up -d
	@echo "开发环境已启动："
	@echo "  Web前端: http://localhost:3000"
	@echo "  后端API: http://localhost:8000"
	@echo "  API文档: http://localhost:8000/docs"

dev-down:
	@echo "停止开发环境..."
	docker-compose down

# 安装依赖
install:
	@echo "安装后端依赖..."
	cd backend && pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd web && npm install
	@echo "安装iOS依赖..."
	cd mobile/ios && pod install
	@echo "安装Android依赖..."
	cd mobile/android && ./gradlew build

# 构建
build-backend:
	@echo "构建后端..."
	cd backend && docker build -t smart-recipe-backend .

build-web:
	@echo "构建Web前端..."
	cd web && npm run build

build-ios:
	@echo "构建iOS应用..."
	cd mobile/ios && xcodebuild -workspace SmartRecipe.xcworkspace -scheme SmartRecipe -configuration Release archive

build-android:
	@echo "构建Android应用..."
	cd mobile/android && ./gradlew assembleRelease

build-all: build-backend build-web build-ios build-android
	@echo "所有平台构建完成"

# 测试
test-backend:
	@echo "运行后端测试..."
	cd backend && python -m pytest

test-web:
	@echo "运行前端测试..."
	cd web && npm test

test-ios:
	@echo "运行iOS测试..."
	cd mobile/ios && xcodebuild test -workspace SmartRecipe.xcworkspace -scheme SmartRecipe -destination 'platform=iOS Simulator,name=iPhone 14'

test-android:
	@echo "运行Android测试..."
	cd mobile/android && ./gradlew test

test: test-backend test-web test-ios test-android
	@echo "所有测试完成"

# 部署
deploy-china:
	@echo "部署到中国环境..."
	./scripts/deploy.sh china

deploy-us:
	@echo "部署到美国环境..."
	./scripts/deploy.sh us

# 清理
clean:
	@echo "清理构建文件..."
	docker-compose down
	docker system prune -f
	cd backend && find . -type d -name "__pycache__" -exec rm -rf {} +
	cd web && rm -rf build/ dist/ node_modules/.cache/
	cd mobile/ios && rm -rf build/ DerivedData/
	cd mobile/android && ./gradlew clean

# 数据库操作
db-migrate:
	@echo "运行数据库迁移..."
	cd backend && python -m alembic upgrade head

db-seed:
	@echo "填充测试数据..."
	cd backend && python scripts/seed_data.py

# 代码质量检查
lint:
	@echo "代码风格检查..."
	cd backend && flake8 app/
	cd web && npm run lint
	cd mobile/ios && swiftlint
	cd mobile/android && ./gradlew ktlintCheck

format:
	@echo "代码格式化..."
	cd backend && black app/
	cd web && npm run format
	cd mobile/ios && swiftformat .
	cd mobile/android && ./gradlew ktlintFormat 