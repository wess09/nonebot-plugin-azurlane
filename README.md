<div align="center">
    <a href="https://v2.nonebot.dev/store">
    <img src="https://raw.githubusercontent.com/fllesser/nonebot-plugin-template/refs/heads/resource/.docs/NoneBotPlugin.svg" width="310" alt="logo"></a>

## ✨ nonebot-plugin-azurlane ✨
[![python](https://img.shields.io/badge/python-3.10|3.11|3.12|3.13|3.14-blue.svg)](https://www.python.org)
[![uv](https://img.shields.io/badge/package%20manager-uv-black?style=flat-square&logo=uv)](https://github.com/astral-sh/uv)
<br/>
[![ruff](https://img.shields.io/badge/code%20style-ruff-black?style=flat-square&logo=ruff)](https://github.com/astral-sh/ruff)
[![pre-commit](https://results.pre-commit.ci/badge/github/wess09/nonebot-plugin-azurlane/master.svg)](https://results.pre-commit.ci/latest/github/wess09/nonebot-plugin-azurlane/master)

</div>

碧蓝航线（AzurLane）NoneBot2 查询插件。对接 B 站碧蓝航线微信小程序后端 `le3-api`（逆向 + 模拟调用，接口约定见 [API.md](API.md)），面板用 [nonebot-plugin-htmlrender](https://github.com/kexue-z/nonebot-plugin-htmlrender) 渲染成图片发送。

> [!IMPORTANT]
> 查询结果**不展示区服**等敏感信息，区服仅用于服务端换算 `server_id`。

## 🎉 功能 / 指令

统一入口 `/blhx`，后接子命令：

| 指令 | 功能 |
| --- | --- |
| `/blhx 信息`（`info`） | 查询指挥官信息（等级、资源、收集率、待办副本等），图片面板展示 |
| `/blhx 建造记录 [数量]`（`记录`/`建造`） | 查询最近建造记录（默认 10 条，上限 500），图片面板展示 |
| `/blhx 绑定`（`登录`/`登陆`/`login`） | 发送一次性绑定二维码，扫码在 Web 登录页填写 UID 并选择区服完成绑定 |

## 📦 安装

<details>
<summary>从 PyPI 安装（推荐）</summary>

```bash
pip install nonebot-plugin-azurlane
# 或 uv
uv add nonebot-plugin-azurlane
```

在 `pyproject.toml` 中注册插件：

```toml
[tool.nonebot]
plugins = ["nonebot_plugin_azurlane"]
```

</details>

<details>
<summary>从源码运行</summary>

```bash
git clone https://github.com/wess09/nonebot-plugin-azurlane.git
cd nonebot-plugin-azurlane
uv sync            # 安装依赖（含 dev/test 组）
python bot.py      # 启动
```

- 需要先运行一个 OneBot 11 实现（[NapCat](https://github.com/NapNeko/NapCatQQ) / [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)），在 `.env` 的 `ONEBOT_WS_URLS` 中填写其正向 WebSocket 地址。

</details>

## ⚙️ 配置（.env）

<details>
<summary>核心配置</summary>

```env
DRIVER = ~fastapi+~httpx+~websockets
HOST = 0.0.0.0
PORT = 8081

# OneBot 11 正向 WS（OneBot 实现方地址）
ONEBOT_WS_URLS = ["ws://127.0.0.1:6700"]

# 绑定链接公开地址（Web 登录页；CDN 部署时改为 CDN 页面地址）
AZURLANE_BIND_BASE_URL = http://127.0.0.1:8081

# bot 服务公网地址（绑定回调跳转目标；CDN 部署时改为 bot 公网地址）
AZURLANE_API_BASE_URL = http://127.0.0.1:8081

# le3-api 可选 Cookie（部分接口不带可能拿不到数据）
AZURLANE_COOKIE =

# htmlrender 渲染配置：本机 Chromium/Edge 可执行文件路径
RENDER__PROVIDER = playwright
RENDER__STARTUP = warmup
RENDER__PROVIDER_CONFIG__EXECUTABLE_PATH = C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
RENDER__PROVIDER_CONFIG__SKIP_BROWSER_INSTALL = true

# 部署者管理员 QQ（可选，接收绑定通知）
AZURLANE_ADMIN_QQ =
```

</details>

<details>
<summary>渲染字体（重要）</summary>

面板通过 `@font-face` 用 `local()` 引用**系统字体**（不内嵌 base64），渲染前需把字体安装到系统（Windows：`C:\Windows\Fonts`）：

| 面板字体名 | 期望的系统字体 | 用途 |
| --- | --- | --- |
| `SourceHanSans` | `Source Han Sans CN` / `SC` / `TC` / `思源黑体` | 正文 |
| `MStiffHei` | `MStiffHei PRC` / `MStiffHei` | 标题 |
| `Agency` | `Agency FB` | 数字 / 英文标语 |

> `local()` 按候选逐个匹配系统注册的字体名，都不命中则 fallback 系统默认字体。

</details>

<details>
<summary>登录页部署到 CDN</summary>

登录页是纯静态自包含页面，可部署到 CDN 加速分发（包内 `src/nonebot_plugin_azurlane/static/login/` 目录：index.html + login_avatar.webp + login_bg.mp4）：

- `AZURLANE_BIND_BASE_URL` 设为 CDN 页面地址（`/绑定` 二维码指向它）
- `AZURLANE_API_BASE_URL` 设为 bot 公网地址（登录页绑定接口与回调跳转目标）
- 部署的 `index.html` 顶部 `const API_BASE = ''` 改为 bot 公网地址（页面与 bot 不同源时）
- bot 已开放 CORS（`allow_origins=["*"]`），支持跨域调用 `/api/*`
- 页面无 token 时提示"请先在 QQ 内发起绑定"，防止直接访问滥用

</details>

## 🔧 开发

<details>
<summary>测试与检查</summary>

```bash
uv run pytest tests/          # 运行测试
uv run ruff check src/ tests/ # lint
uv run ruff format src/ tests/ # 格式化
uvx basedpyright              # 静态类型检查
```

</details>

<details>
<summary>发布新版本（触发 Release 工作流）</summary>

```bash
uv run poe bump patch         # bump 版本 + 自动提交 + 打 tag（bump-my-version）
git push origin master
git push origin --tags        # 触发 release.yml：构建 -> 发布 PyPI -> 创建 GitHub Release
```

> 仓库含 e2e 测试（`tests/e2e_test.py`），配置 `AZURLANE_TEST_UID` / `AZURLANE_TEST_SERVER_ID` secrets 后，每次 push 会用真实账号跑完整链路（查询 + 渲染）。

</details>

## 📁 结构

<details>
<summary>目录结构</summary>

```
bot.py                          # NoneBot2 入口
src/nonebot_plugin_azurlane/
  __init__.py                   # 插件元信息 + CORS + Web 路由挂载
  config.py                     # 插件配置（AZURLANE_*）
  le3api.py                     # le3-api 客户端（异步 / 请求伪装 / 分页）
  server_status.py              # 区服列表与 ID 换算
  binding.py                    # 绑定数据存储（SQLite + localstore）
  session.py                    # 一次性绑定会话（token -> qq/cb，10 分钟有效）
  web.py                        # Web 登录页 / API（session / servers / bind / bind_cb）
  qr.py                         # 绑定二维码（圆角渐变 + 中心头像）
  commands.py                   # 机器人指令（/blhx 信息 / 建造记录 / 绑定）
  renderer.py                   # 渲染面板：读模板 + @font-face + 头像下载；htmlrender 出图
  templates/                    # HTML 面板模板 + 登录页
  data/                         # 渲染资源：logo / 吉祥物（字体走系统 local()）
  static/                       # 登录页素材（login_avatar / login_bg / login/ CDN 副本）
tests/                          # pytest + nonebug 测试
.github/workflows/              # CI（lint / 类型检查 / 测试 / e2e）/ release / release-drafter
```

</details>

## 📊 数据来源

| 数据 | 来源 |
| --- | --- |
| 指挥官详情 / 建造记录 | `le3-api.game.bilibili.com`（需伪装微信小程序请求头） |
| 区服列表与状态 | `server-checker.nanoda.work`（上游 `AzurLaneServerStatus`，实时状态） |
| 指挥官 / 舰船头像 | le3-api 返回的图片 URL（bot 下载后 base64 内嵌，失败回退本地 logo） |

## 已知局限

- 渠道服（华为/小米/应用宝等）`le3-api` 无数据，绑定渠道服会提示失败。
- 接口为逆向结果，无官方文档，小程序更新可能导致失效。
- 请勿高频调用，避免触发风控；勿用于商业用途。
