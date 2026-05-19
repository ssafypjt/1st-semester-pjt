# 🎀 1st-semester-pjt

애니메이션 시청 기록을 다이어리처럼 자유롭게 아카이빙하고 꾸밀 수 있는 웹 서비스입니다.  
사용자는 자신이 감상한 작품을 기록하고, 스티커·텍스트·이미지 등을 활용해 다꾸(Diary Decorating) 스타일로 콘텐츠를 꾸밀 수 있습니다.

---

## 📌 Project Status

> 현재 프론트 UI 작업 진행 중입니다.  
> 백엔드 기능은 팀원과 분리하여 개발 중이며, 아직 API 연동은 완료되지 않은 상태입니다.

현재 Repository에서는:
- 메인 UI 레이아웃 구성
- 다이어리 스타일 디자인 작업
- 스티커/오브젝트 인터랙션 구현
- 프론트엔드 구조 개선

등을 우선적으로 진행하고 있습니다.

---

## 🛠 Tech Stack

### Frontend
- HTML
- CSS
- JavaScript

### Backend
- Python
- Django 5

> 추후 Vue 기반 프론트엔드 구조로 확장 예정

---

## 📂 Project Structure

```bash
1st-semester-pjt/
│
├── anime_archive/
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   ├── templates/
│   ├── views.py
│   └── urls.py
│
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🎨 Main UI Features

### 📖 Diary-style Layout
- 다이어리 형태의 UI 구성
- 감상 기록 중심 레이아웃

### 🖼 Object Decoration
- 스티커 및 오브젝트 배치
- 자유로운 UI 구성 요소 배치

### ✍️ Memo Area
- 작품별 감상 메모 기록 영역

### 🎬 Archive Concept
- 애니메이션 감상 기록 아카이빙
- 디지털 스크랩북 컨셉

---

## ⚙️ Installation

### 1. Clone Repository

```bash
git clone https://github.com/ssafypjt/1st-semester-pjt.git
cd 1st-semester-pjt
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

#### Windows

```bash
source venv/Scripts/activate
```

#### Mac/Linux

```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run Server

```bash
python manage.py runserver
```

---

## 🚧 Current Progress

- [x] Django 프로젝트 초기 세팅
- [x] 메인 페이지 UI 구현
- [x] 정적 리소스 구조 구성
- [x] 다이어리 스타일 레이아웃 작업
- [ ] Vue 기반 프론트엔드 구조 전환
- [ ] Drag & Drop 기능 개선
- [ ] 백엔드 API 연동
- [ ] 사용자 인증 기능

---

## 🌱 Future Improvements

- Vue 기반 컴포넌트 구조 도입
- Drag & Drop 인터랙션 개선
- 애니메이션 API 연동
- 사용자별 다이어리 저장 기능
- 공유 기능 및 커뮤니티 기능
- AI 기반 꾸미기 추천 기능

---

## 👥 Team

SSAFY 관통 프로젝트 팀

---

## 📄 License

This project is created for educational purposes.
