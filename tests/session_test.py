"""session 模块单元测试：会话创建、msg_id 补记、过期清理、一次性消费。"""

import time

import pytest


@pytest.mark.asyncio
async def test_create_and_consume_roundtrip():
    # import 放函数体内：包 __init__ require htmlrender，需等 NoneBot 初始化后执行。
    from nonebot_plugin_azurlane import session

    token = session.create_session("12345", "https://example.com/api/bind_cb", "group", 999)
    sess = session.get_session(token)
    assert sess is not None
    assert sess["qq"] == "12345"
    assert sess["cb"] == "https://example.com/api/bind_cb"
    assert sess["chat_type"] == "group"
    assert sess["peer_id"] == 999
    assert sess["msg_id"] == 0

    # 补记二维码消息 id 后原样可取。
    session.attach_msg_id(token, 42)
    sess = session.get_session(token)
    assert sess is not None
    assert sess["msg_id"] == 42

    # 一次性消费：取走即删除。
    consumed = session.consume_session(token)
    assert consumed is not None
    assert consumed["msg_id"] == 42
    assert session.get_session(token) is None
    assert session.consume_session(token) is None


@pytest.mark.asyncio
async def test_expired_session_returns_none():
    from nonebot_plugin_azurlane import session

    token = session.create_session("12345", "cb", "private", 999)
    # 直接改时间戳模拟过期（绕过 10 分钟真实等待）。
    sess = session.get_session(token)
    assert sess is not None
    sess["created"] = time.time() - session._TTL - 1

    assert session.get_session(token) is None
    assert session.consume_session(token) is None


@pytest.mark.asyncio
async def test_attach_msg_id_unknown_token_is_noop():
    from nonebot_plugin_azurlane import session

    session.attach_msg_id("no-such-token", 1)  # 不应抛错
