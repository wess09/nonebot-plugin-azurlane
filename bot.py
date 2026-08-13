"""碧蓝航线 bot 入口：注册适配器并启动。

默认注册 OneBot V11；其余适配器按需安装对应 nonebot-adapter-<x> 包，并在 .env 用
ADAPTERS 列出（逗号分隔协议名）即可启用。未安装/不可用的适配器仅告警跳过。
"""

import importlib
import os

import nonebot
from nonebot.drivers import Driver
from nonebot.log import logger

# 协议名 -> 适配器模块路径（模块在 nonebot.adapters.<name> 下，均导出 Adapter 类）
_ADAPTER_MODULES: dict[str, str] = {
    "onebot.v11": "nonebot.adapters.onebot.v11",
    "onebot.v12": "nonebot.adapters.onebot.v12",
    "qq": "nonebot.adapters.qq",
    "qqguild": "nonebot.adapters.qqguild",
    "satori": "nonebot.adapters.satori",
    "red": "nonebot.adapters.red",
    "telegram": "nonebot.adapters.telegram",
    "discord": "nonebot.adapters.discord",
    "kaiheila": "nonebot.adapters.kaiheila",
    "feishu": "nonebot.adapters.feishu",
    "ding": "nonebot.adapters.ding",
    "dodo": "nonebot.adapters.dodo",
    "minecraft": "nonebot.adapters.minecraft",
    "console": "nonebot.adapters.console",
    "matrix": "nonebot.adapters.matrix",
    "slack": "nonebot.adapters.slack",
    "whatsapp": "nonebot.adapters.whatsapp",
    "villa": "nonebot.adapters.villa",
    "milky": "nonebot.adapters.milky",
}


def _register_adapters(driver: Driver) -> None:
    """按 ADAPTERS 配置注册适配器；默认 onebot.v11，未安装/不可用仅告警跳过。

    ADAPTERS 写进 .env（pydantic-settings 读入 NoneBot Config，字段名小写为 adapters），
    也兼容真实环境变量。值支持逗号分隔字符串或列表。
    """
    raw = getattr(driver.config, "adapters", None) or os.environ.get("ADAPTERS") or "onebot.v11"
    if isinstance(raw, str):
        names = [n.strip() for n in raw.split(",") if n.strip()]
    else:
        names = [str(n).strip() for n in raw if str(n).strip()]
    for name in names:
        module = _ADAPTER_MODULES.get(name)
        if module is None:
            logger.warning(
                f"[azurlane] 未知适配器名 {name!r}（可用：{', '.join(_ADAPTER_MODULES)}）"
            )
            continue
        try:
            adapter_module = importlib.import_module(module)
        except ImportError as e:
            logger.warning(f"[azurlane] 适配器 {name} 未安装，跳过：{e}")
            continue
        adapter_cls = getattr(adapter_module, "Adapter", None)
        if adapter_cls is None:
            logger.warning(f"[azurlane] 适配器 {name} 未导出 Adapter，跳过")
            continue
        driver.register_adapter(adapter_cls)
        logger.info(f"[azurlane] 已注册适配器：{name}")


nonebot.init()
driver = nonebot.get_driver()
_register_adapters(driver)
nonebot.load_from_toml("pyproject.toml")

if __name__ == "__main__":
    nonebot.run()
