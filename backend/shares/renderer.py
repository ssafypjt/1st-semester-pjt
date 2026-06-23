"""
공유 카드 이미지 렌더러 v2.

4존 구조로 카드를 렌더링한다:
  Zone 1 — 헤더: 날짜 + 덕꾸 로고
  Zone 2 — 콜라주: 포스터 이미지 + 사용자 스티커/장식
  Zone 3 — 메모: 감상문 (20자 이하 원문, 초과 시 AI 발췌)
  Zone 4 — 정보: 작품 제목 + 별점 + 태그

카드 크기: 1080 × 1920 (인스타 스토리 비율, 9:16)
"""
import io
import logging
import os
from urllib.request import urlopen

from PIL import Image, ImageDraw, ImageFont, ImageFilter

logger = logging.getLogger(__name__)

# ─── 카드 기본 사이즈 ────────────────────────────────────
CARD_WIDTH = 1080
CARD_HEIGHT = 1920

# ─── 4존 기본 영역 (y_start, y_end) ─────────────────────
ZONE_HEADER = (0, 140)          # Zone 1
ZONE_COLLAGE = (140, 1100)      # Zone 2
ZONE_MEMO = (1100, 1500)        # Zone 3
ZONE_INFO = (1500, 1920)        # Zone 4

# ─── 리소스 경로 ─────────────────────────────────────────
_FONT_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
_ASSET_DIR = os.path.join(os.path.dirname(__file__), 'assets')
_LOGO_PATH = os.path.join(_ASSET_DIR, 'simple_logo.png')


# ═════════════════════════════════════════════════════════
#  폰트
# ═════════════════════════════════════════════════════════

# NOTE: 향후 폰트 교체 시 아래 font_map 의 파일명만 변경하면 됩니다.
# 예) 손글씨 폰트 적용: 'normal': 'NanumPenScript-Regular.ttf'
_FONT_MAP = {
    'bold': 'NotoSansKR-Bold.ttf',
    'normal': 'NotoSansKR-Regular.ttf',
}


def _load_font(size: int, weight: str = 'normal') -> ImageFont.FreeTypeFont:
    """폰트를 로드한다. 실패 시 Pillow 기본 폰트 반환."""
    font_file = _FONT_MAP.get(weight, _FONT_MAP['normal'])
    font_path = os.path.join(_FONT_DIR, font_file)
    try:
        # NotoSansCJK TTC 컬렉션: index=1 → KR
        return ImageFont.truetype(font_path, size, index=1)
    except (IOError, OSError):
        logger.warning('폰트 로드 실패: %s — 기본 폰트 사용', font_path)
        try:
            return ImageFont.load_default(size)
        except TypeError:
            return ImageFont.load_default()


# ═════════════════════════════════════════════════════════
#  유틸리티
# ═════════════════════════════════════════════════════════

def _download_image(url: str) -> Image.Image | None:
    """URL에서 이미지를 다운로드하여 PIL Image로 반환."""
    if not url:
        return None
    try:
        with urlopen(url, timeout=10) as resp:
            data = resp.read()
        return Image.open(io.BytesIO(data)).convert('RGBA')
    except Exception as e:
        logger.warning('이미지 다운로드 실패: %s — %s', url, e)
        return None


def _load_local_image(path: str) -> Image.Image | None:
    """로컬 파일에서 이미지를 로드."""
    try:
        return Image.open(path).convert('RGBA')
    except Exception as e:
        logger.warning('로컬 이미지 로드 실패: %s — %s', path, e)
        return None


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """텍스트를 max_width에 맞게 줄바꿈한다 (한글 글자 단위)."""
    lines = []
    for paragraph in text.split('\n'):
        if not paragraph.strip():
            lines.append('')
            continue
        current_line = ''
        for char in paragraph:
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


def _draw_text_block(draw, text, x, y, w, font, color='#333333',
                     align='left', max_lines=None):
    """텍스트 블록을 그린다. 반환: 실제 사용한 높이."""
    lines = _wrap_text(text, font, w)
    if max_lines:
        lines = lines[:max_lines]
    line_h = int(font.size * 1.5)
    for i, line in enumerate(lines):
        ly = y + i * line_h
        if ly + font.size > CARD_HEIGHT:
            break
        if align == 'center':
            bbox = font.getbbox(line)
            tw = bbox[2] - bbox[0]
            lx = x + (w - tw) // 2
        elif align == 'right':
            bbox = font.getbbox(line)
            tw = bbox[2] - bbox[0]
            lx = x + w - tw
        else:
            lx = x
        draw.text((lx, ly), line, fill=color, font=font)
    return len(lines) * line_h


