import json
import os
import subprocess
from collections import deque

# ========== 路径打分辅助函数 ==========

_branch_types = set([
    "IfStatement", "SwitchStatement", "ConditionalExpression",
    "ForStatement", "WhileStatement", "DoStatement", "EnhancedForStatement",
    "TryStatement", "CatchClause",
    "if_statement", "switch_statement", "conditional_expression",
    "for_statement", "while_statement", "do_statement", "enhanced_for_statement",
    "try_statement", "catch_clause"
])
_assign_types = set([
    "Assignment", "AssignExpr", "VariableDeclarator", "VariableDeclarationFragment",
    "assignment", "assignment_expression", "variable_declarator", "local_variable_declaration"
])
_identifier_types = set([
    "SimpleName", "Identifier", "NameExpr", "identifier"
])
def _get_node_type(node):
    if not isinstance(node, dict):
        return None
    for k in ("type", "nodeType", "kind", "node_type"):
        t = node.get(k)
        if isinstance(t, str):
            return t
    return None
def _get_node_name(node):
    if not isinstance(node, dict):
        return None
    for key in ("name", "identifier", "methodName", "member", "id"):
        val = node.get(key)
        if isinstance(val, str) and val:
            return val
        if isinstance(val, dict):
            inner = val.get("identifier") or val.get("name")
            if isinstance(inner, str) and inner:
                return inner
    t = _get_node_type(node)
    if t in _identifier_types:
        lbl = node.get("label")
        if isinstance(lbl, str) and lbl:
            return lbl
    return None
