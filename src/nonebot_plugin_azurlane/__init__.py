"""碧蓝航线 NoneBot2 查询插件：注册指令，并挂载 Web 登录绑定路由。"""

from nonebot import get_driver
from nonebot.log import logger
from nonebot.plugin import PluginMetadata, require
from nonebot.drivers import ASGIMixin

require("nonebot_plugin_htmlrender")

# 注册指令（import 副作用），显式 re-export 避免 ruff F401。
from . import commands as commands
from .config import config

__plugin_meta__ = PluginMetadata(
    name="碧蓝航线查询",
    description="指挥官信息 / 建造记录查询，Web 界面登录绑定",
    usage="/blhx 信息\n/blhx 建造记录 [数量]\n/blhx 绑定",
    type="application",
    homepage="https://github.com/wess09/nonebot-plugin-azurlane",
    config=config.__class__,
    supported_adapters={
        "~onebot.v11",
        "~onebot.v12",
        "~qq",
        "~qqguild",
        "~satori",
        "~red",
        "~telegram",
        "~discord",
        "~kaiheila",
        "~feishu",
        "~ding",
        "~dodo",
        "~minecraft",
        "~console",
        "~matrix",
        "~slack",
        "~whatsapp",
        "~villa",
        "~milky",
    },
    extra={"author": "wess09 <wess09@users.noreply.github.com>"},
)

driver = get_driver()

# 仅 FastAPI/ASGI 驱动才有 server_app 可挂载 Web 登录路由；其它驱动下
# Web 登录绑定不可用，仅指令功能可用。跨域由使用者自行配置（勿在此加 CORS）。
if isinstance(driver, ASGIMixin):
    from .web import router

    driver.server_app.include_router(router)
else:
    logger.warning("[azurlane] 当前驱动不支持 ASGI，Web 登录绑定不可用，仅指令功能可用。")
