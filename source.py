from fastapi import APIRouter, Form
from fastapi.responses import JSONResponse
import os
import utils
from utils import save_source_to_java_file

router = APIRouter()

@router.post("/list-methods")
async def list_methods(sessionId: str = Form(...), filePath: str = Form(...)):
    if not filePath.lower().endswith(".java"):
        return JSONResponse(status_code=400, content={"error": "不是java源代码"})
    file_abs_path = os.path.join("uploads", sessionId, filePath)
    methods = utils.get_java_methods(file_abs_path)
    return {"methods": methods}


@router.post("/get-method-source")
async def get_method_source(sessionId: str = Form(...), filePath: str = Form(...), methodName: str = Form(...)):
    if not filePath.lower().endswith(".java"):
        return JSONResponse(status_code=400, content={"error": "不是java源代码"})
    file_abs_path = os.path.join("uploads", sessionId, filePath)
    source = utils.get_java_method_source_by_file(file_abs_path, methodName)
    if not source:
        return JSONResponse(status_code=404, content={"error": "Method not found"})
    
    # 清理旧的结果文件，确保不会使用之前的分析结果
    output_dir = os.path.join("results", sessionId)
    
    # 清理可能存在的旧文件
    try:
        # 删除已存在的输出文件
        for old_file in ['output.png', 'output.dot', 'output.json', 'PathAnalysis.java']:
            old_path = os.path.join(output_dir, old_file)
            if os.path.exists(old_path):
                os.remove(old_path)
                print(f"已删除旧文件: {old_path}")
                
        # 删除已存在的路径目录
        for old_dir in ['paths_dot', 'paths_img', 'paths_json']:
            old_dir_path = os.path.join(output_dir, old_dir)
            if os.path.exists(old_dir_path):
                for old_file in os.listdir(old_dir_path):
                    os.remove(os.path.join(old_dir_path, old_file))
                print(f"已清理目录: {old_dir_path}")
                
        # 删除可能存在的压缩包
        for old_archive in os.listdir(output_dir) if os.path.exists(output_dir) else []:
            if old_archive.endswith(('.zip', '.tar', '.gz', '.tar.gz')):
                os.remove(os.path.join(output_dir, old_archive))
                print(f"已删除旧压缩包: {old_archive}")
    except Exception as e:
        print(f"清理旧文件失败: {e}")
    
    # 保存源码到 results/{sessionId}/PathAnalysis.java
    file_path = save_source_to_java_file(sessionId, source, class_name="PathAnalysis")
    
    # 确保返回的是正确格式的JSON
    return JSONResponse(content={
        "source": source,
        "file": file_path
    })
