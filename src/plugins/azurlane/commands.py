"""机器人指令：指挥官信息 / 建造记录查询。"""

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, MessageSegment
from nonebot.params import CommandArg

from . import le3api, session
from .binding import get_binding
from .config import config
from .qr import make_bind_qr
from .renderer import build_commanders_pic, build_build_records_pic

commander_cmd = on_command("指挥官", aliases={"指挥官信息"}, priority=5, block=True)
build_cmd = on_command("建造", aliases={"建造记录"}, priority=5, block=True)
bind_cmd = on_command("绑定", aliases={"登录"}, priority=5, block=True)


@commander_cmd.handle()
async def handle_commander(bot: Bot, event: MessageEvent):
    qq = str(event.user_id)
    binding = get_binding(qq)
    if binding is None:
        await commander_cmd.finish("尚未绑定。发送「绑定」获取 Web 登录页完成绑定。")
    try:
        detail = le3api.get_user_detail(
            binding.uid, binding.server_id, cookie=config.azurlane_cookie
        )
    except le3api.APIError as e:
        await commander_cmd.finish(f"查询失败：{e}")
    except Exception as e:  # noqa: BLE001
        await commander_cmd.finish(f"查询失败：{e}")

    pic = await build_commanders_pic(detail)
    await commander_cmd.finish(MessageSegment.image(pic))


@build_cmd.handle()
async def handle_build(
    bot: Bot, event: MessageEvent, arg: Message = CommandArg()
):
    qq = str(event.user_id)
    binding = get_binding(qq)
    if binding is None:
        await build_cmd.finish("尚未绑定。发送「绑定」获取 Web 登录页完成绑定。")

    count = 10
    raw = arg.extract_plain_text().strip()
    if raw:
        try:
            count = int(raw)
        except ValueError:
            await build_cmd.finish("建造数量需为数字。用法：建造 10")
    if count > 500:
        await build_cmd.finish("单次最多查询 500 条建造记录。")

    try:
        result = le3api.get_build_record(
            binding.uid, binding.server_id, target_count=count, cookie=config.azurlane_cookie
        )
    except le3api.APIError as e:
        await build_cmd.finish(f"查询失败：{e}")
    except Exception as e:  # noqa: BLE001
        await build_cmd.finish(f"查询失败：{e}")

    if not result["records"]:
        await build_cmd.finish("未查询到建造记录。")

    pic = await build_build_records_pic(result)
    await build_cmd.finish(MessageSegment.image(pic))


@bind_cmd.handle()
async def handle_bind(bot: Bot, event: MessageEvent):
    qq = str(event.user_id)
    # 生成一次性 token 会话，登录 URL 只带 token，不暴露 QQ / 回调信息
    cb = f"{config.azurlane_api_base_url}/api/bind_cb"
    token = session.create_session(qq, cb)
    url = f"{config.azurlane_bind_base_url}/login?t={token}"

    # 生成二维码图片（中心嵌圆形头像）
    img_bytes = make_bind_qr(url)

    await bind_cmd.finish(
        MessageSegment.image(img_bytes)
        + "\n【碧蓝航线 · 指挥官绑定】\n扫描上方二维码完成绑定（填写 UID 并选择区服）。\n提示：绑定信息仅用于查询，区服信息不会在查询结果中展示。"
    )
