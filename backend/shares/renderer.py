"""
공유 카드 이미지 렌더러 v4 — 사용자 이미지 중심 스크랩북.

디자인 철학:
  사용자가 업로드한 이미지가 **주인공**.
  종이 배경 · 테이프 · 스티커 · 장식이 이미지를 **꾸며주는** 형태.
  포스터(작품 커버)는 작은 폴라로이드로 곁들인다.

카드 크기: 1080 × 1920 (인스타 스토리 9:16)
"""
import io
import logging
import os
import random
from urllib.request import urlopen

from PIL import Image, ImageDraw, ImageFont, ImageFilter

logger = logging.getLogger(__name__)

# ─── 카드 기본 사이즈 ────────────────────────────────────
CARD_WIDTH = 1080
CARD_HEIGHT = 1920

# ─── 존 영역 (y_start, y_end) ───────────────────────────
ZONE_HEADER = (0, 140)
ZONE_MAIN = (140, 1200)     # 사용자 이미지 + 포스터 영역 (확장)
ZONE_MEMO = (1200, 1560)
ZONE_INFO = (1560, 1920)

# ─── 리소스 경로 ─────────────────────────────────────────
_FONT_DIR = os.path.join(os.path.dirname(__file__), 'fonts')
_ASSET_DIR = os.path.join(os.path.dirname(__file__), 'assets')
_TEMPLATE_DIR = os.path.join(_ASSET_DIR, 'templates')
_LOGO_PATH = os.path.join(_ASSET_DIR, 'simple_logo.png')

# ─── 에셋 캐시 ──────────────────────────────────────────
_asset_cache: dict[str, Image.Image] = {}


def _load_asset(name: str) -> Image.Image | None:
    if name in _asset_cache:
        return _asset_cache[name].copy()
    path = os.path.join(_TEMPLATE_DIR, name)
    if not os.path.isfile(path):
        return None
    try:
        img = Image.open(path).convert('RGBA')
        _asset_cache[name] = img
        return img.copy()
    except Exception as e:
        logger.warning('에셋 로드 실패: %s — %s', name, e)
        return None


# ─── 분위기 → 에셋 매핑 ─────────────────────────────────
MOOD_THEMES = {
    'warm': {
        'bg': 'bg_beige_grid.png',
        'memo': 'memo_cream_grid.png',
        'tapes': ['tape_pink.png', 'tape_yellow.png'],
        'decos': ['deco_flower_pink.png', 'deco_star_gold.png', 'deco_heart_pink.png', 'deco_sparkle.png'],
        'date_bg': (255, 200, 160, 200),
        'info_accent': '#D97706',
        'paper_tint': (255, 250, 240, 240),
    },
    'cool': {
        'bg': 'bg_lavender_grid.png',
        'memo': 'memo_purple_grid.png',
        'tapes': ['tape_purple.png', 'tape_mint.png'],
        'decos': ['deco_flower_purple.png', 'deco_star_gold.png', 'deco_sparkle.png', 'deco_sparkle_small.png'],
        'date_bg': (200, 180, 230, 200),
        'info_accent': '#7C3AED',
        'paper_tint': (240, 235, 255, 240),
    },
    'cute': {
        'bg': 'bg_pink_lines.png',
        'memo': 'memo_pink_grid.png',
        'tapes': ['tape_pink.png', 'tape_purple.png'],
        'decos': ['deco_heart_pink.png', 'deco_heart_red.png', 'deco_flower_pink.png', 'deco_star_small.png'],
        'date_bg': (255, 180, 200, 200),
        'info_accent': '#EC4899',
        'paper_tint': (255, 240, 245, 240),
    },
    'dark': {
        'bg': 'bg_dark.png',
        'memo': 'memo_purple_grid.png',
        'tapes': ['tape_purple.png', 'tape_mint.png'],
        'decos': ['deco_sparkle.png', 'deco_sparkle_small.png', 'deco_star_gold.png'],
        'date_bg': (80, 70, 110, 200),
        'info_accent': '#A78BFA',
        'paper_tint': (60, 55, 80, 220),
    },
}


