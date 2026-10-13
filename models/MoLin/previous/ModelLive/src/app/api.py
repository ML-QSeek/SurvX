import webview
import sys
import json
import threading
import base64
import os
from datetime import datetime
from rdp_manager import create_rdp_with_windows_credentials  # 新增导入
import subprocess
import tempfile

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
        
        # 然后执行你原来的关闭主窗口逻辑
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
        # 直接返回简单值，避免调用窗口方法
        if self._window_manager:
            # 在新线程中执行实际的操作
            threading.Thread(target=self._window_manager.load_main_page, daemon=True).start()
            return {"success": True, "message": "正在加载主页面..."}
        return {"success": False, "message": "系统错误"}
    
    def center_window(self):
        """居中窗口（供JavaScript调用）"""
        if self._window_manager:
            threading.Thread(target=self._window_manager.center_window, daemon=True).start()
            return {"success": True, "message": "正在居中窗口..."}
        return {"success": False, "message": "系统错误"}

    def download_image(self, base64_data):
        try:
            # 解析 base64 数据
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]
            # 解码 base64
            image_data = base64.b64decode(base64_data)
            # 生成文件名
            filename = f"{int(datetime.now().timestamp())}.png"
            # 保存文件
            save_path = os.path.join(os.path.expanduser('~'), 'Downloads', filename)
            safe_path = json.dumps(save_path)
            with open(save_path, 'wb') as f:
                f.write(image_data)
            # 显示成功消息
            webview.windows[0].evaluate_js(f'WarnMessage("图片已保存到：" + {safe_path})')
            return {"status": "success", "path": save_path}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # ============ 新增RDP相关方法 ============
    
    def connect_remote_desktop(self, host, username, password):
        """
        连接远程桌面
        参数: host, username, password
        """
        try:
            # 调用RDP连接函数
            create_rdp_with_windows_credentials(host, username, password)
            return {"success": True, "message": f"正在连接到 {host}"}
            
        except Exception as e:
            print(f"远程桌面连接失败: {e}")
            return {"success": False, "message": f"连接失败: {str(e)}"}
            
            
    def open_test_window(self,kusername):
        """打开 Jupyter 窗口"""
        print("Python: 收到打开窗口的请求")
        
        username = kusername
        pid_file = os.path.join(tempfile.gettempdir(), f"jupyter_{username}.pid")
        
        should_start = True
        
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    old_pid = int(f.read().strip())
                
                # 更安全的进程检查方式
                import ctypes
                from ctypes import wintypes
                
                # Windows API 检查进程是否存在
                PROCESS_QUERY_INFORMATION = 0x0400
                handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, old_pid)
                
                if handle:
                    exit_code = wintypes.DWORD()
                    ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
                    ctypes.windll.kernel32.CloseHandle(handle)
                    
                    if exit_code.value == 259:  # STILL_ACTIVE
                        print(f"Jupyter 窗口已存在，PID: {old_pid}")
                        should_start = False
                    else:
                        # 进程已退出
                        os.remove(pid_file)
                        should_start = True
                else:
                    # 进程不存在
                    os.remove(pid_file)
                    should_start = True
                    
            except Exception as e:
                print(f"检查进程时出错: {e}")
                try:
                    os.remove(pid_file)
                except:
                    pass
                should_start = True
        
        if should_start:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(current_dir, "jnote.py")
            
            if not os.path.exists(script_path):
                print(f"错误：找不到 jnote.py，路径: {script_path}")
                return
            
            print(f"启动脚本: {script_path}")
            process = subprocess.Popen([sys.executable, script_path, username])
            self.jupyter_pid = process.pid
            print(f"Jupyter 窗口已启动，PID: {process.pid}")