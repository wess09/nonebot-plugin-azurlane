import pytest


@pytest.mark.asyncio
async def test_plugin_loads():
    """插件应能被正常导入（商店 NoneFlow 加载测试等价物）。"""
    import nonebot_plugin_azurlane  # noqa: F401
    from nonebot_plugin_azurlane.commands import (
        bind_cmd,
        build_cmd,
        commander_cmd,
    )

    assert commander_cmd is not None
    assert build_cmd is not None
    assert bind_cmd is not None
