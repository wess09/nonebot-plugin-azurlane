"""绑定流程链路测试：发二维码 -> 记录 msg_id -> 绑定回调撤回并原场景通知。

不依赖真实 OneBot 环境：用 fake bot 记录 API 调用，直接调用
commands._handle_bind 与 web.api_bind_cb，验证整条链路。
"""

from typing import cast

import pytest
from fake import fake_group_message_event_v11, fake_private_message_event_v11
from nonebot.adapters.onebot.v11 import Bot


class FakeBot:
    """记录调用的假 bot：send_group_msg/send_private_msg 返回固定 message_id。"""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def send_group_msg(self, **kwargs) -> dict:
        self.calls.append(("send_group_msg", kwargs))
        return {"message_id": 1001}

    async def send_private_msg(self, **kwargs) -> dict:
        self.calls.append(("send_private_msg", kwargs))
        return {"message_id": 2002}

    async def delete_msg(self, **kwargs) -> None:
        self.calls.append(("delete_msg", kwargs))


def _get_token_for(session, qq: str) -> str:
    """从内存会话里取指定 QQ 最新创建的 token。"""
    tokens = [t for t, s in session._sessions.items() if s["qq"] == qq]
    assert tokens, f"no session for qq={qq}"
    return tokens[-1]


@pytest.mark.asyncio
async def test_bind_flow_in_group(monkeypatch):
    from nonebot_plugin_azurlane import session
    from nonebot_plugin_azurlane.web import api_bind_cb
    from nonebot_plugin_azurlane.commands import _handle_bind

    bot = FakeBot()
    monkeypatch.setattr("nonebot_plugin_azurlane.web.get_bot", lambda: bot)

    event = fake_group_message_event_v11(user_id=12345678, group_id=87654321)
    await _handle_bind(cast(Bot, bot), event)

    # 1) 二维码发到了原群，首段是图片
    assert bot.calls[0][0] == "send_group_msg"
    send_kw = bot.calls[0][1]
    assert send_kw["group_id"] == 87654321
    assert send_kw["message"][0].type == "image"

    # 2) msg_id 已补记进会话
    token = _get_token_for(session, "12345678")
    sess = session.get_session(token)
    assert sess is not None
    assert sess["msg_id"] == 1001
    assert sess["chat_type"] == "group"

    # 3) 绑定完成后：撤回二维码 + 原群发绑定成功
    await api_bind_cb(t=token, nickname="指挥官甲")
    assert ("delete_msg", {"message_id": 1001}) in bot.calls
    last_call, last_kw = bot.calls[-1]
    assert last_call == "send_group_msg"
    assert last_kw["group_id"] == 87654321
    assert "绑定成功" in last_kw["message"]


@pytest.mark.asyncio
async def test_bind_flow_in_private(monkeypatch):
    from nonebot_plugin_azurlane import session
    from nonebot_plugin_azurlane.web import api_bind_cb
    from nonebot_plugin_azurlane.commands import _handle_bind

    bot = FakeBot()
    monkeypatch.setattr("nonebot_plugin_azurlane.web.get_bot", lambda: bot)

    event = fake_private_message_event_v11(user_id=12345)
    await _handle_bind(cast(Bot, bot), event)

    assert bot.calls[0][0] == "send_private_msg"
    assert bot.calls[0][1]["user_id"] == 12345
    assert bot.calls[0][1]["message"][0].type == "image"

    token = _get_token_for(session, "12345")
    sess = session.get_session(token)
    assert sess is not None
    assert sess["msg_id"] == 2002
    assert sess["chat_type"] == "private"

    await api_bind_cb(t=token, nickname="指挥官乙")
    assert ("delete_msg", {"message_id": 2002}) in bot.calls
    last_call, last_kw = bot.calls[-1]
    assert last_call == "send_private_msg"
    assert last_kw["user_id"] == 12345
    assert "绑定成功" in last_kw["message"]
