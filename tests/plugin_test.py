import pytest


@pytest.mark.asyncio
async def test_plugin_loads():
    """插件应能被正常导入（商店 NoneFlow 加载测试等价物）。"""
    # 依赖 conftest 的 after_nonebot_init fixture 先初始化 NoneBot
    import nonebot_plugin_azurlane  # noqa: F401
    from nonebot_plugin_azurlane.commands import (
        blhx_cmd,
    )

    assert blhx_cmd is not None
