#!/bin/bash

# Smart Recipe 部署脚本
# 用法: ./deploy.sh [china|us] [environment]

set -e

REGION=${1:-china}
ENVIRONMENT=${2:-production}

echo "开始部署 Smart Recipe 到 $REGION 地区, 环境: $ENVIRONMENT"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查必要的工具
check_dependencies() {
    print_info "检查部署依赖..."
    
    command -v docker >/dev/null 2>&1 || { print_error "Docker 未安装"; exit 1; }
    command -v kubectl >/dev/null 2>&1 || { print_error "kubectl 未安装"; exit 1; }
    
    if [ "$REGION" = "china" ]; then
        command -v aliyun >/dev/null 2>&1 || { print_warning "阿里云CLI未安装，某些功能可能不可用"; }
    else
        command -v aws >/dev/null 2>&1 || { print_warning "AWS CLI未安装，某些功能可能不可用"; }
    fi
}

# 设置环境变量
setup_environment() {
    print_info "设置环境变量..."
    
    export REGION=$REGION
    export ENVIRONMENT=$ENVIRONMENT
    
    # 加载地区特定的配置
    if [ -f "configs/$REGION/.env" ]; then
        source configs/$REGION/.env
    fi
    
    # 设置Docker镜像标签
    export IMAGE_TAG="${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"
    export BACKEND_IMAGE="smartrecipe/backend:$IMAGE_TAG"
    export WEB_IMAGE="smartrecipe/web:$IMAGE_TAG"
}

# 构建Docker镜像
build_images() {
    print_info "构建Docker镜像..."
    
    # 构建后端镜像
    print_info "构建后端镜像: $BACKEND_IMAGE"
    docker build -t $BACKEND_IMAGE ./backend
    
    # 构建Web前端镜像 (生产环境)
    print_info "构建Web前端镜像: $WEB_IMAGE"
    docker build -f ./web/Dockerfile.prod \
        --build-arg REGION=$REGION \
        --build-arg ENVIRONMENT=$ENVIRONMENT \
        -t $WEB_IMAGE ./web
}

# 推送镜像到仓库
push_images() {
    print_info "推送镜像到容器仓库..."
    
    if [ "$REGION" = "china" ]; then
        # 推送到阿里云容器镜像服务
        REGISTRY="registry.cn-hangzhou.aliyuncs.com/smartrecipe"
        docker tag $BACKEND_IMAGE $REGISTRY/backend:$IMAGE_TAG
        docker tag $WEB_IMAGE $REGISTRY/web:$IMAGE_TAG
        docker push $REGISTRY/backend:$IMAGE_TAG
        docker push $REGISTRY/web:$IMAGE_TAG
    else
        # 推送到AWS ECR
        REGISTRY="123456789012.dkr.ecr.us-east-1.amazonaws.com/smartrecipe"
        docker tag $BACKEND_IMAGE $REGISTRY/backend:$IMAGE_TAG
        docker tag $WEB_IMAGE $REGISTRY/web:$IMAGE_TAG
        docker push $REGISTRY/backend:$IMAGE_TAG
        docker push $REGISTRY/web:$IMAGE_TAG
    fi
}

# 更新Kubernetes配置
update_k8s_config() {
    print_info "更新Kubernetes配置..."
    
    # 替换配置文件中的变量
    sed -i.bak "s/{{IMAGE_TAG}}/$IMAGE_TAG/g" configs/$REGION/k8s/*.yaml
    sed -i.bak "s/{{ENVIRONMENT}}/$ENVIRONMENT/g" configs/$REGION/k8s/*.yaml
}

# 部署到Kubernetes
deploy_to_k8s() {
    print_info "部署到Kubernetes集群..."
    
    # 设置正确的kubectl context
    if [ "$REGION" = "china" ]; then
        kubectl config use-context smartrecipe-china
    else
        kubectl config use-context smartrecipe-us
    fi
    
    # 应用配置
    kubectl apply -f configs/$REGION/k8s/
    
    # 等待部署完成
    kubectl rollout status deployment/smartrecipe-backend -n smartrecipe
    kubectl rollout status deployment/smartrecipe-web -n smartrecipe
}

# 运行数据库迁移
run_migrations() {
    print_info "运行数据库迁移..."
    
    kubectl exec -it deployment/smartrecipe-backend -n smartrecipe -- \
        python -m alembic upgrade head
}

# 构建移动端应用
build_mobile_apps() {
    print_info "构建移动端应用..."
    
    # iOS构建
    if command -v xcodebuild >/dev/null 2>&1; then
        print_info "构建iOS应用..."
        cd mobile/ios
        REGION=$REGION xcodebuild -workspace SmartRecipe.xcworkspace \
            -scheme SmartRecipe \
            -configuration Release \
            archive
        cd ../..
    else
        print_warning "Xcode未安装，跳过iOS构建"
    fi
    
    # Android构建
    if [ -f "mobile/android/gradlew" ]; then
        print_info "构建Android应用..."
        cd mobile/android
        ./gradlew assemble${REGION^}Release
        cd ../..
    else
        print_warning "Android项目未配置，跳过Android构建"
    fi
}

# 健康检查
health_check() {
    print_info "执行健康检查..."
    
    if [ "$REGION" = "china" ]; then
        API_URL="https://api-cn.smartrecipe.com"
        WEB_URL="https://www.smartrecipe.cn"
    else
        API_URL="https://api-us.smartrecipe.com"
        WEB_URL="https://www.smartrecipe.com"
    fi
    
    # 检查API健康状态
    if curl -f -s "$API_URL/health" > /dev/null; then
        print_info "API健康检查通过"
    else
        print_error "API健康检查失败"
        exit 1
    fi
    
    # 检查Web站点
    if curl -f -s "$WEB_URL" > /dev/null; then
        print_info "Web站点健康检查通过"
    else
        print_error "Web站点健康检查失败"
        exit 1
    fi
}

# 主部署流程
main() {
    print_info "开始部署流程..."
    
    check_dependencies
    setup_environment
    build_images
    push_images
    update_k8s_config
    deploy_to_k8s
    run_migrations
    
    # 可选：构建移动端应用
    if [ "$ENVIRONMENT" = "production" ]; then
        build_mobile_apps
    fi
    
    # 等待服务启动
    sleep 30
    health_check
    
    print_info "部署完成！"
    print_info "API地址: $API_URL"
    print_info "Web地址: $WEB_URL"
}

# 执行主函数
main 