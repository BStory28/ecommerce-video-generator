# AI视频脚本提炼与生成器

> **Version:** 1.1.0 | [SKILL.md](SKILL.md) | [Changelog](#)

国际化电商视频管线 **Skill3** — 读取分镜脚本 JSON，AI 压缩至 2000 字以内，提取时长和产品参考图，构建视频生成请求 payload 并提交 aigc API。

## 管线定位

```
Skill1: ecommerce-product-info-generator → product_layer.png + selling_points.json
                    ↓
Skill2: ecommerce-video-script-generator → storyboard.json
                    ↓
Skill3 ← 本技能       → 输出: video_payload.json (可提交 aigc API)
```

## 功能

- 读取分镜脚本 JSON，AI 压缩至 ≤2000 字
- 提取总时长和产品参考图
- 构建视频生成请求 payload
- 支持预览模式（仅生成 payload）和提交模式（调用 aigc API）
- 支持生成 Word 文档（`.docx`）

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 预览模式（只生成 payload 文件，不提交）
python scripts/generate_video.py \
  --script storyboard.json \
  --product product_layer.png

# 提交模式（需配置 AIGC_APP_KEY / AIGC_APP_SECRET 环境变量）
python scripts/generate_video.py \
  --script storyboard.json \
  --product product_layer.png \
  --submit
```

## 环境变量

| 变量 | 必填 | 说明 |
|------|------|------|
| `AIGC_APP_KEY` | ✅（提交模式） | 应用 Key |
| `AIGC_APP_SECRET` | ✅（提交模式） | 应用密钥 |

## 输入参数

| 参数 | 必填 | 说明 |
|------|------|------|
| `--script` | ✅ | 分镜脚本 JSON 路径（Skill2 输出） |
| `--product` | ✅ | 产品白底图路径（Skill1 输出） |
| `--submit` | ❌ | 是否提交到 aigc API |
| `--doc` | ❌ | 输出 Word 文档路径 |

## 输出文件

| 文件 | 说明 |
|------|------|
| `output/video_payload.json` | 视频生成请求 payload（预览模式） |
| `output/response.json` | aigc API 响应（提交模式） |
| `output/*.docx` | Word 文档（可选） |

## 上下游

- **上游**: [ecommerce-product-info-generator](https://github.com/BStory28/ecommerce-product-info-generator) — 产品白底图
- **上游**: [ecommerce-video-script-generator](https://github.com/BStory28/ecommerce-video-script-generator) — 分镜脚本
- 本技能是管线最终环节，无下游

## 注意事项

- 提交模式需要先配置 `AIGC_APP_KEY` 和 `AIGC_APP_SECRET` 环境变量
- 脚本会自动将产品图上传为 URL 用于 API 请求
- AI 会对分镜脚本进行压缩至 2000 字以内（符合 aigc API 限制）
