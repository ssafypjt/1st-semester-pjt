"""
초기 시드 데이터.
사용: python manage.py seed
"""
from django.core.management.base import BaseCommand
from animes.models import Anime
from accounts.models import User
from albums.models import Album, AlbumRecord
from records.models import Record


SAMPLE_ANIMES = [
    {
        'title': '스즈메의 문단속', 'title_ko': '스즈메의 문단속',
        'title_en': 'Suzume', 'genre': '판타지/드라마',
        'release_date': '2023-03-08',
        'poster_image': 'https://image.tmdb.org/t/p/w300/9bd2JnbR8MQuTI4u4Ax5Pe23rEi.jpg',
        'description': '재난과 판타지, 성장의 요소가 자연스럽게 어우러진 작품.',
    },
    {
        'title': '지브리 컬렉션', 'title_ko': '센과 치히로의 행방불명',
        'title_en': 'Spirited Away', 'genre': '판타지',
        'release_date': '2001-07-20',
        'poster_image': 'https://image.tmdb.org/t/p/w300/39wmItIWsg5sZMyRUHLkWBcuVCM.jpg',
        'description': '미야자키 하야오 감독의 명작.',
    },
    {
        'title': '코노스바 3기', 'title_ko': '이 멋진 세계에 축복을! 3',
        'title_en': 'KonoSuba 3', 'genre': '코미디/판타지',
        'release_date': '2024-04-10',
        'poster_image': 'https://image.tmdb.org/t/p/w300/lEgWmJqlOtKfMRyiglYg6XOoOuJ.jpg',
        'description': '카즈마와 동료들의 좌충우돌 모험기.',
    },
    {
        'title': '하이큐!!', 'title_ko': '하이큐!!',
        'title_en': 'Haikyu!!', 'genre': '스포츠',
        'release_date': '2014-04-06',
        'poster_image': 'https://image.tmdb.org/t/p/w300/9YHK85hYqr5GJiyiAESJtWZQQOC.jpg',
        'description': '청춘과 배구의 뜨거운 이야기.',
    },
    {
        'title': '너의 이름은', 'title_ko': '너의 이름은',
        'title_en': 'Your Name', 'genre': '로맨스/드라마',
        'release_date': '2017-01-04',
        'poster_image': 'https://image.tmdb.org/t/p/w300/q719jXXEzOoYaps6babgKnONONX.jpg',
        'description': '신카이 마코토 감독의 대표작.',
    },
]


class Command(BaseCommand):
    help = '샘플 데이터 시딩'

    def handle(self, *args, **opts):
        # demo user
        demo, created = User.objects.get_or_create(
            email='demo@deokkku.local',
            defaults={'nickname': '데모유저'},
        )
        if created:
            demo.set_password('demo1234')
            demo.save()
            self.stdout.write(self.style.SUCCESS('demo 유저 생성: demo@deokkku.local / demo1234'))
        else:
            self.stdout.write('demo 유저 이미 존재')

        # animes
        anime_objs = []
        for data in SAMPLE_ANIMES:
            obj, _ = Anime.objects.get_or_create(title_ko=data['title_ko'], defaults=data)
            anime_objs.append(obj)
        self.stdout.write(self.style.SUCCESS(f'애니 {len(anime_objs)}개 준비 완료'))

        # albums
        album_data = [
            ('인생 애니 모음', '내가 본 인생 애니들', 'public'),
            ('2024 봄 분기', '이번 분기 시청작', 'public'),
            ('지브리 컬렉션', '지브리 명작 모음', 'public'),
        ]
        for name, desc, vis in album_data:
            Album.objects.get_or_create(
                user=demo, name=name,
                defaults={'description': desc, 'visibility': vis},
            )

        # records
        sample_records = [
            (anime_objs[0], 9.5, '재난과 판타지, 성장의 요소가 자연스럽게 어우러진 작품.\n작화도 너무 예쁘고 음악이 정말 한 이야기의 감정선을 잘 담아내어 여운이 오래 남았다.'),
            (anime_objs[1], 8.5, '몇 번을 다시 봐도 좋은 작품. 치히로의 성장이 인상적이다.'),
            (anime_objs[2], 9.0, '시즌 3도 기대를 저버리지 않았다. 카즈마 일행 만세.'),
            (anime_objs[3], 9.0, '청춘 그 자체. 매 경기마다 손에 땀을 쥐게 한다.'),
        ]
        for anime, rating, content in sample_records:
            Record.objects.get_or_create(
                user=demo, anime=anime,
                defaults={
                    'rating': rating,
                    'content': content,
                    'watched_date': '2024-05-12',
                    'visibility': 'public',
                    'canvas_data': {'background': 'sky_theme', 'filter': 'soft_pink'},
                },
            )
        self.stdout.write(self.style.SUCCESS(f'기록 {Record.objects.count()}개 준비 완료'))
        self.stdout.write(self.style.SUCCESS('시드 완료!'))
