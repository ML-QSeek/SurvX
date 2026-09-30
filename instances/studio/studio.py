#!/usr/bin/env python3
"""
AI 代码调试器 - Flask 服务（多项目版）
支持切换工作目录，每个项目独立维护版本
"""

import os
import json
import time
import subprocess
import requests
import logging
import re
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS

# ============================================================
# 配置
# ============================================================

class Config:
    HOST = os.environ.get("DEBUGGER_HOST", "0.0.0.0")
    PORT = int(os.environ.get("DEBUGGER_PORT", "9000"))
    
    GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://127.0.0.1:5000")
    AGENT_ID = os.environ.get("AGENT_ID", "agent-debugger")
    AGENT_MODEL = os.environ.get("AGENT_MODEL", "deepseek-chat")
    AGENT_QUOTA_DAILY = int(os.environ.get("AGENT_QUOTA_DAILY", "500000"))
    
    API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")
    
    # 总工作区目录
    WORKSPACE_ROOT = os.environ.get("WORKSPACE_ROOT", "./workspace")
    # 当前项目指针文件
    CURRENT_PROJECT_FILE = ".current"
    
    RUN_TIMEOUT = int(os.environ.get("RUN_TIMEOUT", "180"))

config = Config()

# ============================================================
# 日志配置
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('debugger')

# ============================================================
# Flask 应用
# ============================================================

app = Flask(__name__)
CORS(app)

# 确保 workspace 根目录存在
Path(config.WORKSPACE_ROOT).mkdir(parents=True, exist_ok=True)


# ============================================================
# 项目管理
# ============================================================

def get_current_project() -> str:
    """获取当前项目名"""
    current_file = Path(config.WORKSPACE_ROOT) / config.CURRENT_PROJECT_FILE
    if current_file.exists():
        project = current_file.read_text(encoding='utf-8').strip()
        # 验证项目是否存在
        project_path = Path(config.WORKSPACE_ROOT) / project
        if project_path.exists() and project_path.is_dir():
            return project
    # 默认项目
    return "default"


def set_current_project(project_name: str):
    """设置当前项目"""
    # 验证项目名合法性
    if not re.match(r'^[a-zA-Z0-9_\-.]+$', project_name):
        raise ValueError("项目名只能包含字母、数字、下划线、中划线、点")
    current_file = Path(config.WORKSPACE_ROOT) / config.CURRENT_PROJECT_FILE
    current_file.write_text(project_name, encoding='utf-8')


def get_project_path(project_name: str = None) -> Path:
    """获取项目目录路径"""
    if project_name is None:
        project_name = get_current_project()
    return Path(config.WORKSPACE_ROOT) / project_name


def ensure_project(project_name: str = None):
    """确保项目目录存在"""
    if project_name is None:
        project_name = get_current_project()
    project_path = get_project_path(project_name)
    project_path.mkdir(parents=True, exist_ok=True)
    return project_path


def list_projects() -> list:
    """列出所有项目"""
    workspace = Path(config.WORKSPACE_ROOT)
    projects = []
    for item in workspace.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # 检查目录是否包含有效内容（至少有一个版本文件）
            projects.append(item.name)
    # 按名称排序
    projects.sort()
    # 如果没有项目，创建 default
    if not projects:
        ensure_project("default")
        projects = ["default"]
    return projects


def get_current_version(project_name: str = None) -> int:
    """获取指定项目的当前最大版本号"""
    project_path = get_project_path(project_name) if project_name else get_project_path()
    version_file = project_path / "current_version.txt"
    if version_file.exists():
        try:
            return int(version_file.read_text().strip())
        except:
            return 0
    return 0


def set_current_version(v: int, project_name: str = None):
    """设置指定项目的当前版本号"""
    project_path = get_project_path(project_name) if project_name else get_project_path()
    version_file = project_path / "current_version.txt"
    version_file.write_text(str(v))


def get_code_file(version: int, project_name: str = None) -> Path:
    project_path = get_project_path(project_name) if project_name else get_project_path()
    return project_path / f"main_v{version}.py"


def get_log_file(version: int, project_name: str = None) -> Path:
    project_path = get_project_path(project_name) if project_name else get_project_path()
    return project_path / f"log_v{version}.txt"


