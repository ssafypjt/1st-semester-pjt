"""
공유 카드 이미지 렌더러 v5 — 고정 템플릿 기반.

레퍼런스 디자인:
  ┌─────────────────────────┐
  │ 날짜           덕꾸 로고 │  ← 헤더 (0~130)
  ├─────────────────────────┤
  │  ┌──────┐  작품 제목    │
  │  │ 메인 │  (KO / EN)   │
  │  │ 이미지│              │  ← 메인 (130~1050)
  │  │      │  "감상평"     │
  │  └──────┘              │
  ├─────────────────────────┤
  │  ┌── MEMO ──┐ ┌RATING┐ │
  │  │ 텍스트.. │ │★★★★☆│ │  ← 메모+레이팅 (1050~1520)
  │  └─────────┘ │ 9.5/10│ │
  │              └───────┘ │
  ├─────────────────────────┤
  │  TAGS  #액션 #성장 ...  │  ← 태그 (1520~1820)
  │  ANILOG · 푸터          │  ← 푸터 (1820~1920)
  └─────────────────────────┘

카드 크기: 1080 × 1920 (인스타 스토리 9:16)
"""
import io
import logging
import os
import random
from urllib.request import urlopen

from PIL import Image, ImageDraw, ImageFont, ImageFilter

logger = logging.getLogger(__name__)

# ─── 카드 사이즈 ─────────────────────────────────────────
CARD_W = 1080
CARD_H = 1920

# ─── 고정 존 영역 ────────────────────────────────────────
Y_HEADER = (0, 160)       # 헤더 (날짜 + 로고) — 상단 여유 확보
Y_MAIN = (160, 960)       # 메인 (이미지 + 제목 + 감상평)
Y_STICKER = (960, 1080)   # 스티커 스트립 (다이어리 스티커 배치)
Y_MEMO = (1080, 1500)     # 메모 + 레이팅 — 메인과 간격 좁힘
Y_TAGS = (1500, 1700)     # 태그
Y_STICKER2 = (1700, 1820) # 하단 스티커 배치
Y_FOOTER = (1820, 1920)   # 푸터

# ─── 여백 ────────────────────────────────────────────────
PAD = 60  # 좌우 여백

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


# ─── 테마 ────────────────────────────────────────────────
THEMES = {
    'dark': {
        'bg_color': '#1a1625',
        'bg_asset': 'bg_dark.png',
        'card_bg': (30, 25, 45, 255),
        'card_border': (120, 90, 200, 180),
        'title_color': '#FFFFFF',
        'subtitle_color': '#A89BC2',
        'text_color': '#D0C8E0',
        'accent': '#A78BFA',
        'memo_bg': (40, 35, 60, 220),
        'memo_border': (100, 80, 160, 150),
        'rating_bg': (50, 40, 75, 230),
        'tag_bg': (60, 50, 85, 200),
        'tag_text': '#C8B8E8',
        'tag_border': (120, 100, 180, 180),
        'footer_color': '#6B5B8A',
        'quote_color': '#B8A0D8',
        'tapes': ['tape_purple.png', 'tape_mint.png'],
    },
    'warm': {
        'bg_color': '#FDF5E6',
        'bg_asset': 'bg_beige_grid.png',
        'card_bg': (255, 250, 240, 255),
        'card_border': (220, 200, 170, 180),
        'title_color': '#3A2F20',
        'subtitle_color': '#8B7355',
        'text_color': '#5D4E37',
        'accent': '#D97706',
        'memo_bg': (255, 248, 230, 240),
        'memo_border': (220, 200, 160, 180),
        'rating_bg': (245, 235, 210, 240),
        'tag_bg': (240, 230, 210, 200),
        'tag_text': '#6B5B3A',
        'tag_border': (200, 180, 140, 180),
        'footer_color': '#A09070',
        'quote_color': '#7B6840',
        'tapes': ['tape_pink.png', 'tape_yellow.png'],
    },
    'cool': {
        'bg_color': '#F0EBF8',
        'bg_asset': 'bg_lavender_grid.png',
        'card_bg': (240, 235, 255, 255),
        'card_border': (180, 160, 220, 180),
        'title_color': '#2D1F4E',
        'subtitle_color': '#7B68A8',
        'text_color': '#4A3B6B',
        'accent': '#7C3AED',
        'memo_bg': (235, 228, 248, 240),
        'memo_border': (180, 160, 220, 180),
        'rating_bg': (228, 220, 245, 240),
        'tag_bg': (220, 210, 240, 200),
        'tag_text': '#5A4880',
        'tag_border': (170, 150, 210, 180),
        'footer_color': '#9080B0',
        'quote_color': '#6B58A0',
        'tapes': ['tape_purple.png', 'tape_mint.png'],
    },
    'cute': {
        'bg_color': '#FFF0F5',
        'bg_asset': 'bg_pink_lines.png',
        'card_bg': (255, 240, 245, 255),
        'card_border': (240, 180, 200, 180),
        'title_color': '#4A2040',
        'subtitle_color': '#B06080',
        'text_color': '#6B4058',
        'accent': '#EC4899',
        'memo_bg': (255, 235, 242, 240),
        'memo_border': (240, 180, 200, 180),
        'rating_bg': (250, 228, 238, 240),
        'tag_bg': (245, 215, 230, 200),
        'tag_text': '#8B4068',
        'tag_border': (230, 170, 195, 180),
        'footer_color': '#C090A8',
        'quote_color': '#A05878',
        'tapes': ['tape_pink.png', 'tape_purple.png'],
    },
}


