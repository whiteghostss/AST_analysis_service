# =================================================================
#  阶段 1: 构建阶段 (Builder)
#  - 任务: 安装所有编译工具和依赖，准备好运行环境
# =================================================================
FROM python:3.10-slim AS builder

# 设置环境变量，避免生成 .pyc 文件并确保输出实时显示
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 1. 安装构建 comex 所需的 C 编译器 (build-essential)
# 2. 安装完整的 Java 开发工具包 (JDK)，用于编译 Java 代码
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential openjdk-17-jdk-headless && \
    rm -rf /var/lib/apt/lists/*

# 创建并激活一个 Python 虚拟环境，隔离项目依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制依赖描述文件
# 这一步会利用 Docker 的层缓存，只要 requirements.txt 不变，后续步骤不会重新执行
WORKDIR /app
COPY requirements.txt .

# 在虚拟环境中安装依赖
RUN pip install --no-cache-dir -r requirements.txt


# =================================================================
#  阶段 2: 最终运行阶段 (Final)
#  - 任务: 构建一个干净、轻量、安全用于生产运行的镜像
# =================================================================
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 1. 安装 Java 运行时环境 (JRE)
# 2. 明确安装 bash 以便调试
# 3. 清理 apt 缓存，减小镜像体积
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jre-headless bash && \
    rm -rf /var/lib/apt/lists/*

# 从构建阶段复制已经安装好依赖的虚拟环境
# 注意：编译工具 (gcc 等) 不会被复制过来
COPY --from=builder /opt/venv /opt/venv

# 复制应用程序源代码
COPY main.py Target.java ./

# 创建一个非 root 用户来运行应用，增强安全性
RUN useradd --create-home --shell /bin/bash appuser
RUN chown -R appuser:appuser /app
USER appuser

# 将虚拟环境的 bin 目录加入 PATH，这样可以直接执行 python
ENV PATH="/opt/venv/bin:$PATH"

# 设置容器默认执行的命令
CMD ["python", "main.py"]