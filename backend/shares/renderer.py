"""
공유 카드 이미지 렌더러.

AI가 반환한 layout_data JSON을 Pillow로 실제 이미지로 렌더링한다.
카드 크기: 1080 x 1920 (인스타 스토리 비율, 9:16)
"""
import io
import logging
import os
import tempfile
from urllib.request import urlopen

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# 카드 기본 사이즈
CARD_WIDTH = 1080
CARD_HEIGHT = 1920

# 기본 폰트 (시스템에 없으면 Pillow 기본 폰트 사용)
# 배포 시 프로젝트에 폰트 파일을 포함하거나 설정으로 경로를 지정
_FONT_DIR = os.path.join(os.path.dirname(__file__), 'fonts')


def _load_font(size: int, weight: str = 'normal') -> ImageFont.FreeTypeFont:
    """폰트를 로드한다. 실패 시 Pillow 기본 폰트 반환."""
    # TODO: 프로젝트에 포함된 한글 폰트 경로로 교체
    font_map = {
        'bold': 'NotoSansKR-Bold.ttf',
        'normal': 'NotoSansKR-Regular.ttf',
    }
    font_file = font_map.get(weight, font_map['normal'])
    font_path = os.path.join(_FONT_DIR, font_file)

    try:
        # NotoSansCJK TTC 컬렉션에서 KR 폰트는 index=1
        return ImageFont.truetype(font_path, size, index=1)
    except (IOError, OSError):
        logger.warning('폰트 로드 실패: %s — 기본 폰트 사용', font_path)
        try:
            return ImageFont.load_default(size)
        except TypeError:
            return ImageFont.load_default()


def _download_image(url: str) -> Image.Image | None:
    """URL에서 이미지를 다운로드하여 PIL Image로 반환."""
    try:
        with urlopen(url, timeout=10) as resp:
            data = resp.read()
        return Image.open(io.BytesIO(data)).convert('RGBA')
    except Exception as e:
        logger.warning('이미지 다운로드 실패: %s — %s', url, e)
        return None


def render_card(layout_data: dict, poster_url: str = '',
                background_url: str = '') -> io.BytesIO:
    """layout_data를 기반으로 공유 카드 이미지를 렌더링한다.

    Args:
        layout_data: AI가 반환한 레이아웃 JSON
        poster_url: 작품 포스터 이미지 URL
        background_url: 카드 템플릿 배경 이미지 URL

    Returns:
        PNG 이미지가 담긴 BytesIO 객체
    """
    # 1) 배경 생성
    bg_info = layout_data.get('background', {})
    bg_color = bg_info.get('color', '#1a1a2e') if isinstance(bg_info, dict) else '#1a1a2e'
    canvas = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), bg_color)

    # 2) 배경 이미지 적용 (템플릿 배경)
    if background_url:
        bg_img = _download_image(background_url)
        if bg_img:
            bg_img = bg_img.resize((CARD_WIDTH, CARD_HEIGHT), Image.LANCZOS)
            canvas = Image.alpha_composite(canvas, bg_img)

    # 3) 오버레이 투명도 적용
    overlay_opacity = 0.0
    if isinstance(bg_info, dict):
        overlay_opacity = bg_info.get('overlay_opacity', 0.0)
    if overlay_opacity > 0:
        overlay = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT),
                            (0, 0, 0, int(255 * overlay_opacity)))
        canvas = Image.alpha_composite(canvas, overlay)

    draw = ImageDraw.Draw(canvas)

    # 4) 요소(elements) 순서대로 렌더링
    elements = layout_data.get('elements', [])
    for elem in elements:
        _render_element(canvas, draw, elem, poster_url=poster_url)

    # 5) RGBA → RGB 변환 후 PNG로 저장
    final = canvas.convert('RGB')
    buf = io.BytesIO()
    final.save(buf, format='PNG', quality=95)
    buf.seek(0)
    return buf


def _render_element(canvas: Image.Image, draw: ImageDraw.Draw,
                    elem: dict, poster_url: str = ''):
    """개별 요소를 캔버스에 렌더링한다."""
    elem_type = elem.get('type', '')
    x = int(elem.get('x', 0))
    y = int(elem.get('y', 0))
    w = int(elem.get('width', 0))
    h = int(elem.get('height', 0))
    style = elem.get('style', {})

    if elem_type == 'image':
        # 포스터 이미지 또는 지정된 이미지 URL
        img_url = elem.get('content', '') or poster_url
        if img_url:
            img = _download_image(img_url)
            if img and w > 0 and h > 0:
                img = img.resize((w, h), Image.LANCZOS)
                canvas.paste(img, (x, y), img if img.mode == 'RGBA' else None)

    elif elem_type in ('text', 'rating', 'date', 'badge'):
        content = str(elem.get('content', ''))
        if not content:
            return

        font_size = int(style.get('font_size', 24))
        font_weight = style.get('font_weight', 'normal')
        color = style.get('color', '#ffffff')
        text_align = style.get('text_align', 'left')

        font = _load_font(font_size, font_weight)

        # 텍스트 영역 내에서 줄바꿈 처리
        if w > 0:
            lines = _wrap_text(content, font, w)
        else:
            lines = [content]

        line_height = int(style.get('line_height', font_size * 1.4))
        for i, line in enumerate(lines):
            ly = y + i * line_height
            if ly > CARD_HEIGHT:
                break

            if text_align == 'center' and w > 0:
                bbox = font.getbbox(line)
                tw = bbox[2] - bbox[0]
                lx = x + (w - tw) // 2
            elif text_align == 'right' and w > 0:
                bbox = font.getbbox(line)
                tw = bbox[2] - bbox[0]
                lx = x + w - tw
            else:
                lx = x

            draw.text((lx, ly), line, fill=color, font=font)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """텍스트를 max_width에 맞게 줄바꿈한다."""
    lines = []
    for paragraph in text.split('\n'):
        if not paragraph.strip():
            lines.append('')
            continue

        words = list(paragraph)  # 한글은 글자 단위로 분리
        current_line = ''
        for char in words:
            test = current_line + char
            bbox = font.getbbox(test)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char
        if current_line:
            lines.append(current_line)

    return lines or ['']