def _draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """둥근 모서리 사각형."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


# ═════════════════════════════════════════════════════════
#  메인 렌더 함수
# ═════════════════════════════════════════════════════════

def render_card(layout_data: dict, poster_url: str = '',
                background_url: str = '', stickers: list = None) -> io.BytesIO:
    """layout_data + 사용자 스티커로 공유 카드를 렌더링한다.

    Args:
        layout_data: AI가 반환한 레이아웃 JSON
        poster_url: 작품 포스터 이미지 URL
        background_url: 카드 템플릿 배경 이미지 URL
        stickers: 사용자 다이어리의 placedItems 리스트

    Returns:
        PNG 이미지가 담긴 BytesIO 객체
    """
    stickers = stickers or []

    # ── 1) 배경 ──────────────────────────────────────────
    bg = layout_data.get('background', {})
    bg_color = bg.get('color', '#FDF5E6') if isinstance(bg, dict) else '#FDF5E6'
    canvas = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), bg_color)

    if background_url:
        bg_img = _download_image(background_url)
        if bg_img:
            bg_img = bg_img.resize((CARD_WIDTH, CARD_HEIGHT), Image.LANCZOS)
            canvas = Image.alpha_composite(canvas, bg_img)

    # 오버레이
    overlay_opacity = bg.get('overlay_opacity', 0.0) if isinstance(bg, dict) else 0.0
    if overlay_opacity > 0:
        overlay = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT),
                            (255, 255, 255, int(255 * overlay_opacity)))
        canvas = Image.alpha_composite(canvas, overlay)

    draw = ImageDraw.Draw(canvas)

    # ── 2) Zone 1: 헤더 (날짜 + 덕꾸 로고) ──────────────
    _render_header(canvas, draw, layout_data)

    # ── 3) Zone 2: 콜라주 (포스터 + 스티커) ──────────────
    _render_collage(canvas, draw, layout_data, poster_url, stickers,
                    ai_sticker_placements=layout_data.get('stickers', []))

    # ── 4) Zone 3: 메모 (감상문) ─────────────────────────
    _render_memo(canvas, draw, layout_data)

    # ── 5) Zone 4: 정보 (제목 + 별점 + 태그) ────────────
    _render_info(canvas, draw, layout_data)

    # ── 6) 최종 출력 ────────────────────────────────────
    final = canvas.convert('RGB')
    buf = io.BytesIO()
    final.save(buf, format='PNG', quality=95)
    buf.seek(0)
    return buf


# ═════════════════════════════════════════════════════════
#  Zone 1: 헤더
# ═════════════════════════════════════════════════════════

def _render_header(canvas, draw, layout_data):
    """날짜 (좌측) + 덕꾸 로고 (우측)."""
    header = layout_data.get('header', {})
    date_text = header.get('date', '')
    text_color = header.get('text_color', '#8B7D6B')

    # 날짜
    if date_text:
        font = _load_font(36, 'normal')
        draw.text((60, 50), date_text, fill=text_color, font=font)

    # 덕꾸 로고
    logo = _load_local_image(_LOGO_PATH)
    if logo:
        # 로고를 높이 60px에 맞게 리사이즈
        ratio = 60 / logo.height
        logo_w = int(logo.width * ratio)
        logo = logo.resize((logo_w, 60), Image.LANCZOS)
        canvas.paste(logo, (CARD_WIDTH - logo_w - 60, 40), logo)


# ═════════════════════════════════════════════════════════
#  Zone 2: 콜라주
# ═════════════════════════════════════════════════════════

def _render_collage(canvas, draw, layout_data, poster_url, stickers,
                    ai_sticker_placements=None):
    """포스터 이미지 + 사용자 스티커 배치."""
    ai_sticker_placements = ai_sticker_placements or []
    collage = layout_data.get('collage', {})

    # ── 포스터 ────────────────────────────────────────
    poster = collage.get('poster', {})
    px = int(poster.get('x', 190))
    py = int(poster.get('y', 200))
    pw = int(poster.get('width', 700))
    ph = int(poster.get('height', 700))
    frame_style = poster.get('frame', 'none')  # none, polaroid, rounded, shadow

    # poster_url이 로컬 파일 경로일 수도 있음
    if poster_url and os.path.isfile(poster_url):
        poster_img = _load_local_image(poster_url)
    else:
        poster_img = _download_image(poster_url)
    if poster_img:
        poster_img = poster_img.resize((pw, ph), Image.LANCZOS)

        if frame_style == 'polaroid':
            _paste_polaroid(canvas, poster_img, px, py, pw, ph)
        elif frame_style == 'rounded':
            _paste_rounded(canvas, poster_img, px, py, pw, ph)
        elif frame_style == 'shadow':
            _paste_with_shadow(canvas, poster_img, px, py)
        else:
            canvas.paste(poster_img, (px, py), poster_img)

    # ── 캐릭터명 / 작품명 (포스터 아래) ──────────────
    poster_label = collage.get('label', '')
    if poster_label:
        font = _load_font(32, 'normal')
        label_color = collage.get('label_color', '#555555')
        bbox = font.getbbox(poster_label)
        tw = bbox[2] - bbox[0]
        lx = px + (pw - tw) // 2
        ly = py + ph + 16
        draw.text((lx, ly), poster_label, fill=label_color, font=font)

    # ── 사용자 스티커 (AI가 결정한 좌표로 배치) ─────
    # AI 배치 정보를 index로 매핑
    placement_map = {}
    for p in ai_sticker_placements:
        idx = p.get('index')
        if idx is not None:
            placement_map[idx] = p

    for i, sticker in enumerate(stickers):
        placement = placement_map.get(i)
        _render_sticker(canvas, sticker, placement=placement)


def _paste_polaroid(canvas, img, x, y, w, h):
    """폴라로이드 프레임 스타일로 이미지를 붙인다."""
    padding = 20
    bottom_padding = 60
    frame_w = w + padding * 2
    frame_h = h + padding + bottom_padding
    frame = Image.new('RGBA', (frame_w, frame_h), (255, 255, 255, 255))
    frame.paste(img, (padding, padding), img if img.mode == 'RGBA' else None)
    # 약간 회전
    frame = frame.rotate(-3, expand=True, fillcolor=(0, 0, 0, 0))
    canvas.paste(frame, (x - padding, y - padding), frame)


def _paste_rounded(canvas, img, x, y, w, h, radius=24):
    """둥근 모서리로 이미지를 잘라서 붙인다."""
    mask = Image.new('L', (w, h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (w, h)], radius=radius, fill=255)
    img.putalpha(mask)
    canvas.paste(img, (x, y), img)


def _paste_with_shadow(canvas, img, x, y, offset=8, blur=12):
    """그림자 효과로 이미지를 붙인다."""
    shadow = Image.new('RGBA', (img.width + blur * 2, img.height + blur * 2), (0, 0, 0, 0))
    shadow_base = Image.new('RGBA', img.size, (0, 0, 0, 80))
    shadow.paste(shadow_base, (blur, blur))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    canvas.paste(shadow, (x + offset - blur, y + offset - blur), shadow)
    canvas.paste(img, (x, y), img if img.mode == 'RGBA' else None)


def _render_sticker(canvas, sticker_data, placement=None):
    """사용자 다이어리의 스티커/말풍선/이미지를 카드에 배치.

    placement가 있으면 AI가 결정한 px 좌표를 사용하고,
    없으면 원본 % 좌표를 px로 변환하여 폴백한다.

    프론트엔드 placedItems 구조:
    - 일반 스티커: {icon: "♡", tone: "pink", x: 6, y: 18, scale: 1.08, rotate: 0}
    - 이미지 스티커: {icon: "", imageSrc: "/api/records/uploads/3/", ...}
    - 말풍선: {type: "bubble", bubbleType: "normal", text: "개꿀잼", ...}
    """
    item_type = sticker_data.get('type', 'sticker')

    if placement:
        # AI가 결정한 px 좌표 사용
        px = int(placement.get('x', 0))
        py = max(int(placement.get('y', 0)), ZONE_COLLAGE[0])  # Zone 1 침범 방지
        ai_w = int(placement.get('width', 0))
        ai_h = int(placement.get('height', 0))
        rotation = int(placement.get('rotation', 0))
    else:
        # 폴백: % → px 변환 (Zone 2~3 범위로 매핑)
        x_pct = sticker_data.get('x', 0)
        y_pct = sticker_data.get('y', 0)
        px = int(x_pct / 100 * CARD_WIDTH)
        py = max(int(y_pct / 100 * CARD_HEIGHT), ZONE_COLLAGE[0])  # Zone 1 침범 방지
        ai_w = 0
        ai_h = 0
        rotation = int(sticker_data.get('rotate', 0))

    if item_type == 'bubble':
        ai_font_size = int(placement.get('font_size', 0)) if placement else 0
        _render_bubble_sticker(canvas, sticker_data, px, py,
                               override_w=ai_w, override_h=ai_h,
                               override_font_size=ai_font_size)
    elif sticker_data.get('imageSrc'):
        _render_image_sticker(canvas, sticker_data, px, py, rotation,
                              override_w=ai_w, override_h=ai_h)
    elif sticker_data.get('icon'):
        _render_icon_sticker(canvas, sticker_data, px, py, rotation,
                             override_size=ai_w)


def _render_icon_sticker(canvas, data, px, py, rotation, override_size=0):
    """이모지/텍스트 아이콘 스티커를 렌더링한다."""
    icon = data.get('icon', '')
    if not icon or icon in ('tape', 'POLA', 'FILM', 'grid', 'dot'):
        if not icon:
            return
    if override_size:
        font_size = max(24, override_size // 2)
    else:
        scale = data.get('scale', 1.0)
        font_size = int(48 * scale)
    font = _load_font(font_size, 'bold')

    # 스티커를 별도 이미지에 그려서 회전 후 합성
    text_img = Image.new('RGBA', (font_size * 3, font_size * 3), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    try:
        bbox = font.getbbox(icon)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
    except Exception:
        tw, th = font_size, font_size
    tx = (text_img.width - tw) // 2
    ty = (text_img.height - th) // 2
    text_draw.text((tx, ty), icon, fill='#6b5b8a', font=font)

    # 투명 여백 제거
    bbox_actual = text_img.getbbox()
    if bbox_actual:
        text_img = text_img.crop(bbox_actual)

    if rotation:
        text_img = text_img.rotate(-rotation, expand=True, fillcolor=(0, 0, 0, 0))

    canvas.paste(text_img, (px, py), text_img)


def _render_image_sticker(canvas, data, px, py, rotation,
                          override_w=0, override_h=0):
    """이미지 스티커를 렌더링한다."""
    local_path = data.get('_local_path', '')
    src = data.get('imageSrc', '')
    if not src and not local_path:
        return

    img = _load_local_image(local_path) if local_path else _download_image(src)
    if not img:
        return

    if override_w and override_h:
        target_w = override_w
        target_h = override_h
    elif override_w:
        ratio = override_w / img.width
        target_w = override_w
        target_h = int(img.height * ratio)
    else:
        scale = data.get('scale', 0.72)
        target_w = int(CARD_WIDTH * 0.12 * scale)
        ratio = target_w / img.width
        target_h = int(img.height * ratio)
    img = img.resize((target_w, target_h), Image.LANCZOS)

    if rotation:
        img = img.rotate(-rotation, expand=True, fillcolor=(0, 0, 0, 0))

    canvas.paste(img, (px, py), img)


def _render_bubble_sticker(canvas, data, px, py, override_w=0, override_h=0,
                           override_font_size=0):
    """말풍선 스티커를 렌더링한다."""
    text = data.get('text', '')
    bubble_type = data.get('bubbleType', 'normal')
    if override_w and override_h:
        width = override_w
        height = override_h
    else:
        width = int(data.get('width', 180) * CARD_WIDTH / 640)
        height = int(data.get('height', 100) * CARD_HEIGHT / 900)

    # AI가 지정한 font_size 우선, 없으면 말풍선 크기에 맞춰 자동 계산
    if override_font_size:
        font_size = override_font_size
    else:
        # 말풍선 크기에 맞춰 글꼴 크기 자동 조정
        font_size = _auto_bubble_font_size(text, width, height)
    bg_color = data.get('bgColor', '#ffffff')
    border_color = data.get('borderColor', '#b49cd8')
    text_color = data.get('textColor', '#342a3f')

    # 말풍선 배경 그리기
    bubble = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    bubble_draw = ImageDraw.Draw(bubble)

    radius = 36 if bubble_type == 'thought' else 24
    bubble_draw.rounded_rectangle(
        [(0, 0), (width - 1, height - 1)],
        radius=radius, fill=bg_color, outline=border_color, width=3,
    )

    # 말풍선 꼬리/구름점
    if bubble_type == 'thought':
        # 구름 점 2개
        bubble_draw.ellipse(
            [20, height - 2, 34, height + 12],
            fill=bg_color, outline=border_color, width=2,
        )
        bubble_draw.ellipse(
            [10, height + 10, 20, height + 20],
            fill=bg_color, outline=border_color, width=2,
        )
    else:
        # 삼각형 꼬리
        tail = [(14, height - 2), (28, height - 2), (10, height + 14)]
        bubble_draw.polygon(tail, fill=bg_color, outline=border_color)
        # 꼬리 내부 흰색으로 경계 덮기
        bubble_draw.line([(16, height - 3), (26, height - 3)], fill=bg_color, width=4)

    # 텍스트
    if text:
        font = _load_font(font_size, 'bold')
        padding = 16
        _draw_text_on_image(bubble_draw, text, padding, padding,
                            width - padding * 2, font, text_color)

    canvas.paste(bubble, (px, py), bubble)


def _auto_bubble_font_size(text: str, width: int, height: int) -> int:
    """말풍선 크기에 맞는 글꼴 크기를 자동 계산한다."""
    if not text:
        return 20
    padding = 16 * 2  # 좌우 패딩
    usable_w = max(width - padding, 60)
    usable_h = max(height - padding, 40)
    # 한글 1글자 ≈ font_size px 폭, 1.4 * font_size 높이
    # 적절한 크기를 이진탐색
    for fs in range(28, 11, -2):
        chars_per_line = max(1, usable_w // fs)
        num_lines = (len(text) + chars_per_line - 1) // chars_per_line
        total_h = int(num_lines * fs * 1.4)
        if total_h <= usable_h:
            return fs
    return 12


def _draw_text_on_image(draw, text, x, y, max_w, font, color):
    """이미지 위에 줄바꿈 텍스트를 그린다."""
    lines = _wrap_text(text, font, max_w)
    line_h = int(font.size * 1.4)
    for i, line in enumerate(lines):
        draw.text((x, y + i * line_h), line, fill=color, font=font)


# ═════════════════════════════════════════════════════════
#  Zone 3: 메모
# ═════════════════════════════════════════════════════════

def _render_memo(canvas, draw, layout_data):
    """감상문 영역. 메모지 느낌의 배경 위에 텍스트 배치."""
    memo = layout_data.get('memo', {})
    text = memo.get('text', '')
    if not text:
        return

    # 메모 영역 좌표
    mx = int(memo.get('x', 100))
    my = int(memo.get('y', ZONE_MEMO[0] + 30))
    mw = int(memo.get('width', 880))
    mh = int(memo.get('height', 340))
    bg_color = memo.get('bg_color', '#FFFFFF')
    text_color = memo.get('text_color', '#444444')
    border_color = memo.get('border_color', None)

    # 메모지 배경
    _draw_rounded_rect(draw, (mx, my, mx + mw, my + mh),
                       radius=12, fill=bg_color,
                       outline=border_color, width=2 if border_color else 0)

    # 텍스트
    # NOTE: 향후 손글씨 폰트 적용 시 여기의 weight를 변경
    font_size = int(memo.get('font_size', 28))
    font = _load_font(font_size, 'normal')
    padding = 30
    _draw_text_block(draw, text, mx + padding, my + padding,
                     mw - padding * 2, font, color=text_color,
                     align='left', max_lines=8)


# ═════════════════════════════════════════════════════════
#  Zone 4: 정보
# ═════════════════════════════════════════════════════════

def _render_info(canvas, draw, layout_data):
    """작품 제목 + 별점 + 태그."""
    info = layout_data.get('info', {})
    text_color = info.get('text_color', '#333333')
    accent_color = info.get('accent_color', '#7C3AED')

    center_x = CARD_WIDTH // 2
    y_cursor = ZONE_INFO[0] + 30

    # 작품 제목
    title = info.get('title', '')
    if title:
        font = _load_font(44, 'bold')
        bbox = font.getbbox(title)
        tw = bbox[2] - bbox[0]
        draw.text((center_x - tw // 2, y_cursor), title,
                  fill=text_color, font=font)
        y_cursor += 70

    # 별점
    rating = info.get('rating', '')
    if rating:
        font = _load_font(52, 'bold')
        rating_str = str(rating)
        bbox = font.getbbox(rating_str)
        tw = bbox[2] - bbox[0]
        draw.text((center_x - tw // 2, y_cursor), rating_str,
                  fill=accent_color, font=font)
        y_cursor += 80

    # 태그
    tags = info.get('tags', [])
    if tags:
        font = _load_font(26, 'normal')
        tag_str = '  '.join(f'#{t}' for t in tags)
        bbox = font.getbbox(tag_str)
        tw = bbox[2] - bbox[0]
        tag_color = info.get('tag_color', '#888888')
        draw.text((center_x - tw // 2, y_cursor), tag_str,
                  fill=tag_color, font=font)
