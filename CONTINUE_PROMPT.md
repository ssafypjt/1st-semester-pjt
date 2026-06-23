# 덕꾸(Deokkku) 프로젝트 컨텍스트 — 대화 이어가기용

이 문서는 이전 대화의 전체 컨텍스트를 정리한 것입니다. 새 대화에서 이 내용을 붙여넣으면 작업을 이어갈 수 있습니다.

---

## 1. 프로젝트 개요

**덕꾸(Deokkku)** — 애니메이션 감상 기록 + 다꾸(다이어리 꾸미기) + AI 공유 카드 생성 웹앱

- **백엔드**: Django 4.x + DRF, SQLite, SessionAuthentication + CSRF
- **프론트엔드**: Vue.js 3 (Options API), Vite 개발 서버 (localhost:5173)
- **AI**: GMS AI Gateway → gpt-4.1-mini (non-reasoning, max_tokens/temperature/system role 지원)
- **이미지 렌더링**: Pillow (서버사이드)

## 2. 디렉토리 구조 (핵심)

```
backend/
├── config/settings.py          # Django 설정
├── accounts/                   # 인증 (login/logout/signup/me/CSRF)
├── works/                      # 작품 DB (애니메이션 정보)
├── records/                    # 감상 기록 CRUD
│   ├── models.py               # Record, RecordImage, StickerAsset, UserSticker, Comment, Like
│   ├── views.py                # RecordViewSet (?mine=1 필터 지원)
│   ├── serializers.py          # RecordListSerializer (canvas_data, content 포함)
│   └── permissions.py          # IsOwnerOrReadOnly
├── shares/                     # AI 공유 카드 시스템
│   ├── models.py               # CardTemplate, ShareCard
│   ├── views.py                # generate_share_card, list_share_cards, list_templates
│   ├── services.py             # GMSClient (GMS AI Gateway 클라이언트) + SYSTEM_PROMPT
│   ├── prompts.py              # build_card_prompt (4존 구조 프롬프트 조립)
│   ├── renderer.py             # render_card (4존 Pillow 렌더러)
│   ├── serializers.py          # CardTemplateSerializer, ShareCardSerializer
│   ├── urls.py                 # API 엔드포인트
│   ├── fonts/                  # NotoSansKR-Regular.ttf, NotoSansKR-Bold.ttf (TTC index=1 for KR)
│   ├── assets/                 # simple_logo.png (덕꾸 로고)
│   └── migrations/
│       ├── 0001_initial.py
│       └── 0002_seed_card_templates.py  # data migration (5개 기본 템플릿)
└── db.sqlite3

frontend/
├── src/
│   ├── App.vue                 # ★ 메인 SPA (Vite dev server용, {{ }} 구분자)
│   ├── assets/
│   │   ├── app.css             # 전체 CSS
│   │   └── images/             # simple_logo.png, main-logo.png
│   └── components/
│       └── layout/Sidebar.vue  # 사이드바 (로고 클릭 → $emit('navigate', '홈'))
├── static/js/app.js            # Django-served 빌드 ([[ ]] 구분자) — 현재 동기화 안 됨
├── templates/index.html        # Django 템플릿 (원본 로그인 UI 참고용)
└── vite.config.js              # /api, /media → http://127.0.0.1:8000 프록시
```

## 3. 공유 카드 시스템 (4존 구조) — 가장 최근 작업

### 아키텍처
```
Record → views.py → prompts.py (프롬프트 조립)
                  → services.py (GMS AI 호출 → layout_data JSON)
                  → renderer.py (Pillow 이미지 렌더링)
                  → ShareCard 저장
```

### 4존 레이아웃 (1080×1920px, 인스타 스토리 비율)
- **Zone 1 — 헤더 (y: 0~140)**: 날짜(좌) + 덕꾸 로고(우, 자동 삽입)
- **Zone 2 — 콜라주 (y: 140~1100)**: 포스터 이미지 + 사용자 다이어리 스티커(placedItems 반영)
  - 포스터 프레임: none / polaroid / rounded / shadow (AI가 선택)
- **Zone 3 — 메모 (y: 1100~1500)**: 감상문 (20자 이하 원문, 초과 시 AI 발췌/요약)
- **Zone 4 — 정보 (y: 1500~1920)**: 작품 제목 + 별점 + 태그