def _pick_theme(layout_data: dict) -> dict:
    mood = layout_data.get('mood', '').lower()
    bg = layout_data.get('background', {})
    bg_color = bg.get('color', '#FDF5E6') if isinstance(bg, dict) else '#FDF5E6'

    if any(k in mood for k in ('다크', 'dark', '액션', '어두', '공포', '스릴러')):
        return MOOD_THEMES['dark']
    if any(k in mood for k in ('귀여', 'cute', '사랑', '로맨스', '분홍', '핑크')):
        return MOOD_THEMES['cute']
    if any(k in mood for k in ('차가', 'cool', '몽환', '판타지', '보라', '우울')):
        return MOOD_THEMES['cool']

    try:
        r, g, b = int(bg_color[1:3], 16), int(bg_color[3:5], 16), int(bg_color[5:7], 16)
        brightness = (r + g + b) / 3
        if brightness < 80:
            return MOOD_THEMES['dark']
        if r > g and r > b and r > 200:
            return MOOD_THEMES['cute']
        if b > r and b > 180:
            return MOOD_THEMES['cool']
    except (ValueError, IndexError):
        pass

    return MOOD_THEMES['warm']


# ═════════════════════════════════════════════════════════
#  폰트
# ═════════════════════════════════════════════════════════
_FONT_MAP = {
    'bold': 'NotoSansKR-Bold.ttf',
    'normal': 'NotoSansKR-Regular.ttf',
}


def _load_font(size: int, weight: str = 'normal') -> ImageFont.FreeTypeFont:
    font_file = _FONT_MAP.get(weight, _FONT_MAP['normal'])
    font_path = os.path.join(_FONT_DIR, font_file)
    try:
        return ImageFont.truetype(font_path, size, index=1)
    except (IOError, OSError):
        try:
            return ImageFont.load_default(size)
        except TypeError:
            return ImageFont.load_default()


# ═════════════════════════════════════════════════════════
#  유틸리티
# ═════════════════════════════════════════════════════════

def _download_image(url: str) -> Image.Image | None:
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
    try:
        return Image.open(path).convert('RGBA')
    except Exception as e:
        logger.warning('로컬 이미지 로드 실패: %s — %s', path, e)
        return None


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
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


# ═════════════════════════════════════════════════════════
#  메인 렌더 함수
# ═════════════════════════════════════════════════════════

def render_card(layout_data: dict, poster_url: str = '',
                background_url: str = '', stickers: list = None) -> io.BytesIO:
    stickers = stickers or []
    theme = _pick_theme(layout_data)

    # 스티커를 메인 이미지 vs 장식으로 분리
    main_images = []
    deco_stickers = []
    for s in stickers:
        if s.get('type') == 'text':
            continue
        if _is_main_image(s):
            main_images.append(s)
        else:
            deco_stickers.append(s)

    # ── 1) 배경 ─────────────────────────────────────────
    bg_asset = _load_asset(theme['bg'])
    if bg_asset:
        canvas = bg_asset.resize((CARD_WIDTH, CARD_HEIGHT), Image.LANCZOS)
    else:
        bg = layout_data.get('background', {})
        bg_color = bg.get('color', '#FDF5E6') if isinstance(bg, dict) else '#FDF5E6'
        canvas = Image.new('RGBA', (CARD_WIDTH, CARD_HEIGHT), bg_color)

    draw = ImageDraw.Draw(canvas)

    # ── 2) 헤더 ─────────────────────────────────────────
    _render_header(canvas, draw, layout_data, theme)

    # ── 3) ★ 사용자 이미지 (주인공) ─────────────────────
    #    종이 배경 + 이미지 + 테이프로 꾸밈
    ai_sticker_placements = layout_data.get('stickers', [])
    _render_hero_images(canvas, draw, main_images, ai_sticker_placements, theme)

    # ── 4) 포스터 (작은 폴라로이드로 곁들이기) ───────────
    _render_poster_mini(canvas, draw, layout_data, poster_url, theme)

    # ── 5) 메모 ─────────────────────────────────────────
    _render_memo(canvas, draw, layout_data, theme)

    # ── 6) 정보 ─────────────────────────────────────────
    _render_info(canvas, draw, layout_data, theme)

    # ── 7) 장식 스티커 (말풍선 · 아이콘 등 — 위에 얹기) ─
    _render_deco_stickers(canvas, deco_stickers, ai_sticker_placements)

    # ── 8) 테마 장식 흩뿌리기 ───────────────────────────
    _scatter_decorations(canvas, theme, layout_data)

    # ── 최종 출력 ───────────────────────────────────────
    final = canvas.convert('RGB')
    buf = io.BytesIO()
    final.save(buf, format='PNG', quality=95)
    buf.seek(0)
    return buf