def _iter_ast_nodes(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            for n in _iter_ast_nodes(v):
                yield n
    elif isinstance(obj, list):
        for item in obj:
            for n in _iter_ast_nodes(item):
                yield n
def _extract_identifiers(node):
    names = []
    for sub in _iter_ast_nodes(node):
        t = _get_node_type(sub)
        if t in _identifier_types or 'name' in sub:
            nm = _get_node_name(sub)
            if isinstance(nm, str) and nm:
                names.append(nm)
    return names
def _collect_assign_left_names(node):
    names = []
    for sub in _iter_ast_nodes(node):
        if not isinstance(sub, dict):
            continue
        t = _get_node_type(sub)
        if t in _assign_types:
            left = sub.get('left') or sub.get('lhs') or sub.get('name') or {}
            if isinstance(left, dict):
                nm = _get_node_name(left)
                if nm:
                    names.append(nm)
            elif isinstance(left, str):
                names.append(left)
            if not names:
                nm = _get_node_name(sub)
                if nm:
                    names.append(nm)
    return names
def _is_branch_node(node):
    t = _get_node_type(node)
    return t in _branch_types
def _extract_key_variables_from_ast(ast_root):
    key_vars = set()
    for node in _iter_ast_nodes(ast_root):
        if not isinstance(node, dict):
            continue
        t = _get_node_type(node)
        if t == 'MethodDeclaration' or t == 'method_declaration':
            params = node.get('parameters') or []
            if isinstance(params, list):
                for p in params:
                    nm = _get_node_name(p)
                    if nm:
                        key_vars.add(nm)
                    if isinstance(p, dict):
                        inner_nm = _get_node_name(p.get('name') or {})
                        if inner_nm:
                            key_vars.add(inner_nm)
        if t in ('ReturnStatement', 'ReturnExpr', 'Return', 'return_statement'):
            for nm in _extract_identifiers(node):
                if nm:
                    key_vars.add(nm)
    return key_vars
def _compute_scores_for_path(path_nodes, ast_root, key_vars):
    score_vars = 0.0
    score_branch = 0.0
    for n in path_nodes:
        # 赋值命中关键变量
        for lv in _collect_assign_left_names(n):
            if lv in key_vars:
                score_vars += 1.0
        # 分支结构
        if _is_branch_node(n):
            score_branch += 1.0
    score_length = float(len(path_nodes))
    return {
        'score_vars': float(score_vars),
        'score_branch': float(score_branch),
        'score_length': float(score_length)
    }
def _weighted_total(score_dict, weights=None):
    if weights is None:
        weights = {
            'score_vars': 0.5,
            'score_branch': 0.2,
            'score_length': 0.3,
        }
    total = 0.0
    for k, w in weights.items():
        total += float(score_dict.get(k, 0.0)) * float(w)
    return total

# ========== 主流程 ==========

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_all_paths(graph, start_node, end_nodes):
    paths = []
    queue = deque([(start_node, [start_node])])
    while queue:
        (node, path) = queue.popleft()
        if node in end_nodes:
            paths.append(path)
        else:
            next_nodes = sorted(graph.get(node, []))
            for next_node in next_nodes:
                if next_node not in path:
                    queue.append((next_node, path + [next_node]))
    return paths

def analyze_with_comex(java_file_path, output_json_path, output_ast_path):
    try:
        subprocess.run(
            ["comex", "--lang", "java", "--code-file", java_file_path, "--graphs", "cfg,ast", "--output", "all"],
            check=True,
            capture_output=True,
            text=True
        )
        if not os.path.exists(output_json_path):
            raise RuntimeError("comex 未生成 output.json")
        if not os.path.exists(output_ast_path):
            raise RuntimeError("comex 未生成 output_ast.json")
        print("comex 分析完成")
    except Exception as e:
        print("调用 comex 失败：", e)
        raise

def main():
    java_file = "Target.java"
    output_json = "output.json"
    output_ast = "output_ast.json"
    paths_json_dir = "paths_json"

    # 步骤1：调用 comex 生成 output.json（CFG）和 output_ast.json（AST）
    analyze_with_comex(java_file, output_json, output_ast)

    # 步骤2：读取 output.json，构建图
    data = load_json(output_json)
    nodes = data['nodes']
    links = data['links']
    nodes_info = {node['id']: node for node in nodes}

    # 构建邻接表
    graph = {}
    for link in links:
        src = link['source']
        tgt = link['target']
        graph.setdefault(src, []).append(tgt)

    # 找到所有起点和终点
    start_nodes = [node['id'] for node in nodes if node.get('type_label') == 'start']
    end_nodes = [node['id'] for node in nodes if node.get('type_label') == 'end']
    if not end_nodes:
        all_targets = set(link['target'] for link in links)
        all_sources = set(link['source'] for link in links)
        end_nodes = list(all_targets - all_sources)
        if not end_nodes:
            end_nodes = [nid for nid in nodes_info if nid not in graph]

    # 步骤3：拆分所有路径
    all_paths = []
    for start in start_nodes:
        paths = find_all_paths(graph, start, end_nodes)
        all_paths.extend(paths)

    # 步骤4：为每条路径生成 json 文件
    os.makedirs(paths_json_dir, exist_ok=True)
    for i, path in enumerate(all_paths):
        json_path = os.path.join(paths_json_dir, f'path_{i+1}.json')
        path_nodes_set = set(path)
        path_nodes = [nodes_info[nid] for nid in path]
        path_links = [link for link in links if link['source'] in path_nodes_set and link['target'] in path_nodes_set]
        path_data = {
            'nodes': path_nodes,
            'links': path_links,
            'path_length': len(path)
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(path_data, f, ensure_ascii=False, indent=2)

    # 步骤5：路径打分与排序
    ast_data = load_json(output_ast)
    key_variables = _extract_key_variables_from_ast(ast_data) if ast_data else set()
    path_scores = []
    path_score_details = []
    for path in all_paths:
        path_nodes = [nodes_info[nid] for nid in path]
        scores = _compute_scores_for_path(path_nodes, ast_data, key_variables)
        total = _weighted_total(scores)
        path_scores.append(total)
        path_score_details.append({**scores, "total": total})

    ranked_indices = sorted(range(len(path_scores)), key=lambda i: path_scores[i], reverse=True)
    print(f'共找到路径数: {len(all_paths)}')
    print(f'每条路径的json已保存在: {paths_json_dir}/')
    print(f'方法AST已保存在: {output_ast}')
    print("路径得分与排序如下：")
    for idx in ranked_indices:
        detail = path_score_details[idx]
        print(f"路径{idx+1} 总分: {detail['total']:.2f} (变量:{detail['score_vars']}, 分支:{detail['score_branch']}, 长度:{detail['score_length']}) 路径: {all_paths[idx]}")

if __name__ == "__main__":
    main()
