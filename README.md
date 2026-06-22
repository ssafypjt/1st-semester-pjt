# 덕꾸 (Deokkku)

> **애니메이션 시청 기록 아카이빙 서비스**  
> 좋아하는 작품의 감상을 다이어리처럼 꾸미고, 앨범으로 모으고, 팔로우한 사람들과 공유하는 웹 플랫폼

<br>

## 📌 서비스 소개

덕꾸는 **덕질(덕후 활동) + 꾸미기(다꾸, Diary Decorating)** 를 합친 이름입니다.  
애니메이션을 보고 난 뒤의 감상을 텍스트로만 남기는 게 아니라, 스티커·메모·이미지를 자유롭게 배치해 나만의 감상 카드로 꾸밀 수 있습니다.

- 작품별 감상 기록 + 평점 + 다이어리 스타일 캔버스 꾸미기
- 꾸민 카드를 이미지로 저장해 SNS 공유
- 기록을 앨범으로 묶어 아카이빙
- 팔로우한 사람의 공개 기록·앨범 열람

<br>

## 🛠 기술 스택

| 구분 | 기술 |
|------|------|
| **Backend** | Python 3.11, Django 5, Django REST Framework |
| **Frontend** | Vue 3, Vite, JavaScript |
| **인증** | 세션 기반 (HttpOnly 쿠키 + CSRF 토큰) |
| **DB** | SQLite (개발) / PostgreSQL 전환 가능 |
| **배포** | Whitenoise (정적 파일), django-environ (환경변수) |
| **기타** | django-cleanup (파일 자동 삭제), django-cors-headers |

<br>

## 📂 프로젝트 구조

```
1st-semester-pjt/
├── backend/
│   ├── accounts/     # 유저·소셜계정·팔로우
│   ├── works/        # 작품 마스터 데이터 (anime/movie/book/game/drama)
│   ├── records/      # 감상 기록 + 다꾸 이미지 업로드
│   ├── albums/       # 기록 앨범 (M:N)
│   └── config/       # Django 설정, URL
└── frontend/
    └── src/
        └── App.vue   # 메인 SPA
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
| `works/` | GET | 작품 목록 |
| `works/<id>/` | GET | 작품 상세 |
| `works/` | POST | 작품 등록 (관리자 전용) |

### 감상 기록 (`/api/records/`)

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `records/` | GET / POST | 기록 목록 / 신규 작성 |
| `records/<id>/` | GET / PATCH / DELETE | 상세 / 수정 / 삭제 |
| `records/upload/` | POST | 다꾸 이미지 업로드 |
| `records/uploads/<pk>/` | GET | 보호된 이미지 응답 |

### 앨범 (`/api/albums/`)

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `albums/` | GET / POST | 앨범 목록 / 생성 |
| `albums/<id>/` | GET / PATCH / DELETE | 상세 / 수정 / 삭제 |
| `albums/<id>/add-record/` | POST | 앨범에 기록 추가 |
| `albums/<id>/remove-record/<record_id>/` | DELETE | 앨범에서 기록 제거 |

<br>

## 🗄 데이터 모델

```
User
 ├── SocialAccount (1:N) — 소셜 로그인 연동 (Google/Kakao/Apple)
 ├── Follow (M:N self) — 팔로우/팔로잉
 ├── Record (1:N) — 감상 기록
 │    └── RecordImage (1:N) — 다꾸 캔버스 이미지
 └── Album (1:N)
      └── AlbumRecord (M:N through) — 앨범-기록 연결

Work — 작품 마스터 (anime/movie/book/game/drama/other)
 └── Record (1:N)
```

<br>

## 🔐 보안 설계

- **세션 인증**: Django 세션 + HttpOnly 쿠키. JWT 미사용으로 토큰 탈취 위험 제거
- **CSRF 정책**: 로그인·회원가입만 exempt, 이후 모든 쓰기 요청은 CSRF 검증
- **파일 접근 제어**: 업로드 이미지는 `/media/` 직접 노출 차단. Protected view를 통해서만 응답 (업로더 본인 또는 public 기록 한정)
- **권한 분리**: 작품 마스터 데이터 쓰기는 `is_staff=True`만 허용. 읽기는 누구나

<br>

## 🎨 프론트엔드 주요 기능

- 다이어리 형태 2페이지 레이아웃 (좌: 작품 정보, 우: 꾸미기 영역)
- 스티커·텍스트 메모 드래그 배치, 크기 조절, 회전
- 실행 취소(Undo) 히스토리
- 감상 카드 PNG 다운로드 (공유 카드)
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
python manage.py seed            # 데모 데이터 생성
python manage.py runserver
```

데모 계정: `demo@deokkku.local` / `demo1234`

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
```

<br>

## 📈 진행 현황

| 기능 | 상태 |
|------|------|
| 회원가입 / 로그인 / 로그아웃 | ✅ 완료 |
| 프로필 수정 / 비밀번호 변경 | ✅ 완료 |
| 팔로우 / 팔로잉 | ✅ 완료 |
| 작품 등록 / 조회 | ✅ 완료 |
| 감상 기록 CRUD | ✅ 완료 |
| 다꾸 이미지 업로드 | ✅ 완료 |
| 앨범 CRUD + 기록 추가/제거 | ✅ 완료 |
| 공유 카드 PNG 다운로드 | ✅ 완료 |
| 좋아요 / 댓글 | 🔄 개발 중 |
| 외부 API 연동 (AniList/TMDB) | 📋 예정 |
| 프론트엔드 컴포넌트 분리 | 📋 예정 |
| 소셜 로그인 | 📋 예정 |

<br>

## 👥 팀

SSAFY 1학기 관통 프로젝트

| 역할 | 담당 |
|------|------|
| **Backend** | 이선형 — Django API 설계 및 구현, 인증·보안, DB 모델링 |
| **Frontend** | 김태은 — Vue 3 UI 구성, 다이어리 인터랙션, API 연동 |