def _is_main_image(sticker: dict) -> bool:
    """사용자가 업로드한 장면/이미지인지 판단."""
    src = sticker.get('imageSrc') or ''
    return '/api/records/uploads/' in src


# ═════════════════════════════════════════════════════════
#  Zone 1: 헤더
# ═════════════════════════════════════════════════════════

def _render_header(canvas, draw, layout_data, theme):
    header = layout_data.get('header', {})
    date_text = header.get('date', '')

    if date_text:
        font = _load_font(32, 'bold')
        bbox = font.getbbox(date_text)
        tw = bbox[2] - bbox[0]
        badge_w = tw + 40
        badge_h = 52
        badge = Image.new('RGBA', (badge_w, badge_h), (0, 0, 0, 0))
        badge_draw = ImageDraw.Draw(badge)
        badge_draw.rounded_rectangle(
            [(0, 0), (badge_w - 1, badge_h - 1)],
            radius=26, fill=theme['date_bg'],
        )
        badge_draw.text((20, 10), date_text, fill='#5D4E37', font=font)
        canvas.paste(badge, (60, 44), badge)

    logo = _load_local_image(_LOGO_PATH)
    if logo:
        ratio = 50 / logo.height
        logo_w = int(logo.width * ratio)
        logo = logo.resize((logo_w, 50), Image.LANCZOS)
        canvas.paste(logo, (CARD_WIDTH - logo_w - 60, 46), logo)


# ═════════════════════════════════════════════════════════
#  ★ 히어로 이미지 (사용자 업로드 이미지 = 주인공)
# ═════════════════════════════════════════════════════════

def _render_hero_images(canvas, draw, main_images, ai_placements, theme):
    """사용자 이미지를 종이 배경 + 테이프로 꾸며서 크게 배치."""
    if not main_images:
        return

    placement_map = {}
    for p in (ai_placements or []):
        idx = p.get('index')
        if idx is not None:
            placement_map[idx] = p

    for img_data in main_images:
        # 이미지 로드
        local_path = img_data.get('_local_path', '')
        src = img_data.get('imageSrc') or ''
        img = _load_local_image(local_path) if local_path else _download_image(src)
        if not img:
            continue

        # AI 배치 또는 기본 배치
        idx = img_data.get('_sticker_index', -1)
        placement = placement_map.get(idx)

        if placement:
            px = int(placement.get('x', 100))
            py = max(int(placement.get('y', 180)), ZONE_MAIN[0])
            pw = int(placement.get('width', 800))
            ph = int(placement.get('height', 700))
            rotation = int(placement.get('rotation', 0))
        else:
            # 기본: Zone 2 중앙에 크게
            px = 80
            py = ZONE_MAIN[0] + 40
            pw = CARD_WIDTH - 160
            ph = ZONE_MAIN[1] - ZONE_MAIN[0] - 120
            rotation = random.choice([-3, -2, 0, 2, 3])

        _paste_hero_photo(canvas, img, px, py, pw, ph, rotation, theme)


