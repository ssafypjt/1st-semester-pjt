-- ============================================================
--  덕꾸 (Deokkku) ERD  —  ERD Cloud 임포트용 DDL (MySQL 방언)
--  생성 기준: backend/ 앱의 Django 모델 & 마이그레이션 코드
-- ============================================================

-- ── 1. user ─────────────────────────────────────────────────
CREATE TABLE `user` (
  `id`            BIGINT        NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `email`         VARCHAR(255)  NOT NULL UNIQUE         COMMENT '이메일 (로그인 ID)',
  `password`      VARCHAR(128)  NOT NULL                COMMENT '해시된 비밀번호',
  `nickname`      VARCHAR(50)   NOT NULL                COMMENT '닉네임',
  `profile_image` VARCHAR(500)      NULL                COMMENT '프로필 이미지 URL',
  `provider`      VARCHAR(20)   NOT NULL DEFAULT 'local' COMMENT '소셜 제공자 (local/google/kakao/apple)',
  `provider_id`   VARCHAR(255)      NULL                COMMENT '소셜 로그인 ID',
  `is_active`     TINYINT(1)    NOT NULL DEFAULT 1,
  `is_staff`      TINYINT(1)    NOT NULL DEFAULT 0,
  `last_login`    DATETIME          NULL,
  `created_at`    DATETIME      NOT NULL                COMMENT '가입일',
  PRIMARY KEY (`id`)
) COMMENT='유저';

-- ── 2. anime ────────────────────────────────────────────────
CREATE TABLE `anime` (
  `id`           BIGINT        NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `external_id`  VARCHAR(100)      NULL                COMMENT '외부 API 작품 ID (AniList/MAL 등)',
  `source`       VARCHAR(30)       NULL                COMMENT '출처 (AniList / MAL 등)',
  `title`        VARCHAR(255)  NOT NULL                COMMENT '원제',
  `title_ko`     VARCHAR(255)      NULL                COMMENT '한국어 제목',
  `title_en`     VARCHAR(255)      NULL                COMMENT '영어 제목',
  `release_date` DATE              NULL                COMMENT '공개일',
  `genre`        VARCHAR(100)      NULL                COMMENT '장르 (쉼표 구분 문자열)',
  `poster_image` VARCHAR(500)      NULL                COMMENT '포스터 URL',
  `description`  TEXT              NULL                COMMENT '작품 설명',
  PRIMARY KEY (`id`)
) COMMENT='애니메이션 작품 메타데이터';

-- ── 3. record ───────────────────────────────────────────────
CREATE TABLE `record` (
  `id`            BIGINT        NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `user_id`       BIGINT        NOT NULL                COMMENT 'FK → user',
  `anime_id`      BIGINT        NOT NULL                COMMENT 'FK → anime (PROTECT)',
  `rating`        DECIMAL(3,1)      NULL                COMMENT '평점 (0.0 ~ 10.0)',
  `watched_date`  DATE              NULL                COMMENT '감상일',
  `content`       TEXT              NULL                COMMENT '감상문',
  `canvas_data`   JSON              NULL                COMMENT '캔버스 설정 (placed_items, main_image_src, analysis 등)',
  `status`        VARCHAR(20)   NOT NULL DEFAULT 'published' COMMENT '상태 (draft/published/archived)',
  `visibility`    VARCHAR(20)   NOT NULL DEFAULT 'public'    COMMENT '공개 범위 (public/friends/private)',
  `like_count`    INT           NOT NULL DEFAULT 0      COMMENT '좋아요 수 (비정규화 캐시)',
  `comment_count` INT           NOT NULL DEFAULT 0      COMMENT '댓글 수 (비정규화 캐시)',
  `created_at`    DATETIME      NOT NULL                COMMENT '생성일',
  `updated_at`    DATETIME      NOT NULL                COMMENT '수정일',
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_record_user`  FOREIGN KEY (`user_id`)  REFERENCES `user`  (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_record_anime` FOREIGN KEY (`anime_id`) REFERENCES `anime` (`id`) ON DELETE RESTRICT
) COMMENT='감상 기록 (서비스 핵심 엔티티)';

