from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import utils
import zipfile
from datetime import datetime

class PackageRequest(BaseModel):
    sessionId: str
    ast_json: Optional[str] = None

router = APIRouter()

def get_safe_filename(name: str) -> str:
    """
    将字符串转换为安全的文件名，去除非法字符
    """
    # 替换非法文件名字符为下划线
    name = name.replace('\\', '_').replace('/', '_').replace(':', '_')
    name = name.replace('*', '_').replace('?', '_').replace('"', '_')
    name = name.replace('<', '_').replace('>', '_').replace('|', '_')
    # 限制长度
    if len(name) > 50:
        name = name[:47] + "..."
    return name

@router.post("/package-ast-result")
async def package_ast_result(data: PackageRequest):
    """
    打包AST分析结果为ZIP文件
    """
    sessionId = data.sessionId
    ast_json = data.ast_json or "ast_output.json"
    
    base_dir = os.path.abspath(os.path.join("results", sessionId))
    
    # 检查AST JSON文件是否存在
    ast_json_path = os.path.join(base_dir, ast_json)
    if not os.path.exists(ast_json_path):
        return JSONResponse(status_code=404, content={"error": f"AST分析结果文件不存在: {ast_json}"})
    
    # 检查PathAnalysis.java文件是否存在
    java_path = os.path.join(base_dir, "PathAnalysis.java")
    if not os.path.exists(java_path):
        return JSONResponse(status_code=404, content={"error": "PathAnalysis.java文件不存在"})
    
    # 生成ZIP文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"ast_analysis_{sessionId}_{timestamp}.zip"
    zip_path = os.path.join(base_dir, zip_filename)
    
    try:
        # 创建ZIP文件
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # 添加AST分析结果JSON文件
            zipf.write(ast_json_path, "ast_analysis.json")
            
            # 添加Java源码文件
            zipf.write(java_path, "PathAnalysis.java")
            
            # 检查是否有comex生成的额外文件
            extra_files = []
            for file_name in ['ast_output.png', 'ast_output.dot']:
                file_path = os.path.join(base_dir, file_name)
                if os.path.exists(file_path):
                    zipf.write(file_path, file_name)
                    extra_files.append(file_name)
            
            # 添加分析信息文件
            analysis_info = {
                "analysis_type": "AST Analysis",
                "session_id": sessionId,
                "analysis_time": datetime.now().isoformat(),
                "files_included": [
                    "ast_analysis.json",
                    "PathAnalysis.java"
                ] + extra_files,
                "description": "Java代码AST分析结果，包含语法树结构和源码",
                "has_visualization": len(extra_files) > 0
            }
            
            zipf.writestr("analysis_info.json", 
                         json.dumps(analysis_info, ensure_ascii=False, indent=2))
        
        # 返回ZIP文件下载链接
        zip_url = f"/results/{sessionId}/{zip_filename}"
        
        return {
            "zip_url": zip_url,
            "zip_filename": zip_filename,
            "message": "AST分析结果打包成功"
        }
        
    except Exception as e:
        print(f"打包AST结果失败: {e}")
        return JSONResponse(status_code=500, content={"error": f"打包失败: {str(e)}"})

@router.get("/download-ast-result/{session_id}")
async def download_ast_result(session_id: str):
    """
    直接下载指定session的AST分析结果JSON文件
    """
    try:
        ast_json_path = os.path.join("results", session_id, "ast_output.json")
        if not os.path.exists(ast_json_path):
            return JSONResponse(status_code=404, content={"error": "AST分析结果不存在"})
        
        return FileResponse(
            path=ast_json_path,
            filename=f"ast_analysis_{session_id}.json",
            media_type="application/json"
        )
        
    except Exception as e:
        print(f"下载AST结果失败: {e}")
        return JSONResponse(status_code=500, content={"error": f"下载失败: {str(e)}"})

@router.get("/list-ast-files/{session_id}")
async def list_ast_files(session_id: str):
    """
    列出指定session中可用的AST分析文件
    """
    try:
        base_dir = os.path.join("results", session_id)
        if not os.path.exists(base_dir):
            return JSONResponse(status_code=404, content={"error": "Session不存在"})
        
        available_files = []
        
        # 检查AST JSON文件
        ast_json_path = os.path.join(base_dir, "ast_output.json")
        if os.path.exists(ast_json_path):
            available_files.append({
                "filename": "ast_output.json",
                "type": "AST分析结果",
                "size": os.path.getsize(ast_json_path),
                "description": "Java代码的抽象语法树分析结果"
            })
        
        # 检查comex生成的AST可视化文件
        for file_name, file_type, description in [
            ("ast_output.png", "AST可视化图片", "comex生成的AST结构可视化图片"),
            ("ast_output.dot", "AST DOT文件", "comex生成的AST结构DOT格式文件")
        ]:
            file_path = os.path.join(base_dir, file_name)
            if os.path.exists(file_path):
                available_files.append({
                    "filename": file_name,
                    "type": file_type,
                    "size": os.path.getsize(file_path),
                    "description": description
                })
        
        # 检查Java源码文件
        java_path = os.path.join(base_dir, "PathAnalysis.java")
        if os.path.exists(java_path):
            available_files.append({
                "filename": "PathAnalysis.java",
                "type": "Java源码",
                "size": os.path.getsize(java_path),
                "description": "分析的目标Java方法源码"
            })
        
        return {
            "session_id": session_id,
            "available_files": available_files,
            "total_files": len(available_files)
        }
        
    except Exception as e:
        print(f"列出AST文件失败: {e}")
        return JSONResponse(status_code=500, content={"error": f"列出文件失败: {str(e)}"})

