import os
import zipfile
import tarfile
import rarfile
import py7zr
import shutil
import uuid
from typing import Optional, List
import chardet

UPLOAD_ROOT = 'uploads'
RESULT_ROOT = 'results'

# 递归生成文件树JSON
def get_file_tree(dir_path: str, rel_path: str = "") -> dict:
    name = os.path.basename(dir_path) if rel_path == "" else os.path.basename(rel_path)
    node = {
        "name": name,
        "path": rel_path,
        "type": "directory" if os.path.isdir(dir_path) else "file"
    }
    if os.path.isdir(dir_path):
        node["children"] = []
        for entry in sorted(os.listdir(dir_path)):
            entry_path = os.path.join(dir_path, entry)
            entry_rel = os.path.join(rel_path, entry) if rel_path else entry
            node["children"].append(get_file_tree(entry_path, entry_rel))
    return node

# 提取Java文件中所有方法签名（简化版本，不使用javalang）
def get_java_methods(file_path: str) -> list:
    methods = []
    if not os.path.exists(file_path):
        return methods
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # 简单的正则表达式匹配方法签名
        import re
        lines = source.split('\n')
        class_stack = []
        
        for line in lines:
            line = line.strip()
            
            # 检测类声明
            class_match = re.search(r'class\s+(\w+)', line)
            if class_match:
                class_stack.append(class_match.group(1))
                continue
            
            # 检测方法声明
            method_match = re.search(r'(?:public|private|protected)?\s*(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?(?:native\s+)?(?:abstract\s+)?(?:strictfp\s+)?(?:<[^>]+>\s+)?(\w+(?:<[^>]+>)?)\s+(\w+)\s*\([^)]*\)', line)
            if method_match:
                return_type = method_match.group(1)
                method_name = method_match.group(2)
                
                # 构建方法签名
                class_name = '.'.join(class_stack) if class_stack else ''
                if class_name:
                    sig = f"{class_name}.{method_name}()"
                else:
                    sig = f"{method_name}()"
                methods.append(sig)
        
        # 如果没有找到方法，返回空列表
        return methods
        
    except Exception as e:
        print(f"解析Java方法失败: {e}")
        return methods

# 解压上传的压缩文件
def extract_zip(file_path: str) -> str:
    session_id = str(uuid.uuid4())
    extract_dir = os.path.join(UPLOAD_ROOT, session_id)
    os.makedirs(extract_dir, exist_ok=True)
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == ".zip":
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        elif ext in [".tar", ".gz", ".tar.gz", ".tgz"]:
            with tarfile.open(file_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_dir)
        elif ext == ".rar":
            with rarfile.RarFile(file_path, 'r') as rar_ref:
                rar_ref.extractall(extract_dir)
        elif ext == ".7z":
            with py7zr.SevenZipFile(file_path, 'r') as sz_ref:
                sz_ref.extractall(extract_dir)
        else:
            raise ValueError("暂不支持该压缩格式")
    except Exception as e:
        print(f"解压失败: {e}")
        raise
    
    # 删除原始压缩包
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"删除原始压缩包失败: {e}")
    
    return session_id, extract_dir

# 获取Java方法源码
def get_java_method_source_by_file(file_path: str, method_name: str) -> Optional[str]:
    if not os.path.exists(file_path):
        return None
    
    # 检测文件编码
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
    
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            source = f.read()
    except:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
    
    try:
        if '.' in method_name:
            class_part, method_part = method_name.split('.', 1)
            method_base = method_part.split('(')[0]
        else:
            class_part = None
            method_base = method_name.split('(')[0]
        
        # 使用简单的文本匹配来查找方法
        lines = source.splitlines()
        current_class = ""
        in_class = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # 检测类声明
            if 'class' in line and ('public' in line or line.startswith('class')):
                import re
                class_match = re.search(r'class\s+(\w+)', line)
                if class_match:
                    current_class = class_match.group(1)
                    in_class = True
                    continue
            
            # 检测方法声明
            if in_class and method_base in line and '(' in line and ')' in line:
                # 检查是否是方法声明
                if any(keyword in line for keyword in ['public', 'private', 'protected', 'static', 'final', 'void', 'int', 'String', 'boolean', 'double', 'float', 'long', 'short', 'byte', 'char']):
                    # 找到方法开始位置
                    start = i
                    end = start
                    brace_count = 0
                    found_opening_brace = False
                    
                    for j in range(start, len(lines)):
                        line_content = lines[j]
                        for char in line_content:
                            if char == '{':
                                brace_count += 1
                                found_opening_brace = True
                            elif char == '}':
                                brace_count -= 1
                        
                        if found_opening_brace and brace_count <= 0:
                            end = j
                            break
                    
                    return '\n'.join(lines[start:end+1])
    except Exception as e:
        print(f"解析Java方法源码失败: {e}")
    
    return None