def _paste_hero_photo(canvas, img, x, y, w, h, rotation, theme):
    """
    히어로 이미지: 종이 매트 + 사진 + 테이프.

    종이 매트(paper_tint)가 배경이 되고,
    그 위에 이미지를 올리고,
    테이프로 고정하는 스크랩북 느낌.
    """
    # 이미지를 목표 크기에 맞춤 (비율 유지, crop-to-fill)
    img_ratio = img.width / img.height
    target_ratio = w / h
    if img_ratio > target_ratio:
        # 이미지가 더 넓음 → 높이 맞추고 가로 crop
        new_h = h
        new_w = int(h * img_ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - w) // 2
        img = img.crop((left, 0, left + w, h))
    else:
        # 이미지가 더 높음 → 가로 맞추고 세로 crop
        new_w = w
        new_h = int(w / img_ratio)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        top = (new_h - h) // 2
        img = img.crop((0, top, w, top + h))

    # 종이 매트 (이미지보다 약간 큰 흰색 종이)
    paper_pad = 20
    paper_w = w + paper_pad * 2
    paper_h = h + paper_pad * 2

    paper = Image.new('RGBA', (paper_w, paper_h), theme.get('paper_tint', (255, 250, 240, 240)))
    paper_draw = ImageDraw.Draw(paper)
    # 종이 테두리 (살짝 어두운 선)
    paper_draw.rounded_rectangle(
        [(0, 0), (paper_w - 1, paper_h - 1)],
        radius=4, outline=(0, 0, 0, 30), width=1,
    )
    # 이미지를 종이 위에 올리기
    paper.paste(img, (paper_pad, paper_pad), img if img.mode == 'RGBA' else None)

    # 그림자
    shadow = Image.new('RGBA', (paper_w + 24, paper_h + 24), (0, 0, 0, 0))
    shadow_base = Image.new('RGBA', (paper_w, paper_h), (0, 0, 0, 45))
    shadow.paste(shadow_base, (12, 12))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))

    # 회전
    if rotation:
        paper = paper.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))
        shadow = shadow.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))

    # 붙이기
    sx = x - paper_pad
    sy = y - paper_pad
    canvas.paste(shadow, (sx, sy), shadow)
    canvas.paste(paper, (sx, sy), paper)

    # 테이프 2개 (위쪽 양 모서리)
    if theme.get('tapes'):
        tape_positions = [
            (x + w // 4 - 30, y - paper_pad - 15),          # 왼쪽 상단
            (x + w * 3 // 4 - 30, y - paper_pad - 15),      # 오른쪽 상단
        ]
        for i, (tx, ty) in enumerate(tape_positions):
            tape_name = theme['tapes'][i % len(theme['tapes'])]
            tape = _load_asset(tape_name)
            if tape:
                tape_scale = random.uniform(0.9, 1.2)
                tape = tape.resize(
                    (int(tape.width * tape_scale), int(tape.height * tape_scale)),
                    Image.LANCZOS,
                )
                tape_rot = random.randint(-20, 20)
                tape = tape.rotate(tape_rot, expand=True, fillcolor=(0, 0, 0, 0))
                canvas.paste(tape, (tx, ty), tape)


# ═════════════════════════════════════════════════════════
#  포스터 (작은 폴라로이드)
# ═════════════════════════════════════════════════════════

def _render_poster_mini(canvas, draw, layout_data, poster_url, theme):
    """포스터를 작은 폴라로이드로 구석에 배치."""
    collage = layout_data.get('collage', {})
    poster = collage.get('poster', {})

    # AI가 지정한 좌표 사용, 없으면 기본값
    px = int(poster.get('x', 80))
    py = int(poster.get('y', 800))
    pw = int(poster.get('width', 220))
    ph = int(poster.get('height', 310))

    # 포스터가 너무 크면 축소 (v4에서는 보조 요소)
    max_poster_w = 320
    if pw > max_poster_w:
        ratio = max_poster_w / pw
        pw = max_poster_w
        ph = int(ph * ratio)

    if poster_url and os.path.isfile(poster_url):
        poster_img = _load_local_image(poster_url)
    else:
        poster_img = _download_image(poster_url)

    if not poster_img:
        return

    poster_img = poster_img.resize((pw, ph), Image.LANCZOS)
    _paste_polaroid(canvas, poster_img, px, py, pw, ph, theme)

    # 라벨 (작품명)
    poster_label = collage.get('label', '')
    if poster_label:
        font = _load_font(22, 'normal')
        bbox = font.getbbox(poster_label)
        tw = bbox[2] - bbox[0]
        lx = px + (pw - tw) // 2
        ly = py + ph + 65
        draw.text((lx, ly), poster_label, fill='#7B6B5A', font=font)


def _paste_polaroid(canvas, img, x, y, w, h, theme):
    """폴라로이드 프레임 + 테이프."""
    pad = 16
    bottom_pad = 50
    frame_w = w + pad * 2
    frame_h = h + pad + bottom_pad

    # 그림자
    shadow = Image.new('RGBA', (frame_w + 16, frame_h + 16), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([(0, 0), (frame_w + 15, frame_h + 15)], radius=4, fill=(0, 0, 0, 35))
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))

    # 프레임
    frame = Image.new('RGBA', (frame_w, frame_h), (255, 255, 255, 255))
    fd = ImageDraw.Draw(frame)
    fd.rounded_rectangle([(0, 0), (frame_w - 1, frame_h - 1)], radius=3, fill=(255, 255, 255, 255))
    frame.paste(img, (pad, pad), img if img.mode == 'RGBA' else None)

    rotation = random.choice([-5, -3, 3, 5, 7])
    frame = frame.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))
    shadow = shadow.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))

    sx = x - pad - 8
    sy = y - pad - 8
    canvas.paste(shadow, (sx + 6, sy + 6), shadow)
    canvas.paste(frame, (sx, sy), frame)

    # 테이프 1개
    if theme.get('tapes'):
        tape_name = random.choice(theme['tapes'])
        tape = _load_asset(tape_name)
        if tape:
            tape_rot = random.randint(-25, 25)
            tape = tape.rotate(tape_rot, expand=True, fillcolor=(0, 0, 0, 0))
            tx = x + w // 2 - tape.width // 2
            ty = y - pad - tape.height // 2
            canvas.paste(tape, (tx, ty), tape)


