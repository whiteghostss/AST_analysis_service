from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import JSONResponse
import os
import utils
import json
import subprocess
from typing import Dict, Any, List

router = APIRouter()

def analyze_java_ast_with_comex(output_dir: str) -> Dict[str, Any]:
    """
    使用comex工具进行AST分析，返回分析结果
    """
    try:
        # 检查PathAnalysis.java文件是否存在
        java_file_path = os.path.join(output_dir, "PathAnalysis.java")
        if not os.path.exists(java_file_path):
            return {"error": f"PathAnalysis.java文件不存在: {java_file_path}"}
        
        print(f"开始comex AST分析，工作目录: {output_dir}")
        print(f"Java文件路径: {java_file_path}")
        
        # 执行comex AST分析
        ast_cmd = [
            'comex',
            '--lang', 'java',
            '--code-file', 'PathAnalysis.java',
            '--graphs', 'ast',
            '--output', 'all'
        ]
        
        print(f"执行comex AST分析命令: {' '.join(ast_cmd)}")
        
        # 执行AST分析
        result = subprocess.run(ast_cmd, check=True, timeout=60, cwd=output_dir, 
                              capture_output=True, text=True)
        print(f"comex AST分析完成，输出: {result.stdout}")
        
        # 重命名AST分析结果文件
        ast_files = ['output.png', 'output.dot', 'output.json']
        ast_new_names = ['ast_output.png', 'ast_output.dot', 'ast_output.json']
        
        for old_name, new_name in zip(ast_files, ast_new_names):
            old_path = os.path.join(output_dir, old_name)
            new_path = os.path.join(output_dir, new_name)
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                print(f"重命名文件: {old_name} -> {new_name}")
        
        # 读取AST分析结果
        ast_json_path = os.path.join(output_dir, "ast_output.json")
        if os.path.exists(ast_json_path):
            with open(ast_json_path, 'r', encoding='utf-8') as f:
                ast_data = json.load(f)
            
            # 添加comex分析信息
            ast_data["analysis_tool"] = "comex"
            ast_data["analysis_type"] = "AST"
            ast_data["output_files"] = {
                "json": "ast_output.json",
                "dot": "ast_output.dot",
                "png": "ast_output.png"
            }
            
            print(f"AST分析成功，JSON文件大小: {os.path.getsize(ast_json_path)} bytes")
            return ast_data
        else:
            return {"error": "comex AST分析完成但未生成JSON文件"}
            
    except subprocess.CalledProcessError as e:
        error_msg = f"comex AST分析失败: {str(e)}"
        if e.stderr:
            error_msg += f", 错误输出: {e.stderr}"
        print(error_msg)
        return {"error": error_msg}
    except subprocess.TimeoutExpired:
        error_msg = "comex AST分析超时"
        print(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"comex AST分析异常: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

@router.post("/analyze-ast")
async def analyze_ast(sessionId: str = Form(...)):
    """
    分析指定session的AST结构（与原后端保持一致）
    """
    try:
        if not sessionId:
            raise HTTPException(status_code=400, detail="sessionId为必填！")
        
        output_dir = os.path.join("results", sessionId)
        code_file = os.path.join(output_dir, "PathAnalysis.java")
        
        if not os.path.exists(code_file):
            return JSONResponse(status_code=404, content={"error": f"未找到Java文件: {code_file}"})
        
        # 清理旧的分析结果文件
        try:
            # 删除已存在的AST输出文件
            for old_file in ['ast_output.png', 'ast_output.dot', 'ast_output.json']:
                old_path = os.path.join(output_dir, old_file)
                if os.path.exists(old_path):
                    os.remove(old_path)
                    print(f"已删除旧文件: {old_path}")
        except Exception as e:
            print(f"清理旧文件失败: {e}")
        
        print(f"开始执行AST分析，使用文件: {code_file}")
        
        # 使用comex进行AST分析
        ast_result = analyze_java_ast_with_comex(output_dir)
        
        if "error" in ast_result:
            print(f"comex AST分析失败: {ast_result['error']}")
            return JSONResponse(status_code=500, content={"error": ast_result["error"]})
        
        print(f"comex AST分析完成，结果文件已生成")
        return {
            "ast_json": "ast_output.json",
            "analysis_status": "success",
            "ast_data": ast_result,
            "source_file": code_file,
            "analysis_tool": "comex"
        }
        
    except Exception as e:
        print(f"AST分析异常: {e}")
        return JSONResponse(status_code=500, content={"error": f"AST分析异常: {str(e)}"})

@router.get("/get-ast-result/{session_id}")
async def get_ast_result(session_id: str):
    """
    获取指定session的AST分析结果
    """
    try:
        ast_json_path = os.path.join("results", session_id, "ast_output.json")
        if not os.path.exists(ast_json_path):
            return JSONResponse(status_code=404, content={"error": "AST分析结果不存在"})
        
        with open(ast_json_path, 'r', encoding='utf-8') as f:
            ast_data = json.load(f)
        
        return {
            "ast_json": "ast_output.json",
            "analysis_status": "success",
            "ast_data": ast_data
        }
        
    except Exception as e:
        print(f"获取AST结果失败: {e}")
        return JSONResponse(status_code=500, content={"error": f"获取AST结果失败: {str(e)}"})

