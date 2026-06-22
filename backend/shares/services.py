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
사용자의 감상 기록(Record) 데이터를 받아서,
주어진 카드 템플릿 위에 텍스트와 이미지를 배치하는 레이아웃 JSON을 생성해.

## 규칙
1. 반드시 JSON 형식으로만 응답해. 다른 텍스트는 포함하지 마.
2. 카드 크기는 1080x1920 (세로형, 인스타 스토리 비율).
3. 모든 좌표는 px 단위, 좌상단 기준 (x, y).
4. 텍스트가 카드 영역 밖으로 나가지 않도록 해.
5. 감상문이 길면 핵심 문장만 발췌해서 배치해.
6. 작품 분위기에 맞는 색상과 폰트 스타일을 추천해.

## 응답 JSON 스키마
{
  "template_id": <선택된 템플릿 ID>,
  "background": {
    "color": "#hex 또는 null (템플릿 배경 사용 시)",
    "overlay_opacity": 0.0~1.0
  },
  "elements": [
    {
      "type": "text" | "image" | "rating" | "date" | "badge",
      "content": "표시할 내용",
      "x": 숫자, "y": 숫자,
      "width": 숫자, "height": 숫자,
      "style": {
        "font_size": 숫자,
        "font_weight": "normal" | "bold",
        "color": "#hex",
        "text_align": "left" | "center" | "right",
        "line_height": 숫자
      }
    }
  ],
  "mood": "분위기 키워드 (예: warm, dark, cheerful)",
  "summary": "감상문 요약 (1~2문장)"
}
"""