def _pick_theme(layout_data: dict) -> dict:
    mood = layout_data.get('mood', '').lower()
    if any(k in mood for k in ('다크', 'dark', '액션', '어두', '공포', '스릴러')):
        return THEMES['dark']
    if any(k in mood for k in ('귀여', 'cute', '사랑', '로맨스', '분홍', '핑크')):
        return THEMES['cute']
    if any(k in mood for k in ('차가', 'cool', '몽환', '판타지', '보라', '우울')):
        return THEMES['cool']
    return THEMES['warm']


# ═════════════════════════════════════════════════════════
#  폰트
# ═════════════════════════════════════════════════════════
_FONT_MAP = {
    'bold': 'NotoSansKR-Bold.ttf',
    'normal': 'NotoSansKR-Regular.ttf',
}


def _font(size: int, weight: str = 'normal') -> ImageFont.FreeTypeFont:
    font_file = _FONT_MAP.get(weight, _FONT_MAP['normal'])
    font_path = os.path.join(_FONT_DIR, font_file)
    try:
        return ImageFont.truetype(font_path, size)
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
            return Image.open(io.BytesIO(resp.read())).convert('RGBA')
    except Exception as e:
        logger.warning('이미지 다운로드 실패: %s — %s', url, e)
        return None


def _load_local_image(path: str) -> Image.Image | None:
    try:
        return Image.open(path).convert('RGBA')
    except Exception as e:
        logger.warning('로컬 이미지 로드 실패: %s — %s', path, e)
        return None


def _wrap_text(text: str, font, max_w: int) -> list[str]:
    lines = []
    for para in text.split('\n'):
        if not para.strip():
            lines.append('')
            continue
        cur = ''
        for ch in para:
            test = cur + ch
            if font.getbbox(test)[2] - font.getbbox(test)[0] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = ch
        if cur:
            lines.append(cur)
    return lines or ['']


def _draw_text(draw, text, x, y, w, font, color, align='left',
               max_lines=None, line_h_mult=1.5):
    lines = _wrap_text(text, font, w)
    if max_lines:
        lines = lines[:max_lines]
    lh = int(font.size * line_h_mult)
    for i, line in enumerate(lines):
        ly = y + i * lh
        if ly + font.size > CARD_H:
            break
        if align == 'center':
            tw = font.getbbox(line)[2] - font.getbbox(line)[0]
            lx = x + (w - tw) // 2
        elif align == 'right':
            tw = font.getbbox(line)[2] - font.getbbox(line)[0]
            lx = x + w - tw
        else:
            lx = x
        draw.text((lx, ly), line, fill=color, font=font)
    return len(lines) * lh


def _rounded_rect_img(w, h, radius, fill, border=None, border_w=2):
    """둥근 사각형 RGBA 이미지 생성."""
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([(0, 0), (w - 1, h - 1)], radius=radius,
                        fill=fill, outline=border, width=border_w)
    return img


# ═════════════════════════════════════════════════════════
#  메인 렌더 함수
# ═════════════════════════════════════════════════════════

