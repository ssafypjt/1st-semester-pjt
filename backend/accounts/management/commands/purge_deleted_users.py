"""탈퇴(soft delete) 후 보관 기간이 지난 유저를 영구 삭제.

회원 탈퇴 정책: 탈퇴 시 User.is_active=False, deleted_at=now() 로 설정 (soft delete).
30일간 보관 후 이 커맨드를 통해 영구 삭제(hard delete)한다.

운영에서는 cron / Windows 작업 스케줄러로 매일 1회 실행:
    python manage.py purge_deleted_users

사용 예:
    python manage.py purge_deleted_users              # 기본 30일 경과 유저 삭제
    python manage.py purge_deleted_users --days 7     # 보관 기간 변경
    python manage.py purge_deleted_users --dry-run    # 삭제 없이 대상만 출력

관련 모델은 FK on_delete=CASCADE 로 정의되어 있어, 유저 삭제 시
Record/Comment/Like/Follow/RecordImage/SocialAccount 등도 함께 정리된다.
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User


class Command(BaseCommand):
    help = '탈퇴 후 보관 기간(기본 30일)이 지난 유저를 영구 삭제합니다.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=30,
            help='보관 기간(일). 이 기간이 지난 탈퇴 계정을 영구 삭제합니다. (기본: 30)',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='실제로 삭제하지 않고 대상 목록만 출력합니다.',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff = timezone.now() - timedelta(days=days)

        qs = User.objects.filter(
            is_active=False,
            deleted_at__isnull=False,
            deleted_at__lte=cutoff,
        )
        count = qs.count()

        if count == 0:
            self.stdout.write('영구 삭제 대상이 없습니다.')
            return

        if dry_run:
            self.stdout.write(f'[dry-run] 영구 삭제 대상 {count}명 (탈퇴 후 {days}일 경과):')
            for u in qs:
                self.stdout.write(f'  - id={u.id} email={u.email} deleted_at={u.deleted_at}')
            return

        for u in qs:
            self.stdout.write(f'영구 삭제: id={u.id} email={u.email} deleted_at={u.deleted_at}')

        qs.delete()
        self.stdout.write(self.style.SUCCESS(f'{count}명의 유저를 영구 삭제했습니다.'))
