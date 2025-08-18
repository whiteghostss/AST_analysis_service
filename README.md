# AST_analysis_service

## 项目简介

本项目为一个 Python 项目，专门分析一个固定的 Java 文件，自动完成以下流程：

1. 调用 comex 工具对 Java 文件进行 CFG/AST 分析；
2. 拆分所有控制流路径，每条路径生成独立的 json 文件（paths_json 目录）；
3. 自动提取方法 AST（output_ast.json）；
4. 对所有路径进行多维度打分与排序，终端输出详细得分和排序结果；
5. 无图片、dot 等无关输出，结构简洁，便于后续分析。

## 使用说明

1. 修改 `Target.java` 文件内容；
2. 一键运行分析脚本（推荐）：

   ```bash
   bash run_docker.sh
   ```

   该脚本会自动构建镜像并后台启动分析容器。

3. 查看分析输出：

   - 路径 json 文件保存在 `paths_json/` 目录下。
   - 方法 AST 结构保存在 `output_ast.json`。
   - 路径得分与排序结果会在容器终端输出，可通过以下命令查看：
     ```bash
     docker logs -f ast_analysis_service
     ```
   - 或者直接前台运行（便于实时查看输出）：
     ```bash
     docker run --rm ast_analysis_service
     ```

4. 也可手动构建和运行：
   ```bash
   docker build -t ast_analysis_service .
   docker run --rm ast_analysis_service
   ```

## 输出目录结构

```
AST_analysis_service/
├── main.py
├── Target.java
├── Dockerfile
├── README.md
├── output.json           # comex 生成的CFG
├── output_ast.json       # comex 生成的AST
└── paths_json/           # 拆分出的每条路径json
    ├── path_1.json
    ├── path_2.json
    └── ...
```

## 结果说明

- 所有路径的详细得分和排序会在终端输出。
- 每条路径的节点、边、长度等信息保存在 paths_json 目录下。
- 方法 AST 结构保存在 output_ast.json，便于后续分析。
