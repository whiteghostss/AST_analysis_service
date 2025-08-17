# AliPathMaker AST Backend

Java代码AST分析专用后端服务，基于FastAPI构建，专注于使用comex工具进行高质量的AST分析。

## 🚀 功能特性

- **文件上传与解压**：支持ZIP、TAR、RAR、7Z等多种压缩格式
- **源码分析**：智能提取Java方法源码
- **AST分析**：使用comex工具进行专业的AST结构分析
- **结果打包**：生成包含AST分析结果的ZIP文件
- **RESTful API**：标准化的API接口设计

## 🛠️ 技术栈

- **后端框架**：FastAPI + Uvicorn
- **AST分析工具**：comex（专业代码分析命令行工具）
- **文件处理**：zipfile、tarfile、rarfile、py7zr

## 📋 API接口

### 文件上传
- `POST /api/upload` - 上传Java源码文件或压缩包

### 源码分析
- `POST /api/list-methods` - 列出Java文件中的所有方法
- `POST /api/get-method-source` - 获取指定方法的源码

### AST分析
- `POST /api/analyze-ast` - 分析指定session的AST结构
- `GET /api/get-ast-result/{session_id}` - 获取AST分析结果

### 结果打包
- `POST /api/package-ast-result` - 打包AST分析结果
- `GET /api/download-ast-result/{session_id}` - 直接下载JSON结果
- `GET /api/list-ast-files/{session_id}` - 列出可用的分析文件

## 🔧 安装部署

### 环境要求
- Python 3.10+
- Docker（推荐）
- comex命令行工具（已包含在Docker镜像中）

### Docker部署（推荐）

```bash
bash deploy.sh
```

### 本地部署

```bash
# 安装依赖
pip install -r requirements.txt

# 安装comex命令行工具
pip install comex

# 验证comex安装
comex --help

# 启动服务
uvicorn main:app --host 0.0.0.0 --port 8000
```

