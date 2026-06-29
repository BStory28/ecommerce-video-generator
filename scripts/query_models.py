#!/usr/bin/env python3
"""
查询 aigc.hkttok.com JeecgBoot OpenAPI 可用模型列表

用法:
  python query_models.py                              # 列出所有模型（从API发现）
  python query_models.py --model "模型名称"            # 查看模型详情
  python query_models.py --model "模型名称" --test     # 查看模型参数
  python query_models.py --json                       # JSON输出
  python query_models.py --key KEY --secret SECRET     # 指定凭据

认证方式: JeecgBoot OpenAPI 签名（MD5）
  环境变量:
    AIGC_APP_KEY     = 你的 appKey
    AIGC_APP_SECRET  = 你的 appSecret
  签名: MD5(appKey + appSecret + timestamp).hexdigest() 小写
"""

import argparse
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jeecg_auth import JeecgAuth


def discover_models(auth: JeecgAuth) -> list:
    """从 OpenAPI /models 发现可用模型"""
    url = auth.models_url()
    try:
        resp = requests.get(url, headers=auth.get_headers(), timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            models = data.get("data", data.get("result", data.get("models", [])))
            if isinstance(models, list):
                return models
            if isinstance(models, dict):
                return list(models.values())
            return []
        else:
            print(f"  API返回状态码: {resp.status_code}")
            try:
                print(f"  响应: {json.dumps(resp.json(), ensure_ascii=False, indent=2)[:500]}")
            except Exception:
                print(f"  响应: {resp.text[:300]}")
            return []
    except requests.RequestException as e:
        print(f"  请求失败: {e}")
        return []


def print_model_list(models: list):
    """格式化打印模型列表"""
    if not models:
        print("  （未发现模型）")
        return
    print(f"\n发现 {len(models)} 个模型:\n")
    for m in models:
        mid = m.get("id", m.get("modelId", m.get("name", "?")))
        mtype = m.get("type", m.get("modelType", m.get("supported_endpoint_types", "?")))
        desc = m.get("description", m.get("remark", ""))
        print(f"  [{mid}]")
        print(f"    类型: {mtype}")
        if desc:
            print(f"    描述: {desc}")
        print()


def print_model_detail(model_name: str, models: list):
    """查找并打印指定模型详情"""
    for m in models:
        mid = str(m.get("id", m.get("modelId", m.get("name", ""))))
        if model_name in mid or model_name.lower() in str(m).lower():
            print(json.dumps(m, indent=2, ensure_ascii=False))
            return
    print(f"未找到模型 '{model_name}'")


def main():
    parser = argparse.ArgumentParser(
        description="查询 aigc.hkttok.com OpenAPI 可用模型",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python query_models.py                          # 列出所有模型
  python query_models.py --model "2057735592451608578"  # 查看模型详情
  python query_models.py --json                   # JSON输出
  python query_models.py --key your_key --secret your_secret  # 指定凭据
        """,
    )
    parser.add_argument("--key", default="", help="appKey（默认从.env读取 AIGC_APP_KEY）")
    parser.add_argument("--secret", default="", help="appSecret（默认从.env读取 AIGC_APP_SECRET）")
    parser.add_argument("--model", help="查看指定模型详情（支持模糊匹配）")
    parser.add_argument("--json", action="store_true", help="JSON格式输出")
    args = parser.parse_args()

    auth = JeecgAuth(app_key=args.key, app_secret=args.secret)
    try:
        auth.validate()
    except ValueError as e:
        print(f"错误: {e}")
        print("请在 .env 文件中设置:")
        print("  AIGC_APP_KEY=your_app_key")
        print("  AIGC_APP_SECRET=your_app_secret")
        sys.exit(1)

    print(f"API Base: {auth.api_base}")
    print(f"APP Key:  {auth.app_key[:8]}...{auth.app_key[-4:]}")
    print()

    print("正在从 API 发现模型...")
    models = discover_models(auth)

    if not models:
        print("未获取到模型列表，请检查:")
        print("  1. AIGC_APP_KEY 和 AIGC_APP_SECRET 是否正确")
        print("  2. API 地址是否可访问")
        sys.exit(1)

    if args.model:
        print_model_detail(args.model, models)
    elif args.json:
        print(json.dumps(models, indent=2, ensure_ascii=False))
    else:
        print_model_list(models)


if __name__ == "__main__":
    main()
