"""compat 跨适配器辅助单元测试：v11/v12 图片构造、场景推断、消息 id 提取。"""

from typing import cast

import pytest
from fake import (
    fake_group_message_event_v11,
    fake_group_message_event_v12,
    fake_private_message_event_v11,
    fake_private_message_event_v12,
)
from nonebot.adapters import Bot


class _StubBot:
    """记录 upload_file 的假 bot，供 v12 上传路径断言。"""

    def __init__(self) -> None:
        self.uploaded: list[dict] = []

    async def upload_file(self, **kwargs) -> dict:
        self.uploaded.append(kwargs)
        return {"file_id": "file-001"}


@pytest.mark.asyncio
async def test_image_message_v11_builds_bytes_segment():
    from nonebot_plugin_azurlane import compat

    bot = _StubBot()
    event = fake_group_message_event_v11()
    msg = await compat.image_message(cast(Bot, bot), event, b"\x89PNG-fake")
    assert len(msg) == 1
    assert msg[0].type == "image"
    # v11：直接 base64 进段，不触发上传。
    assert bot.uploaded == []
    assert msg[0].data["file"].startswith("base64://")


@pytest.mark.asyncio
async def test_image_message_v12_uploads_then_file_id():
    import base64

    from nonebot_plugin_azurlane import compat

    bot = _StubBot()
    event = fake_group_message_event_v12()
    png = b"\x89PNG\r\n\x1a\n fake"
    msg = await compat.image_message(cast(Bot, bot), event, png)
    # v12：先 upload_file 拿 file_id，再引用。
    assert bot.uploaded == [
        {"type": "image", "name": "image.png", "data": base64.b64encode(png).decode()}
    ]
    assert len(msg) == 1
    assert msg[0].type == "image"
    assert msg[0].data["file_id"] == "file-001"


@pytest.mark.asyncio
async def test_detect_scene_v11_group_and_private():
    from nonebot_plugin_azurlane import compat

    assert compat.detect_scene(fake_group_message_event_v11(group_id=87654321)) == (
        "group",
        87654321,
    )
    assert compat.detect_scene(fake_private_message_event_v11(user_id=12345)) == (
        "private",
        12345,
    )


@pytest.mark.asyncio
async def test_detect_scene_v12_group_and_private():
    from nonebot_plugin_azurlane import compat

    assert compat.detect_scene(fake_group_message_event_v12(group_id="87654321")) == (
        "group",
        87654321,
    )
    assert compat.detect_scene(fake_private_message_event_v12(user_id="12345")) == (
        "private",
        12345,
    )


@pytest.mark.asyncio
async def test_extract_msg_id():
    from nonebot_plugin_azurlane import compat

    assert compat.extract_msg_id({"message_id": 1001}) == 1001
    assert compat.extract_msg_id({"message": 42}) == 42
    assert compat.extract_msg_id(7) == 7
    assert compat.extract_msg_id({"data": 1}) == 0
    assert compat.extract_msg_id(None) == 0
