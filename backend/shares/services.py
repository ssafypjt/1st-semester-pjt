"""
GMS AI 서비스 클라이언트.

GMS(제공되는 AI 게이트웨이)를 통해 GPT / Gemini 등을 호출하여
공유 카드 레이아웃 JSON을 생성한다.

Quick Example 기반 curl 구조:
    curl -X POST <GMS_API_URL> \
         -H "Authorization: Bearer <GMS_API_KEY>" \
         -H "Content-Type: application/json" \
         -d '{"model": "...", "messages": [...]}'
"""
import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class GMSClient:
    """GMS AI 게이트웨이 클라이언트."""

    def __init__(self):
        self.api_url = getattr(settings, 'GMS_API_URL',
                               'https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions')
        self.api_key = getattr(settings, 'GMS_API_KEY', '')
        ## 모델 바꾸는 곳
        self.model = getattr(settings, 'GMS_MODEL', 'gpt-4.1-mini')
        self.timeout = getattr(settings, 'GMS_TIMEOUT', 30)

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

    def chat_completion(self, messages: list[dict], **kwargs) -> dict:
        """GMS chat completion API 호출.

        Args:
            messages: [{"role": "system"|"user", "content": "..."}]
            **kwargs: temperature, max_completion_tokens 등 추가 파라미터

        Returns:
            전체 API 응답 dict

        Raises:
            GMSError: API 호출 실패 시
        """
        if not self.api_url or not self.api_key:
            raise GMSError('GMS_API_URL 또는 GMS_API_KEY가 설정되지 않았습니다.')

        payload = {
            'model': kwargs.get('model', self.model),
            'messages': messages,
            'temperature': kwargs.get('temperature', 0.7),
            'max_tokens': kwargs.get('max_tokens', 1024),
        }

        # JSON 응답을 강제하기 위한 response_format (지원되는 모델에 한해)
        if kwargs.get('json_mode', True):
            payload['response_format'] = {'type': 'json_object'}

        try:
            resp = requests.post(
                self.api_url,
                headers=self._headers(),
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            raise GMSError('GMS API 요청 시간 초과')
        except requests.exceptions.HTTPError as e:
            logger.error('GMS API HTTP 오류: %s — %s', e, resp.text)
            raise GMSError(f'GMS API 오류: {resp.status_code}')
        except requests.exceptions.RequestException as e:
            logger.error('GMS API 요청 실패: %s', e)
            raise GMSError(f'GMS API 연결 실패: {e}')

    def generate_card_layout(self, prompt: str, **kwargs) -> dict:
        """공유 카드 레이아웃 JSON을 생성한다.

        Args:
            prompt: 조립된 최종 프롬프트 (시스템 + 유저 메시지)

        Returns:
            AI가 생성한 레이아웃 JSON (dict)
        """
        messages = [
            {
                'role': 'system',
                'content': SYSTEM_PROMPT,
            },
            {
                'role': 'user',
                'content': prompt,
            },
        ]

        response = self.chat_completion(messages, **kwargs)

        # 응답에서 content 추출
        try:
            content = response['choices'][0]['message']['content']
            layout = json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            logger.error('AI 응답 파싱 실패: %s — 원본: %s', e, response)
            raise GMSError(f'AI 응답 파싱 실패: {e}')

        # 토큰 사용량 메타데이터
        usage = response.get('usage', {})
        layout['_meta'] = {
            'model': response.get('model', self.model),
            'prompt_tokens': usage.get('prompt_tokens', 0),
            'completion_tokens': usage.get('completion_tokens', 0),
        }

        return layout


class GMSError(Exception):
    """GMS API 관련 오류."""
    pass


# ─── 시스템 프롬프트 ────────────────────────────────────
SYSTEM_PROMPT = """\
너는 공유 카드 레이아웃 디자이너 AI야.
사용자의 감상 기록을 받아서 **사용자 이미지 중심** 스크랩북 스타일의 레이아웃 JSON을 생성해.

## 핵심 디자인 철학
사용자가 업로드한 이미지(is_main_image: true)가 카드의 **주인공**이다.
종이 배경, 테이프, 스티커, 메모지는 그 이미지를 **꾸며주는 역할**.
포스터(작품 커버)는 작은 폴라로이드로 곁들이는 **보조 요소**.

## 규칙
1. 반드시 JSON 형식으로만 응답해. 다른 텍스트는 절대 포함하지 마.
2. 카드 크기: 1080×1920px (인스타 스토리 비율).
3. 모든 좌표는 px 단위, 좌상단(0,0) 기준.
4. 각 존의 y 범위를 반드시 지켜.
5. 감상문 20자 이하면 원문 그대로, 초과면 핵심 1~2문장 발췌.

## 존 구조 (v4)
- Zone 1 — 헤더: y 0~140
- Zone 2 — 메인 이미지 + 포스터: y 140~1200 (사용자 이미지가 주인공)
- Zone 3 — 메모: y 1200~1560
- Zone 4 — 정보: y 1560~1920

## 응답 JSON 스키마
{
  "template_id": <선택된 템플릿 ID>,
  "background": { "color": "#hex", "overlay_opacity": 0.0~1.0 },
  "header": { "date": "YYYY.MM.DD", "text_color": "#hex" },
  "collage": {
    "poster": {
      "x": 숫자, "y": 숫자, "width": 160~320, "height": 숫자,
      "frame": "polaroid"
    },
    "label": "포스터 아래 작품명 (선택)",
    "label_color": "#hex"
  },
  "stickers": [
    {
      "index": 0,
      "x": 숫자, "y": 숫자,
      "width": 숫자, "height": 숫자,
      "rotation": -15~15,
      "font_size": 16~28 (말풍선만)
    }
  ],
  "memo": {
    "text": "감상문 (원문 또는 발췌)",
    "x": 숫자, "y": 1220~1280, "width": 숫자, "height": 숫자,
    "bg_color": "#hex", "text_color": "#hex",
    "border_color": "#hex 또는 null", "font_size": 24~34
  },
  "info": {
    "title": "작품 제목",
    "rating": "9.5 / 10",
    "tags": ["태그1", "태그2"],
    "text_color": "#hex", "accent_color": "#hex", "tag_color": "#hex"
  },
  "mood": "분위기 키워드"
}

## stickers 배치 규칙
- index는 입력 stickers 배열의 순서 (0부터).
- **모든 y좌표 ≥ 140** (헤더 침범 금지).
- 다이어리 원본 x_pct, y_pct 상대 위치를 카드 크기에 맞게 반영.

### ★ 메인 이미지 (is_main_image: true) — 카드의 주인공
- Zone 2(y: 140~1200) 전체를 **최대한 크게** 차지하도록 배치 (최소 width 600, height 500).
- 여러 장이면 Zone 2를 나눠서 각각 크게.
- 다이어리 상대 위치 반영 (왼쪽에 있던 건 카드 왼쪽).
- 메인 이미지끼리 겹치지 않게.

### 포스터 (collage.poster) — 보조 요소
- width는 160~320px으로 작게. 메인 이미지를 가리지 않는 빈 구석에 배치.
- 폴라로이드 프레임 고정.

### 일반 스티커 / 이미지 스티커 — 꾸미기 요소
- 아이콘: 60~100px, 이미지 스티커: 100~200px.
- 다이어리 원본 위치 참고.
- 메인 이미지 중심 70% 보호 영역에는 배치 금지. 가장자리 30%만 가능.
- rotation: -15~15도 (스크랩북 느낌).
- 메모지 테두리와 10~20% 겹쳐도 됨 (Z-order가 높아서 위에 그려짐).

### 말풍선 (type: "bubble")
- 텍스트가 **절대 잘리지 않도록** 충분한 크기 확보.
- 한글 1글자 ≈ width 28px, height 34px. 최소 width 160px, height 80px.
- font_size 반드시 포함 (16~28).
- 메모지 테두리와 겹쳐도 됨. 스티커는 메모지 위에 렌더링됨.
"""
