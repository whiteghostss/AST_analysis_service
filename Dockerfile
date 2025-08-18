# 基础镜像：带有 Python 和 OpenJDK
FROM python:3.10-slim

# 安装 OpenJDK 和编译工具
RUN apt-get update && \
    apt-get install -y openjdk-21-jre-headless build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 安装 comex
RUN pip install --no-cache-dir comex

# 复制 Python 脚本和 Java 文件
COPY main.py /app/main.py
COPY Target.java /app/Target.java

WORKDIR /app

# 设置容器入口点
CMD ["python", "main.py"]
