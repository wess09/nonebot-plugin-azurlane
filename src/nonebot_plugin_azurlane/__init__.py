"""碧蓝航线 NoneBot2 查询插件：注册指令，并挂载 Web 登录绑定路由。"""

from nonebot import get_driver
from nonebot.log import logger
from nonebot.plugin import PluginMetadata, require

require("nonebot_plugin_htmlrender")

# 注册指令（import 副作用），显式 re-export 避免 ruff F401。
from . import commands as commands
from .config import config

__plugin_meta__ = PluginMetadata(
    name="碧蓝航线查询",
    description="指挥官信息 / 建造记录查询，Web 界面登录绑定",
    usage="/指挥官\n/建造 [数量]\n/绑定",
    type="application",
    homepage="https://github.com/wess09/nonebot-plugin-azurlane",
    config=config.__class__,
    supported_adapters={"~onebot.v11"},
    extra={"author": "wess09 <wess09@users.noreply.github.com>"},
)

driver = get_driver()

# 静态登录页可能部署在 CDN/其他域名，需在应用启动前就放开跨域并挂载 Web 路由。
try:
    from typing import cast

    from fastapi import FastAPI
    from nonebot.drivers import ASGIMixin
    from starlette.middleware.cors import CORSMiddleware

    from .web import router

    # get_driver() 静态类型是基类 Driver，ASGIMixin 才声明 server_app。
    app: FastAPI = cast(ASGIMixin, get_driver()).server_app
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
except Exception as e:
    # 非 FastAPI 驱动时 Web 登录不可用，仅指令功能可用。
    logger.warning(f"[azurlane] Web 登录路由挂载失败: {e!r}")