def get_version_code(version: int, project_name: str = None) -> str:
    f = get_code_file(version, project_name)
    return f.read_text(encoding='utf-8') if f.exists() else ""


def get_version_log(version: int, project_name: str = None) -> str:
    f = get_log_file(version, project_name)
    return f.read_text(encoding='utf-8') if f.exists() else ""


def get_version_status(version: int, project_name: str = None) -> str:
    log = get_version_log(version, project_name)
    if not log:
        return "unknown"
    if "✅" in log or "运行成功" in log:
        return "success"
    if "❌" in log or "报错" in log or "Error" in log:
        return "error"
    if "⏰" in log or "超时" in log:
        return "timeout"
    return "unknown"


def save_code_version(version: int, code: str, project_name: str = None):
    f = get_code_file(version, project_name)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(code, encoding='utf-8')


def save_log_version(version: int, log: str, project_name: str = None):
    f = get_log_file(version, project_name)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(log, encoding='utf-8')


def get_context(project_name: str = None) -> str:
    project_path = get_project_path(project_name) if project_name else get_project_path()
    context_file = project_path / "context.txt"
    return context_file.read_text(encoding='utf-8') if context_file.exists() else ""


def save_context(content: str, project_name: str = None):
    project_path = get_project_path(project_name) if project_name else get_project_path()
    project_path.mkdir(parents=True, exist_ok=True)
    context_file = project_path / "context.txt"
    context_file.write_text(content, encoding='utf-8')


def get_project_files(project_name: str = None) -> list:
    """获取指定项目下的文件列表"""
    project_path = get_project_path(project_name) if project_name else get_project_path()
    if not project_path.exists():
        return []
    files = []
    for f in project_path.iterdir():
        if f.is_file() and f.name not in ['current_version.txt', 'context.txt', '.current']:
            files.append(f.name)
    # 按版本号排序
    def sort_key(name):
        match = re.search(r'_v(\d+)', name)
        if match:
            return int(match.group(1))
        return 0
    files.sort(key=sort_key)
    return files


# ============================================================
# 网关客户端
# ============================================================

class GatewayClient:
    def __init__(self, gateway_url: str, agent_id: str):
        self.gateway_url = gateway_url.rstrip('/')
        self.agent_id = agent_id
        self.registered = False
    
    def register(self) -> bool:
        try:
            url = f"{self.gateway_url}/api/agents/{self.agent_id}"
            payload = {
                "model": config.AGENT_MODEL,
                "quota_daily": config.AGENT_QUOTA_DAILY,
                "enabled": True
            }
            resp = requests.post(url, json=payload, timeout=5)
            if resp.status_code == 200:
                self.registered = True
                logger.info(f"✅ 向网关注册成功: {self.agent_id}")
                return True
            logger.warning(f"⚠️ 网关注册失败: {resp.text}")
            return False
        except Exception as e:
            logger.warning(f"⚠️ 网关注册异常: {e}")
            return False
    
    def report(self, data: dict) -> bool:
        try:
            url = f"{self.gateway_url}/api/report"
            resp = requests.post(url, json=data, timeout=3)
            return resp.status_code == 200
        except Exception:
            return False

gateway = GatewayClient(config.GATEWAY_URL, config.AGENT_ID)


# ============================================================
# 核心函数
# ============================================================

def extract_code_from_markdown(text: str) -> str:
    pattern = r'```(?:python)?\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        return '\n\n'.join(matches).strip()
    if text.strip().startswith('```'):
        lines = text.strip().split('\n')
        if len(lines) > 2:
            lines = lines[1:-1]
            return '\n'.join(lines).strip()
    return text.strip()


def call_api_write_code(prompt: str) -> str:
    try:
        resp = requests.post(
            f"{config.API_URL}/chat",
            json={
                "message": prompt,
                "system_prompt": "你是一个 Python 程序员。根据用户需求写 Python 代码。只输出代码，不要解释，不要用 markdown 代码块包裹。代码应该可以直接运行。",
                "model": config.AGENT_MODEL,
                "temperature": 0.3,
                "max_tokens": 4096,
                "auto_save_code": False
            },
            timeout=120
        )
        if resp.status_code != 200:
            return f"# API 调用失败: {resp.text}\nprint('API 调用失败')"
        data = resp.json()
        if not data.get("success"):
            return f"# API 返回错误: {data.get('error', '未知错误')}\nprint('API 返回错误')"
        return extract_code_from_markdown(data.get("content", ""))
    except Exception as e:
        return f"# API 调用异常: {e}\nprint('API 调用异常')"


