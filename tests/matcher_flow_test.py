"""nonebug 驱动真实事件管道的测试：指令匹配 -> 分派 -> 发送。

与 bind_flow_test 直接调用内部 handler 不同，这里走 nonebug 的 app.test_matcher，
从「收到 /blhx 事件」一路跑到「发消息」，验证 on_command 匹配与子命令分派接线正确。
"""

import pytest
from fake import (
    fake_group_message_event_v11,
    fake_private_message_event_v11,
    fake_private_message_event_v12,
)
from nonebug import App

_USAGE_TEXT = (
    "碧蓝航线 用法：\n"
    "/blhx 信息 —— 查询指挥官信息\n"
    "/blhx 建造记录 [数量] —— 查询建造记录（默认 10，上限 500）\n"
    "/blhx 绑定 —— 获取登录绑定二维码\n"
    "\n子命令别名：信息/info ~ 建造记录/记录 ~~ 绑定/登录/登陆/login"
)
_UNBOUND_TEXT = "尚未绑定。发送「绑定」获取 Web 登录页完成绑定。"
_BIND_TEXT = (
    "\n碧蓝航线·指挥官绑定\n"
    "扫描上方二维码完成绑定（填写 UID 并选择区服）。\n"
    "该二维码为一次性专属：10 分钟内有效，仅限本人扫码，请勿转发他人。\n"
    "提示：绑定信息仅用于查询，区服信息不会在查询结果中展示。"
)


@pytest.mark.asyncio
async def test_blhx_no_subcommand_sends_usage(app: App):
    from nonebot.adapters.onebot.v11 import Bot, Message

    from nonebot_plugin_azurlane.commands import blhx_cmd

    async with app.test_matcher(blhx_cmd) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10001")
        event = fake_group_message_event_v11(message=Message("/blhx"))
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, _USAGE_TEXT)
        ctx.should_finished(blhx_cmd)


@pytest.mark.asyncio
async def test_blhx_commander_unbound(app: App, monkeypatch):
    from nonebot.adapters.onebot.v11 import Bot, Message

    from nonebot_plugin_azurlane.commands import blhx_cmd

    # 隔离 SQLite：无论库里有没有记录都当未绑定，只测指令分派到 commander 路径。
    monkeypatch.setattr("nonebot_plugin_azurlane.commands.get_binding", lambda qq: None)

    async with app.test_matcher(blhx_cmd) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10001")
        event = fake_group_message_event_v11(message=Message("/blhx 信息"))
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, _UNBOUND_TEXT)
        ctx.should_finished(blhx_cmd)


@pytest.mark.asyncio
async def test_blhx_bind_sends_qr_image(app: App, monkeypatch):
    from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment

    from nonebot_plugin_azurlane.commands import blhx_cmd

    # 二维码含随机 token，字节不稳定；固定它以便精确断言发送内容。
    fixed_qr = b"\x89PNG\r\n\x1a\n fake-qr-bytes"
    monkeypatch.setattr("nonebot_plugin_azurlane.commands.make_bind_qr", lambda url: fixed_qr)

    async with app.test_matcher(blhx_cmd) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10001")
        event = fake_private_message_event_v11(user_id=12345, message=Message("/blhx 绑定"))
        ctx.receive_event(bot, event)
        ctx.should_call_send(event, MessageSegment.image(fixed_qr) + _BIND_TEXT)


@pytest.mark.asyncio
async def test_v12_bind_uploads_then_sends_file_id(app: App, monkeypatch):
    import base64

    from nonebot.adapters.onebot.v12 import Bot, Message, MessageSegment

    from nonebot_plugin_azurlane.commands import blhx_cmd

    fixed_qr = b"\x89PNG\r\n\x1a\n fake-qr-bytes"
    monkeypatch.setattr("nonebot_plugin_azurlane.commands.make_bind_qr", lambda url: fixed_qr)

    async with app.test_matcher(blhx_cmd) as ctx:
        bot = ctx.create_bot(base=Bot, self_id="10001", impl="fake-impl", platform="qq")
        event = fake_private_message_event_v12(user_id="12345", message=Message("/blhx 绑定"))
        ctx.receive_event(bot, event)
        # OneBot V12 发图要先 upload_file 拿 file_id，再引用进消息。
        ctx.should_call_api(
            "upload_file",
            {
                "type": "image",
                "name": "image.png",
                "data": base64.b64encode(fixed_qr).decode(),
            },
            result={"file_id": "file-001"},
        )
        ctx.should_call_send(event, MessageSegment.image("file-001") + _BIND_TEXT)
