# AI 공유 카드 기능 — 작업 문서

## 개요

사용자가 감상 기록(Record)에서 "공유" 버튼을 누르면, AI가 기록 내용을 분석하여 공유 카드 이미지를 자동 생성하는 기능.

AI는 그림을 직접 생성하지 않는다. 미리 준비된 카드 템플릿(CardTemplate) 위에 작품 포스터, 제목, 감상문, 평점 등을 AI가 배치하고, 서버(Pillow)가 최종 이미지로 렌더링하여 저장한다.

---

## 작업 브랜치

```
feature/ai-share-card (master에서 분기)
```

---

## 생성된 파일 목록

```
backend/
├── shares/                    ← 새로 생성된 Django 앱
│   ├── __init__.py
│   ├── apps.py                # SharesConfig
│   ├── models.py              # CardTemplate, ShareCard
│   ├── services.py            # GMSClient (GMS AI 게이트웨이 클라이언트)
│   ├── prompts.py             # Record → AI 프롬프트 조립
│   ├── renderer.py            # AI 레이아웃 JSON → Pillow 이미지 렌더링
│   ├── serializers.py         # DRF 시리얼라이저
│   ├── views.py               # API 엔드포인트 (생성/조회)
│   ├── urls.py                # URL 라우팅
│   ├── admin.py               # Django Admin 등록
│   ├── fonts/                 # 한글 폰트 파일 (직접 추가 필요)
│   └── migrations/
│       └── __init__.py
├── config/
│   ├── settings.py            ← 수정됨 (INSTALLED_APPS, GMS 설정)
│   └── urls.py                ← 수정됨 (api/shares/ 경로 추가)
└── .env                       ← GMS_KEY 추가 필요
```

---

## 수정된 기존 파일

### config/settings.py

1. `INSTALLED_APPS`에 `'shares'` 추가
2. 하단에 GMS 설정 3줄 추가:

```python
GMS_API_URL = env('GMS_API_URL', default='https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions')
GMS_API_KEY = env('GMS_KEY', default='')
GMS_TIMEOUT = env.int('GMS_TIMEOUT', default=30)
```

### config/urls.py

```python
path('api/shares/', include('shares.urls')),
```

---

## 환경 변수 (.env)

```dotenv
# 필수 — GMS AI 게이트웨이 키
GMS_KEY=발급받은-키-값

# 선택 — 기본값이 있으므로 변경할 때만 추가
# GMS_API_URL=https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions
# GMS_TIMEOUT=30
```

AI 모델명은 `.env`에 넣지 않는다. 앱마다 다른 모델을 쓸 수 있도록 코드에서 직접 지정한다 (아래 "AI 모델 변경 방법" 참고).

---

## DB 모델

### CardTemplate (card_template)

미리 준비해둔 카드 디자인 템플릿. Admin에서 등록한다.

| 필드 | 타입 | 설명 |
|------|------|------|
| name | varchar(100) | 템플릿 이름 |
| category | varchar(20) | minimal / emotional / retro / cute / dark |
| thumbnail | URL(500) | 썸네일 이미지 URL |
| background_image | URL(500) | 카드 배경 이미지 URL |
| layout_schema | JSON | 텍스트/이미지 슬롯 위치·크기 정의 |
| description_for_ai | text | AI가 템플릿 선택 시 참고할 설명문 |
| is_active | bool | 활성화 여부 |

### ShareCard (share_card)

AI가 생성한 공유 카드. Record 1개에 여러 장 생성 가능 (재생성).

| 필드 | 타입 | 설명 |
|------|------|------|
| record | FK → Record | 원본 감상 기록 |
| template | FK → CardTemplate | 사용된 템플릿 (nullable) |
| layout_data | JSON | AI가 결정한 최종 배치 정보 |
| image | ImageField | 렌더링된 PNG 이미지 파일 |
| ai_model | varchar(50) | 사용된 AI 모델명 |
| ai_prompt_tokens | int | 프롬프트 토큰 수 |
| ai_response_tokens | int | 응답 토큰 수 |

---

## API 엔드포인트

| Method | URL | 인증 | 설명 |
|--------|-----|------|------|
| POST | `/api/shares/<record_id>/generate/` | 필수 (본인 기록만) | AI 공유 카드 생성 |
| GET | `/api/shares/<record_id>/` | 필수 (본인 기록만) | 내 기록의 카드 목록 |
| GET | `/api/shares/card/<card_id>/` | 불필요 | 카드 단건 조회 (공유 링크용) |
| GET | `/api/shares/templates/` | 불필요 | 활성 카드 템플릿 목록 |

