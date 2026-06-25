# 덕꾸 (Deokkku)

> **애니메이션 감상 다이어리 꾸미기 + 소셜 공유 플랫폼**  
> 좋아하는 작품의 감상을 다이어리처럼 꾸미고, AI로 공유 카드를 생성하고, 팔로우한 사람들과 소통하는 웹 서비스

<br>

## 📌 서비스 소개

덕꾸는 **덕질(덕후 활동) + 꾸미기(다꾸, Diary Decorating)** 를 합친 이름입니다.  
애니메이션을 보고 난 뒤의 감상을 텍스트로만 남기는 게 아니라, 스티커·메모·말풍선·이미지를 자유롭게 배치해 나만의 감상 다이어리로 꾸밀 수 있습니다.

- 작품별 감상 기록 + 평점 + 다이어리 스타일 캔버스 꾸미기
- AI(GPT)가 기록을 분석해 공유용 카드 이미지 자동 생성
- AniList API 연동으로 작품 검색 및 태그·포스터 자동 연결
- 홈 피드에서 다른 유저의 기록 탐색, 좋아요·댓글로 소통
- 카드함에서 AI 생성 공유 카드 관리 및 다운로드

<br>

## 🛠 기술 스택

| 구분 | 기술 |
|------|------|
| **Backend** | Python 3.11, Django 5, Django REST Framework |
| **Frontend** | Vue 3 (Options API), Vite, JavaScript |
| **AI** | GMS API Gateway → OpenAI gpt-5-mini (2단계 파이프라인) |
| **외부 API** | AniList GraphQL API (작품 검색·태그·포스터) |
| **인증** | 세션 기반 (HttpOnly 쿠키 + CSRF 토큰) |
| **DB** | SQLite (개발) / PostgreSQL 전환 가능 |
| **배포** | Whitenoise (정적 파일), django-environ (환경변수) |
| **기타** | django-cleanup (파일 자동 삭제), django-cors-headers |

<br>

## 📂 프로젝트 구조

```
1st-semester-pjt/
├── backend/
│   ├── accounts/      # 유저·소셜계정·팔로우
│   ├── works/         # 작품 마스터 데이터 + AniList 연동
│   ├── records/       # 감상 기록·다꾸 캔버스·좋아요·댓글·스티커
│   ├── albums/        # 기록 앨범 (M:N)
│   ├── shares/        # AI 공유 카드 생성·관리 (GPT 파이프라인)
│   └── config/        # Django 설정, URL, SPA 라우팅
└── frontend/
    └── src/
        ├── App.vue                  # 메인 SPA (다이어리 에디터·피드·프리뷰)
        ├── components/
        │   ├── layout/              # Sidebar, Topbar
        │   ├── album/               # SavedAlbumGrid
        │   ├── modal/               # RecordModal, BadgeModal, SaveToast
        │   ├── profile/             # MyPageDashboard, ProfileDropdown, BadgeList
        │   └── record/              # ImageUploadPanel, StickerPanel
        ├── constants/               # navigation, stickers, defaultAnalysis
        └── assets/
            ├── app.css              # 전체 스타일
            └── images/              # 다이어리 프레임·로고·아이콘
```

<br>

## ⚙️ 주요 기능 및 API

### 인증 (`/api/auth/`)

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `csrf/` | GET | CSRF 토큰 발급 |
| `signup/` | POST | 회원가입 (프로필 이미지 선택 업로드) |
| `login/` | POST | 로그인 |
| `logout/` | POST | 로그아웃 |
| `me/` | GET | 내 정보 조회 |
| `me/update/` | PATCH | 닉네임·프로필 이미지 수정 |
| `password/change/` | POST | 비밀번호 변경 |
| `users/<pk>/` | GET | 타인 프로필 조회 |
| `users/<pk>/follow/` | POST | 팔로우/언팔로우 토글 |
| `users/<pk>/followers/` | GET | 팔로워 목록 |
| `users/<pk>/following/` | GET | 팔로잉 목록 |

### 작품 (`/api/works/`)

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| ` ` | GET | 작품 목록 (검색·필터 지원) |
| `<id>/` | GET | 작품 상세 |
| ` ` | POST | 작품 등록 (관리자 전용) |

### 감상 기록 (`/api/records/`)

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| ` ` | GET | 기록 목록 (`?mine=1` 내 기록, `?q=` 검색) |
| ` ` | POST | 신규 기록 작성 |
| `<id>/` | GET / PATCH / DELETE | 상세 / 수정 / 삭제 |
| `<id>/like/` | POST | 좋아요 토글 |
| `<id>/comments/` | GET / POST | 댓글 목록 / 작성 |
| `<id>/comments/<cid>/` | DELETE | 본인 댓글 삭제 |
| `upload/` | POST | 다꾸 이미지 업로드 |
| `uploads/<pk>/` | GET | 보호된 이미지 응답 (업로더 본인만) |
| `stickers/` | GET | 내 스티커 목록 |
| `stickers/all/` | GET | 전체 스티커 카탈로그 |
| `stickers/init/` | POST | 기본 스티커 부여 |
| `stickers/upload/` | POST | 커스텀 스티커 업로드 |

### 앨범 (`/api/albums/`)

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| ` ` | GET / POST | 앨범 목록 / 생성 |
| `<id>/` | GET / PATCH / DELETE | 상세 / 수정 / 삭제 |
| `<id>/add-record/` | POST | 앨범에 기록 추가 |
| `<id>/remove-record/<rid>/` | DELETE | 앨범에서 기록 제거 |