### AI 응답 JSON 스키마
```json
{
  "template_id": 1,
  "background": { "color": "#FDF5E6", "overlay_opacity": 0.0 },
  "header": { "date": "2026.06.22", "text_color": "#8B7D6B" },
  "collage": {
    "poster": { "x": 190, "y": 200, "width": 700, "height": 700, "frame": "polaroid" },
    "label": "Frieren", "label_color": "#555555"
  },
  "memo": {
    "text": "잔잔한 여운이 오래동안 남았던 작품",
    "x": 100, "y": 1130, "width": 880, "height": 340,
    "bg_color": "#FFFFFF", "text_color": "#444444", "border_color": null, "font_size": 28
  },
  "info": {
    "title": "새 감상 기록", "rating": "9.5 / 10",
    "tags": ["힐링", "여운", "판타지"],
    "text_color": "#333333", "accent_color": "#7C3AED", "tag_color": "#888888"
  },
  "mood": "warm"
}
```

### 기본 템플릿 5종 (data migration으로 자동 삽입)
| 카테고리 | 이름 | 적합한 분위기 |
|---------|------|-------------|
| minimal | 미니멀 화이트 | 깔끔, 정갈 |
| emotional | 감성 파스텔 | 힐링, 여운, 감동 |
| retro | 레트로 필름 | 명작, 클래식, 추억 |
| cute | 큐트 버블 | 일상, 코미디, 로맨스 |
| dark | 다크 시네마 | 액션, 스릴러, 다크판타지 |

### 배경 스타일 결정 (향후 확장)
태그 기반으로 AI가 배경 무드를 결정:
- 힐링/감성 → 베이지·파스텔
- 액션/다크 → 어두운 톤
- 판타지/몽환 → 보라·파랑
- 일상/코미디 → 밝은 노란·분홍

## 4. App.vue 주요 기능 (Vite dev server)

### 인증
- SPA 내 로그인/회원가입 (localhost:8000 리다이렉트 없음)
- `checkAuth()` → `/api/auth/me/` (실패 시 currentUser = null, 리다이렉트 안 함)
- `logout()` → csrfToken 비우고 API 호출, 항상 로컬 상태 초기화
- `apiFetch()` — CSRF 403 자동 재시도 (토큰 갱신 후 1회 재시도)

### 기록 관리
- `loadSavedCards()` → `/api/records/?mine=1` (본인 레코드만)
- `deleteSavedCard()` — 404 시 프론트에서 제거 (DB에 없는 경우)
- `saveCard()` — POST(신규) / PATCH(수정), canvas_data에 placedItems 포함

### 새로고침/데이터 보호
- `beforeunload` — **기록 작성 중 + _dirty일 때만** 경고 표시
- `_dirty` 플래그: watch(placedItems/mainImageSrc/currentRecord) → true, 저장 성공 → false
- `_autosaveDraft()` — localStorage에 임시저장 (기록 작성 페이지일 때만)
- `_checkAutosaveRestore()` — 복원 시 _dirty = true 설정 (연속 새로고침 대응)
- `activePage` — localStorage에 저장/복원 (새로고침 시 이전 페이지 유지)
- `openSavedCard()` — 레코드 열기 후 $nextTick에서 _dirty = false

### 공유 카드
- `downloadShareImage()` — fetch → blob → createObjectURL → a.click 다운로드
- 공유 모달에서 "이미지 저장" 버튼 → 파일 다운로드 (브라우저에서 열리지 않음)

## 5. 해결된 이슈들

