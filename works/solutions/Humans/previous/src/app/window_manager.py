import webview
import threading
import time
import os
import sys
import json
import requests
import tkinter as tk
import subprocess
import signal
import atexit
from api import Api
from connection_pool import ConnectionPool
from credential_manager import CredentialManager


class WindowManager:
    def __init__(self, server_port=8765, server_host='127.0.0.1'):
        self.window = None
        self.user_data = None
        self.window_width = 800
        self.window_height = 480
        self.is_hidden = False
        self.backend_process = None
        self.is_closing = False
        
        # 服务器配置 (从外部传入)
        self.server_port = server_port
        self.server_host = server_host
        
        # 创建连接池
        self.connection_pool = ConnectionPool()
        
        # 创建凭证管理器
        self.credential_manager = CredentialManager()
        
        # 创建Api实例
        self.api = Api()
        self.api.set_window_manager(self)
        
        # 注册退出处理函数
        atexit.register(self.cleanup)
    
    def start_backend_as_new_process(self):
        """启动 SurvX 消息队列服务器 (server.py) 作为独立进程"""
        try:
            # 查找 server.py
            script_path = os.path.join(os.path.dirname(__file__), 'server.py')
            if not os.path.exists(script_path):
                script_path = os.path.join(os.path.dirname(__file__), '..', 'server.py')
            
            if not os.path.exists(script_path):
                print(f"错误：找不到 server.py")
                return None
            
            print(f"正在启动 SurvX 服务器 (端口 {self.server_port})...")
            
            if sys.platform == 'win32':
                DETACHED_PROCESS = 0x00000008
                CREATE_NEW_PROCESS_GROUP = 0x00000200
                
                process = subprocess.Popen(
                    [sys.executable, script_path, self.server_host, str(self.server_port)],
                    cwd=os.path.dirname(script_path),
                    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True
                )
            else:
                process = subprocess.Popen(
                    [sys.executable, script_path, self.server_host, str(self.server_port)],
                    cwd=os.path.dirname(script_path),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    close_fds=True,
                    start_new_session=True
                )
            
            print(f"✅ SurvX 服务器已启动，PID: {process.pid}")
            return process
            
        except Exception as e:
            print(f"❌ 启动 SurvX 服务器失败: {e}")
            return None
    
    def kill_backend_process(self):
        """彻底杀死后端进程（包括子进程）"""
        if self.backend_process is None:
            return
        
        if self.backend_process.poll() is not None:
            print(f"后端进程 {self.backend_process.pid} 已经结束")
            self.backend_process = None
            return
        
        try:
            print(f"正在关闭后端进程 (PID: {self.backend_process.pid})...")
            
            if sys.platform == 'win32':
                result = subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(self.backend_process.pid)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    print(f"✅ 已关闭后端进程 {self.backend_process.pid}")
                else:
                    print(f"关闭进程失败: {result.stderr}")
                    try:
                        self.backend_process.terminate()
                        self.backend_process.wait(timeout=3)
                        print(f"进程 {self.backend_process.pid} 已终止")
                    except subprocess.TimeoutExpired:
                        self.backend_process.kill()
                        print(f"进程 {self.backend_process.pid} 已被强制杀死")
            else:
                try:
                    os.killpg(os.getpgid(self.backend_process.pid), signal.SIGTERM)
                    time.sleep(2)
                    if self.backend_process.poll() is None:
                        os.killpg(os.getpgid(self.backend_process.pid), signal.SIGKILL)
                        print(f"已强制关闭进程组 {self.backend_process.pid}")
                except ProcessLookupError:
                    print(f"进程 {self.backend_process.pid} 已不存在")
                except Exception as e:
                    print(f"关闭进程时出错: {e}")
                    try:
                        self.backend_process.terminate()
                        self.backend_process.kill()
                    except:
                        pass
        except Exception as e:
            print(f"关闭进程时出错: {e}")
        finally:
            self.backend_process = None
    
    def on_window_closing(self):
        """窗口关闭时的回调"""
        print("窗口正在关闭，清理资源...")
        self.is_closing = True
        self.cleanup()
    
    def cleanup(self):
        """清理资源，关闭后端进程"""
        if self.is_closing:
            return
        
        self.is_closing = True
        print("开始清理资源...")
        
        if self.backend_process:
            self.kill_backend_process()
        
        print("清理完成")
    
    def create_app(self):
        """创建应用窗口"""
        if hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath("../../")
        
        login_path = os.path.join(base_path, "src/ui/index.html")
        dash_path = os.path.join(base_path, "src/ui/main.html")
        self.dash_path = dash_path
        
        if not os.path.exists(login_path):
            print(f"错误: {login_path} 文件不存在!")
            return
        
        self.window = webview.create_window(
            '请先登录',
            url=f'file://{login_path}',
            width=self.window_width,
            height=self.window_height,
            x=-2000,
            y=-2000,
            resizable=False,
            frameless=True,
            min_size=(800, 480),
            easy_drag=True,
            on_top=False,
            js_api=self.api
        )
        
        webview.start(debug=True, func=self.after_start, private_mode=False)
    
    def after_start(self):
        """webview启动后的回调"""
        if self.window:
            self.monitor_window_close()
            threading.Timer(3, self.show_visible_window).start()
            threading.Thread(target=self.test_server_connections, daemon=True).start()
    
    def monitor_window_close(self):
        """监控窗口是否关闭"""
        def check():
            while not self.is_closing:
                try:
                    if self.window and not self.window.closed:
                        time.sleep(1)
                    else:
                        print("检测到窗口关闭")
                        self.cleanup()
                        break
                except Exception as e:
                    print(f"监控窗口时出错: {e}")
                    break
        
        threading.Thread(target=check, daemon=True).start()
    
    def test_server_connections(self):
        """测试服务器连接"""
        print("正在测试服务器连接...")
        print("不需要连接服务器!")
        '''
        server = self.connection_pool.get_available_server()
        if server:
            print(f"已选择服务器: {server['name']} ({server['url']})")
        else:
            print("警告：没有可用的服务器，登录后可能会无法加载主页面")
        '''
    
    def show_visible_window(self):
        """显示窗口到屏幕中央"""
        try:
            root = tk.Tk()
            root.withdraw()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            current_width = self.window_width
            current_height = self.window_height
            x = (screen_width - current_width) // 2
            y = (screen_height - current_height) // 2
            
            self.window.move(x, y)
            
            root.destroy()
            root.quit()
        except Exception as e:
            print(f"显示窗口失败: {e}")
    
    def center_window(self):
        """供JavaScript调用的居中方法"""
        try:
            root = tk.Tk()
            root.withdraw()
            
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            current_width = self.window_width
            current_height = self.window_height
            
            x = (screen_width - current_width) // 2
            y = (screen_height - current_height) // 2
            
            self.window.move(x, y)
            print(f"JavaScript调用：窗口已居中 ({x}, {y})")
            
            root.destroy()
            root.quit()
            return True
        except Exception as e:
            print(f"JavaScript调用居中失败: {e}")
            return False
    
    def handle_login(self, user_data):
        """处理登录请求"""
        print(f"收到登录请求: 用户名={user_data.get('username', '')}")
        
        #success = self.validate_login(user_data)
        success = True
        
        if success:
            self.user_data = user_data
            
            remember_password = user_data.get('rememberPassword', False)
            auto_login = user_data.get('autoLogin', False)
            password = user_data.get('password', '')
            
            if remember_password:
                self.credential_manager.save_credentials(
                    username=user_data['username'],
                    password=password,
                    remember_password=remember_password,
                    auto_login=auto_login
                )
            elif auto_login:
                self.credential_manager.save_credentials(
                    username=user_data['username'],
                    password="",
                    remember_password=False,
                    auto_login=True
                )
            
            return {"success": True, "message": "登录成功"}
        else:
            return {"success": False, "message": "用户名或密码错误"}
    
    '''
    def validate_login(self, user_data):
        """验证用户名和密码"""
        username = user_data.get('username', '').strip()
        password = user_data.get('password', '').strip()
        
        Url = 'http://10.10.98.51/test/sys/qi/qi00002/qi04635C/MQDataAPICtest.php'
        Sub_Field = {
            'sflag': 'login',
            'sid': '_04',
            'username': username,
            'password': password,
        } 
        r = requests.post(Url, data=Sub_Field)
        rtext = r.text.strip()[1:]
        rtext = json.loads(rtext)
        if type(rtext) == list:
            print(rtext[0]['Q14123103'] + '：登录成功！')
            return True
        return False
    '''
    def get_saved_credentials(self):
        """获取保存的登录凭证（供JavaScript调用）"""
        try:
            credentials = self.credential_manager.get_credentials()
            print(f"获取保存的凭证: {credentials.get('username', '')}")
            return credentials
        except Exception as e:
            print(f"获取保存凭证失败: {e}")
            return {
                'has_saved': False,
                'username': "",
                'password': "",
                'rememberPassword': False,
                'autoLogin': False
            }
    
    def clear_saved_credentials(self):
        """清除保存的登录凭证（供JavaScript调用）"""
        try:
            success = self.credential_manager.clear_credentials()
            return {"success": success}
        except Exception as e:
            print(f"清除保存凭证失败: {e}")
            return {"success": False}
    
    def load_main_page(self):
        """加载主应用页面"""
        username = self.user_data.get('username', '').strip()
        
        # 启动 SurvX 服务器
        print(f"正在启动 SurvX 服务器...")
        self.backend_process = self.start_backend_as_new_process()
        
        if self.backend_process is None:
            print("⚠️ 警告：SurvX 服务器启动失败，主页面可能无法连接 WebSocket")
        else:
            # 等待服务器启动
            time.sleep(2)
            print(f"✅ SurvX 服务器已运行 (PID: {self.backend_process.pid})")
        
        # 调整窗口大小
        new_width = 1800
        new_height = 900
        self.window.resize(new_width, new_height)
        
        root = tk.Tk()
        root.withdraw()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - new_width) // 2
        y = (screen_height - new_height) // 2
        self.window.move(x, y)
        
        self.window_width = new_width
        self.window_height = new_height
        
        # 加载主页面，把端口传给前端
        server_url = self.dash_path
        full_url = f"{server_url}?par={username}&ws_port={self.server_port}&ws_host={self.server_host}"
        print(f"正在加载主页面: {full_url}")
        self.window.load_url(full_url)
        
        root.destroy()
        root.quit()