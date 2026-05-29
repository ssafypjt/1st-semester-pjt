
# 🎀 1st-semester-pjt

애니메이션 시청 기록을 다이어리처럼 자유롭게 아카이빙하고 꾸밀 수 있는 웹 서비스입니다.  
사용자는 자신이 감상한 작품을 기록하고, 스티커·텍스트·이미지 등을 활용해 다꾸(Diary Decorating) 스타일로 콘텐츠를 꾸밀 수 있습니다.

---

## 📌 Project Status

> 현재 Vue 3 + Vite 기반 프론트엔드 구조로 전환 완료 후 UI 및 기능 안정화 작업 진행 중입니다.  
> 백엔드 기능은 팀원과 역할을 분리하여 Django 기반으로 개발 중이며, 일부 API 연동은 진행 단계에 있습니다.

현재 Repository에서는:
- Vue 3 기반 메인 UI 구성
- 다이어리 스타일 디자인 작업
- 스티커/오브젝트 인터랙션 구현
- Django + Vue 분리 구조 구성
- Vite build 기반 프론트엔드 구조 전환

등을 우선적으로 진행하고 있습니다.

---

## 🛠 Tech Stack

### Frontend
- Vue 3
- Vite
- JavaScript
- CSS

### Backend
- Python
- Django 5
- Django REST Framework

---

## 📂 Project Structure

```bash
1st-semester-pjt/
│
├── backend/
│   ├── config/
│   ├── accounts/
│   ├── animes/
│   ├── albums/
│   ├── records/
│   └── templates/
│
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── App.vue
│   │   └── main.js
│   ├── static/
│   ├── templates/
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
├── manage.py
├── requirements.txt
└── README.md
````

---

## 🎨 Main UI Features

### 📖 Diary-style Layout

* 다이어리 형태의 UI 구성
* 감상 기록 중심 레이아웃

### 🖼 Object Decoration

* 스티커 및 오브젝트 배치
* 드래그 기반 위치 이동
* 크기 조절 / 회전 기능

### ✍️ Memo Area

* 작품별 감상 메모 기록 영역
* 자유로운 메모 배치

### 🎬 Archive Concept

* 애니메이션 감상 기록 아카이빙
* 디지털 스크랩북 컨셉

---

## ⚙️ Installation

### 1. Clone Repository

```bash
git clone https://github.com/ssafypjt/1st-semester-pjt.git
cd 1st-semester-pjt
```

---

## 🐍 Backend Server Run

### 1. Create Virtual Environment

```bash
python -m venv venv
```

### 2. Activate Virtual Environment

#### Windows

```bash
source venv/Scripts/activate
```

#### Mac/Linux

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Django Server

```bash
python manage.py runserver
```

기본 주소:

```text
http://127.0.0.1:8000
```

---

## ⚡ Frontend Development Server Run

### 1. Move to Frontend Directory

```bash
cd frontend
```

### 2. Install Frontend Packages

```bash
npm install
```

### 3. Run Vite Development Server

```bash
npm run dev
```

기본 주소:

```text
http://127.0.0.1:5173
```

---

## 🏗 Build

```bash
cd frontend
npm run build
```

빌드 완료 후 생성된 `frontend/dist`를 Django가 서빙하는 구조입니다.

---

## 🚧 Current Progress

* [x] Django 프로젝트 초기 세팅
* [x] Vue 3 + Vite 프론트엔드 구조 전환
* [x] 메인 페이지 UI 구현
* [x] 다이어리 스타일 레이아웃 작업
* [x] 로그인 / 로그아웃 연동
* [x] Django + Vue build 연동
* [x] 정적 리소스 구조 구성
* [ ] Drag & Drop 기능 개선
* [ ] 백엔드 API 연동 안정화
* [ ] 사용자 데이터 저장 기능 개선
* [ ] 컴포넌트 구조 분리

---

## 🌱 Future Improvements

* Vue 컴포넌트 구조 세분화
* Drag & Drop 인터랙션 개선
* 애니메이션 API 연동
* 사용자별 다이어리 저장 기능
* 공유 기능 및 커뮤니티 기능
* AI 기반 꾸미기 추천 기능

---

## 👥 Team

SSAFY 관통 프로젝트 팀

### 역할 분담

#### Backend

* Django API
* 인증 및 DB 관리
* 데이터 처리 및 저장

#### Frontend

* Vue UI 구성
* 다이어리 인터랙션
* 화면 상태 관리
* API 연동 및 프론트 구조 설계

---

## 📄 License

This project is created for educational purposes.

