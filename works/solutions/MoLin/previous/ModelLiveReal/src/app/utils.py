"""
工具函数
"""
import os
import sys

def restart_application():
    """重启当前应用"""
    python = sys.executable
    os.execl(python, python, *sys.argv)