def call_api_chat(message: str) -> str:
    try:
        resp = requests.post(
            f"{config.API_URL}/chat",
            json={
                "message": message,
                "system_prompt": "你是一个 AI 助手，帮助用户调试代码和回答问题。",
                "model": config.AGENT_MODEL,
                "temperature": 0.7,
                "max_tokens": 4096,
                "auto_save_code": False
            },
            timeout=120
        )
        if resp.status_code != 200:
            return f"API 调用失败: {resp.text}"
        data = resp.json()
        if not data.get("success"):
            return f"API 返回错误: {data.get('error', '未知错误')}"
        return data.get("content", "")
    except Exception as e:
        return f"请求失败: {str(e)}"


def run_python_code(code: str, version: int, project_name: str = None) -> tuple:
    """执行 Python 代码，返回 (log, status, elapsed_ms)"""
    code_file = get_code_file(version, project_name)
    log_file = get_log_file(version, project_name)
    
    # 确保项目目录存在
    code_file.parent.mkdir(parents=True, exist_ok=True)
    code_file.write_text(code, encoding='utf-8')
    logger.info(f"📝 保存代码: {code_file}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            ["python", str(code_file)],
            capture_output=True,
            text=True,
            timeout=config.RUN_TIMEOUT,
            cwd=str(code_file.parent)
        )
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        log_content = ""
        if result.stdout:
            log_content += result.stdout
        if result.stderr:
            if log_content:
                log_content += "\n"
            log_content += result.stderr
        
        status = "success" if result.returncode == 0 else "error"
        log_file.write_text(log_content, encoding='utf-8')
        logger.info(f"📋 保存日志: {log_file} (状态: {status}, 耗时: {elapsed_ms}ms)")
        return log_content, status, elapsed_ms
        
    except subprocess.TimeoutExpired:
        elapsed_ms = int((time.time() - start_time) * 1000)
        log_content = f"⏰ 代码运行超时（超过 {config.RUN_TIMEOUT} 秒）"
        log_file.write_text(log_content, encoding='utf-8')
        return log_content, "timeout", elapsed_ms
    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        log_content = f"❌ 运行异常: {str(e)}"
        log_file.write_text(log_content, encoding='utf-8')
        return log_content, "error", elapsed_ms


# ============================================================
# API 端点
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')


# ---------- 项目管理 ----------
@app.route('/api/projects', methods=['GET'])
def api_list_projects():
    """列出所有项目"""
    return jsonify({
        'success': True,
        'projects': list_projects(),
        'current': get_current_project()
    })


@app.route('/api/projects/current', methods=['GET'])
def api_get_current_project():
    """获取当前项目"""
    return jsonify({
        'success': True,
        'project': get_current_project()
    })


@app.route('/api/projects/switch', methods=['POST'])
def api_switch_project():
    """切换项目"""
    data = request.get_json()
    project_name = data.get('project', '').strip()
    
    if not project_name:
        return jsonify({'success': False, 'error': '项目名不能为空'}), 400
    
    # 验证项目是否存在
    project_path = get_project_path(project_name)
    if not project_path.exists() or not project_path.is_dir():
        return jsonify({'success': False, 'error': f'项目 "{project_name}" 不存在'}), 404
    
    set_current_project(project_name)
    logger.info(f"🔄 切换到项目: {project_name}")
    
    total = get_current_version()
    return jsonify({
        'success': True,
        'project': project_name,
        'total_versions': total,
        'current_version': total
    })


@app.route('/api/projects/create', methods=['POST'])
def api_create_project():
    """创建新项目"""
    data = request.get_json()
    project_name = data.get('project', '').strip()
    
    if not project_name:
        return jsonify({'success': False, 'error': '项目名不能为空'}), 400
    
    if not re.match(r'^[a-zA-Z0-9_\-.]+$', project_name):
        return jsonify({'success': False, 'error': '项目名只能包含字母、数字、下划线、中划线、点'}), 400
    
    project_path = get_project_path(project_name)
    if project_path.exists():
        return jsonify({'success': False, 'error': f'项目 "{project_name}" 已存在'}), 400
    
    project_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"🆕 创建项目: {project_name}")
    
    return jsonify({
        'success': True,
        'project': project_name
    })


