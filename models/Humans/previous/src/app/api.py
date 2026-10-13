import webview
import sys
import json
import threading
import base64
import os
from datetime import datetime
import subprocess
import tempfile
from pathlib import Path
import shutil
import signal
import sqlite3
import math
import time

class Api:
    def __init__(self):
        self._window_manager = None
        self._running_processes = {}  # instance_name -> dict with processes and channel_id
    
    def set_window_manager(self, manager):
        """设置WindowManager引用"""
        self._window_manager = manager
    
    def get_window(self):
        """安全获取窗口对象"""
        try:
            if self._window_manager and hasattr(self._window_manager, 'window'):
                return self._window_manager.window
            
            if webview.windows:
                return webview.windows[0]
            
            return None
        except Exception as e:
            print(f"获取窗口失败: {e}")
            return None
    
    def minimize_window(self):
        """最小化窗口"""
        window = self.get_window()
        if window:
            try:
                window.minimize()
            except Exception as e:
                print(f"最小化窗口失败: {e}")
    
    def maximize_window(self):
        """最大化窗口"""
        window = self.get_window()
        if window:
            try:
                window.maximize()
            except Exception as e:
                print(f"最大化窗口失败: {e}")
    
    def restore_window(self):
        """恢复窗口"""
        window = self.get_window()
        if window:
            try:
                window.restore()
            except Exception as e:
                print(f"恢复窗口失败: {e}")
    
    def close_window(self):
        """关闭窗口"""
        # 先停止所有运行的实例
        for instance_name in list(self._running_processes.keys()):
            self.stop_instance(instance_name)
        
        window = self.get_window()
        if window:
            try:
                window.destroy()
            except Exception as e:
                print(f"关闭窗口失败: {e}")
    
    def login(self, user_data):
        """处理登录请求"""
        if self._window_manager:
            return self._window_manager.handle_login(user_data)
        return {"success": False, "message": "系统错误"}
    
    def get_saved_credentials(self):
        """获取保存的登录凭证"""
        if self._window_manager:
            return self._window_manager.get_saved_credentials()
        return {"has_saved": False, "username": "", "rememberPassword": False, "autoLogin": False}
    
    def clear_saved_credentials(self):
        """清除保存的登录凭证"""
        if self._window_manager:
            return self._window_manager.clear_saved_credentials()
        return {"success": False}
    
    def load_main_page(self):
        """加载主页面（供JavaScript调用）"""
        if self._window_manager:
            threading.Thread(target=self._window_manager.load_main_page, daemon=True).start()
            return {"success": True, "message": "正在加载主页面..."}
        return {"success": False, "message": "系统错误"}
    
    def center_window(self):
        """居中窗口（供JavaScript调用）"""
        if self._window_manager:
            threading.Thread(target=self._window_manager.center_window, daemon=True).start()
            return {"success": True, "message": "正在居中窗口..."}
        return {"success": False, "message": "系统错误"}
    
    def get_files_in_directory(self, relative_path):
        """
        获取指定相对目录下的所有非目录文件名
        
        Args:
            relative_path (str): 相对路径目录
            
        Returns:
            dict: 包含成功状态和文件列表的字典
                {
                    "success": bool,
                    "files": list,  # 文件名列表
                    "message": str  # 错误信息（如果失败）
                }
        """
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            target_dir = os.path.join(current_dir, relative_path)
            
            if not os.path.exists(target_dir):
                return {
                    "success": False,
                    "files": [],
                    "message": f"目录不存在: {relative_path}"
                }
            
            if not os.path.isdir(target_dir):
                return {
                    "success": False,
                    "files": [],
                    "message": f"路径不是目录: {relative_path}"
                }
            
            files = []
            for item in os.listdir(target_dir):
                item_path = os.path.join(target_dir, item)
                if os.path.isfile(item_path):
                    files.append(item)
            
            return {
                "success": True,
                "files": files,
                "message": f"成功获取 {len(files)} 个文件"
            }
            
        except PermissionError:
            return {
                "success": False,
                "files": [],
                "message": f"没有权限访问目录: {relative_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "files": [],
                "message": f"获取文件列表失败: {str(e)}"
            }

    def get_subdirectories_in_directory(self, relative_path):
        """
        获取指定相对目录下的所有子目录名
        
        Args:
            relative_path (str): 相对路径目录
            
        Returns:
            dict: 包含成功状态和子目录列表的字典
                {
                    "success": bool,
                    "directories": list,  # 子目录名列表
                    "message": str       # 错误信息（如果失败）
                }
        """
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            target_dir = os.path.join(current_dir, relative_path)
            
            if not os.path.exists(target_dir):
                return {
                    "success": False,
                    "directories": [],
                    "message": f"目录不存在: {relative_path}"
                }
            
            if not os.path.isdir(target_dir):
                return {
                    "success": False,
                    "directories": [],
                    "message": f"路径不是目录: {relative_path}"
                }
            
            directories = []
            for item in os.listdir(target_dir):
                item_path = os.path.join(target_dir, item)
                if os.path.isdir(item_path):
                    directories.append(item)
            
            return {
                "success": True,
                "directories": directories,
                "message": f"成功获取 {len(directories)} 个子目录"
            }
            
        except PermissionError:
            return {
                "success": False,
                "directories": [],
                "message": f"没有权限访问目录: {relative_path}"
            }
        except Exception as e:
            return {
                "success": False,
                "directories": [],
                "message": f"获取子目录列表失败: {str(e)}"
            }
        
    def decouple_field_ego(self, instance_name):
        """
        解耦指定实例：将 instance_name 下的 field_*.db 和 ego_*.db 复制到对应目录，
        并生成 JSON 元数据文件供前端使用。
        
        返回值:
        {
            "success": True/False,
            "message": "提示信息",
            "data": {
                "field": {"db": "路径", "json": "路径", "name": "名称"},
                "egos": [{"db": "路径", "json": "路径", "name": "名称"}, ...]
            }
        }
        """
        base_data_dir = Path("../data/instance") / instance_name
        s_field_dir = Path("../data/s_field")
        s_ego_dir = Path("../data/s_ego")
        ui_field_dir = Path("../ui/data/s_field")
        ui_ego_dir = Path("../ui/data/s_ego")
        
        if not base_data_dir.exists():
            return {
                "success": False,
                "message": f"实例目录不存在: {base_data_dir}",
                "data": None
            }
        
        s_field_dir.mkdir(parents=True, exist_ok=True)
        s_ego_dir.mkdir(parents=True, exist_ok=True)
        ui_field_dir.mkdir(parents=True, exist_ok=True)
        ui_ego_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        result_data = {
            "field": None,
            "egos": []
        }
        
        for file_path in base_data_dir.iterdir():
            if not file_path.is_file():
                continue
            
            filename = file_path.name
            
            if filename.startswith("field_") and filename.endswith(".db"):
                result = self._copy_and_export(
                    file_path=file_path,
                    filename=filename,
                    instance_name=instance_name,
                    timestamp=timestamp,
                    data_target_dir=s_field_dir,
                    ui_target_dir=ui_field_dir,
                    prefix="field_"
                )
                if result:
                    result_data["field"] = result
            
            elif filename.startswith("ego_") and filename.endswith(".db"):
                result = self._copy_and_export(
                    file_path=file_path,
                    filename=filename,
                    instance_name=instance_name,
                    timestamp=timestamp,
                    data_target_dir=s_ego_dir,
                    ui_target_dir=ui_ego_dir,
                    prefix="ego_"
                )
                if result:
                    result_data["egos"].append(result)
        
        if result_data["field"] is None and len(result_data["egos"]) == 0:
            return {
                "success": False,
                "message": f"实例 {instance_name} 中没有找到 field_*.db 或 ego_*.db 文件",
                "data": None
            }
        
        return {
            "success": True,
            "message": f"实例 {instance_name} 解耦成功！field: {1 if result_data['field'] else 0} 个，ego: {len(result_data['egos'])} 个",
            "data": result_data
        }
        
    def _copy_and_export(self, file_path, filename, instance_name, timestamp, data_target_dir, ui_target_dir, prefix):
        """
        拷贝 .db 文件并生成对应的 .json 元数据
        """
        try:
            base_name = filename[:-3]
            new_filename = f"{base_name}_{instance_name}_{timestamp}.db"
            new_filepath = data_target_dir / new_filename
            
            shutil.copy2(file_path, new_filepath)
            
            original_name = filename[len(prefix):-3]
            
            json_file_path = ui_target_dir / f"{filename[:-3]}.json"
            img_field = ""
            if json_file_path.exists():
                try:
                    with open(json_file_path, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        img_field = json_data.get("img", "")
                except Exception as e:
                    print(f"读取 JSON 文件失败: {json_file_path}, 错误: {e}")
            else:
                print(f"未找到对应的 JSON 文件: {json_file_path}，img 字段留空")
            
            metadata = {
                "name": original_name,
                "note": new_filename,
                "img": img_field
            }
            
            json_output_path = ui_target_dir / f"{base_name}_{instance_name}_{timestamp}.json"
            with open(json_output_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            return {
                "db": str(new_filepath),
                "json": str(json_output_path),
                "name": original_name
            }
        
        except Exception as e:
            print(f"解耦文件失败: {filename}, 错误: {e}")
            return None
        
    #创建实例
    def create_instance(self, config: dict):
        """
        创建实例
        
        Args:
            config: {
                "instance": str,        # 实例名称
                "field": str,           # 场域JSON文件名 (如 field_01.json)
                "ego": list[str],       # 人物JSON文件名列表 (如 ["ego_01.json", "ego_02.json"])
                "note": str,            # 实例简介
                "image": str            # 封面图片文件名
            }
        
        Returns:
            dict: {
                "success": bool,
                "message": str          # 成功或错误信息
            }
        """   
        try:
            instance_name = config.get("instance", "").strip()
            field_json = config.get("field", "")
            ego_list = config.get("ego", [])
            note = config.get("note", "")
            image = config.get("image", "")
    
            if not instance_name:
                return {"success": False, "message": "实例名称不能为空"}
            if not field_json:
                return {"success": False, "message": "场域文件不能为空"}
            if not ego_list or len(ego_list) == 0:
                return {"success": False, "message": "至少选择一个人物"}
    
            base_data_dir = Path("../data/instance")
            instance_dir = base_data_dir / instance_name
    
            if instance_dir.exists():
                return {"success": False, "message": f"实例 '{instance_name}' 已存在"}
    
            instance_dir.mkdir(parents=True, exist_ok=False)
            
            field_db = field_json.replace(".json", ".db")
            field_db_path = Path("../data/s_field") / field_db
            if not field_db_path.exists():
                return {"success": False, "message": f"场域数据库文件不存在: {field_db}"}
    
            shutil.copy2(field_db_path, instance_dir / field_db)
    
            for ego_json in ego_list:
                ego_db = ego_json.replace(".json", ".db")
                ego_db_path = Path("../data/s_ego") / ego_db
                if not ego_db_path.exists():
                    return {"success": False, "message": f"人物数据库文件不存在: {ego_db}"}
                shutil.copy2(ego_db_path, instance_dir / ego_db)
    
            ui_instance_dir = Path("../ui/data/instance")
            ui_instance_dir.mkdir(parents=True, exist_ok=True)
            
            meta_data = {
                "name": instance_name,
                "note": note,
                "img": image
            }
            
            meta_file = ui_instance_dir / f"{instance_name}.json"
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=2)
    
            return {"success": True, "message": f"实例 '{instance_name}' 创建成功"}
    
        except FileExistsError:
            return {"success": False, "message": f"实例 '{instance_name}' 已存在"}
        except PermissionError as e:
            return {"success": False, "message": f"权限错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"创建实例失败: {str(e)}"}

    # ================================================================
    # 启动实例
    # ================================================================
    
    def start_instance(self, instance_name: str):
        """
        启动实例: 启动 field.py，通过 HTTP 获取 channel_id，再启动 ego.py
        """
        try:
            instance_dir = Path("../data/instance") / instance_name
    
            if not instance_dir.exists():
                return {"success": False, "message": f"实例目录不存在: {instance_name}"}
    
            if instance_name in self._running_processes:
                self.stop_instance(instance_name)
    
            # 扫描 db 文件
            db_files = []
            for f in instance_dir.iterdir():
                if f.is_file() and f.name.endswith('.db'):
                    db_files.append(f)
    
            if not db_files:
                return {"success": False, "message": f"实例目录下没有 .db 文件: {instance_name}"}
    
            field_db = None
            ego_dbs = []
            for f in db_files:
                if f.name.startswith('field_'):
                    field_db = f
                elif f.name.startswith('ego_'):
                    ego_dbs.append(f)
    
            if field_db is None:
                return {"success": False, "message": f"实例目录下没有 field_*.db 文件: {instance_name}"}
    
            current_dir = Path(__file__).resolve().parent
            src_dir = current_dir.parent
            utils_dir = src_dir / 'utils'
    
            # 启动 field.py（不捕获输出）
            field_cmd = [
                sys.executable,
                str(utils_dir / 'field.py'),
                instance_name,
                '127.0.0.1',
                '8765'
            ]
    
            print(f"[API] 启动 field: {' '.join(field_cmd)}")
    
            field_proc = subprocess.Popen(
                field_cmd,
                stdout=None,
                stderr=None,
            )
    
            # 通过 HTTP 查询 channel_id
            import requests
            channel_id = None
            server_url = f"http://127.0.0.1:8766/api/channel/{instance_name}"
            
            for i in range(30):  # 最多等待 15 秒
                time.sleep(0.5)
                try:
                    resp = requests.get(server_url, timeout=1)
                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get('success') and data.get('channel_id') is not None:
                            channel_id = data['channel_id']
                            break
                except:
                    pass
    
            if channel_id is None:
                field_proc.terminate()
                return {"success": False, "message": "无法获取 channel_id"}
    
            print(f"[API] 获取到 channel_id: {channel_id}")
    
            # 启动 ego
            processes = [field_proc]
            for ego_db in ego_dbs:
                char_id = ego_db.name[4:-3]
                char_name = char_id
    
                ego_cmd = [
                    sys.executable,
                    str(utils_dir / 'ego.py'),
                    instance_name,
                    char_id,
                    char_name,
                    '127.0.0.1',
                    '8765',
                    str(channel_id)
                ]
    
                print(f"[API] 启动 ego: {' '.join(ego_cmd)}")
    
                ego_proc = subprocess.Popen(
                    ego_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                processes.append(ego_proc)
    
                # 启动线程打印 ego 输出
                def print_output(proc, name):
                    for line in proc.stdout:
                        print(f"[{name}] {line.strip()}")
    
                t = threading.Thread(target=print_output, args=(ego_proc, f"ego_{char_name}"), daemon=True)
                t.start()
    
            self._running_processes[instance_name] = {
                'processes': processes,
                'channel_id': channel_id
            }
    
            return {
                "success": True,
                "message": f"实例 '{instance_name}' 启动成功 (field: 1, ego: {len(ego_dbs)})",
                "pids": [p.pid for p in processes],
                "channel_id": channel_id
            }
    
        except Exception as e:
            return {"success": False, "message": f"启动实例失败: {str(e)}"}

    # ================================================================
    # 停止实例
    # ================================================================
    
    def stop_instance(self, instance_name: str):
        """停止实例: 杀死所有相关进程"""
        try:
            if instance_name not in self._running_processes:
                return {"success": False, "message": f"实例 '{instance_name}' 未运行"}
    
            info = self._running_processes[instance_name]
            processes = info['processes'] if isinstance(info, dict) else info
    
            killed = 0
            for proc in processes:
                try:
                    proc.terminate()
                    killed += 1
                except Exception as e:
                    print(f"杀死进程失败: {proc.pid}, 错误: {e}")
    
            for proc in processes:
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    try:
                        proc.kill()
                    except:
                        pass
    
            del self._running_processes[instance_name]
    
            return {
                "success": True,
                "message": f"实例 '{instance_name}' 已停止 (终止 {killed} 个进程)"
            }
    
        except Exception as e:
            return {"success": False, "message": f"停止实例失败: {str(e)}"}


    # ================================================================
    # 数据观测 API (新增)
    # ================================================================

    def _connect_db(self, db_path):
        """统一数据库连接，只读模式，Row工厂"""
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_db_type(self, filename):
        """判断数据库类型：环境 或 人物"""
        if filename.startswith("field_"):
            return "环境"
        elif filename.startswith("ego_"):
            return "人物"
        return "未知"

    def _get_db_display_name(self, filename):
        """获取数据库的显示名称"""
        if filename.startswith("field_"):
            return filename.replace("field_", "").replace(".db", "")
        elif filename.startswith("ego_"):
            return filename.replace("ego_", "").replace(".db", "")
        return filename.replace(".db", "")

    def _extract_scalar_value(self, value_json_str, field_path=None):
        """从JSON中提取标量值"""
        try:
            obj = json.loads(value_json_str)
        except Exception:
            return None

        if field_path is None:
            if isinstance(obj, (int, float)):
                return obj
            if isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], (int, float)):
                return obj[0]
            return None

        if isinstance(obj, dict) and field_path in obj:
            val = obj[field_path]
            if isinstance(val, (int, float)):
                return val
            if isinstance(val, (list, tuple)) and len(val) > 0 and isinstance(val[0], (int, float)):
                return val[0]
        return None

    def get_instances(self):
        """
        获取所有实例及其包含的数据库列表
        
        Returns:
            dict: {
                "success": bool,
                "data": [{
                    "name": str,           # 实例名称
                    "databases": [{
                        "filename": str,    # 数据库文件名
                        "db_name": str,     # 显示名称
                        "type": str,        # "环境" 或 "人物"
                        "display_name": str,# 显示名
                        "tick_min": int,
                        "tick_max": int,
                        "tables": [str]     # 表名列表
                    }]
                }],
                "message": str
            }
        """
        try:
            instance_root = Path("../data/instance")
            
            if not instance_root.exists():
                return {
                    "success": True,
                    "data": [],
                    "message": "实例目录不存在"
                }
            
            result = []
            for instance_dir in instance_root.iterdir():
                if not instance_dir.is_dir():
                    continue
                
                if instance_dir.name.startswith("."):
                    continue
                
                databases = []
                for db_file in instance_dir.glob("*.db"):
                    db_path = str(db_file)
                    filename = db_file.name
                    db_type = self._get_db_type(filename)
                    db_name = self._get_db_display_name(filename)
                    
                    try:
                        conn = self._connect_db(db_path)
                        info = {"min_tick": 0, "max_tick": 0, "tables": []}
                        
                        try:
                            row = conn.execute("SELECT MIN(tick) as min_tick, MAX(tick) as max_tick FROM 状态").fetchone()
                            if row:
                                info["min_tick"] = row["min_tick"] or 0
                                info["max_tick"] = row["max_tick"] or 0
                        except:
                            pass
                        
                        try:
                            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
                            info["tables"] = [t["name"] for t in tables]
                        except:
                            pass
                        
                        conn.close()
                        
                        databases.append({
                            "filename": filename,
                            "db_name": db_name,
                            "type": db_type,
                            "display_name": f"{db_type} {db_name}",
                            "tick_min": info["min_tick"],
                            "tick_max": info["max_tick"],
                            "tables": info["tables"],
                        })
                    except Exception as e:
                        databases.append({
                            "filename": filename,
                            "db_name": db_name,
                            "type": db_type,
                            "display_name": f"{db_type} {db_name}",
                            "tick_min": 0,
                            "tick_max": 0,
                            "tables": [],
                            "error": str(e)
                        })
                
                if databases:
                    databases.sort(key=lambda x: (x["type"] != "环境", x["db_name"]))
                    result.append({
                        "name": instance_dir.name,
                        "databases": databases
                    })
            
            return {
                "success": True,
                "data": sorted(result, key=lambda x: x["name"]),
                "message": f"成功获取 {len(result)} 个实例"
            }
            
        except Exception as e:
            return {
                "success": False,
                "data": [],
                "message": f"获取实例列表失败: {str(e)}"
            }

    def get_db_info(self, instance_name, db_filename):
        """
        获取数据库元信息
        
        Args:
            instance_name: 实例名称
            db_filename: 数据库文件名 (如 field_世界.db)
            
        Returns:
            dict: {
                "success": bool,
                "data": {
                    "tick_range": [min, max],
                    "tables": [str],
                    "entities": [str],
                    "entity_fields": {"entity": [fields]},
                    "table_columns": {"table": [columns]},
                    "database_type": str,
                    "database_name": str
                },
                "message": str
            }
        """
        try:
            db_path = Path("../data/instance") / instance_name / db_filename
            
            if not db_path.exists():
                return {
                    "success": False,
                    "data": None,
                    "message": f"数据库文件不存在: {db_path}"
                }
            
            info = {
                "tick_range": [0, 0],
                "tables": [],
                "entities": [],
                "entity_fields": {},
                "table_columns": {},
                "database_type": self._get_db_type(db_filename),
                "database_name": self._get_db_display_name(db_filename),
            }
            
            conn = self._connect_db(str(db_path))
            
            try:
                row = conn.execute("SELECT MIN(tick) as min_tick, MAX(tick) as max_tick FROM 状态").fetchone()
                if row and row["max_tick"] is not None:
                    info["tick_range"] = [row["min_tick"] or 0, row["max_tick"]]
            except:
                pass

            try:
                tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
                info["tables"] = [t["name"] for t in tables]
            except:
                pass

            try:
                entities = conn.execute("SELECT DISTINCT 字段名 FROM 状态 ORDER BY 字段名").fetchall()
                info["entities"] = [e["字段名"] for e in entities]
            except:
                pass

            for entity in info["entities"]:
                field_set = set()
                try:
                    rows = conn.execute(
                        "SELECT 值 FROM 状态 WHERE 字段名 = ? ORDER BY tick LIMIT 200",
                        (entity,)
                    ).fetchall()
                    for r in rows:
                        try:
                            obj = json.loads(r["值"])
                            if isinstance(obj, dict):
                                for k, v in obj.items():
                                    if isinstance(v, (int, float)):
                                        field_set.add(k)
                                    elif isinstance(v, (list, tuple)) and len(v) > 0 and isinstance(v[0], (int, float)):
                                        field_set.add(k)
                        except Exception:
                            pass
                except:
                    pass
                info["entity_fields"][entity] = sorted(field_set)

            for table in info["tables"]:
                try:
                    cursor = conn.execute(f'SELECT * FROM [{table}] LIMIT 1')
                    info["table_columns"][table] = [desc[0] for desc in cursor.description]
                except Exception:
                    info["table_columns"][table] = []

            conn.close()
            
            return {
                "success": True,
                "data": info,
                "message": "获取数据库信息成功"
            }
            
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "message": f"获取数据库信息失败: {str(e)}"
            }

    def get_timeseries(self, instance_name, db_filename, source, target, field, tick_min=None, tick_max=None):
        """
        获取时间序列数据
        
        Args:
            instance_name: 实例名称
            db_filename: 数据库文件名
            source: "entity" 或 "table"
            target: 实体名或表名
            field: 字段名
            tick_min: 最小tick (可选)
            tick_max: 最大tick (可选)
            
        Returns:
            dict: {
                "success": bool,
                "data": [{"tick": int, "value": float}],
                "count": int,
                "message": str
            }
        """
        try:
            db_path = Path("../data/instance") / instance_name / db_filename
            
            if not db_path.exists():
                return {
                    "success": False,
                    "data": [],
                    "count": 0,
                    "message": f"数据库文件不存在: {db_path}"
                }
            
            result_data = []
            conn = self._connect_db(str(db_path))

            if source == "entity":
                where = "字段名 = ?"
                params = [target]
                if tick_min is not None:
                    where += " AND tick >= ?"
                    params.append(tick_min)
                if tick_max is not None:
                    where += " AND tick <= ?"
                    params.append(tick_max)

                rows = conn.execute(
                    f"SELECT tick, 值 FROM 状态 WHERE {where} ORDER BY tick", params
                ).fetchall()

                for r in rows:
                    val = self._extract_scalar_value(r["值"], field)
                    if val is not None and not (math.isnan(val) or math.isinf(val)):
                        result_data.append({"tick": r["tick"], "value": val})

            elif source == "table":
                safe_table = target.replace('"', '""')
                safe_field = field.replace('"', '""') if field else "值"

                where_parts = []
                params = []
                if tick_min is not None:
                    where_parts.append("tick >= ?")
                    params.append(tick_min)
                if tick_max is not None:
                    where_parts.append("tick <= ?")
                    params.append(tick_max)
                where_clause = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""

                try:
                    rows = conn.execute(
                        f'SELECT tick, "{safe_field}" as val FROM [{safe_table}]{where_clause} ORDER BY tick',
                        params
                    ).fetchall()
                    for r in rows:
                        try:
                            v = float(r["val"]) if r["val"] is not None else None
                            if v is not None and not (math.isnan(v) or math.isinf(v)):
                                result_data.append({"tick": r["tick"], "value": v})
                        except (ValueError, TypeError):
                            pass
                except Exception:
                    pass

            conn.close()
            
            return {
                "success": True,
                "data": result_data,
                "count": len(result_data),
                "message": f"获取 {len(result_data)} 个数据点"
            }
            
        except Exception as e:
            return {
                "success": False,
                "data": [],
                "count": 0,
                "message": f"获取时间序列数据失败: {str(e)}"
            }

    def get_snapshot(self, instance_name, db_filename, tick=None):
        """
        获取快照数据
        
        Args:
            instance_name: 实例名称
            db_filename: 数据库文件名
            tick: tick号 (可选，不传则取最大tick)
            
        Returns:
            dict: {
                "success": bool,
                "data": {
                    "tick": int,
                    "snapshot": {"entity": {...}},
                    "experiences": {"table_name": [{"类型": str, "描述": str}]}
                },
                "message": str
            }
        """
        try:
            db_path = Path("../data/instance") / instance_name / db_filename
            
            if not db_path.exists():
                return {
                    "success": False,
                    "data": None,
                    "message": f"数据库文件不存在: {db_path}"
                }
            
            conn = self._connect_db(str(db_path))

            if tick is None:
                row = conn.execute("SELECT MAX(tick) as max_tick FROM 状态").fetchone()
                tick = row["max_tick"] if row and row["max_tick"] is not None else 0

            rows = conn.execute(
                "SELECT 字段名, 值 FROM 状态 WHERE tick = ?", (tick,)
            ).fetchall()

            snapshot = {}
            for r in rows:
                try:
                    snapshot[r["字段名"]] = json.loads(r["值"])
                except Exception:
                    snapshot[r["字段名"]] = r["值"]

            experiences = {}
            for table_name in ["鲁滨逊经历", "荒岛经历", "人物经历"]:
                try:
                    rows = conn.execute(
                        f"SELECT 事件类型, 描述 FROM {table_name} WHERE tick = ?", (tick,)
                    ).fetchall()
                    if rows:
                        experiences[table_name] = [{"类型": r["事件类型"], "描述": r["描述"]} for r in rows]
                except:
                    pass

            conn.close()

            return {
                "success": True,
                "data": {
                    "tick": tick,
                    "snapshot": snapshot,
                    "experiences": experiences
                },
                "message": f"获取 tick {tick} 快照成功"
            }
            
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "message": f"获取快照失败: {str(e)}"
            }

    def get_table_data(self, instance_name, db_filename, table, page=1, per_page=100, tick_min=None, tick_max=None):
        """
        获取表数据
        
        Args:
            instance_name: 实例名称
            db_filename: 数据库文件名
            table: 表名
            page: 页码
            per_page: 每页条数
            tick_min: 最小tick (可选)
            tick_max: 最大tick (可选)
            
        Returns:
            dict: {
                "success": bool,
                "data": {
                    "table": str,
                    "columns": [str],
                    "total": int,
                    "page": int,
                    "per_page": int,
                    "rows": [dict]
                },
                "message": str
            }
        """
        try:
            db_path = Path("../data/instance") / instance_name / db_filename
            
            if not db_path.exists():
                return {
                    "success": False,
                    "data": None,
                    "message": f"数据库文件不存在: {db_path}"
                }
            
            conn = self._connect_db(str(db_path))

            safe_table = table.replace('"', '""')
            where_parts = []
            params = []
            if tick_min is not None:
                where_parts.append("tick >= ?")
                params.append(tick_min)
            if tick_max is not None:
                where_parts.append("tick <= ?")
                params.append(tick_max)
            where_clause = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""

            count_row = conn.execute(
                f'SELECT COUNT(*) as cnt FROM [{safe_table}]{where_clause}', params
            ).fetchone()
            total = count_row["cnt"] if count_row else 0

            sample = conn.execute(f'SELECT * FROM [{safe_table}] LIMIT 1')
            columns = [desc[0] for desc in sample.description]

            offset = (page - 1) * per_page
            rows = conn.execute(
                f'SELECT * FROM [{safe_table}]{where_clause} ORDER BY tick LIMIT ? OFFSET ?',
                params + [per_page, offset]
            ).fetchall()

            result_rows = []
            for r in rows:
                row_dict = {}
                for col in columns:
                    val = r[col]
                    if isinstance(val, str):
                        try:
                            row_dict[col] = json.loads(val)
                        except Exception:
                            row_dict[col] = val
                    else:
                        row_dict[col] = val
                result_rows.append(row_dict)

            conn.close()

            return {
                "success": True,
                "data": {
                    "table": table,
                    "columns": columns,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "rows": result_rows
                },
                "message": f"获取表 {table} 数据成功"
            }
            
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "message": f"获取表数据失败: {str(e)}"
            }
        


    # fieldeditor 新增方法    
    def create_field_project(self,oldname, name, img, note):
        """
        创建场域项目
        
        Args:
            name: 项目名称
            img: 图片文件名
            note: 描述
        
        Returns:
            dict: {"success": bool, "message": str}
        """
        import json
        from pathlib import Path
                
        if not name or not name.strip():
            return {"success": False, "message": "项目名称不能为空"}
        
        name = name.strip()
        
        data_field_dir = Path("../data/s_field")
        ui_field_dir = Path("../ui/data/s_field")
        
        data_field_dir.mkdir(parents=True, exist_ok=True)
        ui_field_dir.mkdir(parents=True, exist_ok=True)
        
        db_filename = f"field_{name}.db"
        json_filename = f"field_{name}.json"
        
        olddb_filename = f"{oldname}.db"
        
        olddb_path = data_field_dir / olddb_filename
        db_path = data_field_dir / db_filename
        json_path = ui_field_dir / json_filename
        
        if db_path.exists():
            return {"success": False, "message": f"名称 '{name}' 已存在，请更换名称"}
        
        try:
            shutil.copy2(str(olddb_path), str(db_path))
            result = {"success": True, "message": f"成功从 '{oldname}' 复制到 '{name}'"}
        except Exception as e:
            result = {"success": False, "message": f"复制数据库失败: {str(e)}"}
        
        if not result["success"]:
            return {"success": False, "message": result["message"]}
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "name": name,
                "img": img or "",
                "note": note or ""
            }, f, ensure_ascii=False, indent=2)
        
        return {"success": True, "message": f"项目 '{name}' 创建成功"}

    # 载入field数据库文件
    def load_field_project(self, name):
        """
        加载场域项目
        
        Args:
            name: 项目名称（对应 db 文件名）
        
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "data": {
                    "tables": [str]  # 表名列表
                }
            }
        """
        from pathlib import Path
        import sqlite3
        
        db_path = Path("../data/s_field") / f"{name}.db"
        
        if not db_path.exists():
            return {
                "success": False,
                "message": f"数据库文件 {name}.db 不存在",
                "data": None
            }
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            rows = cursor.fetchall()
            tables = [row[0] for row in rows]
            
            conn.close()
            
            return {
                "success": True,
                "message": f"加载成功，共 {len(tables)} 个表",
                "data": {
                    "tables": tables
                }
            }
            
        except sqlite3.Error as e:
            return {
                "success": False,
                "message": f"数据库连接失败: {str(e)}",
                "data": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"加载失败: {str(e)}",
                "data": None
            }
        
    def get_field_table_data(self, db_name, table_name, search=''):
        """
        获取场域数据库表数据（专供 Field 编辑器前端使用）
        
        Args:
            db_name: 数据库文件名 (如 "field_创世.db")
            table_name: 表名
            search: 搜索关键字 (可选)
        
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "columns": [str],
                "data": [dict]
            }
        """
        from pathlib import Path
        import sqlite3
        import json
        
        db_path = Path("../data/s_field") / db_name
        
        if not db_path.exists():
            return {
                "success": False,
                "message": f"数据库文件不存在: {db_name}",
                "columns": [],
                "data": []
            }
        
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                conn.close()
                return {
                    "success": False,
                    "message": f"表 '{table_name}' 不存在",
                    "columns": [],
                    "data": []
                }
            
            # 获取列信息 - 使用 PRAGMA table_info 获取表结构（即使表为空也能获取列名）
            cursor.execute(f"PRAGMA table_info([{table_name}])")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]  # col[1] 是列名
            
            if not columns:
                conn.close()
                return {
                    "success": True,
                    "message": "表没有列",
                    "columns": [],
                    "data": []
                }
            
            # 构建查询
            if search:
                # 在所有文本列中搜索
                search_conditions = []
                params = []
                for col in columns:
                    # 检查列类型是否为文本
                    cursor.execute(f"SELECT typeof([{col}]) FROM [{table_name}] LIMIT 1")
                    row = cursor.fetchone()
                    if row and row[0] in ('text', 'TEXT'):
                        search_conditions.append(f"[{col}] LIKE ?")
                        params.append(f"%{search}%")
                
                if search_conditions:
                    where_clause = " WHERE " + " OR ".join(search_conditions)
                else:
                    where_clause = ""
            else:
                where_clause = ""
                params = []
            
            # 使用 rowid 代替 id（兼容所有表）
            query = f"SELECT * FROM [{table_name}]{where_clause} ORDER BY rowid"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                row_dict = {}
                for col in columns:
                    val = row[col]
                    if isinstance(val, str):
                        try:
                            row_dict[col] = json.loads(val)
                        except:
                            row_dict[col] = val
                    else:
                        row_dict[col] = val
                data.append(row_dict)
            
            conn.close()
            
            return {
                "success": True,
                "message": f"获取 {len(data)} 条记录",
                "columns": columns,
                "data": data
            }
            
        except sqlite3.Error as e:
            return {
                "success": False,
                "message": f"数据库错误: {str(e)}",
                "columns": [],
                "data": []
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取数据失败: {str(e)}",
                "columns": [],
                "data": []
            }
        
    
    def save_field_row(self, db_name, table_name, row_data):
        """
        保存场域表单行数据（新增或更新）
        
        Args:
            db_name: 数据库文件名
            table_name: 表名
            row_data: 行数据字典，包含 id 和其他字段
        
        Returns:
            dict: {"success": bool, "message": str, "row_id": int}
        """
        from pathlib import Path
        import sqlite3
        import json
        
        db_path = Path("../data/s_field") / db_name
        
        if not db_path.exists():
            return {"success": False, "message": f"数据库文件不存在: {db_name}", "row_id": None}
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # 获取表列信息
            cursor.execute(f"PRAGMA table_info([{table_name}])")
            columns_info = cursor.fetchall()
            all_columns = [col[1] for col in columns_info]
            
            row_id = row_data.get('id')
            is_new = row_id is None or row_id < 0
            
            if is_new:
                # 新增
                insert_columns = [col for col in all_columns if col != 'id']
                placeholders = ','.join(['?' for _ in insert_columns])
                columns_str = ','.join([f'[{col}]' for col in insert_columns])
                
                values = []
                for col in insert_columns:
                    val = row_data.get(col, '')
                    if isinstance(val, (dict, list)):
                        val = json.dumps(val, ensure_ascii=False)
                    values.append(val)
                
                cursor.execute(f"INSERT INTO [{table_name}] ({columns_str}) VALUES ({placeholders})", values)
                new_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                return {"success": True, "message": "新增成功", "row_id": new_id}
            else:
                # 更新
                set_clause = ','.join([f'[{col}]=?' for col in all_columns if col != 'id'])
                values = []
                for col in all_columns:
                    if col == 'id':
                        continue
                    val = row_data.get(col, '')
                    if isinstance(val, (dict, list)):
                        val = json.dumps(val, ensure_ascii=False)
                    values.append(val)
                values.append(row_id)
                
                cursor.execute(f"UPDATE [{table_name}] SET {set_clause} WHERE id=?", values)
                conn.commit()
                conn.close()
                
                return {"success": True, "message": "更新成功", "row_id": row_id}
            
        except sqlite3.Error as e:
            return {"success": False, "message": f"数据库错误: {str(e)}", "row_id": None}
        except Exception as e:
            return {"success": False, "message": f"保存失败: {str(e)}", "row_id": None}
    
    
    def delete_field_row(self, db_name, table_name, row_id):
        """
        删除场域表单行数据（硬删除）
        
        Args:
            db_name: 数据库文件名
            table_name: 表名
            row_id: 行ID
        
        Returns:
            dict: {"success": bool, "message": str}
        """
        from pathlib import Path
        import sqlite3
        
        db_path = Path("../data/s_field") / db_name
        
        if not db_path.exists():
            return {"success": False, "message": f"数据库文件不存在: {db_name}"}
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute(f"DELETE FROM [{table_name}] WHERE id=?", (row_id,))
            conn.commit()
            conn.close()
            
            return {"success": True, "message": f"删除成功，ID: {row_id}"}
            
        except sqlite3.Error as e:
            return {"success": False, "message": f"数据库错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"删除失败: {str(e)}"}
    
    
    def logic_chain_query(self, db_name, table_name, row_id):
        """
        逻辑链查询（虚函数，暂返回提示信息）
        
        Args:
            db_name: 数据库文件名
            table_name: 表名
            row_id: 行ID
        
        Returns:
            dict: {"success": bool, "message": str, "data": dict}
        """
        return {
            "success": True,
            "message": "逻辑链查询功能开发中",
            "data": {
                "table": table_name,
                "row_id": row_id,
                "note": "该行数据暂未关联其他逻辑链"
            }
        }

    
    # Field推演
    def validate_field(self, db_name):
        """
        执行场域推演检查
        
        Args:
            db_name: 数据库文件名 (如 "field_创世.db")
        
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "issues": [
                    {"l": "e"|"w"|"i", "m": str, "loc": str}
                ]
            }
        """
        import subprocess
        import json
        import sys
        from pathlib import Path
        
        # 获取 Deduction/Field.py 的路径
        current_dir = Path(__file__).resolve().parent
        deduction_script = current_dir / "Deduction" / "Field.py"
        
        if not deduction_script.exists():
            return {
                "success": False,
                "message": f"推演脚本不存在: {deduction_script}",
                "issues": []
            }
        
        try:
            # 调用 Deduction/Field.py
            result = subprocess.run(
                [sys.executable, str(deduction_script), db_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"推演脚本执行失败: {result.stderr}",
                    "issues": []
                }
            
            # 解析返回的 JSON
            try:
                output = json.loads(result.stdout)
                return output
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "message": f"解析推演结果失败: {str(e)}",
                    "issues": []
                }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "推演超时 (30秒)",
                "issues": []
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"推演执行失败: {str(e)}",
                "issues": []
            }
        
    # 模拟
    
    def run_simulation(self, db_name, script_name):
        """
        执行场域模拟
        
        Args:
            db_name: 数据库文件名 (如 "field_创世.db")
            script_name: 脚本名称 (如 "生物入侵" 或 "自然灾害")
        
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "logs": [str]
            }
        """
        import subprocess
        import json
        import sys
        from pathlib import Path
        
        # 获取 Simulation/Field/ 目录下的脚本路径
        current_dir = Path(__file__).resolve().parent
        script_path = current_dir / "Simulation" / "Field" / f"{script_name}.py"
        
        if not script_path.exists():
            return {
                "success": False,
                "message": f"模拟脚本不存在: {script_name}.py",
                "logs": []
            }
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path), db_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"模拟脚本执行失败: {result.stderr}",
                    "logs": []
                }
            
            try:
                output = json.loads(result.stdout)
                return output
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "message": f"解析模拟结果失败: {str(e)}",
                    "logs": []
                }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "模拟超时 (60秒)",
                "logs": []
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"模拟执行失败: {str(e)}",
                "logs": []
            }
        
    #EgoEditor 新增方法
    
    def create_ego_project(self,oldname, name, img, note):
        """
        创建 Ego 项目
        
        Args:
            name: 项目名称
            img: 图片文件名
            note: 描述
        
        Returns:
            dict: {"success": bool, "message": str}
        """
        import json
        from pathlib import Path
        
        if not name or not name.strip():
            return {"success": False, "message": "项目名称不能为空"}
        
        name = name.strip()
        
        data_dir = Path("../data/s_ego")
        ui_dir = Path("../ui/data/s_ego")
        
        data_dir.mkdir(parents=True, exist_ok=True)
        ui_dir.mkdir(parents=True, exist_ok=True)
        
        db_filename = f"ego_{name}.db"
        json_filename = f"ego_{name}.json"
        olddb_filename = f"{oldname}.db"
        
        olddb_path = data_dir / olddb_filename
        db_path = data_dir / db_filename
        json_path = ui_dir / json_filename
        
        if db_path.exists():
            return {"success": False, "message": f"名称 '{name}' 已存在，请更换名称"}
        
        try:
            shutil.copy2(str(olddb_path), str(db_path))
            result = {"success": True, "message": f"成功从 '{oldname}' 复制到 '{name}'"}
        except Exception as e:
            result = {"success": False, "message": f"复制数据库失败: {str(e)}"}
        
        if not result["success"]:
            return {"success": False, "message": result["message"]}
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "name": name,
                "img": img or "",
                "note": note or ""
            }, f, ensure_ascii=False, indent=2)
        
        return {"success": True, "message": f"Ego 项目 '{name}' 创建成功"}
    
    
    def load_ego_project(self, name):
        """
        加载 Ego 项目
        
        Args:
            name: 项目名称（对应 db 文件名，不含后缀）
        
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "data": {
                    "tables": [str]
                }
            }
        """
        from pathlib import Path
        import sqlite3
        
        db_path = Path("../data/s_ego") / f"{name}.db"
        
        if not db_path.exists():
            return {
                "success": False,
                "message": f"数据库文件 {name}.db 不存在",
                "data": None
            }
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            rows = cursor.fetchall()
            tables = [row[0] for row in rows]
            
            conn.close()
            
            return {
                "success": True,
                "message": f"加载成功，共 {len(tables)} 个表",
                "data": {
                    "tables": tables
                }
            }
            
        except sqlite3.Error as e:
            return {
                "success": False,
                "message": f"数据库连接失败: {str(e)}",
                "data": None
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"加载失败: {str(e)}",
                "data": None
            }
    
    
    def get_ego_table_data(self, db_name, table_name, search=''):
        """
        获取 Ego 数据库表数据
        
        Args:
            db_name: 数据库文件名 (如 "ego_鲁滨逊.db")
            table_name: 表名
            search: 搜索关键字 (可选)
        
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "columns": [str],
                "data": [dict]
            }
        """
        from pathlib import Path
        import sqlite3
        import json
        
        db_path = Path("../data/s_ego") / db_name
        
        if not db_path.exists():
            return {
                "success": False,
                "message": f"数据库文件不存在: {db_name}",
                "columns": [],
                "data": []
            }
        
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                conn.close()
                return {
                    "success": False,
                    "message": f"表 '{table_name}' 不存在",
                    "columns": [],
                    "data": []
                }
            
            cursor.execute(f"PRAGMA table_info([{table_name}])")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            
            if not columns:
                conn.close()
                return {
                    "success": True,
                    "message": "表没有列",
                    "columns": [],
                    "data": []
                }
            
            if search:
                search_conditions = []
                params = []
                for col in columns:
                    cursor.execute(f"SELECT typeof([{col}]) FROM [{table_name}] LIMIT 1")
                    row = cursor.fetchone()
                    if row and row[0] in ('text', 'TEXT'):
                        search_conditions.append(f"[{col}] LIKE ?")
                        params.append(f"%{search}%")
                
                if search_conditions:
                    where_clause = " WHERE " + " OR ".join(search_conditions)
                else:
                    where_clause = ""
            else:
                where_clause = ""
                params = []
            
            query = f"SELECT * FROM [{table_name}]{where_clause} ORDER BY rowid"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            data = []
            for row in rows:
                row_dict = {}
                for col in columns:
                    val = row[col]
                    if isinstance(val, str):
                        try:
                            row_dict[col] = json.loads(val)
                        except:
                            row_dict[col] = val
                    else:
                        row_dict[col] = val
                data.append(row_dict)
            
            conn.close()
            
            return {
                "success": True,
                "message": f"获取 {len(data)} 条记录",
                "columns": columns,
                "data": data
            }
            
        except sqlite3.Error as e:
            return {
                "success": False,
                "message": f"数据库错误: {str(e)}",
                "columns": [],
                "data": []
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取数据失败: {str(e)}",
                "columns": [],
                "data": []
            }
    
    
    def save_ego_row(self, db_name, table_name, row_data):
        """
        保存 Ego 表单行数据（新增或更新）
        
        Args:
            db_name: 数据库文件名
            table_name: 表名
            row_data: 行数据字典，包含 id 和其他字段
        
        Returns:
            dict: {"success": bool, "message": str, "row_id": int}
        """
        from pathlib import Path
        import sqlite3
        import json
        
        db_path = Path("../data/s_ego") / db_name
        
        if not db_path.exists():
            return {"success": False, "message": f"数据库文件不存在: {db_name}", "row_id": None}
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute(f"PRAGMA table_info([{table_name}])")
            columns_info = cursor.fetchall()
            all_columns = [col[1] for col in columns_info]
            
            row_id = row_data.get('id')
            is_new = row_id is None or row_id < 0
            
            if is_new:
                insert_columns = [col for col in all_columns if col != 'id']
                placeholders = ','.join(['?' for _ in insert_columns])
                columns_str = ','.join([f'[{col}]' for col in insert_columns])
                
                values = []
                for col in insert_columns:
                    val = row_data.get(col, '')
                    if isinstance(val, (dict, list)):
                        val = json.dumps(val, ensure_ascii=False)
                    values.append(val)
                
                cursor.execute(f"INSERT INTO [{table_name}] ({columns_str}) VALUES ({placeholders})", values)
                new_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                return {"success": True, "message": "新增成功", "row_id": new_id}
            else:
                set_clause = ','.join([f'[{col}]=?' for col in all_columns if col != 'id'])
                values = []
                for col in all_columns:
                    if col == 'id':
                        continue
                    val = row_data.get(col, '')
                    if isinstance(val, (dict, list)):
                        val = json.dumps(val, ensure_ascii=False)
                    values.append(val)
                values.append(row_id)
                
                cursor.execute(f"UPDATE [{table_name}] SET {set_clause} WHERE id=?", values)
                conn.commit()
                conn.close()
                
                return {"success": True, "message": "更新成功", "row_id": row_id}
            
        except sqlite3.Error as e:
            return {"success": False, "message": f"数据库错误: {str(e)}", "row_id": None}
        except Exception as e:
            return {"success": False, "message": f"保存失败: {str(e)}", "row_id": None}
    
    
    def delete_ego_row(self, db_name, table_name, row_id):
        """
        删除 Ego 表单行数据（硬删除）
        
        Args:
            db_name: 数据库文件名
            table_name: 表名
            row_id: 行ID
        
        Returns:
            dict: {"success": bool, "message": str}
        """
        from pathlib import Path
        import sqlite3
        
        db_path = Path("../data/s_ego") / db_name
        
        if not db_path.exists():
            return {"success": False, "message": f"数据库文件不存在: {db_name}"}
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            cursor.execute(f"DELETE FROM [{table_name}] WHERE id=?", (row_id,))
            conn.commit()
            conn.close()
            
            return {"success": True, "message": f"删除成功，ID: {row_id}"}
            
        except sqlite3.Error as e:
            return {"success": False, "message": f"数据库错误: {str(e)}"}
        except Exception as e:
            return {"success": False, "message": f"删除失败: {str(e)}"}
    
    
    def logic_chain_query_ego(self, db_name, table_name, row_id):
        """
        Ego 逻辑链查询（虚函数，暂返回提示信息）
        
        Args:
            db_name: 数据库文件名
            table_name: 表名
            row_id: 行ID
        
        Returns:
            dict: {"success": bool, "message": str, "data": dict}
        """
        return {
            "success": True,
            "message": "Ego 逻辑链查询功能开发中",
            "data": {
                "table": table_name,
                "row_id": row_id,
                "note": "该行数据暂未关联其他逻辑链"
            }
        }
    
    
    def validate_ego(self, db_name):
        """
        执行 Ego 推演检查
        
        Args:
            db_name: 数据库文件名 (如 "ego_鲁滨逊.db")
        
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "issues": [
                    {"l": "e"|"w"|"i", "m": str, "loc": str}
                ]
            }
        """
        import subprocess
        import json
        import sys
        from pathlib import Path
        
        current_dir = Path(__file__).resolve().parent
        deduction_script = current_dir / "Deduction" / "Ego.py"
        
        if not deduction_script.exists():
            return {
                "success": False,
                "message": f"推演脚本不存在: {deduction_script}",
                "issues": []
            }
        
        try:
            result = subprocess.run(
                [sys.executable, str(deduction_script), db_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"推演脚本执行失败: {result.stderr}",
                    "issues": []
                }
            
            try:
                output = json.loads(result.stdout)
                return output
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "message": f"解析推演结果失败: {str(e)}",
                    "issues": []
                }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "推演超时 (30秒)",
                "issues": []
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"推演执行失败: {str(e)}",
                "issues": []
            }
    
    
    def run_ego_simulation(self, db_name, script_name):
        """
        执行 Ego 模拟
        
        Args:
            db_name: 数据库文件名 (如 "ego_鲁滨逊.db")
            script_name: 脚本名称 (如 "身体机能" 或 "精神意志")
        
        Returns:
            dict: {
                "success": bool,
                "message": str,
                "logs": [str]
            }
        """
        import subprocess
        import json
        import sys
        from pathlib import Path
        
        current_dir = Path(__file__).resolve().parent
        script_path = current_dir / "Simulation" / "Ego" / f"{script_name}.py"
        
        if not script_path.exists():
            return {
                "success": False,
                "message": f"模拟脚本不存在: {script_name}.py",
                "logs": []
            }
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path), db_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "message": f"模拟脚本执行失败: {result.stderr}",
                    "logs": []
                }
            
            try:
                output = json.loads(result.stdout)
                return output
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "message": f"解析模拟结果失败: {str(e)}",
                    "logs": []
                }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "message": "模拟超时 (60秒)",
                "logs": []
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"模拟执行失败: {str(e)}",
                "logs": []
            }
        
        
        #删除ENTITY
    
    def delete_entity(self, name, entity_type):
        """
        删除实体（实例/项目）
        
        Args:
            name: 实体名称
            entity_type: 实体类型 ("instance" | "field" | "ego" | "art" | "innovation" | "literature")
        
        Returns:
            dict: {"success": bool, "message": str}
        """
        import shutil
        from pathlib import Path
        
        if not name or not name.strip():
            return {"success": False, "message": "实体名称不能为空"}
        
        name = name.strip()
        
        if entity_type == "instance":
            target_path = Path("../data/instance") / name
            ui_path = Path("../ui/data/instance") / f"{name}.json"
            
            if not target_path.exists():
                return {"success": False, "message": f"实例 '{name}' 不存在"}
            
            try:
                shutil.rmtree(target_path)
                if ui_path.exists():
                    ui_path.unlink()
                return {"success": True, "message": f"实例 '{name}' 已删除"}
            except Exception as e:
                return {"success": False, "message": f"删除实例失败: {str(e)}"}
        
        elif entity_type == "field":
            db_path = Path("../data/s_field") / f"{name}.db"
            json_path = Path("../ui/data/s_field") / f"{name}.json"
            
            if not db_path.exists():
                return {"success": False, "message": f"场域项目 '{name}' 不存在"}
            
            try:
                if db_path.exists():
                    db_path.unlink()
                if json_path.exists():
                    json_path.unlink()
                return {"success": True, "message": f"场域项目 '{name}' 已删除"}
            except Exception as e:
                return {"success": False, "message": f"删除场域项目失败: {str(e)}"}
        
        elif entity_type == "ego":
            db_path = Path("../data/s_ego") / f"{name}.db"
            json_path = Path("../ui/data/s_ego") / f"{name}.json"
            
            if not db_path.exists():
                return {"success": False, "message": f"Ego 项目 '{name}' 不存在"}
            
            try:
                if db_path.exists():
                    db_path.unlink()
                if json_path.exists():
                    json_path.unlink()
                return {"success": True, "message": f"Ego 项目 '{name}' 已删除"}
            except Exception as e:
                return {"success": False, "message": f"删除 Ego 项目失败: {str(e)}"}
        
        elif entity_type == "art":
            base_dir = Path("../ui/data/civilization/art")
            if not base_dir.exists():
                return {"success": False, "message": f"Art 目录不存在"}
            
            try:
                deleted = []
                for ext in ['json', 'png', 'mid']:
                    file_path = base_dir / f"{name}.{ext}"
                    if file_path.exists():
                        file_path.unlink()
                        deleted.append(f"{name}.{ext}")
                
                if not deleted:
                    return {"success": False, "message": f"未找到名为 '{name}' 的 art 文件"}
                
                return {"success": True, "message": f"Art '{name}' 已删除 (删除: {', '.join(deleted)})"}
            except Exception as e:
                return {"success": False, "message": f"删除 art 失败: {str(e)}"}
        
        elif entity_type == "innovation":
            base_dir = Path("../ui/data/civilization/innovation")
            if not base_dir.exists():
                return {"success": False, "message": f"Innovation 目录不存在"}
            
            try:
                # 删除所有匹配前缀的文件
                deleted = []
                for file_path in base_dir.glob(f"{name}.*"):
                    file_path.unlink()
                    deleted.append(file_path.name)
                
                if not deleted:
                    return {"success": False, "message": f"未找到名为 '{name}' 的 innovation 文件"}
                
                return {"success": True, "message": f"Innovation '{name}' 已删除 (删除: {', '.join(deleted)})"}
            except Exception as e:
                return {"success": False, "message": f"删除 innovation 失败: {str(e)}"}
        
        elif entity_type == "literature":
            base_dir = Path("../ui/data/civilization/literature")
            if not base_dir.exists():
                return {"success": False, "message": f"Literature 目录不存在"}
            
            try:
                # 删除所有匹配前缀的文件
                deleted = []
                for file_path in base_dir.glob(f"{name}.*"):
                    file_path.unlink()
                    deleted.append(file_path.name)
                
                if not deleted:
                    return {"success": False, "message": f"未找到名为 '{name}' 的 literature 文件"}
                
                return {"success": True, "message": f"Literature '{name}' 已删除 (删除: {', '.join(deleted)})"}
            except Exception as e:
                return {"success": False, "message": f"删除 literature 失败: {str(e)}"}
        
        else:
            return {"success": False, "message": f"不支持的实体类型: {entity_type}"}
