# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

碧蓝航线（AzurLane）NoneBot2 查询机器人。对接 B 站碧蓝航线微信小程序后端 `le3-api`（逆向 + 模拟调用，接口约定见 [API.md](API.md)），用 nonebot-plugin-htmlrender 渲染 HTML 面板成图片发送。QQ 发 `/绑定` 得到二维码，扫码在 Web 登录页完成 UID+区服绑定。

## 常用命令

```bash
python bot.py                  # 启动 bot（OneBot V11 正向 WS 连接 NapCat/go-cqhttp）
python -m pip install -e ".[fastapi]"   # 安装依赖
python -m playwright install chromium   # 安装渲染浏览器（国内用 PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/ 加速）
```

## 架构

```
bot.py                 # 入口：nonebot.init -> 注册 OneBot 适配器 -> load_from_toml
src/plugins/azurlane/
  __init__.py          # require htmlrender；加载时挂载 CORS + FastAPI 路由（必须在启动前，on_startup 里 add_middleware 会报 "Cannot add middleware after an application has started"）
  config.py            # AZURLANE_* 配置（Cookie、绑定页 URL、API 地址、管理员 QQ）
  le3api.py            # le3-api 客户端：get/user_detail、get/build_record（分页）
  server_status.py     # 区服列表（server-checker.nanoda.work）+ 纯序号->le3_id 换算
  binding.py           # QQ -> (uid, server_id) 绑定存储，SQLite 持久化 data/azurlane.db
  session.py           # 一次性绑定会话：token -> {qq, cb}，纯内存 10 分钟过期
  web.py               # FastAPI 路由：/login、/api/session/<token>、/api/servers、/api/bind、/api/bind_cb、/static/*
  qr.py                # 绑定二维码：圆角码点 + 天蓝->海蓝水平渐变 + 中心圆形头像
  commands.py          # 指令：/指挥官、/建造、/绑定（发二维码）
  renderer.py          # 读 templates/*.html 替换占位符 -> htmlrender render_html -> bytes
  templates/           # commander.html / build_record.html / login.html
static/login/          # CDN 部署的静态登录页副本（index.html + 视频 + 头像）
```

## 绑定流程

1. `/绑定` → `session.create_session(qq, cb)` 生成一次性 token（10 分钟），`qr.make_bind_qr()` 生成二维码发图
2. 扫码打开 `login?t=<token>`，前端 `GET /api/session/<token>` 换 QQ，填 UID + 选区服
3. `POST /api/bind`（带 token）校验 le3-api 后写入 SQLite
4. 前端跳回 `/api/bind_cb?t=<token>&nickname=xx`，bot 消费会话并发私聊通知

## 关键约定

- **le3-api 调用**（le3api.py）：必须带微信小程序 UA + Referer 伪装请求头；响应统一信封 `{code, message, data}`，`code != 0` 抛 `APIError`。**必须用 `httpx.Client(trust_env=False)`**——本机系统代理（127.0.0.1:7890）会劫持导致 TLS 失败。
- **区服换算**：`AzurLaneServerStatus` 返回的服务器 `id` 是游戏协议纯序号，le3-api 需要 `100+id`（官网）/ `200+id`（iOS）；渠道服 `300+id` le3-api **无数据**，绑定需拒绝。换算在 `server_status.server_id_for()`。
- **敏感信息**：区服、server_id **只存服务端**（binding.py），绝不出现在任何 QQ 回复、HTML 面板中。这是硬性要求。
- **登录页静态化**：login.html 是纯静态自包含页面（QQ 从 URL `t` 参数经 /api/session 换取），可部署 CDN；`static/login/` 是它的副本。改模板后需 `cp src/plugins/azurlane/templates/login.html static/login/index.html` 同步。
- **渲染**（renderer.py）：htmlrender 0.8+ API 是 `render_html(html, ...)` 返回 `RenderedImage`（`.data` 为 bytes）；模板用 `{{KEY}}` 占位符手工替换，不引入 Jinja。需在 .env 配 `RENDER__PROVIDER=playwright` + `RENDER__PROVIDER_CONFIG__EXECUTABLE_PATH` 指向已装 Chromium。
- **collection_rate** 实测是字符串 `"0.0%"`（非文档的 0~1 小数），renderer 里 `_fmt_collection_rate` 两种都兼容。

## 运行前提

- 一个 OneBot 11 实现（NapCat/go-cqhttp）监听 `ONEBOT_WS_URLS` 指定地址，否则 bot 启动后持续重连（正常现象）。
- 8081 端口被本机另一进程（pywebio）占用，故 bot 用 8081 而非默认 8080。改端口需同步改 `.env`、`pyproject.toml`、`AZURLANE_BIND_BASE_URL`、`AZURLANE_API_BASE_URL`。
- Chromium 手动装在 `C:\Users\AzurLane\AppData\Local\ms-playwright\chromium_headless_shell-1234\...`。
- `data/azurlane.db`（SQLite）被 .gitignore 忽略，运行时自动创建；字体、static/、登录页资源会提交进仓库。
