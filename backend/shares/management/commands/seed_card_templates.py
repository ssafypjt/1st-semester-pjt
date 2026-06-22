"""CardTemplate 초기 데이터 생성 커맨드."""
from django.core.management.base import BaseCommand
from shares.models import CardTemplate


TEMPLATES = [
    {
        'name': '미니멀 화이트',
        'category': 'minimal',
        'description_for_ai': '깔끔한 흰색 배경에 작품 포스터와 감상평을 정갈하게 배치하는 미니멀 디자인',
        'layout_schema': {
            'slots': [
                {'type': 'poster', 'x': 340, 'y': 200, 'w': 400, 'h': 560},
                {'type': 'title', 'x': 100, 'y': 840, 'w': 880, 'h': 80},
                {'type': 'rating', 'x': 100, 'y': 940, 'w': 880, 'h': 60},
                {'type': 'comment', 'x': 100, 'y': 1060, 'w': 880, 'h': 300},
                {'type': 'tags', 'x': 100, 'y': 1420, 'w': 880, 'h': 60},
            ],
        },
    },
    {
        'name': '감성 그라데이션',
        'category': 'emotional',
        'description_for_ai': '부드러운 파스텔 그라데이션 배경 위에 감상 문구를 중심으로 배치하는 감성적 디자인',
        'layout_schema': {
            'slots': [
                {'type': 'poster', 'x': 290, 'y': 160, 'w': 500, 'h': 700},
                {'type': 'title', 'x': 80, 'y': 920, 'w': 920, 'h': 80},
                {'type': 'rating', 'x': 80, 'y': 1020, 'w': 920, 'h': 60},
                {'type': 'comment', 'x': 80, 'y': 1140, 'w': 920, 'h': 320},
                {'type': 'tags', 'x': 80, 'y': 1520, 'w': 920, 'h': 60},
            ],
        },
    },
    {
        'name': '레트로 필름',
        'category': 'retro',
        'description_for_ai': '빈티지 필름 느낌의 어두운 톤에 노이즈 텍스처가 있는 레트로 디자인',
        'layout_schema': {
            'slots': [
                {'type': 'poster', 'x': 190, 'y': 200, 'w': 700, 'h': 500},
                {'type': 'title', 'x': 100, 'y': 780, 'w': 880, 'h': 80},
                {'type': 'rating', 'x': 100, 'y': 880, 'w': 880, 'h': 60},
                {'type': 'comment', 'x': 100, 'y': 1000, 'w': 880, 'h': 340},
                {'type': 'tags', 'x': 100, 'y': 1400, 'w': 880, 'h': 60},
            ],
        },
    },
    {
        'name': '큐트 버블',
        'category': 'cute',
        'description_for_ai': '밝고 귀여운 색상에 둥근 프레임과 말풍선 스타일의 큐트 디자인',
        'layout_schema': {
            'slots': [
                {'type': 'poster', 'x': 290, 'y': 180, 'w': 500, 'h': 700},
                {'type': 'title', 'x': 90, 'y': 940, 'w': 900, 'h': 80},
                {'type': 'rating', 'x': 90, 'y': 1040, 'w': 900, 'h': 60},
                {'type': 'comment', 'x': 90, 'y': 1160, 'w': 900, 'h': 300},
                {'type': 'tags', 'x': 90, 'y': 1520, 'w': 900, 'h': 60},
            ],
        },
    },
    {
        'name': '다크 시네마',
        'category': 'dark',
        'description_for_ai': '어두운 배경에 네온 포인트 색상으로 영화관 분위기를 내는 다크 디자인',
        'layout_schema': {
            'slots': [
                {'type': 'poster', 'x': 240, 'y': 160, 'w': 600, 'h': 840},
                {'type': 'title', 'x': 80, 'y': 1060, 'w': 920, 'h': 80},
                {'type': 'rating', 'x': 80, 'y': 1160, 'w': 920, 'h': 60},
                {'type': 'comment', 'x': 80, 'y': 1280, 'w': 920, 'h': 280},
                {'type': 'tags', 'x': 80, 'y': 1620, 'w': 920, 'h': 60},
            ],
        },
    },
]


class Command(BaseCommand):
    help = 'CardTemplate 초기 데이터를 생성합니다.'

    def handle(self, *args, **options):
        created = 0
        for t in TEMPLATES:
            _, is_new = CardTemplate.objects.get_or_create(
                name=t['name'],
                defaults={
                    'category': t['category'],
                    'description_for_ai': t['description_for_ai'],
                    'layout_schema': t['layout_schema'],
                    'is_active': True,
                },
            )
            if is_new:
                created += 1
                self.stdout.write(f'  + {t["name"]}')
            else:
                self.stdout.write(f'  = {t["name"]} (이미 존재)')

        self.stdout.write(self.style.SUCCESS(
            f'완료: {created}개 생성, {len(TEMPLATES) - created}개 기존'
        ))
