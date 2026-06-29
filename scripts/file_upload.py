"""
本地图片 → 可访问 URL 转换工具

当前策略（按优先级）：
  1. 通过 aigc.hkttok.com 的 upload API 上传（需补充 endpoint）
  2. 本地启动 HTTP 文件服务器 + ngrok 公网暴露（开发调试用）
  3. base64 data URI（仅适用于支持 data: URI 的 API）

使用方式：
  from file_upload import local_to_url
  url = local_to_url("E:/产品图/白底图.png")
"""

import io
import os
import base64
import mimetypes
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    requests = None


# ── 可配置项 ────────────────────────────────────────────
# aigc 上传接口（可通过环境变量 AIGC_UPLOAD_URL 覆盖）
_AIGC_UPLOAD_BASE = os.environ.get("AIGC_API_BASE", "https://aigc.hkttok.com").rstrip("/")
AIGC_UPLOAD_URL = os.environ.get(
    "AIGC_UPLOAD_URL",
    f"{_AIGC_UPLOAD_BASE}/jeecg-boot/openapi/call/file/upload"
)

# 本地文件服务端口（配合 ngrok / frp 使用）
LOCAL_SERVER_PORT = 18520


def _upload_via_aigc(file_path: str) -> Optional[str]:
    """通过 aigc API 上传文件，返回 URL"""
    if requests is None:
        return None
    try:
        # 导入 JeecgAuth（避免循环依赖）
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from jeecg_auth import JeecgAuth

        auth = JeecgAuth()
        headers = auth.get_headers()
        # 部分上传接口不使用 content-type application/json
        del headers["Content-Type"]

        path = Path(file_path)
        mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"

        with open(path, "rb") as f:
            files = {"file": (path.name, f, mime)}
            resp = requests.post(AIGC_UPLOAD_URL, headers=headers, files=files, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            # 根据实际响应调整字段名
            url = data.get("result", {}).get("url") or data.get("data", {}).get("url") or data.get("url")
            if url:
                return url

        print(f"  [upload] aigc upload failed ({resp.status_code}): {resp.text[:100]}")
        return None
    except Exception as e:
        print(f"  [upload] aigc upload error: {e}")
        return None


def _upload_via_local_server(file_path: str) -> Optional[str]:
    """通过本地 HTTP 文件服务器暴露文件（需配合 ngrok/frp）"""
    path = Path(file_path).resolve()
    if not path.is_file():
        return None

    # 返回 localhost URL（仅当 aigc API 在本地或同一内网时可用）
    return f"http://localhost:{LOCAL_SERVER_PORT}/{path.name}"


def _to_data_uri(file_path: str) -> Optional[str]:
    """转 base64 data URI（仅 API 支持 data: URI 时可用）"""
    try:
        path = Path(file_path)
        mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None


def local_to_url(file_path: str, strategy: str = "auto") -> str:
    """
    将本地图片路径转换为可访问的 URL

    参数:
      file_path: 本地文件路径
      strategy: 上传策略
        "auto"    - 按优先级依次尝试
        "aigc"    - 仅用 aigc upload API
        "local"   - 仅用本地 HTTP 服务
        "datauri" - 仅用 data URI

    返回:
      URL 字符串

    抛出:
      RuntimeError: 所有策略都失败
    """
    path = Path(file_path)
    if not path.is_file():
        raise RuntimeError(f"文件不存在: {file_path}")

    strategies = {
        "aigc": _upload_via_aigc,
        "local": _upload_via_local_server,
        "datauri": _to_data_uri,
    }

    if strategy == "auto":
        order = ["datauri"]
    else:
        order = [strategy]

    for name in order:
        fn = strategies.get(name)
        if fn is None:
            continue
        url = fn(str(file_path))
        if url:
            print(f"  [upload] {name}: {url}")
            return url

    # 最后兜底：直接返回文件路径（留给调用方处理）
    raise RuntimeError(
        f"无法将文件转换为 URL: {file_path}\n"
        f"请先补充 aigc 上传接口的 endpoint，或使用 --product 直接指定远程 URL"
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url = local_to_url(sys.argv[1])
        print(url)
