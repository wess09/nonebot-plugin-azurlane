"""跨适配器辅助：把消息构造、场景推断、撤回/通知从 OneBot V11 中解耦。

插件主体改用 NoneBot 泛型基类（Bot / Event / Message），本模块封装那些「基类没声明、
但各官方适配器按约定实现」的操作——尤其是图片消息段。

各适配器发图方式不一：OneBot V11 直接在 image 段里放 base64 字节；OneBot V12 需先
upload_file 拿 file_id 再引用。本模块按 image 工厂的签名自动分派，其余差异尽力而为。
"""

import base64
import inspect
from typing import Any

from nonebot import get_bot
from nonebot.log import logger
from nonebot.adapters import Bot, Event, Message


async def image_message(bot: Bot, event: Event, data: bytes) -> Message:
    """用事件所属适配器的消息段类构造图片消息（跨适配器）。

    适配器的 image 工厂签名决定发图方式：收 file_id 的（OneBot V12 等）先 upload_file
    拿 file_id；收原始字节的（OneBot V11 等）直接把字节塞进段。其余签名尽力而为。
    """
    msg_cls = type(event.get_message())
    seg_cls = msg_cls.get_segment_class()
    if _image_takes_file_id(seg_cls):
        seg = seg_cls.image(await _upload_image(bot, data))
    else:
        seg = seg_cls.image(data)  # type: ignore[attr-defined]
    return msg_cls(seg)  # type: ignore[abstract]


def _image_takes_file_id(seg_cls: type) -> bool:
    """image 工厂签名里带 file_id 参数的适配器需先上传拿 file_id。"""
    try:
        return "file_id" in inspect.signature(seg_cls.image).parameters
    except (TypeError, ValueError):
        return False


async def _upload_image(bot: Bot, data: bytes) -> str:
    """OneBot V12 式：upload_file 上传图片返回 file_id。"""
    resp = await bot.upload_file(
        type="image",
        name="image.png",
        data=base64.b64encode(data).decode(),
    )
    return str(resp["file_id"])  # type: ignore[index]


def detect_scene(event: Event) -> tuple[str, int] | None:
    """推断事件所在的会话场景，返回 (chat_type, peer_id)。

    支持 OneBot V11（message_type）与 OneBot V12（detail_type）的群/私聊；其它适配器
    返回 None——不影响绑定，只是后续撤回/通知尽力而为地跳过。
    """
    message_type = getattr(event, "message_type", None)
    if message_type == "group":
        peer = getattr(event, "group_id", None)
        if peer is not None:
            return "group", int(peer)
    if message_type in ("private", "friend"):
        peer = getattr(event, "user_id", None)
        if peer is not None:
            return "private", int(peer)

    detail_type = getattr(event, "detail_type", None)
    if detail_type == "group":
        peer = getattr(event, "group_id", None)
        if peer is not None:
            return "group", int(peer)
    if detail_type == "private":
        peer = getattr(event, "user_id", None)
        if peer is not None:
            return "private", int(peer)
    return None


def resolve_bot(self_id: str) -> Bot | None:
    """按 self_id 取回发起绑定的 bot；缺失时回退到任意 bot，都没有则返回 None。"""
    try:
        return get_bot(self_id or None)
    except (KeyError, ValueError):
        pass
    try:
        return get_bot()
    except (KeyError, ValueError):
        return None


def extract_msg_id(resp: Any) -> int:
    """从 bot.send 返回值中尽力提取消息 id（用于撤回）；提取不到返回 0。"""
    if isinstance(resp, dict):
        for key in ("message_id", "message"):
            if key in resp:
                try:
                    return int(resp[key])
                except (TypeError, ValueError):
                    return 0
    if isinstance(resp, int):
        return resp
    return 0


async def recall(bot: Bot, msg_id: int) -> None:
    """尽力撤回消息：OneBot V11 用 delete_msg，V12 用 delete_message，失败静默。"""
    if not msg_id:
        return
    for api_name in ("delete_msg", "delete_message"):
        api = getattr(bot, api_name, None)
        if api is None:
            continue
        try:
            await api(message_id=msg_id)
            return
        except Exception:
            continue


async def notify(bot: Bot, chat_type: str, peer_id: int, message: str) -> None:
    """尽力在原场景补发通知：OneBot V11 用 send_group_msg/send_private_msg，
    V12 用 send_message + detail_type；都不是或失败时静默跳过。"""
    if chat_type not in ("group", "private"):
        return
    if chat_type == "group":
        attempts: list[tuple[str, dict[str, Any]]] = [
            ("send_group_msg", {"group_id": peer_id}),
            ("send_message", {"detail_type": "group", "group_id": str(peer_id)}),
        ]
    else:
        attempts = [
            ("send_private_msg", {"user_id": peer_id}),
            ("send_message", {"detail_type": "private", "user_id": str(peer_id)}),
        ]
    for api_name, kwargs in attempts:
        api = getattr(bot, api_name, None)
        if api is None:
            continue
        try:
            await api(message=message, **kwargs)
            return
        except Exception as e:
            logger.debug(f"[azurlane] {api_name} 调用失败，尝试下一种: {e!r}")
            continue
