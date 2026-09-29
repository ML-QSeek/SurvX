from fastapi.responses import FileResponse
from pathlib import Path

BASE_DIR = Path(__file__).parent
DOWNLOAD_DIR = BASE_DIR / "files"   # 专门放可下载的文件

def download(name: str):
    # 只允许文件名，不允许路径分隔符
    if "/" in name or "\\" in name or ".." in name:
        return {"error": "非法文件名"}

    file_path = (DOWNLOAD_DIR / name).resolve()

    # 二次确认：解析后仍在 DOWNLOAD_DIR 内
    if not str(file_path).startswith(str(DOWNLOAD_DIR.resolve())):
        return {"error": "非法路径"}

    if not file_path.exists() or not file_path.is_file():
        return {"error": f"文件不存在: {name}"}

    return FileResponse(
        path=file_path,
        filename=name,
        media_type="application/octet-stream",
    )