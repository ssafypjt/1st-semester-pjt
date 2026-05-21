import json
from datetime import date

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


RECORDS = [
    {
        "date": "2024.05.12",
        "title": "스즈메의 문단속",
        "memo": "매번 상상만 했던 곳을 떠나는 용기를 얻게 된 것 같은 기분이었다.",
        "rating": 9.5,
        "tags": ["여행", "성장", "감동", "OST"],
        "count": 24,
        "cover": "linear-gradient(160deg, #7256b7, #f2a7c7)",
    },
    {
        "date": "2024.05.10",
        "title": "2024 봄 분기",
        "memo": "이번 분기는 청량하고 귀여운 장면이 많아서 계속 저장하게 된다.",
        "rating": 8.5,
        "tags": ["청량", "일상", "최애"],
        "count": 12,
        "cover": "linear-gradient(160deg, #2188c9, #e4f8ff)",
    },
    {
        "date": "2024.05.08",
        "title": "지브리 컬렉션",
        "memo": "숲과 바람, 오래된 집 냄새가 같이 떠오르는 앨범.",
        "rating": 9,
        "tags": ["지브리", "몽환", "힐링"],
        "count": 8,
        "cover": "linear-gradient(160deg, #5ab8ad, #39578f)",
    },
    {
        "date": "2024.05.06",
        "title": "눈물샘 폭발",
        "memo": "알고 봐도 또 울게 되는 장면들만 모았다.",
        "rating": 7.5,
        "tags": ["피폐", "눈물", "명대사"],
        "count": 7,
        "cover": "linear-gradient(160deg, #48536f, #a9d4de)",
    },
]

MOOD_TAGS = {
    "여운": ["여운", "관계성서사", "명대사", "감정선"],
    "청량": ["청량", "여름", "청춘", "OST"],
    "새벽감성": ["새벽감성", "고요", "독백", "몽글"],
    "몽환": ["몽환", "판타지", "빛", "꿈결"],
    "피폐": ["피폐", "서사", "눈물", "몰입"],
}


def render_app(request, page="home", object_id=None):
    return render(request, "index.html", {
        "initial_route": {
            "page": page,
            "objectId": object_id,
        },
    })


def home(request):
    return render_app(request, "home")


def login_page(request):
    return render_app(request, "login")


def signup_page(request):
    return render_app(request, "signup")


def diary_list_page(request):
    return render_app(request, "diary-list")


def diary_detail_page(request, diary_id):
    return render_app(request, "diary-detail", diary_id)


def review_list_page(request):
    return render_app(request, "review-list")


def review_detail_page(request, review_id):
    return render_app(request, "review-detail", review_id)


def mypage(request):
    return render_app(request, "mypage")


def share_page(request, diary_id):
    return render_app(request, "share", diary_id)


def parse_json_body(request):
    if not request.body:
        return {}
    return json.loads(request.body.decode("utf-8"))


def analyze_text(title, memo, mood):
    tags = MOOD_TAGS.get(mood, MOOD_TAGS["여운"])
    title_text = title or "이 작품"
    return {
        "summary": (
            f"{mood} 분위기가 강하게 남는 감상이에요. "
            "문장 속에서 장면의 잔상과 캐릭터를 오래 붙잡고 싶은 취향이 보여요."
        ),
        "phrase": f"{title_text}은 오래 펼쳐보고 싶은 한 장면 같아요.",
        "tags": tags,
        "preference": "감정선과 관계성 서사를 오래 곱씹는 아카이빙 취향",
    }


def records_api(request):
    return JsonResponse({"records": RECORDS})


@csrf_exempt
def analyze_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    payload = parse_json_body(request)
    analysis = analyze_text(
        payload.get("title", ""),
        payload.get("memo", ""),
        payload.get("mood", "여운"),
    )
    return JsonResponse({"analysis": analysis})


@csrf_exempt
def create_record_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    payload = parse_json_body(request)
    raw_tags = payload.get("tags", "")
    tags = [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
    analysis = analyze_text(
        payload.get("title", ""),
        payload.get("memo", ""),
        payload.get("mood", "여운"),
    )
    record = {
        "date": date.today().strftime("%Y.%m.%d"),
        "title": payload.get("title") or "새 감상 기록",
        "memo": payload.get("memo") or "좋아하는 장면을 기록했어요.",
        "rating": 9,
        "tags": tags or analysis["tags"][:4],
        "count": 1,
        "cover": "linear-gradient(160deg, #b99be0, #ffd1e4)",
    }
    RECORDS.insert(0, record)
    return JsonResponse({"record": record, "analysis": analysis}, status=201)
