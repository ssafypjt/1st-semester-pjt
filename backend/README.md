# 덕꾸 Backend

Django 4.x + DRF 기반 백엔드 서버입니다.

---

## 환경 설정

### 1. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/Scripts/activate   # Windows
source venv/bin/activate       # Mac/Linux
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 (.env)

`backend/.env` 파일을 생성합니다:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True

# AI 공유 카드 생성용 GMS API
GMS_API_URL=https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions
GMS_API_KEY=your-gms-api-key
GMS_MODEL=gpt-4.1-mini
```

### 4. 폰트 다운로드

AI 공유 카드 이미지 렌더링에 NotoSansKR 폰트가 필요합니다.

```bash
python setup_fonts.py
```

Google Fonts에서 자동 다운로드되어 `shares/fonts/`에 저장됩니다.
폰트 파일은 `.gitignore`에 포함되어 git에 올라가지 않습니다.

### 5. DB 마이그레이션

```bash
python manage.py migrate
```

마이그레이션 시 AI 공유 카드 템플릿 5종이 자동 생성됩니다.

### 6. 관리자 계정 생성

```bash
python manage.py createsuperuser
```

### 7. 서버 실행

```bash
python manage.py runserver
```

기본 주소: `http://127.0.0.1:8000`
