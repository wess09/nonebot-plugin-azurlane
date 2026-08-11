# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

碧蓝航线（AzurLane）NoneBot2 查询机器人。对接 B 站碧蓝航线微信小程序后端 `le3-api`（逆向 + 模拟调用，接口约定见 [API.md](API.md)），用 nonebot-plugin-htmlrender 渲染 HTML 面板成图片发送。QQ 发 `/绑定` 得到二维码，扫码在 Web 登录页完成 UID+区服绑定。

## 常用命令

```bash
uv run python bot.py          # 启动 bot（uv 环境，OneBot V11 正向 WS 连接 NapCat/go-cqhttp）
uv sync                       # 安装依赖（含 dev/test 组）
uv run pytest tests/          # 运行测试
uv run pytest tests/plugin_test.py::test_plugin_loads   # 运行单个测试
uv run poe test               # CI 用的带覆盖率测试（pytest --cov=src，见 pyproject [tool.poe.tasks]）
uvx basedpyright              # 静态类型检查（CI 同款；pyproject 里 reportUnknown* 已降为 warning）
uv run ruff check src/ tests/ # lint
uv run ruff format src/ tests/# 格式化
uv run python -m playwright install chromium   # 安装渲染浏览器（国内用 PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/ 加速）
```

## 架构

```
bot.py                 # 入口：nonebot.init -> 注册 OneBot 适配器 -> load_from_toml
src/nonebot_plugin_azurlane/
  __init__.py          # require htmlrender；加载时挂载 CORS + FastAPI 路由（必须在启动前，on_startup 里 add_middleware 会报 "Cannot add middleware after an application has started"）
  config.py            # AZURLANE_* 配置（Cookie、绑定页 URL、API 地址、管理员 QQ）
  le3api.py            # le3-api 客户端：get/user_detail、get/build_record（分页），httpx.AsyncClient（禁止同步）
  types.py             # le3-api 响应结构 TypedDict（UserDetail / BuildRecordResult 等）
  server_status.py     # 区服列表（server-checker.nanoda.work）+ 纯序号->le3_id 换算
  binding.py           # QQ -> (uid, server_id) 绑定存储，SQLite 存于 localstore 数据目录
  session.py           # 一次性绑定会话：token -> {qq, cb}，纯内存 10 分钟过期
  web.py               # FastAPI 路由：/login、/api/session/<token>、/api/servers、/api/bind、/api/bind_cb、/static/*（全部 async）
  qr.py                # 绑定二维码：圆角码点 + 天蓝->海蓝水平渐变 + 中心圆形头像（qrcode + Pillow）
  commands.py          # 指令：/指挥官、/建造、/绑定（发二维码）
  renderer.py          # 读 templates/*.html 替换占位符 -> htmlrender render_html -> bytes
  templates/           # commander.html / build_record.html / login.html
  data/                # 渲染资源：字体(.ttf)、logo、吉祥物（renderer 按包内路径读取）
  static/              # 登录页素材：login_avatar.webp / login_bg.mp4 / login/（CDN 静态副本）
tests/                 # pytest + nonebug（模板骨架，nonebug 中文消息对比在 Windows 有兼容问题，测试用加载 smoke test）
.github/workflows/     # CI / release（uv + basedpyright + prek + typos）
```

> 资源路径约定：渲染资源（`data/` 的字体/logo/吉祥物）与登录页素材（`static/`）都打进包内，代码用 `Path(__file__).parent / "data"`、`/ "static"` 定位（`templates/` 同理），随 wheel 一起分发，`pip install` 装完即用。仓库根目录的 `data/` 只剩 localstore 运行时产物（`nonebot_plugin_*`，gitignore 已忽略）。
> Python 版本固定在 `.python-version` = 3.12（模板 CI 同）。

## 绑定流程

1. `/绑定` → `session.create_session(qq, cb)` 生成一次性 token（10 分钟），`qr.make_bind_qr()` 生成二维码发图
2. 扫码打开 `login?t=<token>`，前端 `GET /api/session/<token>` 换 QQ，填 UID + 选区服
3. `POST /api/bind`（带 token）校验 le3-api 后写入 SQLite
4. 前端跳回 `/api/bind_cb?t=<token>&nickname=xx`，bot 消费会话并发私聊通知

## 关键约定

- **le3-api 调用**（le3api.py）：必须带微信小程序 UA + Referer 伪装请求头；响应统一信封 `{code, message, data}`，`code != 0` 抛 `APIError`。**必须用 `httpx.AsyncClient(trust_env=False)`**（异步 + 直连）——本机系统代理（127.0.0.1:7890）会劫持导致 TLS 失败；同步 `httpx.Client` 会阻塞事件循环，禁用。
- **区服换算**：`AzurLaneServerStatus` 返回的服务器 `id` 是游戏协议纯序号，le3-api 需要 `100+id`（官网）/ `200+id`（iOS）；渠道服 `300+id` le3-api **无数据**，绑定需拒绝。换算在 `server_status.server_id_for()`。
- **敏感信息**：区服、server_id **只存服务端**（binding.py），绝不出现在任何 QQ 回复、HTML 面板中。这是硬性要求。
- **登录页静态化**：login.html 是纯静态自包含页面（QQ 从 URL `t` 参数经 /api/session 换取），可部署 CDN；包内 `static/login/` 是它的副本。改模板后需 `cp src/nonebot_plugin_azurlane/templates/login.html src/nonebot_plugin_azurlane/static/login/index.html` 同步。
- **渲染**（renderer.py）：htmlrender 0.8+ API 是 `render_html(html, ...)` 返回 `RenderedImage`（`.data` 为 bytes）；模板用 `{{KEY}}` 占位符手工替换，不引入 Jinja。需在 .env 配 `RENDER__PROVIDER=playwright` + `RENDER__PROVIDER_CONFIG__EXECUTABLE_PATH` 指向已装 Chromium（本地另配了 `RENDER__PROVIDER_CONFIG__SKIP_BROWSER_INSTALL=true` 跳过自动安装）。
- **collection_rate** 实测是字符串 `"0.0%"`（非文档的 0~1 小数），renderer 里 `_fmt_collection_rate` 两种都兼容。

## 运行前提

- 一个 OneBot 11 实现（NapCat/go-cqhttp）监听 `ONEBOT_WS_URLS` 指定地址，否则 bot 启动后持续重连（正常现象）。
- bot 监听 8081（`.env` 的 `PORT`）而非 NoneBot 默认 8080。改端口需同步改 `.env` 的 `PORT`、`AZURLANE_BIND_BASE_URL`、`AZURLANE_API_BASE_URL`（`.env` 是端口唯一来源，pyproject.toml 无端口配置）。
- Chromium 手动装在 `C:\Users\AzurLane\AppData\Local\ms-playwright\chromium_headless_shell-1234\...`。
- 绑定数据 SQLite 存于 nonebot-plugin-localstore 数据目录（`get_plugin_data_dir()/azurlane.db`），运行时自动创建；`data/`（字体/logo/吉祥物）、`static/`（登录页素材）、登录页资源随包打进 wheel 已提交进仓库。