# 保存源码到Java文件
def save_source_to_java_file(session_id: str, source: str, class_name: str = "PathAnalysis") -> str:
    output_dir = os.path.join(RESULT_ROOT, session_id)
    os.makedirs(output_dir, exist_ok=True)
    java_file = os.path.join(output_dir, f"{class_name}.java")
    
    source = source.strip()
    
    if source.startswith("public class") or source.startswith("class"):
        with open(java_file, "w", encoding="utf-8") as f:
            f.write(source)
    else:
        with open(java_file, "w", encoding="utf-8") as f:
            f.write(f"public class {class_name} {{\n")
            f.write(source)
            if not source.rstrip().endswith("}"):
                f.write("\n}")
            else:
                f.write("\n}")
    
    return java_file

# 打包文件为ZIP
def package_selected_files(zip_path: str, file_list: list, extra_texts: dict = None, base_dir: str = None):
    if base_dir:
        base_dir = os.path.abspath(base_dir)
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in file_list:
            if isinstance(file, tuple):
                abs_file, arcname = file
            else:
                abs_file = os.path.abspath(file)
                arcname = os.path.basename(file)
            if base_dir and not abs_file.startswith(base_dir):
                raise ValueError(f"文件 {abs_file} 不在指定目录 {base_dir} 下")
            zipf.write(abs_file, arcname)
        if extra_texts:
            for fname, content in extra_texts.items():
                zipf.writestr(fname, content)

def rename_ast_output_files(output_dir: str) -> bool:
    """
    重命名AST分析结果文件
    """
    try:
        ast_files = ['output.png', 'output.dot', 'output.json']
        ast_new_names = ['ast_output.png', 'ast_output.dot', 'ast_output.json']
        
        for old_name, new_name in zip(ast_files, ast_new_names):
            old_path = os.path.join(output_dir, old_name)
            new_path = os.path.join(output_dir, new_name)
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                print(f"重命名文件: {old_name} -> {new_name}")
        return True
    except Exception as e:
        print(f"重命名AST文件失败: {e}")
        return False

def validate_ast_output(output_dir: str) -> bool:
    """
    验证AST分析结果文件是否存在
    """
    ast_files = ['ast_output.png', 'ast_output.dot', 'ast_output.json']
    return all(os.path.exists(os.path.join(output_dir, f)) for f in ast_files)

def check_comex_available() -> bool:
    """
    检查comex工具是否可用
    """
    try:
        import subprocess
        print("检查comex工具可用性...")
        
        # 检查comex命令是否存在
        result = subprocess.run(['which', 'comex'], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            print("comex命令未找到在PATH中")
            return False
        
        comex_path = result.stdout.strip()
        print(f"找到comex命令: {comex_path}")
        
        # 检查comex帮助信息
        help_result = subprocess.run(['comex', '--help'], capture_output=True, text=True, timeout=10)
        if help_result.returncode != 0:
            print(f"comex帮助命令失败: {help_result.stderr}")
            return False
        
        print("comex工具检查通过")
        return True
        
    except subprocess.TimeoutExpired:
        print("comex工具检查超时")
        return False
    except FileNotFoundError:
        print("comex命令未找到")
        return False
    except subprocess.SubprocessError as e:
        print(f"comex工具检查异常: {e}")
        return False
    except Exception as e:
        print(f"comex工具检查失败: {e}")
        return False
