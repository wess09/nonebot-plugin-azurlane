"""机器人指令：统一入口 /blhx，按子命令分派到「信息 / 建造 / 绑定」。

只走 /blhx 单一入口，不保留旧的 /指挥官 /建造 /绑定 独立命令。
"""

from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    MessageSegment,
    GroupMessageEvent,
    PrivateMessageEvent,
)

from . import le3api, session
from .qr import make_bind_qr
from .config import config
from .binding import get_binding
from .renderer import build_commanders_pic, build_build_records_pic

# 统一入口 /blhx，按子命令分派（不保留旧的 /指挥官 /建造 /绑定）：
#   /blhx 信息                   -> 指挥官面板
#   /blhx 建造记录 [n] / /blhx 记录 [n] -> 建造记录
#   /blhx 绑定 / /blhx 登录 / /blhx login -> 绑定二维码
blhx_cmd = on_command("blhx", priority=5, block=True)

_TOKENS = {
    # commander（指挥官信息面板）
    "信息": "commander",
    "info": "commander",
    "指挥官": "commander",
    "查询": "commander",
    # build（建造记录）
    "建造记录": "build",
    "记录": "build",
    "建造": "build",
    "build": "build",
    "record": "build",
    "gacha": "build",
    # bind（绑定二维码）
    "绑定": "bind",
    "登录": "bind",
    "登陆": "bind",
    "login": "bind",
    "signin": "bind",
}


@blhx_cmd.handle()
async def handle_blhx(bot: Bot, event: MessageEvent, arg: Message = CommandArg()) -> None:
    """/blhx 入口：按子命令 token 分派到各子命令处理。"""
    raw = arg.extract_plain_text().strip()
    # 取最长匹配的子命令 token 作前缀，剩余部分作为参数，
    # 同时兼容 "建造 10" 与 "建造10"（不带空格）两种写法。
    action: str | None = None
    rest = ""
    for key in sorted(_TOKENS, key=len, reverse=True):
        if raw.lower().startswith(key.lower()):
            action = _TOKENS[key]
            rest = raw[len(key):].strip()
            break

    # 未识别的子命令给出用法提示。
    if action is None:
        await blhx_cmd.finish(
            "碧蓝航线 用法：\n"
            "/blhx 信息 —— 查询指挥官信息\n"
            "/blhx 建造记录 [数量] —— 查询建造记录（默认 10，上限 500）\n"
            "/blhx 绑定 —— 获取登录绑定二维码\n"
            "\n子命令别名：信息/info ~ 建造记录/记录 ~~ 绑定/登录/登陆/login"
        )

    if action == "commander":
        await _handle_commander(event)
    elif action == "build":
        await _handle_build(event, rest)
    else:
        await _handle_bind(bot, event)


async def _handle_commander(event: MessageEvent) -> None:
    """查询指挥官信息并发送面板图片。"""
    qq = str(event.user_id)
    binding = get_binding(qq)
    if binding is None:
        await blhx_cmd.finish("尚未绑定。发送「绑定」获取 Web 登录页完成绑定。")
    try:
        detail = await le3api.get_user_detail(
            binding.uid, binding.server_id, cookie=config.azurlane_cookie
        )
    except le3api.APIError as e:
        await blhx_cmd.finish(f"查询失败：{e}")
    except Exception as e:
        await blhx_cmd.finish(f"查询失败：{e}")

    pic = await build_commanders_pic(detail)
    await blhx_cmd.finish(MessageSegment.image(pic))


async def _handle_build(event: MessageEvent, rest: str) -> None:
    """查询建造记录并发送面板图片。rest 为数量（可选）。"""
    qq = str(event.user_id)
    binding = get_binding(qq)
    if binding is None:
        await blhx_cmd.finish("尚未绑定。发送「绑定」获取 Web 登录页完成绑定。")

    count = 10
    raw = rest.strip()
    if raw:
        try:
            count = int(raw)
        except ValueError:
            await blhx_cmd.finish("建造数量需为数字。用法：建造 10")
    if count > 500:
        await blhx_cmd.finish("单次最多查询 500 条建造记录。")

    try:
        result = await le3api.get_build_record(
            binding.uid, binding.server_id, target_count=count, cookie=config.azurlane_cookie
        )
    except le3api.APIError as e:
        await blhx_cmd.finish(f"查询失败：{e}")
    except Exception as e:
        await blhx_cmd.finish(f"查询失败：{e}")

    if not result["records"]:
        await blhx_cmd.finish("未查询到建造记录。")

    pic = await build_build_records_pic(result)
    await blhx_cmd.finish(MessageSegment.image(pic))


async def _handle_bind(bot: Bot, event: MessageEvent) -> None:
    """生成一次性会话并发送登录二维码，记录消息 id 以便绑定完成后原路撤回。"""
    qq = str(event.user_id)

    # 定位会话：二维码发在哪（群/私聊），绑定成功后就原路撤回并在同场景通知。
    if isinstance(event, GroupMessageEvent):
        chat_type, peer_id = "group", event.group_id
    elif isinstance(event, PrivateMessageEvent):
        chat_type, peer_id = "private", event.user_id
    else:
        await blhx_cmd.finish("仅支持在群聊或私聊中发起绑定。")

    # 登录 URL 只带 token，不暴露 QQ / 回调信息。
    cb = f"{config.azurlane_api_base_url}/api/bind_cb"
    token = session.create_session(qq, cb, chat_type, peer_id)
    url = f"{config.azurlane_bind_base_url}/login?t={token}"

    # 生成二维码图片（中心嵌圆形头像）。
    img_bytes = make_bind_qr(url)

    text = (
        "\n碧蓝航线·指挥官绑定\n"
        "扫描上方二维码完成绑定（填写 UID 并选择区服）。\n"
        "该二维码为一次性专属：10 分钟内有效，仅限本人扫码，请勿转发他人。\n"
        "提示：绑定信息仅用于查询，区服信息不会在查询结果中展示。"
    )
    msg = MessageSegment.image(img_bytes) + text

    try:
        if chat_type == "group":
            resp = await bot.send_group_msg(group_id=peer_id, message=msg)
        else:
            resp = await bot.send_private_msg(user_id=peer_id, message=msg)
    except Exception as e:
        # 发送失败：不阻塞，提示用户；残留会话由 10 分钟 TTL 清理。
        await blhx_cmd.finish(f"绑定二维码发送失败：{e}")

    # 记下消息 id，绑定完成后用 delete_msg 撤回二维码。
    session.attach_msg_id(token, int(resp["message_id"]))