# ═════════════════════════════════════════════════════════
#  장식 스티커 (말풍선 · 아이콘 · 기본 스티커)
# ═════════════════════════════════════════════════════════

def _render_deco_stickers(canvas, deco_stickers, ai_placements):
    """메인 이미지가 아닌 스티커들을 위에 얹는다."""
    placement_map = {}
    for p in (ai_placements or []):
        idx = p.get('index')
        if idx is not None:
            placement_map[idx] = p

    for sticker in deco_stickers:
        idx = sticker.get('_sticker_index', -1)
        placement = placement_map.get(idx)
        _render_sticker(canvas, sticker, placement)


def _render_sticker(canvas, sticker_data, placement=None):
    item_type = sticker_data.get('type', 'sticker')

    if placement:
        px = int(placement.get('x', 0))
        py = max(int(placement.get('y', 0)), ZONE_MAIN[0])
        ai_w = int(placement.get('width', 0))
        ai_h = int(placement.get('height', 0))
        rotation = int(placement.get('rotation', 0))
    else:
        x_pct = sticker_data.get('x', 0)
        y_pct = sticker_data.get('y', 0)
        px = int(x_pct / 100 * CARD_WIDTH)
        py = max(int(y_pct / 100 * CARD_HEIGHT), ZONE_MAIN[0])
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
    icon = data.get('icon', '')
    if not icon:
        return
    if override_size:
        font_size = max(24, override_size // 2)
    else:
        scale = data.get('scale', 1.0)
        font_size = int(48 * scale)
    font = _load_font(font_size, 'bold')

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

    bbox_actual = text_img.getbbox()
    if bbox_actual:
        text_img = text_img.crop(bbox_actual)

    if rotation:
        text_img = text_img.rotate(-rotation, expand=True, fillcolor=(0, 0, 0, 0))

    canvas.paste(text_img, (px, py), text_img)


def _render_image_sticker(canvas, data, px, py, rotation,
                          override_w=0, override_h=0):
    local_path = data.get('_local_path', '')
    src = data.get('imageSrc') or ''
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
        target_w = int(CARD_WIDTH * 0.15 * scale)
        ratio = target_w / img.width
        target_h = int(img.height * ratio)
    img = img.resize((target_w, target_h), Image.LANCZOS)

    # 둥근 모서리
    radius = min(12, target_w // 8, target_h // 8)
    mask = Image.new('L', (target_w, target_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([(0, 0), (target_w, target_h)], radius=radius, fill=255)
    img.putalpha(mask)

    if rotation:
        img = img.rotate(-rotation, expand=True, fillcolor=(0, 0, 0, 0))

    # 그림자
    shadow = Image.new('RGBA', (img.width + 8, img.height + 8), (0, 0, 0, 0))
    shadow_base = Image.new('RGBA', img.size, (0, 0, 0, 35))
    shadow.paste(shadow_base, (4, 4))
    shadow = shadow.filter(ImageFilter.GaussianBlur(4))
    canvas.paste(shadow, (px, py), shadow)

    canvas.paste(img, (px, py), img)


def _render_bubble_sticker(canvas, data, px, py, override_w=0, override_h=0,
                           override_font_size=0):
    text = data.get('text', '')
    bubble_type = data.get('bubbleType', 'normal')
    if override_w and override_h:
        width = override_w
        height = override_h
    else:
        width = int(data.get('width', 180) * CARD_WIDTH / 640)
        height = int(data.get('height', 100) * CARD_HEIGHT / 900)

    if override_font_size:
        font_size = override_font_size
    else:
        font_size = _auto_bubble_font_size(text, width, height)

    bg_color = data.get('bgColor', '#ffffff')
    border_color = data.get('borderColor', '#b49cd8')
    text_color = data.get('textColor', '#342a3f')

    total_h = height + 24 if bubble_type == 'thought' else height + 18
    bubble = Image.new('RGBA', (width + 8, total_h + 8), (0, 0, 0, 0))
    bubble_draw = ImageDraw.Draw(bubble)

    # 그림자
    radius = 28 if bubble_type == 'thought' else 20
    bubble_draw.rounded_rectangle(
        [(6, 6), (width + 5, height + 5)],
        radius=radius, fill=(0, 0, 0, 25),
    )

    # 본체
    bubble_draw.rounded_rectangle(
        [(2, 2), (width + 1, height + 1)],
        radius=radius, fill=bg_color, outline=border_color, width=2,
    )

    # 꼬리
    if bubble_type == 'thought':
        bubble_draw.ellipse([18, height, 30, height + 10], fill=bg_color, outline=border_color, width=2)
        bubble_draw.ellipse([10, height + 8, 18, height + 16], fill=bg_color, outline=border_color, width=2)
    else:
        tail = [(14, height - 1), (26, height - 1), (10, height + 14)]
        bubble_draw.polygon(tail, fill=bg_color, outline=border_color)
        bubble_draw.line([(16, height - 1), (24, height - 1)], fill=bg_color, width=3)

    if text:
        font = _load_font(font_size, 'bold')
        padding = 14
        _draw_text_on_image(bubble_draw, text, padding + 2, padding + 2,
                            width - padding * 2, font, text_color)

    canvas.paste(bubble, (px, py), bubble)


def _auto_bubble_font_size(text: str, width: int, height: int) -> int:
    if not text:
        return 20
    padding = 16 * 2
    usable_w = max(width - padding, 60)
    usable_h = max(height - padding, 40)
    for fs in range(28, 11, -2):
        chars_per_line = max(1, usable_w // fs)
        num_lines = (len(text) + chars_per_line - 1) // chars_per_line
        total_h = int(num_lines * fs * 1.4)
        if total_h <= usable_h:
            return fs
    return 12


def _draw_text_on_image(draw, text, x, y, max_w, font, color):
    lines = _wrap_text(text, font, max_w)
    line_h = int(font.size * 1.4)
    for i, line in enumerate(lines):
        draw.text((x, y + i * line_h), line, fill=color, font=font)


# ═════════════════════════════════════════════════════════
#  Zone 3: 메모
# ═════════════════════════════════════════════════════════

def _render_memo(canvas, draw, layout_data, theme):
    memo = layout_data.get('memo', {})
    text = memo.get('text', '')
    if not text:
        return

    mx = int(memo.get('x', 100))
    my = int(memo.get('y', ZONE_MEMO[0] + 20))
    mw = int(memo.get('width', 880))
    mh = int(memo.get('height', 300))
    text_color = memo.get('text_color', '#444444')

    # 메모지 에셋
    memo_asset = _load_asset(theme.get('memo', 'memo_cream_grid.png'))
    if memo_asset:
        memo_asset = memo_asset.resize((mw, mh), Image.LANCZOS)
        shadow = Image.new('RGBA', (mw + 12, mh + 12), (0, 0, 0, 0))
        shadow_base = Image.new('RGBA', (mw, mh), (0, 0, 0, 30))
        shadow.paste(shadow_base, (6, 6))
        shadow = shadow.filter(ImageFilter.GaussianBlur(6))
        canvas.paste(shadow, (mx, my), shadow)
        canvas.paste(memo_asset, (mx, my), memo_asset)
    else:
        bg_color = memo.get('bg_color', '#FFFFFF')
        border_color = memo.get('border_color', None)
        draw.rounded_rectangle(
            (mx, my, mx + mw, my + mh),
            radius=12, fill=bg_color,
            outline=border_color, width=2 if border_color else 0,
        )

    # 테이프 2개
    if theme.get('tapes'):
        for i, pos in enumerate([(mx + 20, my - 12), (mx + mw - 60, my - 12)]):
            tape_name = theme['tapes'][i % len(theme['tapes'])]
            tape = _load_asset(tape_name)
            if tape:
                tape_rot = random.choice([-15, -10, 10, 15])
                tape = tape.rotate(tape_rot, expand=True, fillcolor=(0, 0, 0, 0))
                canvas.paste(tape, pos, tape)

    font_size = int(memo.get('font_size', 28))
    font = _load_font(font_size, 'normal')
    padding = 30
    _draw_text_block(draw, text, mx + padding, my + padding + 10,
                     mw - padding * 2, font, color=text_color,
                     align='left', max_lines=8)


# ═════════════════════════════════════════════════════════
#  Zone 4: 정보
# ═════════════════════════════════════════════════════════

def _render_info(canvas, draw, layout_data, theme):
    info = layout_data.get('info', {})
    text_color = info.get('text_color', '#333333')
    accent_color = info.get('accent_color', theme.get('info_accent', '#7C3AED'))

    center_x = CARD_WIDTH // 2
    y_cursor = ZONE_INFO[0] + 30

    # 구분선
    draw.line(
        [(center_x - 200, y_cursor - 10), (center_x + 200, y_cursor - 10)],
        fill=accent_color + '40' if len(accent_color) == 7 else accent_color,
        width=2,
    )

    # 작품 제목
    title = info.get('title', '')
    if title:
        font = _load_font(42, 'bold')
        bbox = font.getbbox(title)
        tw = bbox[2] - bbox[0]
        draw.text((center_x - tw // 2, y_cursor), title,
                  fill=text_color, font=font)
        y_cursor += 65

    # 별점
    rating = info.get('rating', '')
    if rating:
        font = _load_font(44, 'bold')
        rating_str = f'★ {rating}'
        bbox = font.getbbox(rating_str)
        tw = bbox[2] - bbox[0]
        draw.text((center_x - tw // 2, y_cursor), rating_str,
                  fill=accent_color, font=font)
        y_cursor += 70

    # 태그
    tags = info.get('tags', [])
    if tags:
        font = _load_font(22, 'normal')
        tag_color = info.get('tag_color', '#888888')
        total_w = 0
        tag_sizes = []
        for t in tags:
            tag_text = f'#{t}'
            bbox = font.getbbox(tag_text)
            tw = bbox[2] - bbox[0]
            tag_sizes.append((tag_text, tw))
            total_w += tw + 28 + 10
        total_w -= 10

        start_x = center_x - total_w // 2
        for tag_text, tw in tag_sizes:
            badge_w = tw + 28
            badge_h = 36
            draw.rounded_rectangle(
                [(start_x, y_cursor), (start_x + badge_w, y_cursor + badge_h)],
                radius=18, fill=accent_color + '20' if len(accent_color) == 7 else accent_color,
                outline=accent_color + '40' if len(accent_color) == 7 else accent_color,
            )
            draw.text((start_x + 14, y_cursor + 5), tag_text,
                      fill=tag_color, font=font)
            start_x += badge_w + 10


# ═════════════════════════════════════════════════════════
#  장식 흩뿌리기
# ═════════════════════════════════════════════════════════

def _scatter_decorations(canvas, theme, layout_data):
    decos = theme.get('decos', [])
    if not decos:
        return

    random.seed(hash(str(layout_data.get('header', {}).get('date', ''))) % 2**32)

    positions = [
        (CARD_WIDTH - 160, 20), (CARD_WIDTH - 100, 90),
        (40, 200), (CARD_WIDTH - 100, 250),
        (60, 500), (CARD_WIDTH - 80, 600),
        (CARD_WIDTH - 120, 900),
        (80, 1160), (CARD_WIDTH - 100, 1180),
        (CARD_WIDTH - 80, 1450),
        (80, 1850), (CARD_WIDTH - 100, 1830),
    ]

    count = min(len(positions), random.randint(4, 6))
    chosen = random.sample(positions, count)

    for i, (dx, dy) in enumerate(chosen):
        deco_name = decos[i % len(decos)]
        deco = _load_asset(deco_name)
        if not deco:
            continue
        scale = random.uniform(0.7, 1.3)
        new_w = int(deco.width * scale)
        new_h = int(deco.height * scale)
        deco = deco.resize((new_w, new_h), Image.LANCZOS)
        rot = random.randint(-30, 30)
        deco = deco.rotate(rot, expand=True, fillcolor=(0, 0, 0, 0))
        ox = dx + random.randint(-15, 15)
        oy = dy + random.randint(-15, 15)
        canvas.paste(deco, (ox, oy), deco)
