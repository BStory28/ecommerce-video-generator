# AI视频生成 API 接口文档

## 概述

本管线统一使用 **aigc.hkttok.com JeecgBoot OpenAPI** 进行图生视频和文生视频生成。
语音合成（TTS）和 FFmpeg 编辑为辅助功能，可根据目标市场选用外部服务。

---

## 1. 认证方式（JeecgBoot OpenAPI 签名）

```python
# 使用 scripts/jeecg_auth.py
from jeecg_auth import JeecgAuth

auth = JeecgAuth(app_key="xxx", app_secret="xxx")
headers = auth.get_headers()
# → {
#     "X-Tenant-Id": "1000",
#     "appkey": "xxx",
#     "signature": "md5(appkey+appsecret+timestamp)",
#     "timestamp": "1718000000000",
#     "Content-Type": "application/json"
#   }
```

### 签名算法

```
sign_str = appKey + appSecret + str(timestamp_ms)
signature = MD5(sign_str.encode("utf-8")).hexdigest()  # 小写32位
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AIGC_API_BASE` | API 基础地址 | `https://aigc.hkttok.com` |
| `AIGC_APP_KEY` | 应用 Key（必填） | — |
| `AIGC_APP_SECRET` | 应用 Secret（必填） | — |
| `AIGC_TENANT_ID` | 租户 ID | `1000` |
| `AIGC_IMAGE_MODEL` | 图片模型 ID | `2049087333668446209`（Seedream 5.0 Lite） |
| `AIGC_VIDEO_MODEL` | 视频模型 ID | `2043940117168529416`（Seedance 2.0 fast） |

---

## 2. API 端点

所有请求通过网关转发：`{AIGC_API_BASE}/jeecg-boot/openapi/call/{path}`

### 2.1 模型查询

```
GET /jeecg-boot/openapi/call/models
```

获取可用模型列表，返回所有模型 ID、名称、类型和能力说明。

### 2.2 图片生成

```
POST /jeecg-boot/openapi/call/generation/image/submit
Content-Type: application/json

{
  "model": "{model_id}",
  "prompt": "产品展示图，白色磨砂瓶身，金色泵头",
  "negative_prompt": "文字，水印，杂乱背景",
  "image": "{base64_encoded_image或URL}",
  "image_resolution": "1080x1920",
  "n": 1,
  "size": "1080x1920",
  "response_format": "b64_json",
  "parameters": {
    "product_preservation_level": "high"
  }
}

Response:
{
  "id": "task_xxx",
  "status": "pending"
}
```

### 2.3 查询图片结果

```
GET /jeecg-boot/openapi/call/generation/image/query?id={taskId}

Response:
{
  "status": "SUCCESS",
  "url": "https://cdn.hkttok.com/images/xxx.png",
  ...
}
```

### 2.4 视频生成

```
POST /jeecg-boot/openapi/call/generation/video/submit
Content-Type: application/json

{
  "model": "{video_model_id}",
  "prompt": "展示亮黄色金属罐装茶饮，泰国人物手持，泰式庭院背景，暖调阳光",
  "images": [
    "/path/to/product_layer.png",
    "/path/to/people_layer.png",
    "/path/to/continuity_frame.png"
  ],
  "duration": 5,
  "size": "1080x1920"
}

Response:
{
  "id": "task_abc123",
  "status": "pending"
}
```

### 2.5 查询视频结果

```
GET /jeecg-boot/openapi/call/generation/video/query?id={taskId}

Response:
{
  "taskStatus": "SUCCESS",
  "url": "https://cdn.hkttok.com/videos/xxx.mp4",
  "duration": 5.0,
  ...
}
```

---

## 3. 图片生成流程（generate_base_image.py）

```
Step 1: 调用 /generation/image/submit
  → 返回 taskId

Step 2: 轮询 /generation/image/query
  → 2秒间隔，最多60次（120秒超时）
  → 状态为 SUCCESS → 获取 URL 并下载
  → 解码：base64 → 文件 或 URL → requests.get → 文件
```

---

## 4. 视频生成流程（generate_video.py）

```
Step 1: 解析分镜 JSON → shots 列表
Step 2: 按段（segment）逐镜生成
  - 每镜调用 /generation/video/submit + 轮询
  - 跨段边界传入 continuity_frame（上一段尾帧）
  - 图生视频优先（有 product_layer 参考图）
  - 文生视频补充（无参考图场景）
Step 3: FFmpeg 拼接所有视频片段
Step 4: 可选：叠加音频/TTS/字幕/调色
Step 5: 输出最终 MP4
```

---

## 5. FFmpeg 视频编辑（本地）

```bash
# 拼接视频
ffmpeg -f concat -safe 0 -i filelist.txt -c copy output.mp4

# 叠加字幕（SRT）
ffmpeg -i video.mp4 -vf "subtitles=subtitle.srt:force_style='FontName=Noto+Sans+JP,FontSize=24'" output_sub.mp4

# 调色
ffmpeg -i video.mp4 -vf "eq=brightness=0.05:saturation=0.8:contrast=1.1" output_color.mp4

# 音频叠加
ffmpeg -i video.mp4 -i bgm.mp3 -i voice.mp3 \
  -filter_complex "[1:a]volume=0.3[bgm];[2:a]volume=1.0[voice];[bgm][voice]amix=inputs=2:duration=first" \
  output_audio.mp4

# 提取尾帧
ffmpeg -sseof -1 -i video.mp4 -vframes 1 last_frame.png
```

---

## 6. 语音合成 API（可选外部服务）

### 6.1 ElevenLabs（多语言推荐）

```
POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
Authorization: Bearer {key}

{
  "text": "28日間使って、本音で語ります",
  "model_id": "eleven_multilingual_v2",
  "voice_settings": { "stability": 0.5, "similarity_boost": 0.75 }
}
```

### 6.2 微软 Azure TTS（多语言）

```
POST https://{region}.tts.speech.microsoft.com/cognitiveservices/v1
Ocp-Apim-Subscription-Key: {key}

<speak version='1.0' xml:lang='ja-JP'>
  <voice name='ja-JP-NanamiNeural'>テキスト</voice>
</speak>
```

---

## 7. 市场适配参考

| 市场 | 字幕字体 | TTS | 调色参数 |
|------|---------|-----|---------|
| 中国 | Noto+Sans+SC | Azure/TTS | brightness=0.03,saturation=0.95,contrast=1.05 |
| 北美 | Montserrat | ElevenLabs | brightness=0.00,saturation=1.10,contrast=1.10 |
| 欧洲 | Helvetica | ElevenLabs | brightness=-0.02,saturation=0.85,contrast=1.15 |
| 日本 | Noto+Sans+JP | Azure | brightness=0.05,saturation=0.80,contrast=1.05 |
| 韩国 | Noto+Sans+KR | Azure | brightness=0.08,saturation=0.90,contrast=1.00 |
| 东南亚 | Arial | ElevenLabs | brightness=0.03,saturation=1.20,contrast=1.05 |
| 巴西 | Arial | ElevenLabs | brightness=0.05,saturation=1.25,contrast=1.10 |