| 이슈 | 원인 | 해결 |
|------|------|------|
| 한글 □□□ 렌더링 | NotoSansCJK TTC index 미지정 | index=1 (KR) 설정 |
| 스티커 미저장 | placedItems가 localStorage에만 존재 | canvas_data JSONField로 백엔드 저장 |
| 로그인 리다이렉트 | checkAuth/logout이 window.location.href 사용 | SPA 내 상태 관리로 전환 |
| CSRF 403 (로그아웃) | stale CSRF 토큰 | csrfToken 비우고 재시도 로직 |
| CSRF 403 (삭제) | response.text() 이중 읽기 | body 한 번만 읽고 재시도 판단 |
| 타인 레코드 삭제 403 | /api/records/가 public 레코드도 반환 | ?mine=1 필터 추가 |
| 내 앨범에서 새로고침 경고 | beforeunload이 항상 발동 | activePage === '기록 작성' && _dirty 조건 |
| 저장 후 새로고침 복원 | _dirty가 리셋 안 됨 | 저장 성공 시 _dirty = false |
| 복원 후 연속 새로고침 | 복원 시 _dirty 미설정 | 복원 후 $nextTick에서 _dirty = true |
| DB 손상 | SQLite malformed | DB 초기화 (del db.sqlite3 + migrate) |

## 6. 미완료/향후 작업

- [ ] **통합 테스트**: 공유 카드 생성 API → AI 응답 → 4존 렌더링 전체 흐름 실제 테스트
- [ ] **frontend/static/js/app.js 동기화**: Django-served 빌드가 App.vue와 동기화 안 됨
- [ ] **스티커 에셋 등록**: StickerAsset에 실제 스티커 이미지 업로드 (Django admin)
- [ ] **배경 스타일 확장**: 태그 기반 배경 무드 API 파라미터화
- [ ] **폰트 교체 대비**: renderer.py에 주석으로 교체 지점 표시됨 (_FONT_MAP, memo 영역)
- [ ] **Git push**: 변경사항 커밋 + 푸시

## 7. 환경 설정

```bash
# 백엔드
cd backend
pip install -r requirements.txt
python setup_fonts.py           # NotoSansKR 폰트 자동 다운로드
# .env 파일에 GMS_API_KEY 설정 필요
python manage.py migrate        # CardTemplate 5개 자동 생성됨
python manage.py createsuperuser

# 프론트엔드
cd frontend
npm install
npm run dev                     # localhost:5173
```

### Vite 프록시 (vite.config.js)
```js
server: {
  proxy: {
    "/api": "http://127.0.0.1:8000",
    "/media": "http://127.0.0.1:8000",
  }
}
```

## 8. feature/autocomplete-and-ui-improvements 브랜치 (별도 작업)

이 브랜치에서 추가된 기능들 (anilist-api 브랜치로 작업):

### 8-1. 작품 자동완성 (AniList API 연동)
- 로컬 DB + AniList API 하이브리드 검색 (한글→DB, 영어→AniList)
- 300ms debounce, 키보드 방향키/Enter 탐색
- 작품 선택 시 한글 제목 없으면 사용자 직접 입력 → DB 저장
- **파일**: `backend/works/views.py` (autocomplete, select_work), `backend/works/services/anilist.py`, `frontend/src/components/modal/RecordModal.vue`
- **API**: `GET /api/works/autocomplete/?q=검색어`, `POST /api/works/select/`

### 8-2. 공개 범위(Visibility) 선택 UI
- 기록 저장 툴바에 `나만 보기` / `전체 공개` 토글
- `recordVisibility` 상태, 저장 시 `visibility` 필드 전송
- 저장된 카드 열 때 기존 visibility 복원

### 8-3. 이미지 원본 비율 표시 + 크기 조절
- `object-fit: contain`, `height: auto`로 잘림 방지
- 리사이즈를 scale 기반 → width 기반(60~500px)으로 변경

### 8-4. 홈 피드 (Public 게시글)
- `loadFeedRecords()` → `GET /api/records/` (public 기록 조회)
- 피드 카드 UI: 포스터, 제목, 별점, 좋아요, 댓글 수

### 이 브랜치의 남은 TODO
- **홈 피드 재설계**: Record 표시 → ShareCard 기반 Pinterest 레이아웃으로 변경
- **공개 모드 조건**: ShareCard 생성 후에만 public 전환 가능하도록 제한
- **한글 시드 데이터**: 인기 애니 한글↔영문 매핑 초기 데이터

## 9. 보안 참고
- GMS API 키는 .env에만 존재하며 코드에 하드코딩하지 않음
- CSRF 토큰은 `/api/auth/csrf/`에서 발급, 쿠키 기반
- SessionAuthentication 사용, credentials: 'include' 필수