### AI 공유 카드 (`/api/shares/`)

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `templates/` | GET | 카드 템플릿 목록 |
| `<record_id>/` | GET | 특정 기록의 공유 카드 목록 |
| `<record_id>/generate/` | POST | AI 공유 카드 생성 (GPT 2단계 파이프라인) |
| `my/` | GET | 내 전체 공유 카드 (카드함) |
| `card/<id>/` | GET | 공유 카드 단건 조회 |
| `card/<id>/delete/` | DELETE | 공유 카드 삭제 |

<br>

## 🗄 데이터 모델

```
User (커스텀 유저: email 인증)
 ├── SocialAccount (1:N) — 소셜 로그인 연동 (Google/Kakao/Apple)
 ├── Follow (M:N self) — 팔로우/팔로잉
 ├── Record (1:N) — 감상 기록
 │    ├── RecordImage (1:N) — 다꾸 캔버스 이미지
 │    ├── Decoration (1:N) — 스티커 배치 데이터
 │    ├── FavoriteScene (1:N) — 명장면 이미지
 │    ├── Like (1:N) — 좋아요 (user+record 유니크)
 │    ├── Comment (1:N) — 댓글
 │    └── ShareCard (1:N) — AI 생성 공유 카드
 ├── UserSticker (1:N) — 보유 스티커
 └── Album (1:N)
      └── AlbumRecord (M:N through) — 앨범-기록 연결

Work — 작품 마스터 (anime/movie/book/game/drama/other)
 ├── Record (1:N)
 └── anilist_tags (JSONField) — AniList 태그 캐시

StickerAsset — 스티커 원본 (기본/커스텀)
CardTemplate — AI 공유 카드 레이아웃 템플릿
```

<br>

## 🔐 보안 설계

- **세션 인증**: Django 세션 + HttpOnly 쿠키. JWT 미사용으로 토큰 탈취 위험 제거
- **CSRF 정책**: 로그인·회원가입만 exempt, 이후 모든 쓰기 요청은 CSRF 검증
- **파일 접근 제어**: 업로드 이미지는 `/media/` 직접 노출 차단. Protected view를 통해서만 응답 (업로더 본인만 200, 타인은 404)
- **권한 분리**: 작품 마스터 데이터 쓰기는 `is_staff=True`만 허용. 읽기는 누구나
- **기록 공개 범위**: public(전체), friends(팔로워), private(본인만) 3단계 visibility
- **댓글 삭제 권한**: 본인 댓글만 삭제 가능 (403 반환)
- **소프트 삭제**: 탈퇴 유저 기록·댓글은 30일 보관 후 비공개 처리, 재로그인 시 자동 복구

<br>

## 🎨 프론트엔드 주요 기능

- 다이어리 형태 2페이지 레이아웃 (좌: 작품 정보, 우: 꾸미기 영역)
- 스티커·텍스트 메모·말풍선(일반/상상) 드래그 배치, 크기 조절, 회전
- 버블 툴바: 글꼴 크기, 배경색, 테두리색 커스터마이징 (메모·말풍선 공용)
- 반응형 캔버스 스케일 (ResizeObserver로 요소 비례 축소)
- 실행 취소(Undo) 히스토리
- AI 공유 카드 생성·다운로드·카드함 관리
- 홈 피드: 검색(제목·태그), 다이어리 프리뷰, 좋아요, 댓글
- AniList 작품 검색 + 태그·포스터 자동 연결
- 로그인/회원가입 세션 연동

<br>

## 🚀 로컬 실행 방법

### 백엔드

```bash
cd backend
python -m venv ../venv
source ../venv/Scripts/activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_anilist_top100  # AniList 인기 작품 시드 데이터
python manage.py runserver
```

### 프론트엔드

```bash
cd frontend
npm install
npm run dev
```

기본 주소: `http://localhost:5173`

### 환경변수 (`backend/.env`)

```
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173
MEDIA_MAX_UPLOAD_MB=8
GMS_API_KEY=your-gms-api-key
```

<br>

## 📈 진행 현황

| 기능 | 상태 |
|------|------|
| 회원가입 / 로그인 / 로그아웃 | ✅ 완료 |
| 프로필 수정 / 비밀번호 변경 | ✅ 완료 |
| 팔로우 / 팔로잉 | ✅ 완료 |
| 작품 등록 / 조회 / AniList 연동 | ✅ 완료 |
| AniList 인기 작품 시드 데이터 | ✅ 완료 |
| 감상 기록 CRUD | ✅ 완료 |
| 다꾸 캔버스 (스티커·메모·말풍선·이미지 배치) | ✅ 완료 |
| 반응형 캔버스 스케일 | ✅ 완료 |
| 버블 툴바 (메모·말풍선 공용) | ✅ 완료 |
| 다꾸 이미지 업로드 (보호된 미디어) | ✅ 완료 |
| 스티커 시스템 (기본·커스텀·카테고리) | ✅ 완료 |
| 앨범 CRUD + 기록 추가/제거 | ✅ 완료 |
| AI 공유 카드 생성 (GPT 2단계 파이프라인) | ✅ 완료 |
| 카드함 (공유 카드 갤러리·다운로드·삭제) | ✅ 완료 |
| 좋아요 토글 | ✅ 완료 |
| 댓글 작성 / 삭제 (본인만) | ✅ 완료 |
| 홈 피드 검색 (제목·태그 통합) | ✅ 완료 |
| 다이어리 프리뷰 + 댓글 패널 | ✅ 완료 |
| 소셜 로그인 | 📋 예정 |

<br>

## 👥 팀

SSAFY 1학기 관통 프로젝트

| 역할 | 담당 |
|------|------|
| **Backend** | 이선형 — Django API 설계 및 구현, 인증·보안, DB 모델링, AI 파이프라인 |
| **Frontend** | 김태은 — Vue 3 UI 구성, 다이어리 인터랙션, API 연동 |
