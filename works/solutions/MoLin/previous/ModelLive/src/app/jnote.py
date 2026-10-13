# -*- coding: utf-8 -*-
"""
Created on Wed May 27 12:20:00 2026

@author: Administrator
"""

import sys
import webview
import os
import tempfile
import tkinter as tk
import signal

def main():
    username = sys.argv[1] if len(sys.argv) > 1 else "default"
    
    # 忽略中断信号，避免报错
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    
    # 创建 PID 记录文件
    pid_file = os.path.join(tempfile.gettempdir(), f"jupyter_{username}.pid")
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))
    
    hub_url = "http://10.10.98.123:30080"
    storage_path = os.path.join(os.path.expanduser("~"), f".jupyter_{username}")
    os.makedirs(storage_path, exist_ok=True)
    
    def on_loaded(window):
        window.load_url(f"{hub_url}/hub/login")
        window.evaluate_js(f"""
            setTimeout(function() {{
                var u = document.querySelector('input[name="username"]');
                var p = document.querySelector('input[name="password"]');
                if (u && p) {{
                    u.value = '{username}';
                    p.value = '{username}';
                    document.querySelector('form').submit();
                }}
            }}, 500);
        """)
    
    main_width = 1600
    main_height = 800
    
    # 获取屏幕尺寸计算居中
    root = tk.Tk()
    root.withdraw()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - main_width) // 2
    y = (screen_height - main_height) // 2
    root.destroy()
    
    window = webview.create_window(
        f"ModelLive-策略研究 - {username}",
        width=main_width,
        height=main_height,
        x=x,
        y=y,
    )
    
    # 窗口关闭时删除 PID 文件并强制退出
    def on_closed():
        if os.path.exists(pid_file):
            os.remove(pid_file)
        # 强制退出进程
        os._exit(0)
    
    window.events.closed += on_closed
    webview.start(on_loaded, window, private_mode=False, storage_path=storage_path)

if __name__ == '__main__':
    main()