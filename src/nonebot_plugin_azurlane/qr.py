"""二维码生成：圆角码点 + 天蓝→海蓝水平渐变，中心嵌圆形 logo（登录页头像）。"""

import io
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import HorizontalGradiantColorMask
from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer

# 头像文件：static/login_avatar.webp
AVATAR_PATH = Path(__file__).parent.parent.parent / "static" / "login_avatar.webp"

# 渐变配色：天蓝 -> 海蓝
_LEFT_COLOR = (74, 157, 232)  # #4a9de8
_RIGHT_COLOR = (26, 95, 180)  # #1a5fb4


def _round_logo(size: int) -> Image.Image:
    """裁剪头像为圆形，返回 size×size RGBA。"""
    img = Image.open(AVATAR_PATH).convert("RGBA")
    img = img.resize((size, size), Image.Resampling.LANCZOS)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(img, (0, 0), mask)
    return canvas


def make_bind_qr(url: str) -> bytes:
    """生成绑定二维码 PNG bytes：圆角码点 + 水平渐变 + 中心圆形头像。"""
    # 错误修正 H：中心放 logo 后仍可扫描
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    mask = HorizontalGradiantColorMask(
        back_color=(255, 255, 255),
        left_color=_LEFT_COLOR,
        right_color=_RIGHT_COLOR,
    )
    qr_img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
        color_mask=mask,
    ).convert("RGBA")

    # 中心 logo：占二维码 ~22% 边长
    logo_size = int(qr_img.size[0] * 0.22)
    logo = _round_logo(logo_size)
    pos = ((qr_img.size[0] - logo_size) // 2, (qr_img.size[1] - logo_size) // 2)
    qr_img.alpha_composite(logo, pos)

    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    return buf.getvalue()
