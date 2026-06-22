"""CardTemplate 기본 데이터 자동 삽입.

migrate 실행 시 5개 카테고리별 기본 템플릿이 생성된다.
"""
from django.db import migrations


TEMPLATES = [
    {
        'name': '미니멀 화이트',
        'category': 'minimal',
        'description_for_ai': '깔끔한 흰색 배경. 포스터를 깔끔하게 보여주고 정보를 정갈하게 배치하는 미니멀 디자인. 프레임: rounded 권장.',
        'layout_schema': {
            'canvas': {'w': 1080, 'h': 1920},
            'palette': ['#FFFFFF', '#F8F8F8', '#333333', '#7C3AED'],
            'zones': {
                'header': {'y': [0, 140]},
                'collage': {'y': [140, 1100], 'poster_area': [140, 180, 940, 850]},
                'memo': {'y': [1100, 1500]},
                'info': {'y': [1500, 1920]},
            },
        },
    },
    {
        'name': '감성 파스텔',
        'category': 'emotional',
        'description_for_ai': '부드러운 파스텔 베이지/핑크 배경. 폴라로이드 프레임으로 감성적인 분위기. 힐링·여운·감동 작품에 적합.',
        'layout_schema': {
            'canvas': {'w': 1080, 'h': 1920},
            'palette': ['#FDF5E6', '#FFE4E1', '#F5E6D0', '#8B7D6B', '#C9A96E'],
            'zones': {
                'header': {'y': [0, 140]},
                'collage': {'y': [140, 1100], 'poster_area': [190, 200, 890, 900]},
                'memo': {'y': [1100, 1500]},
                'info': {'y': [1500, 1920]},
            },
        },
    },
    {
        'name': '레트로 필름',
        'category': 'retro',
        'description_for_ai': '빈티지 필름 느낌. 따뜻한 세피아·갈색 톤 배경에 shadow 프레임. 명작·클래식·추억 작품에 적합.',
        'layout_schema': {
            'canvas': {'w': 1080, 'h': 1920},
            'palette': ['#F5E6D0', '#D4A574', '#8B6914', '#4A3728', '#FFFAF0'],
            'zones': {
                'header': {'y': [0, 140]},
                'collage': {'y': [140, 1100], 'poster_area': [165, 200, 915, 900]},
                'memo': {'y': [1100, 1500]},
                'info': {'y': [1500, 1920]},
            },
        },
    },
    {
        'name': '큐트 버블',
        'category': 'cute',
        'description_for_ai': '밝고 귀여운 분홍·라벤더 배경. polaroid 프레임에 동글동글한 느낌. 일상·코미디·로맨스 작품에 적합.',
        'layout_schema': {
            'canvas': {'w': 1080, 'h': 1920},
            'palette': ['#FFF0F5', '#E8D5F5', '#FFB6C1', '#9B59B6', '#FF69B4'],
            'zones': {
                'header': {'y': [0, 140]},
                'collage': {'y': [140, 1100], 'poster_area': [190, 180, 890, 920]},
                'memo': {'y': [1100, 1500]},
                'info': {'y': [1500, 1920]},
            },
        },
    },
    {
        'name': '다크 시네마',
        'category': 'dark',
        'description_for_ai': '어두운 배경에 네온 포인트. shadow 프레임으로 극장 느낌. 액션·스릴러·다크판타지 작품에 적합.',
        'layout_schema': {
            'canvas': {'w': 1080, 'h': 1920},
            'palette': ['#1A1A2E', '#16213E', '#0F3460', '#E94560', '#EAEAEA'],
            'zones': {
                'header': {'y': [0, 140]},
                'collage': {'y': [140, 1100], 'poster_area': [190, 180, 890, 920]},
                'memo': {'y': [1100, 1500]},
                'info': {'y': [1500, 1920]},
            },
        },
    },
]


def seed_templates(apps, schema_editor):
    CardTemplate = apps.get_model('shares', 'CardTemplate')
    for t in TEMPLATES:
        CardTemplate.objects.get_or_create(
            name=t['name'],
            defaults={
                'category': t['category'],
                'description_for_ai': t['description_for_ai'],
                'layout_schema': t['layout_schema'],
                'is_active': True,
            },
        )


def unseed_templates(apps, schema_editor):
    CardTemplate = apps.get_model('shares', 'CardTemplate')
    names = [t['name'] for t in TEMPLATES]
    CardTemplate.objects.filter(name__in=names).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('shares', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_templates, unseed_templates),
    ]
