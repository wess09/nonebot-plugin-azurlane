from nonebot import get_driver
from nonebot.plugin import PluginMetadata, require
from nonebot.log import logger

require("nonebot_plugin_htmlrender")

from . import commands  # noqa: E402  (注册指令)

from .config import config  # noqa: E402

__plugin_meta__ = PluginMetadata(
    name="碧蓝航线查询",
    description="指挥官信息 / 建造记录查询，Web 界面登录绑定",
    usage="/指挥官\n/建造 [数量]\n/绑定",
    type="application",
    homepage="https://github.com/example/azurlane-bot",
    config=config.__class__,
)

driver = get_driver()

# 静态登录页可能部署在 CDN/其他域名，需在应用启动前就放开跨域并挂载 Web 路由
try:
    from fastapi import FastAPI
    from starlette.middleware.cors import CORSMiddleware

    from .web import router

    app: FastAPI = get_driver().server_app
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)
except Exception as e:  # noqa: BLE001
    # 非 FastAPI 驱动时 Web 登录不可用，仅指令功能可用
    logger.warning(f"[azurlane] Web 登录路由挂载失败: {e!r}")
