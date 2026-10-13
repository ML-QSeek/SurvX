#!/usr/bin/env python3
"""
主程序入口
"""
import sys
import os
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import threading
import time
import atexit

# Windows DPI 支持
if sys.platform == 'win32':
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)

from window_manager import WindowManager
from utils import restart_application


def start_background_services():
    """
    启动后台服务进程（系统监控等）
    这个函数在窗口启动前调用
    """
    try:
        print("正在启动后台服务...")
        
        # 导入进程池模块
        from process_manager import get_process_pool, shutdown_process_pool
        
        # 获取进程池单例
        pool = get_process_pool(max_processes=15)
        
        # 1. 启动系统监控进程
        monitor_config = {
            "script_path": os.path.join(os.path.dirname(__file__), "system_monitor_daemon.py"),
            "config_name": "system_monitor",
            "script_name": "system_monitor_daemon.py",
            "server_url": "http://10.10.98.51:3213",
            "monitor_name": "client_001",
            "collect_interval": 10,
            "push_interval": 180,
            "cpu_threshold": 85.0,
            "memory_threshold": 80.0,
            "disk_threshold": 90.0
        }
        
        # 创建监控进程
        monitor_pid = pool.create_process(monitor_config)
        if monitor_pid:
            print(f"✅ 系统监控进程已启动: {monitor_pid}")
        else:
            print("⚠️ 系统监控进程启动失败")
        
        # 2. 注册退出清理函数（确保应用退出时清理进程池）
        atexit.register(shutdown_process_pool)
        
        print("✅ 后台服务启动完成")
        return pool
        
    except Exception as e:
        print(f"❌ 启动后台服务失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def perform_update_with_window(updater, root, update_window, progress_bar):
    """
    在新线程中执行更新操作
    """
    try:
        print("开始自动下载更新...")
        success = updater.perform_update()
        
        if success:
            # 更新成功
            progress_bar.stop()
            
            # 在主线程中更新UI
            def update_success():
                for widget in update_window.winfo_children():
                    widget.destroy()
                
                tk.Label(
                    update_window,
                    text="✅ 更新完成！\n应用即将重启...",
                    font=("微软雅黑", 12),
                    justify="center"
                ).pack(expand=True, fill="both", padx=20, pady=40)
                
                update_window.update()
                time.sleep(2)
                
                # 关闭所有窗口
                update_window.destroy()
                root.destroy()
                
                # 重启应用
                print("更新完成，正在重启应用...")
                restart_application()
                sys.exit(0)
            
            # 在主线程中执行UI更新
            root.after(0, update_success)
        else:
            # 更新失败
            progress_bar.stop()
            
            def update_failed():
                update_window.minsize(400, 200)
                
                for widget in update_window.winfo_children():
                    widget.destroy()
                
                tk.Label(
                    update_window,
                    text="❌ 更新失败！\n将使用当前版本启动应用",
                    font=("微软雅黑", 12),
                    justify="center",
                    fg="red"
                ).pack(expand=True, fill="both", padx=20, pady=40)
                
                tk.Button(
                    update_window,
                    text="确定",
                    command=lambda: [update_window.destroy(), root.destroy()],
                    width=10
                ).pack(pady=10)
                
                update_window.update()
                print("更新失败，继续启动应用")
            
            root.after(0, update_failed)
            
    except Exception as e:
        print(f"更新过程中出错: {e}")
        error_msg = str(e)  # 在这里捕获异常信息
        progress_bar.stop()
        
        def update_error(error_msg=error_msg):  # 通过参数传递
            for widget in update_window.winfo_children():
                widget.destroy()
            
            tk.Label(
                update_window,
                text=f"更新错误：{error_msg[:50]}\n将使用当前版本启动应用",
                font=("微软雅黑", 11),
                justify="center",
                fg="red",
                wraplength=350
            ).pack(expand=True, fill="both", padx=20, pady=20)
            
            tk.Button(
                update_window,
                text="确定",
                command=lambda: [update_window.destroy(), root.destroy()],
                width=10
            ).pack(pady=10)
            
            update_window.update()
        
        root.after(0, update_error)


def main():
    """主函数"""
    # 第一步：检查更新（如果存在updater模块）
    try:
        from updater import ClientUpdater
        
        updater = ClientUpdater("http://10.10.98.51/update1", "../../")
        
        if updater.check_for_updates():
            # 显示更新对话框
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            # 询问是否自动更新
            result = messagebox.askyesno(
                "发现新版本",
                "检测到新版本可用，是否立即自动更新？\n\n"
                "点击'是'：自动下载更新并重启\n"
                "点击'否'：跳过更新，直接启动应用",
                parent=root
            )
            
            if result:
                # 显示更新进度对话框
                update_window = tk.Toplevel(root)
                update_window.title("正在更新")
                update_window.attributes('-topmost', True)
                
                # 设置窗口大小和位置
                update_window.geometry("400x150")
                screen_width = update_window.winfo_screenwidth()
                screen_height = update_window.winfo_screenheight()
                x = (screen_width - 400) // 2
                y = (screen_height - 150) // 2
                update_window.geometry(f"400x150+{x}+{y}")
                
                # 禁止调整大小和关闭
                update_window.resizable(False, False)
                update_window.protocol("WM_DELETE_WINDOW", lambda: None)
                
                # 添加更新提示
                tk.Label(
                    update_window,
                    text="正在更新应用，请稍候...",
                    font=("微软雅黑", 12)
                ).pack(pady=20)
                
                # 添加进度条
                progress_bar = ttk.Progressbar(
                    update_window,
                    mode='indeterminate',
                    length=300
                )
                progress_bar.pack(pady=10)
                progress_bar.start()
                
                update_window.update()
                
                # 在新线程中执行更新
                threading.Thread(
                    target=perform_update_with_window,
                    args=(updater, root, update_window, progress_bar),
                    daemon=True
                ).start()
                
                # 运行主循环
                root.mainloop()
            else:
                print("用户选择跳过更新，直接启动应用")
                root.destroy()
                root.quit()
        else:
            print("没有发现新版本")
            
    except ImportError:
        print("updater模块不存在，跳过更新检查")
    except Exception as e:
        print(f"检查更新时发生错误，将直接启动应用: {e}")
    
    # 第二步：启动后台服务（在窗口启动前）
    process_pool = start_background_services()
    
    # 第三步：启动窗口应用
    print("正在启动窗口应用...")
    manager = WindowManager()
    manager.create_app()

if __name__ == '__main__':
    main()