### 카드 생성 요청 예시

```bash
POST /api/shares/3/generate/
Content-Type: application/json

{
  "template_id": 1       # 선택사항. 생략하면 AI가 자동 선택
}
```

### 응답 예시

```json
{
  "id": 7,
  "record": 3,
  "template": 1,
  "template_name": "미니멀 다크",
  "layout_data": { ... },
  "image_url": "http://localhost:8000/media/uploads/shares/1/share_card_7.png",
  "ai_model": "gpt-5-mini",
  "created_at": "2026-06-22T15:30:00+09:00"
}
```

---

## 처리 흐름

```
[프론트: 공유 버튼 클릭]
  → POST /api/shares/<record_id>/generate/
    → ① Record + Work 데이터 조회
    → ② 활성 CardTemplate 목록 조회
    → ③ prompts.py: Record 데이터 + 템플릿 목록 → AI 프롬프트 조립
    → ④ services.py: GMS API 호출 (GPT/Gemini) → 레이아웃 JSON 수신
    → ⑤ renderer.py: Pillow로 1080×1920 PNG 이미지 렌더링
    → ⑥ ShareCard 모델에 이미지 + 레이아웃 저장
    → ⑦ image_url 반환
```

---

## AI 모델 변경 방법

모델 설정은 `.env`나 `settings.py`에 없다. 각 앱의 코드에서 `GMSClient` 생성 시 직접 지정한다.

### 기본 구조

```python
from shares.services import GMSClient

# 기본값 사용 (gpt-5-mini)
client = GMSClient()

# 다른 모델 지정
client = GMSClient('gemini-2.0-flash')

# 호출 시점에 일회성 오버라이드도 가능
client.generate_card_layout(prompt, model='gpt-5-mini')
```

### 현재 앱별 모델 설정

| 앱 | 용도 | 모델 | 설정 위치 |
|----|------|------|-----------|
| shares | 공유 카드 레이아웃 | gpt-5-mini | `shares/services.py` → `GMSClient.DEFAULT_MODEL` |
| (예정) stickers | 스티커 생성 | gemini 등 | 해당 앱의 서비스 모듈에서 지정 |

### 기본 모델을 변경하려면

`shares/services.py`에서 `DEFAULT_MODEL` 값을 수정:

```python
class GMSClient:
    DEFAULT_MODEL = 'gpt-5-mini'   # ← 이 값을 변경
```

### 새 앱에서 다른 모델을 쓰려면

해당 앱의 서비스 코드에서 GMSClient를 import하고 모델을 지정:

```python
# stickers/services.py (예시)
from shares.services import GMSClient

def generate_sticker(prompt):
    client = GMSClient('gemini-2.0-flash')
    return client.chat_completion([
        {'role': 'developer', 'content': '스티커 생성 시스템 프롬프트'},
        {'role': 'user', 'content': prompt},
    ])
```

> GMSClient는 shares 앱에 있지만 프로젝트 공용 AI 클라이언트로 쓸 수 있다.
> 앱이 많아지면 별도 `common/` 또는 `ai/` 앱으로 분리하는 것을 권장한다.

---

## 셋업 체크리스트

- [ ] `.env`에 `GMS_KEY` 추가
- [ ] `python manage.py makemigrations shares`
- [ ] `python manage.py migrate`
- [ ] Admin에서 CardTemplate 최소 1개 등록 (배경 이미지 URL, 카테고리, AI 설명문)
- [ ] `shares/fonts/`에 한글 폰트 배치 (NotoSansKR-Regular.ttf, NotoSansKR-Bold.ttf)
- [ ] `pip install Pillow requests` (requirements.txt에 추가)
- [ ] 프론트엔드에서 공유 버튼 → POST /api/shares/<id>/generate/ 연결

---

## 남은 작업

1. CardTemplate 디자인 및 데이터 등록 (배경 이미지, layout_schema 정의)
2. 한글 폰트 파일 추가 (fonts/ 디렉토리)
3. 프론트엔드 공유 버튼 UI 연결
4. 프롬프트 튜닝 (실제 AI 응답 품질 보고 조정)
5. (선택) 스티커 생성 앱 — GMSClient에 다른 모델 지정하여 활용
6. (선택) 공유 카드 SNS 공유 기능 (카카오톡, 인스타 스토리 등)
