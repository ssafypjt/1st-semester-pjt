# 덕꾸 Frontend

Vue 3 + Vite 기반 프론트엔드입니다.

---

## 환경 설정

### 1. 패키지 설치

```bash
npm install
```

### 2. 개발 서버 실행

```bash
npm run dev
```

기본 주소: `http://127.0.0.1:5173`

Vite 프록시가 `/api`, `/media` 요청을 백엔드(`http://127.0.0.1:8000`)로 전달합니다.
백엔드 서버가 먼저 실행 중이어야 합니다.

### 3. 빌드

```bash
npm run build
```

빌드 결과물은 `dist/`에 생성됩니다.
