"""
API接口定义，供JavaScript调用
"""
import webview
import threading
import os
from typing import Dict, Optional, Any
import json

class Api:
    def __init__(self):
        self._window_manager = None
    
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
    
    # 窗口操作相关API
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
        window = self.get_window()
        if window:
            try:
                window.destroy()
            except Exception as e:
                print(f"关闭窗口失败: {e}")
    
    # 登录相关API
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
    
    # 页面加载相关API
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
    
    # 文件操作相关API
    def select_directory(self):
        """打开目录选择对话框"""
        try:
            window = self.get_window()
            result = window.create_file_dialog(
                webview.FOLDER_DIALOG,
                directory=os.path.expanduser("~")
            )
            if result and len(result) > 0:
                return result[0]
            return None
        except Exception as e:
            print(f"Error selecting directory: {e}")
            return None
    
    # 配置管理相关API
    def get_trading_configs(self, username):
        """获取交易配置"""
        if self._window_manager and hasattr(self._window_manager, 'credential_manager'):
            return self._window_manager.credential_manager.get_trading_configs(username)
        return {"success": False, "message": "系统错误", "configs": [], "count": 0}
    
    def save_trading_config(self, username, config_name, account_name, api_name, target_dir, strategy_name):
        """保存交易配置"""
        if self._window_manager and hasattr(self._window_manager, 'credential_manager'):
            return self._window_manager.credential_manager.save_trading_config(
                username, config_name, account_name, api_name, target_dir, strategy_name
            )
        return {"success": False, "message": "系统错误"}
    
    def update_trading_config(self, config_id, kwargs):
        """更新交易配置"""
        if self._window_manager and hasattr(self._window_manager, 'credential_manager'):
            return self._window_manager.credential_manager.update_trading_config(config_id, **kwargs)
        return {"success": False, "message": "系统错误"}
    
    def delete_trading_config(self, username, config_name=None, config_id=None):
        """删除交易配置"""
        if self._window_manager and hasattr(self._window_manager, 'credential_manager'):
            return self._window_manager.credential_manager.delete_trading_config(username, config_name, config_id)
        return {"success": False, "message": "系统错误"}
    
    # 交易进程管理API
    def start_trading_process(self, configs):
        """启动交易进程"""
        if not self._window_manager:
            return {
                "success": False,
                "message": "系统错误：WindowManager未初始化"
            }
        
        # 检查是否有进程池
        # 直接从进程池单例获取
        from process_manager import get_process_pool
        process_pool = get_process_pool()
        
        if not process_pool:
            return {
                "success": False,
                "message": "进程池未初始化"
            }
        try:
            
            #print(type(configs))
            #print(configs)
            # 3. 使用进程池启动进程
            process_id = process_pool.create_process(json.loads(configs))
            
            if process_id:
                return {
                    "success": True,
                    "process_id": process_id,
                    "message": "启动成功"
                }
            else:
                return {
                    "success": False,
                    "message": "进程创建失败（可能已达到最大进程数限制）"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"启动异常: {str(e)}"
            }
    
    def stop_trading_process(self, process_id):
        """停止交易进程"""
        if not self._window_manager:
            return {
                "success": False,
                "message": "系统错误：WindowManager未初始化"
            }
        
        # 检查是否有进程池
        # 直接从进程池单例获取
        from process_manager import get_process_pool
        process_pool = get_process_pool()
        
        if not process_pool:
            return {
                "success": False,
                "message": "进程池未初始化"
            }
        try:
            return process_pool.stop_process(process_id)
        except Exception as e:
            print(f"停止进程失败: {e}")
            return False
    
    def restart_trading_process(self, process_id):
        """重启交易进程"""
        if not self._window_manager or not hasattr(self._window_manager, 'process_pool'):
            return False
        
        try:
            return self._window_manager.process_pool.restart_process(process_id)
        except Exception as e:
            print(f"重启进程失败: {e}")
            return False
    
    def get_process_status(self, process_id):
        """获取进程状态"""
        if not self._window_manager or not hasattr(self._window_manager, 'process_pool'):
            return {
                "success": False,
                "message": "进程池未初始化",
                "process_id": process_id
            }
        
        try:
            status = self._window_manager.process_pool.get_process_status(process_id)
            if status:
                return {
                    "success": True,
                    "data": status,
                    "process_id": process_id
                }
            else:
                return {
                    "success": False,
                    "message": "进程不存在",
                    "process_id": process_id
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取状态失败: {str(e)}",
                "process_id": process_id
            }
    
    def get_all_processes(self):
        """获取所有进程状态"""
        
        if not self._window_manager:
            return {
                "success": False,
                "message": "系统错误：WindowManager未初始化"
            }
        
        # 检查是否有进程池
        # 直接从进程池单例获取
        from process_manager import get_process_pool
        process_pool = get_process_pool()
        
        if not process_pool:
            return {
                "success": False,
                "message": "进程池未初始化"
            }
        
        try:
            all_status = process_pool.get_all_status()
            return {
                "success": True,
                "processes": all_status,
                "count": len(all_status)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取进程列表失败: {str(e)}",
                "processes": []
            }
    
    def send_command(self, process_id, command, data=None):
        """发送命令到进程"""
        if not self._window_manager or not hasattr(self._window_manager, 'process_pool'):
            return {
                "success": False,
                "message": "进程池未初始化"
            }
        
        try:
            if data:
                success = self._window_manager.process_pool.send_command_to_process(process_id, command, data)
            else:
                success = self._window_manager.process_pool.send_command_to_process(process_id, command)
            
            return {
                "success": success,
                "process_id": process_id,
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"发送命令失败: {str(e)}",
                "process_id": process_id,
                "command": command
            }
    
    def broadcast_command(self, command, data=None):
        """向所有进程广播命令"""
        if not self._window_manager or not hasattr(self._window_manager, 'process_pool'):
            return {
                "success": False,
                "message": "进程池未初始化"
            }
        
        try:
            results = self._window_manager.process_pool.broadcast_command(command, data)
            return {
                "success": True,
                "results": results,
                "command": command,
                "count": len(results)
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"广播命令失败: {str(e)}",
                "command": command
            }
    
    # 系统管理API
    def get_system_info(self):
        """获取系统信息"""
        import platform
        import psutil
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            return {
                "success": True,
                "system": platform.system(),
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "cpu_cores": psutil.cpu_count(),
                "cpu_percent": cpu_percent,
                "memory_total": memory.total,
                "memory_used": memory.used,
                "memory_percent": memory.percent
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取系统信息失败: {str(e)}"
            }
    
    # 实用工具API
    def ping(self):
        """测试API连接"""
        return {
            "success": True,
            "message": "API连接正常",
            "timestamp": webview.datetime.now().isoformat() if hasattr(webview, 'datetime') else "N/A"
        }