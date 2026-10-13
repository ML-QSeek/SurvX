import os
import json
import shutil
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Optional
import logging

class ClientUpdater:
    def __init__(self, base_url: str, local_root: str = "."):
        """
        Args:
            base_url: 服务器基础URL (如: http://your-server.com/update/)
            local_root: 本地根目录
        """
        self.base_url = base_url.rstrip('/')
        self.local_root = Path(local_root)
        self.manifest_url = f"{self.base_url}/manifest.json"
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def download_file(self, url: str, local_path: Path) -> bool:
        """下载单个文件"""
        try:
            # 确保目录存在
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # 下载文件
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.logger.info(f"下载成功: {local_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"下载失败 {url}: {e}")
            return False
    
    def delete_path(self, path_str: str) -> bool:
        """删除文件或目录"""
        try:
            target_path = self.local_root / path_str
            
            if not target_path.exists():
                self.logger.warning(f"路径不存在: {path_str}")
                return True
            
            if target_path.is_file():
                target_path.unlink()
                self.logger.info(f"删除文件: {path_str}")
            else:
                shutil.rmtree(target_path)
                self.logger.info(f"删除目录: {path_str}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"删除失败 {path_str}: {e}")
            return False
    
    def verify_file_hash(self, file_path: Path, expected_hash: str) -> bool:
        """验证文件哈希值"""
        if not expected_hash or not expected_hash.startswith("sha256:"):
            return True  # 不强制校验
        
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            actual_hash = f"sha256:{sha256_hash.hexdigest()}"
            return actual_hash == expected_hash
            
        except Exception as e:
            self.logger.error(f"哈希校验失败 {file_path}: {e}")
            return False
    
    def fetch_manifest(self) -> Optional[Dict]:
        """获取服务器清单"""
        try:
            response = requests.get(self.manifest_url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"获取清单失败: {e}")
            return None
    
    def perform_update(self) -> bool:
        """执行更新操作"""
        # 1. 获取清单
        self.logger.info("正在获取更新清单...")
        manifest = self.fetch_manifest()
        if not manifest:
            return False
        
        version = manifest.get("version", "unknown")
        self.logger.info(f"开始更新到版本: {version}")
        
        # 2. 执行删除操作
        delete_list = manifest.get("operations", {}).get("delete", [])
        self.logger.info(f"需要删除 {len(delete_list)} 个文件/目录")
        
        delete_success = True
        for path_str in delete_list:
            if not self.delete_path(path_str):
                delete_success = False
        
        # 3. 执行下载操作
        download_list = manifest.get("operations", {}).get("download", [])
        self.logger.info(f"需要下载 {len(download_list)} 个文件")
        
        download_success = True
        for file_info in download_list:
            remote_url = f"{self.base_url}/{file_info['url']}"
            local_path = self.local_root / file_info['local_path']
            expected_hash = file_info.get('hash', '')
            
            # 下载文件
            if self.download_file(remote_url, local_path):
                # 验证哈希
                if expected_hash and not self.verify_file_hash(local_path, expected_hash):
                    self.logger.error(f"文件校验失败: {local_path}")
                    local_path.unlink()  # 删除损坏的文件
                    download_success = False
            else:
                download_success = False
        
        # 4. 保存版本信息
        if download_success and delete_success:
            version_file = self.local_root / "version.txt"
            version_file.write_text(f"version={version}\nupdated={manifest.get('timestamp', '')}")
            self.logger.info("更新完成！")
            return True
        else:
            self.logger.error("更新失败，部分操作未完成")
            return False
    
    def check_for_updates(self) -> Optional[str]:
        """检查是否有更新"""
        try:
            # 读取本地版本
            local_version = "0.0.0"
            version_file = self.local_root / "version.txt"
            if version_file.exists():
                for line in version_file.read_text().splitlines():
                    if line.startswith("version="):
                        local_version = line.split("=")[1]
            
            # 获取服务器版本
            response = requests.get(f"{self.base_url}/latest-version.txt", timeout=5)
            server_version = response.text.strip()
            
            if server_version > local_version:
                return server_version
            return None
                
        except Exception as e:
            self.logger.error(f"检查更新失败: {e}")
            return None


# 使用示例
if __name__ == "__main__":
    # 配置
    SERVER_URL = "http://10.10.98.51/update"  # 修改为你的服务器地址
    LOCAL_DIR = "./"  # 本地应用目录
    
    # 创建更新器
    updater = ClientUpdater(SERVER_URL, LOCAL_DIR)
    
    # 可选：先检查更新
    new_version = updater.check_for_updates()
    if new_version:
        print(f"发现新版本: {new_version}")
        
        # 执行更新
        success = updater.perform_update()
        if success:
            print("更新成功！")
        else:
            print("更新失败，请检查网络或联系管理员")
    else:
        print("当前已是最新版本")