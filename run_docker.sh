#!/bin/bash
# 一键构建镜像并启动容器（无端口映射）

# 镜像与容器名
IMG_NAME="ast_analysis_service"
CONTAINER_NAME="ast_analysis_service"

# 构建镜像
docker build -t $IMG_NAME .

# 若已存在同名容器则先删除
docker rm -f $CONTAINER_NAME 2>/dev/null

# 启动容器（无端口映射，自动删除）
docker run -d --rm --name $CONTAINER_NAME $IMG_NAME
