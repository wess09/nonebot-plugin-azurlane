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

喵呜~ 如果本喵帮到了指挥官,记得点个 ⭐ Star 支持一下喵~

<img width="100%" src="https://starify.komoridevs.icu/api/starify?owner=wess09&repo=nonebot-plugin-azurlane" alt="starify" />

喵呜~ 欢迎指挥官!这里是 **nonebot-plugin-azurlane**,一只专属于您的碧蓝航线查询小助手喵。在 QQ 里喊本喵一声,就能查到指挥官信息、建造记录,绑定后随时一键查询,所有结果都会渲染成漂漂亮亮的图片面板送给指挥官喵~

> [!IMPORTANT]
> 指挥官请放心,查询结果**不会展示**区服等敏感信息喵!

## 🎉 功能 / 指令

喵,统一入口是 `/blhx`,后面跟上子命令就阔以啦喵:

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
uv sync            # 安装依赖
python bot.py      # 启动
```

- 需要先运行一个 OneBot 11 实现（[NapCat](https://github.com/NapNeko/NapCatQQ) / [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)），在 `.env` 的 `ONEBOT_WS_URLS` 中填写其正向 WebSocket 地址。

</details>

## 🔌 适配器（多协议支持）

消息处理已按 NoneBot 泛型基类解耦，指令（`/blhx 信息`、`/blhx 建造记录`、`/blhx 绑定`）可挂到不同协议喵。**已适配并测试**：

| 协议 | 发图方式 | 绑定撤回/通知 |
| --- | --- | --- |
| **OneBot V11** | 图片字节直接进消息段（base64） | ✅ 完整 |
| **OneBot V12** | 先 `upload_file` 拿 file_id 再引用 | ✅ `delete_message` / `send_message` |

想接入别的协议，三步搞定：

1. 安装对应适配器包，例如 `uv add nonebot-adapter-telegram`；
2. 在 `.env` 用 `ADAPTERS` 列出协议名（逗号分隔），例如 `ADAPTERS = onebot.v11,telegram`；
3. 按该适配器要求补上它的连接配置（Token / URL 等），重启即可。

支持的协议名：`onebot.v11`、`onebot.v12`、`qq`、`qqguild`、`satori`、`red`、`telegram`、`discord`、`kaiheila`、`feishu`、`ding`、`dodo`、`minecraft`、`console`、`matrix`、`slack`、`whatsapp`、`villa`、`milky`。

> [!IMPORTANT]
> 除 OneBot V11/V12 外，其余协议**未在本机实测**：各协议的 `MessageSegment.image` 签名不一（有的收原始字节、有的收 file_id、有的收 URL），本插件按签名自动分派、对未知签名尽力而为，但**不能保证图片能正常发出**。接入前请自测图片发送与绑定回调喵。

> [!NOTE]
> `/blhx 绑定` 在任意适配器都能发出二维码并完成绑定；但「扫码后自动撤回二维码 + 在原会话补发绑定成功通知」依赖各协议的撤回/发消息 API，只在 OneBot V11/V12 上完整可用，其它适配器会尽力而为（失败静默跳过，不影响绑定本身）喵。

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

# 可选 Cookie（部分接口不带可能拿不到数据）
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

图片面板需要用到下面这些**系统字体**,渲染前记得安装到系统哦(Windows: `C:\Windows\Fonts`)喵:

| 字体 | 用途 |
| --- | --- |
| `Source Han Sans CN` / `思源黑体` | 正文 |
| `MStiffHei PRC` | 标题 |
| `Agency FB` | 数字 / 英文标语 |

</details>

<details>
<summary>登录页部署到 CDN</summary>

- 将包内 `static/login/` 目录（index.html + login_avatar.webp + login_bg.mp4）上传至 CDN
- `AZURLANE_BIND_BASE_URL` 设为 CDN 页面地址（`/绑定` 二维码指向它）
- `AZURLANE_API_BASE_URL` 设为 bot 公网地址
- 若页面与 bot 不同源，把 `index.html` 顶部的 `const API_BASE = ''` 改为 bot 公网地址

</details>

## 已知局限

- 渠道服（华为/小米/应用宝等）本喵暂时查不了,绑定渠道服会提示失败,抱歉喵。
- 请勿高频调用喵,小心触发风控;也别拿本喵去商用喵。