-- ── 4. record_image ─────────────────────────────────────────
CREATE TABLE `record_image` (
  `id`            BIGINT        NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `uploader_id`   BIGINT        NOT NULL                COMMENT 'FK → user',
  `record_id`     BIGINT            NULL                COMMENT 'FK → record (NULL 허용: 업로드 후 연결)',
  `file`          VARCHAR(500)  NOT NULL                COMMENT '파일 경로 (uploads/<user_id>/<uuid>.<ext>)',
  `original_name` VARCHAR(255)      NULL                COMMENT '원본 파일명',
  `size`          INT UNSIGNED  NOT NULL DEFAULT 0      COMMENT '파일 크기 (bytes)',
  `created_at`    DATETIME      NOT NULL                COMMENT '업로드 시각',
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_ri_uploader` FOREIGN KEY (`uploader_id`) REFERENCES `user`   (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ri_record`   FOREIGN KEY (`record_id`)   REFERENCES `record` (`id`) ON DELETE SET NULL
) COMMENT='다꾸 캔버스용 업로드 이미지 (업로더 본인만 접근 가능)';

-- ── 5. decoration  [2단계 예정] ──────────────────────────────
CREATE TABLE `decoration` (
  `id`         BIGINT        NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `record_id`  BIGINT        NOT NULL                COMMENT 'FK → record',
  `type`       VARCHAR(20)   NOT NULL                COMMENT '종류 (sticker/text/image/gif/frame/tape)',
  `content`    TEXT              NULL                COMMENT '텍스트 내용 또는 이미지 URL',
  `position_x` DOUBLE        NOT NULL DEFAULT 0      COMMENT 'X 좌표 (%)',
  `position_y` DOUBLE        NOT NULL DEFAULT 0      COMMENT 'Y 좌표 (%)',
  `width`      DOUBLE        NOT NULL DEFAULT 100,
  `height`     DOUBLE        NOT NULL DEFAULT 100,
  `rotation`   DOUBLE        NOT NULL DEFAULT 0      COMMENT '회전 각도 (deg)',
  `z_index`    INT           NOT NULL DEFAULT 0      COMMENT 'Z 레이어 순서',
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_decoration_record` FOREIGN KEY (`record_id`) REFERENCES `record` (`id`) ON DELETE CASCADE
) COMMENT='캔버스 데코레이션 요소 [2단계 예정]';

-- ── 6. favorite_scene  [2단계 예정] ─────────────────────────
CREATE TABLE `favorite_scene` (
  `id`          BIGINT        NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `record_id`   BIGINT        NOT NULL                COMMENT 'FK → record',
  `image_url`   VARCHAR(500)  NOT NULL                COMMENT '명장면 이미지 URL',
  `order_index` INT           NOT NULL DEFAULT 0      COMMENT '정렬 순서',
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_fs_record` FOREIGN KEY (`record_id`) REFERENCES `record` (`id`) ON DELETE CASCADE
) COMMENT='명장면 [2단계 예정]';

-- ── 7. album ────────────────────────────────────────────────
CREATE TABLE `album` (
  `id`          BIGINT        NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `user_id`     BIGINT        NOT NULL                COMMENT 'FK → user',
  `name`        VARCHAR(100)  NOT NULL                COMMENT '앨범명',
  `description` TEXT              NULL                COMMENT '앨범 설명',
  `cover_image` VARCHAR(500)      NULL                COMMENT '커버 이미지 URL',
  `visibility`  VARCHAR(20)   NOT NULL DEFAULT 'private' COMMENT '공개 범위 (public/friends/private)',
  `created_at`  DATETIME      NOT NULL                COMMENT '생성일',
  PRIMARY KEY (`id`),
  CONSTRAINT `fk_album_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) COMMENT='앨범 (기록 컬렉션)';

-- ── 8. album_record  (M:N 중간 테이블) ──────────────────────
CREATE TABLE `album_record` (
  `id`        BIGINT    NOT NULL AUTO_INCREMENT COMMENT 'PK',
  `album_id`  BIGINT    NOT NULL                COMMENT 'FK → album',
  `record_id` BIGINT    NOT NULL                COMMENT 'FK → record',
  `added_at`  DATETIME  NOT NULL                COMMENT '앨범에 추가된 시각',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_album_record` (`album_id`, `record_id`),
  CONSTRAINT `fk_ar_album`  FOREIGN KEY (`album_id`)  REFERENCES `album`  (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ar_record` FOREIGN KEY (`record_id`) REFERENCES `record` (`id`) ON DELETE CASCADE
) COMMENT='앨범-기록 M:N 중간 테이블';
