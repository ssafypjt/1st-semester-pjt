"""
GMS AI 서비스 클라이언트 — 2단계 파이프라인.

Stage 1: 콘텐츠 생성 AI — 메모·말풍선·감상평을 종합하여 카드 텍스트 생성
Stage 2: 배치 AI — 작품 정보 + Stage 1 결과로 최종 카드 데이터 JSON 생성

GMS 게이트웨이를 통해 gpt-5-mini를 호출한다.
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
        self.model = getattr(settings, 'GMS_MODEL', 'gpt-5-mini')
        self.timeout = getattr(settings, 'GMS_TIMEOUT', 30)

    def _headers(self):
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }

    def chat_completion(self, messages: list[dict], **kwargs) -> dict:
        """GMS chat completion API 호출."""
        if not self.api_url or not self.api_key:
            raise GMSError('GMS_API_URL 또는 GMS_API_KEY가 설정되지 않았습니다.')

        payload = {
            'model': kwargs.get('model', self.model),
            'messages': messages,
            'temperature': kwargs.get('temperature', 1),
            'max_completion_tokens': kwargs.get('max_completion_tokens', 4096),
        }

        if kwargs.get('json_mode', True):
            payload['response_format'] = {'type': 'json_object'}

        try:
            logger.info('GMS 요청: model=%s, messages=%d개, url=%s',
                        payload['model'], len(messages), self.api_url)
            resp = requests.post(
                self.api_url,
                headers=self._headers(),
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info('GMS 응답: status=%s, finish=%s',
                        resp.status_code,
                        data.get('choices', [{}])[0].get('finish_reason', 'N/A'))
            return data
        except requests.exceptions.Timeout:
            raise GMSError('GMS API 요청 시간 초과')
        except requests.exceptions.HTTPError as e:
            logger.error('GMS API HTTP 오류: %s — %s', e, resp.text)
            raise GMSError(f'GMS API 오류: {resp.status_code}')
        except requests.exceptions.RequestException as e:
            logger.error('GMS API 요청 실패: %s', e)
            raise GMSError(f'GMS API 연결 실패: {e}')

    def _call_json(self, developer_prompt: str, user_prompt: str,
                   **kwargs) -> dict:
        """developer + user 메시지로 JSON 응답을 받아 파싱한다."""
        messages = [
            {'role': 'developer', 'content': developer_prompt},
            {'role': 'user', 'content': user_prompt},
        ]
        response = self.chat_completion(messages, **kwargs)

        try:
            content = response['choices'][0]['message']['content']
            if not content or not content.strip():
                finish = response['choices'][0].get('finish_reason', 'unknown')
                logger.error('AI 응답 빈 content — finish_reason: %s, response: %s', finish, response)
                raise GMSError(f'AI가 빈 응답을 반환했습니다 (finish_reason: {finish})')
            result = json.loads(content)
        except (KeyError, IndexError) as e:
            logger.error('AI 응답 구조 오류: %s — 원본: %s', e, response)
            raise GMSError(f'AI 응답 구조 오류: {e}')
        except json.JSONDecodeError as e:
            logger.error('AI 응답 JSON 파싱 실패: %s — content: %s', e, content[:500] if content else '(empty)')
            raise GMSError(f'AI 응답 JSON 파싱 실패: {e}')

        # 토큰 사용량
        usage = response.get('usage', {})
        result['_meta'] = {
            'model': response.get('model', self.model),
            'prompt_tokens': usage.get('prompt_tokens', 0),
            'completion_tokens': usage.get('completion_tokens', 0),
        }
        return result

    # ─── Stage 1: 콘텐츠 생성 ────────────────────────────

    def generate_content(self, prompt: str, **kwargs) -> dict:
        """Stage 1 — 메모·말풍선·감상평을 종합하여 카드 텍스트를 생성한다.

        Returns:
            {"quote": "...", "memo_text": "...", "_meta": {...}}
        """
        return self._call_json(STAGE1_PROMPT, prompt, **kwargs)

    # ─── Stage 2: 카드 데이터 생성 ───────────────────────

    def generate_card_layout(self, prompt: str, **kwargs) -> dict:
        """Stage 2 — 작품 정보 + Stage 1 결과로 최종 카드 데이터를 생성한다.

        Returns:
            {"mood": "...", "quote": "...", "memo_text": "...",
             "tags": [...], "title_ko": "...", "title_en": "...", "_meta": {...}}
        """
        return self._call_json(STAGE2_PROMPT, prompt, **kwargs)


class GMSError(Exception):
    """GMS API 관련 오류."""
    pass


# ═════════════════════════════════════════════════════════
#  Stage 1 — 콘텐츠 생성 프롬프트
# ═════════════════════════════════════════════════════════
STAGE1_PROMPT = """\
너는 애니메이션 감상 카드의 텍스트 라이터야.
사용자의 다이어리 데이터(감상평, 메모, 말풍선 텍스트)를 받아서
공유 카드에 넣을 텍스트를 생성해.

## 규칙
1. 반드시 JSON 형식으로만 응답해.
2. quote: 감상의 핵심을 담은 한 줄 (30자 내). 임팩트 있게.
3. memo_text: 감상 내용을 3문장 이내로 정리. 메모·말풍선·감상평을 종합.
4. 입력이 부족하면 작품명과 분위기에 맞게 적절히 생성해.

## 응답 JSON
{
  "quote": "한 줄 인용문 (30자 내)",
  "memo_text": "메모 영역 텍스트 (3문장 내)"
}
"""

# ═════════════════════════════════════════════════════════
#  Stage 2 — 카드 배치 프롬프트
# ═════════════════════════════════════════════════════════
STAGE2_PROMPT = """\
너는 애니메이션 감상 카드 배치 AI야.
작품 정보와 생성된 텍스트를 받아서 최종 카드 데이터 JSON을 만들어.

## 규칙
1. 반드시 JSON 형식으로만 응답해.
2. 좌표·크기·색상은 지정하지 마. 렌더러가 처리한다.
3. mood: 작품 장르·감상 분위기에 맞는 한 단어.
4. tags: 작품 장르·태그를 한글로 5개 이내 (Action → 액션).
5. quote, memo_text는 Stage 1 결과를 그대로 사용하되, 필요시 다듬어.

## 응답 JSON
{
  "mood": "분위기 한 단어 (다크/귀여운/차가운/따뜻한/몽환적/열정적)",
  "quote": "한 줄 인용문 (30자 내)",
  "memo_text": "메모 영역 텍스트 (3문장 내)",
  "tags": ["태그1", "태그2", ...],
  "title_ko": "한국어 제목",
  "title_en": "ENGLISH TITLE"
}
"""