# ---------- 状态 ----------
@app.route('/api/status', methods=['GET'])
def get_status():
    """获取当前项目的状态"""
    project = get_current_project()
    total = get_current_version()
    return jsonify({
        'success': True,
        'total_versions': total,
        'current_version': total,
        'project': project
    })


@app.route('/api/version/<int:v>', methods=['GET'])
def get_version(v: int):
    """获取指定版本的代码和日志"""
    if v < 1:
        return jsonify({'success': False, 'error': '版本号从 1 开始'}), 400
    
    code = get_version_code(v)
    log = get_version_log(v)
    status = get_version_status(v)
    
    if not code and not log:
        return jsonify({'success': False, 'error': f'版本 {v} 不存在'}), 404
    
    return jsonify({
        'success': True,
        'version': v,
        'code': code,
        'log': log,
        'status': status
    })


# ---------- 背景要求 ----------
@app.route('/api/context', methods=['GET'])
def get_context_api():
    return jsonify({
        'success': True,
        'content': get_context()
    })


@app.route('/api/context', methods=['POST'])
def save_context_api():
    data = request.get_json()
    content = data.get('content', '')
    save_context(content)
    return jsonify({'success': True, 'message': '已保存'})


# ---------- 文件列表 ----------
@app.route('/api/files', methods=['GET'])
def list_files():
    return jsonify({
        'success': True,
        'files': get_project_files()
    })


@app.route('/api/file/<filename>', methods=['GET'])
def get_file(filename):
    """获取项目中的文件内容"""
    project_path = get_project_path()
    filepath = project_path / filename
    if not filepath.exists():
        return jsonify({'success': False, 'error': '文件不存在'}), 404
    content = filepath.read_text(encoding='utf-8')
    return jsonify({
        'success': True,
        'filename': filename,
        'content': content
    })


# ---------- 核心操作 ----------
@app.route('/api/send', methods=['POST'])
def send():
    """「发送」按钮"""
    data = request.get_json()
    mode = data.get('mode', 'code')
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'success': False, 'error': '请输入内容'}), 400
    
    project = get_current_project()
    
    if mode == 'chat':
        reply = call_api_chat(content)
        return jsonify({
            'success': True,
            'mode': 'chat',
            'content': reply
        })
    
    current_v = get_current_version()
    if current_v == 0:
        prompt = f"请写一个 Python 脚本，实现以下功能：\n{content}\n\n只输出代码，不要解释，不要用 markdown 包裹。"
    else:
        current_code = get_version_code(current_v)
        current_log = get_version_log(current_v)
        prompt = f"""你之前写的代码，现在用户提出了新需求，请修改代码：

【当前代码】
{current_code}

【运行日志】
{current_log if current_log else '（无日志）'}

【用户需求】
{content}

请只输出修改后的完整 Python 代码，不要解释，不要用 markdown 包裹。"""
    
    new_version = current_v + 1
    code = call_api_write_code(prompt)
    log, status, elapsed_ms = run_python_code(code, new_version, project)
    set_current_version(new_version)
    
    gateway.report({
        "agent_id": config.AGENT_ID,
        "model": config.AGENT_MODEL,
        "prompt_tokens": len(prompt) // 2,
        "completion_tokens": len(code) // 2,
        "total_tokens": (len(prompt) + len(code)) // 2,
        "latency_ms": elapsed_ms,
        "status_code": 200 if status == "success" else 500,
        "error_msg": "" if status == "success" else log[:200]
    })
    
    return jsonify({
        'success': True,
        'mode': 'code',
        'version': new_version,
        'total_versions': new_version,
        'code': code,
        'log': log,
        'status': status,
        'elapsed_ms': elapsed_ms
    })


