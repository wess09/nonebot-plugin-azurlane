"""真实 le3-api 端到端测试（CI 专用）。

用 GitHub Actions secrets 注入的测试账号（AZURLANE_TEST_UID / AZURLANE_TEST_SERVER_ID）
跑完整链路：查询指挥官 -> 查询建造记录 -> 渲染面板图片。

未配置 secret 时跳过（本地/PR 不会误跑真实接口）。
"""

import os

import pytest

pytestmark = pytest.mark.asyncio

_UID = os.environ.get("AZURLANE_TEST_UID", "")
_SERVER_ID = os.environ.get("AZURLANE_TEST_SERVER_ID", "")


def _require_credentials() -> None:
    if not _UID or not _SERVER_ID:
        pytest.skip("未配置 AZURLANE_TEST_UID / AZURLANE_TEST_SERVER_ID，跳过 e2e")


async def test_user_detail_and_panel():
    """真实调用 get/user_detail 并渲染指挥官面板。"""
    _require_credentials()
    from nonebot_plugin_azurlane import le3api
    from nonebot_plugin_azurlane.renderer import build_commanders_pic

    detail = await le3api.get_user_detail(_UID, _SERVER_ID)
    ui = detail["user_info"]
    assert ui.get("nickname"), "user_detail 未返回昵称"
    assert ui.get("level"), "user_detail 未返回等级"

    pic = await build_commanders_pic(detail)
    assert isinstance(pic, bytes)
    assert len(pic) > 1000, "指挥官面板渲染结果为空"


async def test_build_record_and_panel():
    """真实调用 get/build_record 并渲染建造记录面板。"""
    _require_credentials()
    from nonebot_plugin_azurlane import le3api
    from nonebot_plugin_azurlane.renderer import build_build_records_pic

    result = await le3api.get_build_record(_UID, _SERVER_ID, target_count=10)
    assert len(result["records"]) > 0, "建造记录为空"

    pic = await build_build_records_pic(result)
    assert isinstance(pic, bytes)
    assert len(pic) > 1000, "建造记录面板渲染结果为空"
