# 碧蓝航线 NoneBot2 机器人

基于 [NoneBot2](https://github.com/nonebot/nonebot2) 的碧蓝航线查询机器人，面板用 [nonebot-plugin-htmlrender](https://github.com/kexue-z/nonebot-plugin-htmlrender) 渲染成图片发送。

对接 B 站碧蓝航线微信小程序后端 `le3-api`（接口定义见 [API.md](API.md)，为逆向 + 模拟调用）。

## 功能

- `/指挥官` — 查询指挥官信息（等级、资源、收集率、待办副本等），以图片面板展示
- `/建造 [数量]` — 查询最近建造记录（默认 10 条，上限 500），以图片面板展示
- `/绑定` — 发送**绑定二维码**（一次性 token 会话），扫码在 Web 登录页填写 UID 并选择区服完成绑定
- 查询/面板**不展示区服**等敏感信息，区服仅用于服务端换算 `server_id`

## 绑定流程

1. QQ 发送 `/绑定`，bot 生成一次性 token 会话（10 分钟有效）并发送二维码图片
2. 扫码打开登录页（URL 只带短 token，不暴露 QQ/回调信息），填写 UID 并选区服
3. 绑定成功后前端跳回 bot 回调接口，bot 给 QQ 发私聊通知

## 安装

### 通过 NoneBot2 插件商店（NB-CLI）

```bash
nb plugin install nonebot-plugin-azurlane
```

### 从源码运行

```bash
# 1. 安装依赖
pip install -e .

# 2. 安装渲染用 Chromium（如已通过 htmlrender 自动安装可跳过）
python -m playwright install chromium
# 国内可加速：
PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/ python -m playwright install chromium

# 3. 配置 .env（OneBot 实现方地址、htmlrender 的 chromium 可执行路径等）
# 复制 .env 并填写 ONEBOT_WS_URLS、RENDER__PROVIDER_CONFIG__EXECUTABLE_PATH 等

# 4. 启动
python bot.py
```

- 需要先运行一个 OneBot 11 实现（如 [NapCat](https://github.com/NapNeko/NapCatQQ) / [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)），在 `.env` 的 `ONEBOT_WS_URLS` 中填写其正向 WebSocket 地址。
- 面板渲染使用 `nonebot-plugin-htmlrender`（0.8+ 需在 `.env` 配置 `RENDER__PROVIDER=playwright`，并指定 `RENDER__PROVIDER_CONFIG__EXECUTABLE_PATH` 指向 Chromium 可执行文件）。
- Web 登录页由 bot 自身通过 FastAPI 提供，地址见 `.env` 的 `AZURLANE_BIND_BASE_URL`（外部访问需要内网穿透）。

### 登录页部署到 CDN

登录页是**纯静态自包含**页面，可部署到 CDN 加速分发（`static/login/` 目录）：

```bash
# 部署 static/login/ 目录到 CDN 即可：index.html + login_bg.mp4 + login_avatar.webp
```

- `.env` 中 `AZURLANE_BIND_BASE_URL` 设为 CDN 页面地址（`/绑定` 指令的二维码指向它）
- `AZURLANE_API_BASE_URL` 设为 bot 公网地址（登录页绑定接口与回调跳转目标）
- 登录页 `static/login/index.html` 顶部 `API_BASE` 常量改为 bot 公网地址（若与页面不同源）
- bot 已开放 CORS（`allow_origins=["*"]`），支持跨域调用 `/api/*`
- 页面无 token 时提示"请先在 QQ 内发起绑定"，防止直接访问滥用

## 结构

```
bot.py                          # NoneBot2 入口
src/nonebot_plugin_azurlane/
  __init__.py                   # 插件元信息 + CORS + Web 路由挂载
  config.py                     # 插件配置
  le3api.py                     # le3-api 客户端（异步 / 请求伪装 / 分页）
  server_status.py              # 区服列表与 ID 换算
  binding.py                    # 绑定数据存储（SQLite + localstore）
  session.py                    # 一次性绑定会话（token -> qq/cb，10 分钟有效）
  web.py                        # Web 登录页 / API（session / servers / bind / bind_cb）
  qr.py                         # 绑定二维码（圆角渐变 + 中心头像）
  commands.py                   # 机器人指令（/指挥官 /建造 /绑定）
  templates/                    # HTML 面板模板 + 登录页
static/login/                   # CDN 部署的静态登录页（index.html + 视频 + 头像）
tests/                          # pytest + nonebug 测试
.github/workflows/              # CI / release
```

## 数据来源

| 数据 | 来源 |
| --- | --- |
| 指挥官详情 / 建造记录 | `le3-api.game.bilibili.com`（需伪装微信小程序请求头） |
| 区服列表与状态 | `server-checker.nanoda.work`（上游 `AzurLaneServerStatus`，实时状态） |

## 已知局限

- 渠道服（华为/小米/应用宝等）`le3-api` 无数据，绑定渠道服会提示失败。
- 接口为逆向结果，无官方文档，小程序更新可能导致失效。
- 请勿高频调用，避免触发风控；勿用于商业用途。