@app.route('/api/fix', methods=['POST'])
def fix():
    """「提交代码」按钮"""
    data = request.get_json()
    code = data.get('code', '').strip()
    log = data.get('log', '').strip()
    instruction = data.get('instruction', '').strip()
    mode = data.get('mode', 'code')
    
    if not instruction:
        return jsonify({'success': False, 'error': '请输入内容'}), 400
    
    project = get_current_project()
    context = get_context()
    context_text = f"\n\n【背景要求】\n{context}" if context else ""
    
    if mode == 'chat':
        prompt = f"""用户想和你讨论代码，请根据以下信息回答：

【当前代码】
{code if code else '（无代码）'}

【运行日志】
{log if log else '（无日志）'}{context_text}

【用户问题】
{instruction}

请给出详细的回答和建议。"""
        
        reply = call_api_chat(prompt)
        return jsonify({
            'success': True,
            'mode': 'chat',
            'content': reply
        })
    
    if not code:
        return jsonify({'success': False, 'error': '代码不能为空'}), 400
    
    prompt = f"""你之前写的代码运行后产生了以下结果，请修复或修改代码：

【当前代码】
{code}

【运行日志】
{log if log else '（无日志）'}{context_text}

【用户指令】
{instruction}

请只输出修正后的完整 Python 代码，不要解释，不要用 markdown 包裹。"""
    
    new_version = get_current_version() + 1
    new_code = call_api_write_code(prompt)
    new_log, status, elapsed_ms = run_python_code(new_code, new_version, project)
    set_current_version(new_version)
    
    gateway.report({
        "agent_id": config.AGENT_ID,
        "model": config.AGENT_MODEL,
        "prompt_tokens": len(prompt) // 2,
        "completion_tokens": len(new_code) // 2,
        "total_tokens": (len(prompt) + len(new_code)) // 2,
        "latency_ms": elapsed_ms,
        "status_code": 200 if status == "success" else 500,
        "error_msg": "" if status == "success" else new_log[:200]
    })
    
    return jsonify({
        'success': True,
        'mode': 'code',
        'version': new_version,
        'total_versions': new_version,
        'code': new_code,
        'log': new_log,
        'status': status,
        'elapsed_ms': elapsed_ms
    })


@app.route('/api/run', methods=['POST'])
def run():
    """代码框「运行」按钮"""
    data = request.get_json()
    code = data.get('code', '').strip()
    
    if not code:
        return jsonify({'success': False, 'error': '代码不能为空'}), 400
    
    project = get_current_project()
    new_version = get_current_version() + 1
    log, status, elapsed_ms = run_python_code(code, new_version, project)
    set_current_version(new_version)
    
    gateway.report({
        "agent_id": config.AGENT_ID,
        "model": config.AGENT_MODEL,
        "prompt_tokens": len(code) // 2,
        "completion_tokens": 0,
        "total_tokens": len(code) // 2,
        "latency_ms": elapsed_ms,
        "status_code": 200 if status == "success" else 500,
        "error_msg": "" if status == "success" else log[:200]
    })
    
    return jsonify({
        'success': True,
        'version': new_version,
        'total_versions': new_version,
        'code': code,
        'log': log,
        'status': status,
        'elapsed_ms': elapsed_ms
    })


@app.route('/api/workspace/<path:filename>', methods=['GET'])
def get_workspace_file(filename):
    filepath = Path(config.WORKSPACE_ROOT) / filename
    if not filepath.exists():
        return jsonify({'success': False, 'error': '文件不存在'}), 404
    return send_file(filepath, as_attachment=False)


# ============================================================
# 启动
# ============================================================

def main():
    # 确保默认项目存在
    ensure_project("default")
    set_current_project("default")
    
    gateway.register()
    
    print("=" * 60)
    print("🤖 AI 代码调试器（多项目版）")
    print("=" * 60)
    print(f"📡 服务地址: http://{config.HOST}:{config.PORT}")
    print(f"🔗 网关地址: {config.GATEWAY_URL}")
    print(f"🤖 Agent ID: {config.AGENT_ID}")
    print(f"📂 工作区: {config.WORKSPACE_ROOT}")
    print(f"📁 当前项目: {get_current_project()}")
    print(f"⏰ 运行超时: {config.RUN_TIMEOUT} 秒")
    print("=" * 60)
    
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=False,
        threaded=True
    )


if __name__ == "__main__":
    main()