def render_card(layout_data: dict, poster_url: str = '',
                background_url: str = '', stickers: list = None,
                deco_stickers: list = None) -> io.BytesIO:
    """
    고정 템플릿 기반 공유 카드 렌더링.

    layout_data에서 사용하는 필드:
      - mood: 테마 선택용
      - quote: AI가 추출한 한 줄 감상 (또는 content 앞부분)
      - memo_text: 메모 영역 텍스트
      - title_ko, title_en: 작품 제목
      - rating: 평점 문자열
      - tags: 태그 리스트
      - date: 날짜 문자열
    """
    stickers = stickers or []
    deco_stickers = deco_stickers or []
    theme = _pick_theme(layout_data)

    # ── 메인 이미지 결정 (사용자 업로드 > 포스터) ────────
    main_img = None
    for s in stickers:
        src = s.get('imageSrc') or ''
        if '/api/records/uploads/' in src:
            path = s.get('_local_path', '')
            main_img = _load_local_image(path) if path else _download_image(src)
            if main_img:
                break

    if not main_img:
        if poster_url and os.path.isfile(poster_url):
            main_img = _load_local_image(poster_url)
        else:
            main_img = _download_image(poster_url)

    # ── 1) 배경 ──────────────────────────────────────────
    bg_asset = _load_asset(theme.get('bg_asset', ''))
    if bg_asset:
        canvas = bg_asset.resize((CARD_W, CARD_H), Image.LANCZOS)
    else:
        canvas = Image.new('RGBA', (CARD_W, CARD_H), theme['bg_color'])
    draw = ImageDraw.Draw(canvas)

    # ── 2) 헤더 ──────────────────────────────────────────
    _render_header(canvas, draw, layout_data, theme)

    # ── 3) 메인 영역 (이미지 + 제목 + 감상평) ────────────
    _render_main(canvas, draw, layout_data, main_img, theme)

    # ── 3.5) 스티커 스트립 (메인~메모 사이) ──────────────
    _render_sticker_strip(canvas, deco_stickers, Y_STICKER, theme)

    # ── 4) 메모 + 레이팅 ─────────────────────────────────
    _render_memo_rating(canvas, draw, layout_data, theme)

    # ── 5) 태그 ──────────────────────────────────────────
    _render_tags(canvas, draw, layout_data, theme)

    # ── 5.5) 하단 스티커 스트립 ──────────────────────────
    _render_sticker_strip(canvas, deco_stickers, Y_STICKER2, theme, offset=3)

    # ── 6) 푸터 ──────────────────────────────────────────
    _render_footer(canvas, draw, theme)

    # ── 7) 장식 ──────────────────────────────────────────
    _render_decorations(canvas, theme, layout_data)

    # 출력
    final = canvas.convert('RGB')
    buf = io.BytesIO()
    final.save(buf, format='PNG', quality=95)
    buf.seek(0)
    return buf


# ═════════════════════════════════════════════════════════
#  헤더 (날짜 + 로고)
# ═════════════════════════════════════════════════════════

def _render_header(canvas, draw, data, theme):
    date_text = data.get('date', '')
    header_top = 55  # 상단 경계에서 충분한 여유

    # 날짜 뱃지
    if date_text:
        f = _font(30, 'bold')
        bbox = f.getbbox(date_text)
        tw = bbox[2] - bbox[0]
        badge = _rounded_rect_img(tw + 36, 48, 24, theme['card_bg'], theme['card_border'])
        canvas.paste(badge, (PAD, header_top), badge)
        draw.text((PAD + 18, header_top + 8), date_text, fill=theme['title_color'], font=f)

    # 덕꾸 로고 (2.5배 확대)
    logo = _load_local_image(_LOGO_PATH)
    if logo:
        logo_h = 115  # 기존 46 × 2.5
        ratio = logo_h / logo.height
        lw = int(logo.width * ratio)
        logo = logo.resize((lw, logo_h), Image.LANCZOS)
        logo_y = header_top + 24 - logo_h // 2  # 날짜 뱃지와 수직 중앙 맞춤
        canvas.paste(logo, (CARD_W - lw - PAD, max(20, logo_y)), logo)


# ═════════════════════════════════════════════════════════
#  메인 영역 (이미지 + 제목 + 감상평)
# ═════════════════════════════════════════════════════════

