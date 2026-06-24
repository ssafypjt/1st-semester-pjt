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
너는 애니메이션 감상 카드 콘텐츠 큐레이터 AI야.
사용자의 감상 기록을 받아서 카드에 들어갈 **콘텐츠 데이터 JSON**을 생성해.

## 규칙
1. 반드시 JSON 형식으로만 응답해. 다른 텍스트는 절대 포함하지 마.
2. 좌표·크기·색상은 지정하지 마. 레이아웃은 렌더러가 처리한다.
3. 감상평이 짧으면(20자 이하) 원문 그대로, 길면 핵심 1~2문장 발췌.
4. 태그는 한글로 변환 (Action → 액션, Fantasy → 판타지).

## 응답 JSON 스키마
{
  "mood": "분위기 한 단어 (다크/귀여운/차가운/따뜻한/몽환적/열정적)",
  "quote": "한 줄 인용문 (30자 내)",
  "memo_text": "메모 영역 텍스트 (3문장 내)",
  "tags": ["태그1", "태그2", ...],
  "title_ko": "한국어 제목",
  "title_en": "ENGLISH TITLE"
}
"""
