from fastapi import APIRouter, UploadFile, File
import os
import shutil
import utils

router = APIRouter()

@router.post("/upload")
async def upload_project(file: UploadFile = File(...)):
    UPLOAD_DIR = "uploads"
    # 支持的压缩包类型
    allowed_exts = [".zip", ".tar", ".gz", ".tar.gz", ".tgz", ".rar", ".7z"]
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_exts:
        print(f"上传文件类型不支持: {filename}")
        return {"error": f"暂只支持以下格式压缩包: {', '.join(allowed_exts)}"}
    try:
        file_location = os.path.join(UPLOAD_DIR, filename)
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)
        print(f"已保存上传文件: {file_location}")
        
        # 解压文件
        session_id, extract_dir = utils.extract_zip(file_location)
        print(f"已解压到: {extract_dir}, sessionId: {session_id}")
        
        # 生成文件树
        try:
            file_tree = utils.get_file_tree(extract_dir)
            if not file_tree or (isinstance(file_tree, dict) and not file_tree.get('children')):
                print(f"警告: 生成的文件树为空，可能解压失败或编码问题")
                # 尝试重新扫描目录
                if os.path.exists(extract_dir):
                    print(f"重新扫描目录: {extract_dir}")
                    # 强制重新扫描目录结构
                    file_tree = utils.get_file_tree(extract_dir)
        except Exception as tree_error:
            print(f"生成文件树失败: {tree_error}")
            # 尝试返回简化的文件树
            file_tree = {
                "name": os.path.basename(extract_dir),
                "path": "",
                "type": "directory",
                "children": [{"name": "解析文件树失败，请检查压缩包格式", "path": "", "type": "file"}]
            }
        
        return {"sessionId": session_id, "fileTree": file_tree}
    except Exception as e:
        print(f"上传或解压失败: {e}")
        return {"error": f"上传或解压失败: {str(e)}"}
