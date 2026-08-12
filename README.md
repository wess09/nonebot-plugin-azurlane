# 碧蓝航线 NoneBot2 机器人

基于 [NoneBot2](https://github.com/nonebot/nonebot2) 的碧蓝航线查询机器人，面板用 [nonebot-plugin-htmlrender](https://github.com/kexue-z/nonebot-plugin-htmlrender) 渲染成图片发送。

对接 B 站碧蓝航线微信小程序后端 `le3-api`（接口定义见 [API.md](API.md)，为逆向 + 模拟调用）。

## 功能 / 指令

统一入口 `/blhx`，后接子命令：

- `/blhx 信息` — 查询指挥官信息（等级、资源、收集率、待办副本等），以图片面板展示
- `/blhx 建造记录 [数量]`（或 `/blhx 记录`） — 查询最近建造记录（默认 10 条，上限 500），以图片面板展示
- `/blhx 绑定`（或 `/blhx 登录` / `/blhx login`） — 发送**绑定二维码**（一次性 token 会话），扫码在 Web 登录页填写 UID 并选择区服完成绑定
- 查询/面板**不展示区服**等敏感信息，区服仅用于服务端换算 `server_id`

> 旧命令 `/指挥官`、`/建造`、`/绑定` 不再支持，统一改用 `/blhx`。

## 绑定流程

1. QQ 发送 `/blhx 绑定`，bot 生成一次性 token 会话（10 分钟有效）并发送二维码图片
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

# 2. 配置 .env（见下方「渲染与绑定配置」）

# 3. 启动
python bot.py
```

> 渲染用 Chromium 请参考下方「渲染配置」。插件不强制自动下载浏览器，建议用本机已有的 Edge 或手动安装的 Playwright Chromium 并通过 `RENDER__PROVIDER_CONFIG__EXECUTABLE_PATH` 指定。

- 需要先运行一个 OneBot 11 实现（如 [NapCat](https://github.com/NapNeko/NapCatQQ) / [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)），在 `.env` 的 `ONEBOT_WS_URLS` 中填写其正向 WebSocket 地址。
- Web 登录页由 bot 自身通过 FastAPI 提供，地址见 `.env` 的 `AZURLANE_BIND_BASE_URL`（外部访问需要内网穿透）。

## 渲染与绑定配置（.env）

```env
# ---- NoneBot 驱动（必须含 fastapi + httpx，bot 需要 API 服务与访问 le3-api）----
DRIVER = ~fastapi+~httpx+~websockets
HOST = 0.0.0.0
PORT = 8081

# ---- OneBot 11 正向 WS（OneBot 实现方地址）----
ONEBOT_WS_URLS = ["ws://127.0.0.1:6700"]
ONEBOT_ACCESS_TOKEN =

# ---- 绑定链接公开地址（Web 登录页；CDN 部署时改为 CDN 页面地址）----
AZURLANE_BIND_BASE_URL = http://127.0.0.1:8081

# ---- bot 服务公网地址（绑定回调跳转目标；CDN 部署时改为 bot 公网可访问地址）----
AZURLANE_API_BASE_URL = http://127.0.0.1:8081

# ---- le3-api 可选 Cookie（部分接口不带可能拿不到数据）----
AZURLANE_COOKIE =

# ---- htmlrender 渲染配置 ----
RENDER__PROVIDER = playwright
RENDER__STARTUP = warmup
RENDER__PROVIDER_CONFIG__ENGINE = chromium
# 指向本机 Edge 或已装的 Playwright Chromium 可执行文件（必须填，否则找不到浏览器）
RENDER__PROVIDER_CONFIG__EXECUTABLE_PATH = C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
RENDER__PROVIDER_CONFIG__SKIP_BROWSER_INSTALL = true

# ---- 部署者管理员 QQ（可选，接收绑定通知）----
AZURLANE_ADMIN_QQ =
```

### 字体（重要：渲染性能）

面板通过 `@font-face` 用 `local('字体名')` **直接引用系统字体，不内嵌 base64**。因此渲染前**需把面板用到的字体安装到系统**（Windows：`C:\Windows\Fonts`，或双击 TTF → 安装），否则字体 fallback 到系统默认、外观不同，且可能拖慢渲染。

本插件 `renderer.py` 里 `_SYSTEM_FACES` 定义的面板字体：

| 面板字体名 | 期望的系统字体 | 用途 |
| --- | --- | --- |
| `SourceHanSans` | `Source Han Sans CN` / `SC` / `TC` / `思源黑体` | 正文 |
| `MStiffHei` | `MStiffHei PRC` / `MStiffHei` | 标题 |
| `Agency` | `Agency FB` | 数字 / 英文标语 |

> `local()` 会按候选逐个匹配系统里真实注册的字体名，命中一个即可；都不命中则 fallback 到系统默认字体。
> 历史版本曾把字体 base64 内嵌进 HTML（27MB 级别），导致渲染慢；现已改为系统字体引用，面板 HTML 显著变小。

### 登录页部署到 CDN

登录页是**纯静态自包含**页面，可部署到 CDN 加速分发（包内 `src/nonebot_plugin_azurlane/static/login/` 目录）：

```bash
# 部署 src/nonebot_plugin_azurlane/static/login/ 目录到 CDN 即可：index.html + login_bg.mp4 + login_avatar.webp
```

- `.env` 中 `AZURLANE_BIND_BASE_URL` 设为 CDN 页面地址（`/绑定` 指令的二维码指向它）
- `AZURLANE_API_BASE_URL` 设为 bot 公网地址（登录页绑定接口与回调跳转目标）
- 登录页 `src/nonebot_plugin_azurlane/static/login/index.html` 顶部 `API_BASE` 常量改为 bot 公网地址（若与页面不同源）
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
  renderer.py                   # 渲染面板：读模板 + @font-face + 头像下载；htmlrender 出图
  templates/                    # HTML 面板模板 + 登录页
  data/                         # 渲染资源：logo / 吉祥物（字体走系统 local()，可不放这里）
  static/                       # 登录页素材（login_avatar / login_bg / login/ CDN 副本）
tests/                          # pytest + nonebug 测试
.github/workflows/              # CI / release
```

## 数据来源

| 数据 | 来源 |
| --- | --- |
| 指挥官详情 / 建造记录 | `le3-api.game.bilibili.com`（需伪装微信小程序请求头） |
| 区服列表与状态 | `server-checker.nanoda.work`（上游 `AzurLaneServerStatus`，实时状态） |
| 指挥官 / 舰船头像 | le3-api 返回的图片 URL（由 bot 下载后 base64 内嵌，避免渲染时联网失败坏图） |

## 渲染说明

- 面板由 bot 拼好 HTML 字符串交给 htmlrender（Playwright）截图，再以图片发送。
- **字体**：用 `local()` 引用系统字体，需预装（见上文「字体」），避免 27MB 级 base64 拖慢渲染。
- **头像/吉祥物**：吉祥物是本地文件 base64 内嵌；指挥官/舰船头像来自 le3-api 的图片 URL，由 bot 下载后转 base64——若 URL 为空或下载失败则回退到本地 `logo.webp`，保证面板不出现坏图，也不会让渲染卡在等待外网图片。
- 渲染超时：`renderer.py` 里 `_render` 的 `timeout_seconds`（默认 120）。网络慢或机器弱可适当调高。

## 已知局限

- 渠道服（华为/小米/应用宝等）`le3-api` 无数据，绑定渠道服会提示失败。
- 接口为逆向结果，无官方文档，小程序更新可能导致失效。
- 请勿高频调用，避免触发风控；勿用于商业用途。
