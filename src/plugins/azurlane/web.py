"""Web 登录界面：绑定 UID 与区服，绑定成功后回发 QQ 通知。"""

import re
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from nonebot import get_bot

from . import le3api, server_status, session
from .binding import Binding, save_binding
from .config import config

router = APIRouter()

TEMPLATE_DIR = Path(__file__).parent / "templates"

_QQ_RE = re.compile(r"^\d{5,15}$")
_UID_RE = re.compile(r"^\d{3,12}$")


@router.get("/static/login_avatar.webp")
async def static_login_avatar():
    """本地头像（登录页品牌用），避免浏览器直连 B 站 CDN 失败。"""
    from fastapi.responses import FileResponse

    path = Path(__file__).parent.parent.parent.parent / "static" / "login_avatar.webp"
    if path.exists():
        return FileResponse(path, media_type="image/webp")
    return JSONResponse({"ok": False, "message": "头像资源缺失"}, status_code=404)


@router.get("/static/login_bg.mp4")
async def static_login_bg():
    """本地登录页背景视频，避免浏览器直连 B 站 CDN 失败。"""
    from fastapi.responses import FileResponse

    path = Path(__file__).parent.parent.parent.parent / "static" / "login_bg.mp4"
    if path.exists():
        return FileResponse(path, media_type="video/mp4")
    return JSONResponse({"ok": False, "message": "视频资源缺失"}, status_code=404)


@router.get("/login")
async def login_page(qq: str = "") -> HTMLResponse:
    # 登录页已改为纯静态（QQ 由前端从 URL 读取、资源相对路径），
    # bot 本地 /login 也可直接用：相对资源指向 /static/，由本服务托管。
    html = (TEMPLATE_DIR / "login.html").read_text(encoding="utf-8")
    # 本地托管：把相对资源路径指回 /static/（CDN 部署用静态版，见 static/login/）
    html = html.replace("./login_bg.mp4", "/static/login_bg.mp4")
    html = html.replace("./login_avatar.webp", "/static/login_avatar.webp")
    return HTMLResponse(html)


@router.get("/api/servers")
async def api_servers() -> JSONResponse:
    try:
        servers = server_status.fetch_servers()
    except Exception as e:  # noqa: BLE001
        return JSONResponse(
            {"ok": False, "message": f"区服列表拉取失败：{e}"}, status_code=502
        )

    regions: dict[str, dict] = {}
    for sv in servers:
        if sv["key"] in server_status.CHANNEL_KEYS:
            continue
        le3_id = server_status.server_id_for(sv["key"], sv["id"])
        if le3_id is None:
            continue
        region = regions.setdefault(
            sv["key"], {"key": sv["key"], "name": sv["region_name"], "servers": []}
        )
        region["servers"].append(
            {
                "id": sv["id"],
                "name": sv["name"],
                "status": sv["status"],
                "le3_id": str(le3_id),
            }
        )
    return JSONResponse({"ok": True, "regions": list(regions.values())})


@router.get("/api/session/{token}")
async def api_session(token: str) -> JSONResponse:
    """登录页换取会话信息：返回绑定的 QQ（用于页面展示）。"""
    sess = session.get_session(token)
    if sess is None:
        return JSONResponse({"ok": False, "message": "会话不存在或已过期，请重新在 QQ 内发起绑定。"}, status_code=404)
    return JSONResponse({"ok": True, "qq": sess["qq"]})


@router.post("/api/bind")
async def api_bind(request: Request) -> JSONResponse:
    body = await request.json()
    token = str(body.get("token", "")).strip()
    uid = str(body.get("uid", "")).strip()
    le3_id = str(body.get("le3_id", "")).strip()
    server_label = str(body.get("server_label", "")).strip()

    # 通过一次性 token 定位 QQ 会话，避免 URL 暴露 QQ
    sess = session.get_session(token)
    if sess is None:
        return JSONResponse({"ok": False, "message": "会话不存在或已过期，请重新在 QQ 内发起绑定。"})
    qq = sess["qq"]

    if not _UID_RE.match(uid):
        return JSONResponse({"ok": False, "message": "UID 不合法，请检查是否为纯数字。"})
    if not le3_id:
        return JSONResponse({"ok": False, "message": "请选择区服。"})

    # 校验：调用 le3-api 确认 UID + 区服有效，顺带取昵称
    try:
        detail = le3api.get_user_detail(uid, le3_id, cookie=config.azurlane_cookie)
        nickname = detail.get("user_info", {}).get("nickname") or ""
    except le3api.APIError as e:
        return JSONResponse({"ok": False, "message": str(e)})
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"ok": False, "message": f"查询失败：{e}"})

    save_binding(qq, Binding(uid=uid, server_id=le3_id, server_label=server_label))
    return JSONResponse({"ok": True, "nickname": nickname})


@router.get("/api/bind_cb")
async def api_bind_cb(t: str = "", nickname: str = "") -> JSONResponse:
    """绑定回调：绑定成功后前端跳转到此接口（带 token），由 bot 补发私聊通知。"""
    sess = session.consume_session(t)
    if sess is not None and _QQ_RE.match(sess["qq"]):
        try:
            bot = get_bot()
            await bot.send_private_msg(
                user_id=int(sess["qq"]),
                message=(
                    f"绑定成功，指挥官 {nickname or ''}！\n"
                    "发送「指挥官」查询指挥官信息，发送「建造 10」查询最近建造记录。"
                ),
            )
        except Exception:  # noqa: BLE001  bot 未连接等，私聊通知失败不影响
            pass
    return JSONResponse({"ok": True})
