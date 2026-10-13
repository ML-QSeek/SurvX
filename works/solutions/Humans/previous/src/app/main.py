import sys
import os
import time
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from window_manager import WindowManager
from updater import ClientUpdater


# ============================================================
# 🔧 全局配置
# ============================================================

SURVX_WEBSOCKET_HOST = '127.0.0.1'
SURVX_WEBSOCKET_PORT = 8765


# ============================================================
# 应用程序管理
# ============================================================

def restart_application():
    """重启当前应用"""
    python = sys.executable
    os.execl(python, python, *sys.argv)


def main():
    # 设置DPI感知（Windows）
    if sys.platform == 'win32':
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass

    # ============================================================
    # 第一步：检查更新
    # ============================================================
    '''
    try:
        updater = ClientUpdater("http://10.10.98.51/update", "../../")

        if updater.check_for_updates():
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            result = messagebox.askyesno(
                "发现新版本",
                "检测到新版本可用，是否立即自动更新？\n\n"
                "点击'是'：自动下载更新并重启\n"
                "点击'否'：跳过更新，直接启动应用",
                parent=root
            )

            if result:
                update_window = tk.Toplevel(root)
                update_window.title("正在更新")
                update_window.attributes('-topmost', True)
                update_window.geometry("400x150")
                screen_width = update_window.winfo_screenwidth()
                screen_height = update_window.winfo_screenheight()
                x = (screen_width - 400) // 2
                y = (screen_height - 150) // 2
                update_window.geometry(f"400x150+{x}+{y}")
                update_window.resizable(False, False)
                update_window.protocol("WM_DELETE_WINDOW", lambda: None)

                tk.Label(
                    update_window,
                    text="正在更新应用，请稍候...",
                    font=("微软雅黑", 12)
                ).pack(pady=20)

                progress_bar = ttk.Progressbar(
                    update_window,
                    mode='indeterminate',
                    length=300
                )
                progress_bar.pack(pady=10)
                progress_bar.start()
                update_window.update()

                def perform_update():
                    try:
                        print("开始自动下载更新...")
                        success = updater.perform_update()

                        if success:
                            progress_bar.stop()
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
                            update_window.destroy()
                            root.destroy()
                            restart_application()
                            sys.exit(0)
                        else:
                            progress_bar.stop()
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
                    except Exception as e:
                        print(f"更新过程中出错: {e}")
                        progress_bar.stop()
                        for widget in update_window.winfo_children():
                            widget.destroy()

                        tk.Label(
                            update_window,
                            text=f"更新错误：{str(e)[:50]}\n将使用当前版本启动应用",
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

                threading.Thread(target=perform_update, daemon=True).start()
                root.mainloop()
                return
            else:
                print("用户选择跳过更新，直接启动应用")
                root.destroy()
                root.quit()
        else:
            print("没有发现新版本")

    except Exception as e:
        print(f"检查更新时发生错误，将直接启动应用: {e}")
    '''
    # ============================================================
    # 第二步：启动 WindowManager (加载登录页面)
    #    端口通过构造函数传入
    # ============================================================
    print("正在启动应用...")

    try:
        manager = WindowManager(
            server_port=SURVX_WEBSOCKET_PORT,
            server_host=SURVX_WEBSOCKET_HOST
        )
        manager.create_app()
    except Exception as e:
        print(f"应用启动失败: {e}")
    finally:
        print("应用已退出")


if __name__ == '__main__':
    main()