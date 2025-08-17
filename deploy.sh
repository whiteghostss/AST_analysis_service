#!/bin/bash

echo "开始部署 AliPathMaker AST Backend..."

# 停止并删除旧容器
echo "停止旧容器..."
docker rm -f alipathmaker-ast-backend 2>/dev/null || true

# 构建新镜像
echo "构建Docker镜像..."
docker build -t alipathmaker-ast-backend .

# 运行新容器
echo "启动新容器..."
docker run -d \
    --name alipathmaker-ast-backend \
    -p 8000:8000 \
    -v $(pwd)/uploads:/app/uploads \
    -v $(pwd)/results:/app/results \
    alipathmaker-ast-backend

echo "部署完成！"
echo "服务地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "查看日志: docker logs -f alipathmaker-ast-backend"
echo "停止服务: docker stop alipathmaker-ast-backend"

