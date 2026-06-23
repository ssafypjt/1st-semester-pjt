#!/usr/bin/env python3
"""
NotoSansKR 폰트 자동 다운로드 스크립트.

사용법:
    python setup_fonts.py

Google Fonts GitHub에서 NotoSansKR Regular/Bold를 다운로드하여
shares/fonts/ 디렉토리에 저장한다.
"""
import os
import sys
import urllib.request

FONT_DIR = os.path.join(os.path.dirname(__file__), 'shares', 'fonts')

# Google Fonts GitHub raw URL (안정적인 소스)
FONTS = {
    'NotoSansKR-Regular.ttf': (
        'https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf'
    ),
    'NotoSansKR-Bold.ttf': (
        'https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf'
    ),
}

# Variable 폰트는 하나의 파일로 Regular/Bold 모두 지원
# 동일 파일을 두 이름으로 복사 (renderer.py가 파일명으로 구분)
VARIABLE_FONT_URL = (
    'https://github.com/google/fonts/raw/main/ofl/notosanskr/NotoSansKR%5Bwght%5D.ttf'
)


def download_font(url, dest_path):
    """URL에서 폰트를 다운로드한다."""
    print(f'  다운로드 중: {os.path.basename(dest_path)}', end=' ... ')
    try:
        urllib.request.urlretrieve(url, dest_path)
        size_mb = os.path.getsize(dest_path) / (1024 * 1024)
        print(f'완료 ({size_mb:.1f}MB)')
        return True
    except Exception as e:
        print(f'실패: {e}')
        return False


def main():
    os.makedirs(FONT_DIR, exist_ok=True)

    # 이미 폰트가 있는지 확인
    regular = os.path.join(FONT_DIR, 'NotoSansKR-Regular.ttf')
    bold = os.path.join(FONT_DIR, 'NotoSansKR-Bold.ttf')

    if os.path.exists(regular) and os.path.getsize(regular) > 1000:
        print(f'폰트가 이미 존재합니다: {FONT_DIR}')
        print(f'  - NotoSansKR-Regular.ttf ({os.path.getsize(regular) / 1024 / 1024:.1f}MB)')
        if os.path.exists(bold):
            print(f'  - NotoSansKR-Bold.ttf ({os.path.getsize(bold) / 1024 / 1024:.1f}MB)')
        print('다시 다운로드하려면 해당 파일을 삭제 후 재실행하세요.')
        return

    print('NotoSansKR 폰트를 다운로드합니다...')
    print(f'저장 위치: {FONT_DIR}\n')

    # Variable 폰트 다운로드 (Regular/Bold 통합)
    variable_path = os.path.join(FONT_DIR, 'NotoSansKR-Variable.ttf')
    success = download_font(VARIABLE_FONT_URL, variable_path)

    if not success:
        print('\n❌ 다운로드 실패. 네트워크를 확인하세요.')
        print('수동 다운로드: https://fonts.google.com/noto/specimen/Noto+Sans+KR')
        sys.exit(1)

    # Variable 폰트를 Regular/Bold 이름으로 복사
    import shutil
    shutil.copy2(variable_path, regular)
    shutil.copy2(variable_path, bold)
    print(f'\n  복사: NotoSansKR-Variable.ttf → NotoSansKR-Regular.ttf')
    print(f'  복사: NotoSansKR-Variable.ttf → NotoSansKR-Bold.ttf')

    print('\n✅ 폰트 설치 완료!')
    print('renderer.py에서 index=1 (KR)로 로드합니다.')


if __name__ == '__main__':
    main()