def _render_main(canvas, draw, data, main_img, theme):
    y_start = Y_MAIN[0] + 30  # 헤더와 간격 확보

    # 이미지 영역: 좌측 절반
    img_x = PAD
    img_y = y_start
    img_w = 500
    img_h = 600  # 존 높이에 맞게 조정

    if main_img:
        # crop-to-fill
        r = main_img.width / main_img.height
        tr = img_w / img_h
        if r > tr:
            nh = img_h
            nw = int(img_h * r)
            main_img = main_img.resize((nw, nh), Image.LANCZOS)
            left = (nw - img_w) // 2
            main_img = main_img.crop((left, 0, left + img_w, img_h))
        else:
            nw = img_w
            nh = int(img_w / r)
            main_img = main_img.resize((nw, nh), Image.LANCZOS)
            top = (nh - img_h) // 2
            main_img = main_img.crop((0, top, img_w, top + img_h))

        # 흰 프레임 (폴라로이드 스타일)
        frame_pad = 14
        frame_bottom = 50
        frame_w = img_w + frame_pad * 2
        frame_h = img_h + frame_pad + frame_bottom

        # 그림자
        shadow = Image.new('RGBA', (frame_w + 16, frame_h + 16), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rounded_rectangle([(0, 0), (frame_w + 15, frame_h + 15)],
                             radius=6, fill=(0, 0, 0, 40))
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        canvas.paste(shadow, (img_x - frame_pad + 4, img_y - frame_pad + 4), shadow)

        # 프레임
        frame = Image.new('RGBA', (frame_w, frame_h), (255, 255, 255, 250))
        fd = ImageDraw.Draw(frame)
        fd.rounded_rectangle([(0, 0), (frame_w - 1, frame_h - 1)],
                             radius=4, fill=(255, 255, 255, 250))
        frame.paste(main_img, (frame_pad, frame_pad),
                    main_img if main_img.mode == 'RGBA' else None)

        # 살짝 기울이기
        rot = random.choice([-3, -2, 2, 3])
        frame = frame.rotate(rot, expand=True, fillcolor=(0, 0, 0, 0))
        canvas.paste(frame, (img_x - frame_pad, img_y - frame_pad), frame)

        # 테이프
        if theme.get('tapes'):
            tape = _load_asset(theme['tapes'][0])
            if tape:
                tape_rot = random.randint(-15, 15)
                tape = tape.rotate(tape_rot, expand=True, fillcolor=(0, 0, 0, 0))
                tx = img_x + img_w // 2 - tape.width // 2
                ty = img_y - frame_pad - tape.height // 2
                canvas.paste(tape, (tx, ty), tape)

    # 우측: 제목 + 감상평
    text_x = 600
    text_w = CARD_W - text_x - PAD

    # 작품 제목 (한글)
    title_ko = data.get('title_ko', '')
    title_en = data.get('title_en', '')
    y_cursor = y_start + 30

    if title_ko:
        f = _font(48, 'bold')
        h = _draw_text(draw, title_ko, text_x, y_cursor, text_w, f,
                       theme['title_color'], max_lines=3)
        y_cursor += h + 8

    # 영어 제목
    if title_en:
        f = _font(22, 'normal')
        draw.text((text_x, y_cursor), title_en.upper(),
                  fill=theme['subtitle_color'], font=f)
        y_cursor += 40

    # 구분선
    draw.line([(text_x, y_cursor), (text_x + text_w - 20, y_cursor)],
              fill=theme['card_border'], width=2)
    y_cursor += 30

    # 감상평 (인용 스타일)
    quote = data.get('quote', '')
    if quote:
        # 인용부호
        qf = _font(60, 'bold')
        draw.text((text_x - 5, y_cursor - 15), '“',
                  fill=theme['accent'], font=qf)
        y_cursor += 35

        f = _font(28, 'normal')
        h = _draw_text(draw, quote, text_x + 10, y_cursor, text_w - 20, f,
                       theme['quote_color'], max_lines=8, line_h_mult=1.6)
        y_cursor += h + 10

        draw.text((text_x + text_w - 50, y_cursor), '”',
                  fill=theme['accent'], font=qf)


# ═════════════════════════════════════════════════════════
#  메모 + 레이팅
# ═════════════════════════════════════════════════════════

def _render_memo_rating(canvas, draw, data, theme):
    y_start = Y_MEMO[0] + 15

    # ── 메모 카드 (좌측) ─────────────────────────────────
    memo_text = data.get('memo_text', '')
    memo_x = PAD
    memo_y = y_start
    memo_w = 600
    memo_h = Y_MEMO[1] - Y_MEMO[0] - 30

    memo_bg = _rounded_rect_img(memo_w, memo_h, 16,
                                theme['memo_bg'], theme['memo_border'])
    canvas.paste(memo_bg, (memo_x, memo_y), memo_bg)

    # MEMO 라벨
    lf = _font(20, 'bold')
    draw.text((memo_x + 24, memo_y + 18), 'MEMO',
              fill=theme['accent'], font=lf)

    # 메모 텍스트
    if memo_text:
        f = _font(26, 'normal')
        _draw_text(draw, memo_text, memo_x + 24, memo_y + 58,
                   memo_w - 48, f, theme['text_color'],
                   max_lines=10, line_h_mult=1.55)

    # ── 레이팅 카드 (우측) ───────────────────────────────
    rating_str = data.get('rating', '')
    rating_x = memo_x + memo_w + 30
    rating_y = y_start
    rating_w = CARD_W - rating_x - PAD
    rating_h = memo_h

    rating_bg = _rounded_rect_img(rating_w, rating_h, 16,
                                  theme['rating_bg'], theme['card_border'])
    canvas.paste(rating_bg, (rating_x, rating_y), rating_bg)

    # MY RATING 라벨
    draw.text((rating_x + 24, rating_y + 18), 'MY RATING',
              fill=theme['accent'], font=lf)

    if rating_str:
        # 숫자 파싱
        try:
            score = float(rating_str.split('/')[0].strip())
        except (ValueError, IndexError):
            score = 0

        # 별 표시
        filled = int(round(score / 2))
        stars = '★' * filled + '☆' * (5 - filled)
        sf = _font(44, 'bold')
        star_bbox = sf.getbbox(stars)
        star_w = star_bbox[2] - star_bbox[0]
        sx = rating_x + (rating_w - star_w) // 2
        draw.text((sx, rating_y + 80), stars,
                  fill=theme['accent'], font=sf)

        # 숫자
        nf = _font(72, 'bold')
        score_text = f'{score:g}'
        sb = nf.getbbox(score_text)
        sw = sb[2] - sb[0]

        nf2 = _font(36, 'normal')
        suffix = ' / 10'
        sb2 = nf2.getbbox(suffix)
        sw2 = sb2[2] - sb2[0]

        total_w = sw + sw2
        start_x = rating_x + (rating_w - total_w) // 2
        ny = rating_y + 150
        draw.text((start_x, ny), score_text,
                  fill=theme['title_color'], font=nf)
        draw.text((start_x + sw, ny + 30), suffix,
                  fill=theme['subtitle_color'], font=nf2)


# ═════════════════════════════════════════════════════════
#  태그
# ═════════════════════════════════════════════════════════

def _render_tags(canvas, draw, data, theme):
    tags = data.get('tags', [])
    if not tags:
        return

    y_start = Y_TAGS[0] + 20

    # TAGS 라벨
    lf = _font(22, 'bold')
    draw.text((PAD + 8, y_start), 'TAGS', fill=theme['accent'], font=lf)
    y_start += 48

    # 태그 뱃지들
    f = _font(24, 'normal')
    x_cursor = PAD
    line_y = y_start

    for tag in tags:
        tag_text = f'#{tag}'
        bbox = f.getbbox(tag_text)
        tw = bbox[2] - bbox[0]
        badge_w = tw + 32
        badge_h = 44

        # 줄바꿈 체크
        if x_cursor + badge_w > CARD_W - PAD:
            x_cursor = PAD
            line_y += badge_h + 14

        badge = _rounded_rect_img(badge_w, badge_h, 22,
                                  theme['tag_bg'], theme['tag_border'])
        canvas.paste(badge, (x_cursor, line_y), badge)
        draw.text((x_cursor + 16, line_y + 8), tag_text,
                  fill=theme['tag_text'], font=f)
        x_cursor += badge_w + 12


# ═════════════════════════════════════════════════════════
#  스티커 스트립
# ═════════════════════════════════════════════════════════

def _render_sticker_strip(canvas, deco_stickers, y_zone, theme, offset=0):
    """다이어리 스티커를 지정된 Y 존에 배치한다.

    offset: 스티커 리스트에서 시작 인덱스 (상단/하단 분배용)
    """
    if not deco_stickers:
        return

    zone_h = y_zone[1] - y_zone[0]
    zone_mid_y = y_zone[0] + zone_h // 2

    # 사용할 스티커 선택 (offset부터 최대 3개)
    batch = deco_stickers[offset:offset + 3]
    if not batch:
        # offset이 범위 밖이면 처음부터 다시
        batch = deco_stickers[:min(2, len(deco_stickers))]

    # 균등 분배 X 좌표
    n = len(batch)
    if n == 0:
        return

    spacing = (CARD_W - PAD * 2) // (n + 1)

    for i, sticker in enumerate(batch):
        img = _load_sticker_image(sticker)
        if not img:
            continue

        # 크기 조정 (존 높이에 맞게, 최대 120px)
        max_size = min(zone_h - 10, 120)
        scale = min(max_size / img.width, max_size / img.height)
        sw = int(img.width * scale)
        sh = int(img.height * scale)
        img = img.resize((sw, sh), Image.LANCZOS)

        # 살짝 회전
        rot = random.randint(-15, 15)
        img = img.rotate(rot, expand=True, fillcolor=(0, 0, 0, 0))

        # 배치
        sx = PAD + spacing * (i + 1) - img.width // 2
        sy = zone_mid_y - img.height // 2
        canvas.paste(img, (sx, sy), img)


def _load_sticker_image(sticker: dict) -> Image.Image | None:
    """스티커 dict에서 이미지를 로드한다."""
    local = sticker.get('_local_path', '')
    if local:
        return _load_local_image(local)
    src = sticker.get('imageSrc') or ''
    if src and not src.startswith('/api/records/uploads/'):
        return _download_image(src) if src.startswith('http') else None
    return None


# ═════════════════════════════════════════════════════════
#  푸터
# ═════════════════════════════════════════════════════════

def _render_footer(canvas, draw, theme):
    y = Y_FOOTER[0] + 20
    f = _font(20, 'normal')

    # 좌측: 덕꾸
    draw.text((PAD, y), 'DEOKKKU', fill=theme['footer_color'], font=f)

    # 우측: 날짜 등
    right_text = 'RECORD YOUR ANIME LIFE'
    bbox = f.getbbox(right_text)
    tw = bbox[2] - bbox[0]
    draw.text((CARD_W - PAD - tw, y), right_text,
              fill=theme['footer_color'], font=f)

    # 구분선
    draw.line([(PAD, Y_FOOTER[0] + 5), (CARD_W - PAD, Y_FOOTER[0] + 5)],
              fill=theme['card_border'], width=1)


# ═════════════════════════════════════════════════════════
#  장식
# ═════════════════════════════════════════════════════════

def _render_decorations(canvas, theme, data):
    """테마 장식을 카드 여백에 가볍게 배치."""
    random.seed(hash(str(data.get('date', ''))) % 2**32)

    # 존 경계 근처에 장식 2~3개만
    deco_map = {
        'dark': ['deco_sparkle.png', 'deco_sparkle_small.png'],
        'warm': ['deco_flower_pink.png', 'deco_star_gold.png'],
        'cool': ['deco_flower_purple.png', 'deco_sparkle.png'],
        'cute': ['deco_heart_pink.png', 'deco_flower_pink.png'],
    }

    # 테마 키 추정
    mood = data.get('mood', '').lower()
    if any(k in mood for k in ('다크', 'dark')):
        decos = deco_map['dark']
    elif any(k in mood for k in ('귀여', 'cute')):
        decos = deco_map['cute']
    elif any(k in mood for k in ('차가', 'cool')):
        decos = deco_map['cool']
    else:
        decos = deco_map['warm']

    positions = [
        (CARD_W - 120, 30),
        (CARD_W - 80, Y_MAIN[1] - 60),
        (40, Y_TAGS[0] - 30),
    ]

    for i, (dx, dy) in enumerate(positions):
        deco = _load_asset(decos[i % len(decos)])
        if not deco:
            continue
        scale = random.uniform(0.6, 1.0)
        deco = deco.resize((int(deco.width * scale), int(deco.height * scale)),
                           Image.LANCZOS)
        rot = random.randint(-20, 20)
        deco = deco.rotate(rot, expand=True, fillcolor=(0, 0, 0, 0))
        canvas.paste(deco, (dx, dy), deco)
