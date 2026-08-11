from pydantic import BaseModel

from nonebot import get_plugin_config


class Config(BaseModel):
    """插件配置，读取自 .env 的 AZURLANE_* 前缀。"""

    # le3-api 可选 Cookie（部分接口不带可能拿不到数据）
    azurlane_cookie: str = ""

    # Web 登录页对外公开地址（CDN 部署的静态页，或本 bot 的 /login）
    azurlane_bind_base_url: str = "http://127.0.0.1:8081"

    # bot 服务公网地址（绑定回调接口所在，CDN 页面前端回调用）
    azurlane_api_base_url: str = "http://127.0.0.1:8081"

    # 部署者 QQ，用于接收绑定通知（可选）
    azurlane_admin_qq: str = ""


config: Config = get_plugin_config(Config)
