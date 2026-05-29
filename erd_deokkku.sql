-- 덕꾸(Deokkku) ERD — ERDCloud import용 MySQL DDL
-- 생성일: 2026-05-29
-- 주의: Django 내부 테이블(auth_*, django_*) 제외. 앱 테이블만 포함.

CREATE TABLE `user` (
    `id`            BIGINT          NOT NULL AUTO_INCREMENT COMMENT '유저 PK',
    `email`         VARCHAR(255)    NOT NULL COMMENT '이메일 (로그인 ID)',
    `password`      VARCHAR(128)    NOT NULL COMMENT '해시된 비밀번호',
    `nickname`      VARCHAR(50)     NOT NULL COMMENT '닉네임',
    `profile_image` VARCHAR(500)    NULL     COMMENT '프로필 이미지 경로 (로컬 업로드)',
    `is_active`     TINYINT(1)      NOT NULL DEFAULT 1,
    `is_staff`      TINYINT(1)      NOT NULL DEFAULT 0,
    `is_superuser`  TINYINT(1)      NOT NULL DEFAULT 0,
    `last_login`    DATETIME        NULL,
    `created_at`    DATETIME        NOT NULL COMMENT '가입일',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_user_email` (`email`)
) COMMENT='이메일 기반 사용자 계정';


CREATE TABLE `social_account` (
    `id`            BIGINT          NOT NULL AUTO_INCREMENT COMMENT 'PK',
    `user_id`       BIGINT          NOT NULL COMMENT 'FK → user',
    `provider`      VARCHAR(20)     NOT NULL COMMENT 'google | kakao | apple',
    `provider_id`   VARCHAR(255)    NOT NULL COMMENT '소셜 제공자 고유 ID',
    `access_token`  TEXT            NULL     COMMENT '액세스 토큰 (추후 암호화 예정)',
    `refresh_token` TEXT            NULL     COMMENT '리프레시 토큰 (추후 암호화 예정)',
    `created_at`    DATETIME        NOT NULL COMMENT '연동일',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_social_provider` (`provider`, `provider_id`),
    CONSTRAINT `fk_social_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) COMMENT='소셜 로그인 연동 정보 (1계정 N소셜)';


CREATE TABLE `work` (
    `id`            BIGINT          NOT NULL AUTO_INCREMENT COMMENT '작품 PK',
    `work_type`     VARCHAR(20)     NOT NULL DEFAULT 'anime' COMMENT 'anime | movie | book | game | drama | other',
    `source`        VARCHAR(30)     NOT NULL DEFAULT '' COMMENT '외부 API 출처 (AniList / TMDB / Google Books 등)',
    `external_id`   VARCHAR(100)    NOT NULL DEFAULT '' COMMENT '외부 API 작품 ID (2단계 연동용)',
    `title`         VARCHAR(255)    NOT NULL COMMENT '원제',
    `title_ko`      VARCHAR(255)    NOT NULL DEFAULT '' COMMENT '한국어 제목',
    `title_en`      VARCHAR(255)    NOT NULL DEFAULT '' COMMENT '영어 제목',
    `release_date`  DATE            NULL     COMMENT '공개일',
    `genre`         VARCHAR(100)    NOT NULL DEFAULT '' COMMENT '장르 (저장 시 strip 정규화)',
    `poster_image`  VARCHAR(500)    NOT NULL DEFAULT '' COMMENT '포스터 URL (HTTPS 필수)',
    `description`   TEXT            NOT NULL DEFAULT '' COMMENT '작품 설명',
    PRIMARY KEY (`id`)
) COMMENT='작품 마스터 데이터 (애니·영화·도서·게임 등)';


CREATE TABLE `record` (
    `id`            BIGINT          NOT NULL AUTO_INCREMENT COMMENT '기록 PK',
    `user_id`       BIGINT          NOT NULL COMMENT 'FK → user',
    `work_id`       BIGINT          NOT NULL COMMENT 'FK → work (PROTECT)',
    `rating`        DECIMAL(3,1)    NULL     COMMENT '평점 (0.0 ~ 10.0)',
    `watched_date`  DATE            NULL     COMMENT '감상일',
    `content`       TEXT            NOT NULL DEFAULT '' COMMENT '감상문',
    `canvas_data`   JSON            NOT NULL COMMENT '다꾸 캔버스 설정 (배경/필터/테마/BGM)',
    `status`        VARCHAR(20)     NOT NULL DEFAULT 'published' COMMENT 'draft | published | archived',
    `visibility`    VARCHAR(20)     NOT NULL DEFAULT 'public' COMMENT 'public | friends | private',
    `like_count`    INT             NOT NULL DEFAULT 0 COMMENT '좋아요 수 (비정규화 캐싱)',
    `comment_count` INT             NOT NULL DEFAULT 0 COMMENT '댓글 수 (비정규화 캐싱)',
    `created_at`    DATETIME        NOT NULL COMMENT '생성일',
    `updated_at`    DATETIME        NOT NULL COMMENT '수정일',
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_record_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_record_work` FOREIGN KEY (`work_id`) REFERENCES `work` (`id`) ON DELETE RESTRICT
) COMMENT='감상 기록 (다이어리 핵심 엔티티)';


CREATE TABLE `record_image` (
    `id`            BIGINT          NOT NULL AUTO_INCREMENT COMMENT 'PK',
    `uploader_id`   BIGINT          NOT NULL COMMENT 'FK → user',
    `record_id`     BIGINT          NULL     COMMENT 'FK → record (nullable — 업로드 직후 미연결)',
    `file`          VARCHAR(500)    NOT NULL COMMENT '이미지 파일 경로',
    `original_name` VARCHAR(255)    NOT NULL DEFAULT '' COMMENT '원본 파일명',
    `size`          INT UNSIGNED    NOT NULL DEFAULT 0 COMMENT '파일 크기 (bytes)',
    `created_at`    DATETIME        NOT NULL COMMENT '업로드 시각',
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_recimg_uploader` FOREIGN KEY (`uploader_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_recimg_record`   FOREIGN KEY (`record_id`)   REFERENCES `record` (`id`) ON DELETE SET NULL
) COMMENT='다꾸 캔버스용 업로드 이미지 (업로더 본인만 접근 가능)';


CREATE TABLE `decoration` (
    `id`            BIGINT          NOT NULL AUTO_INCREMENT COMMENT 'PK',
    `record_id`     BIGINT          NOT NULL COMMENT 'FK → record',
    `type`          VARCHAR(20)     NOT NULL COMMENT 'sticker | text | image | gif | frame | tape',
    `content`       TEXT            NOT NULL DEFAULT '' COMMENT '스티커 URL 또는 텍스트 내용',
    `position_x`    DOUBLE          NOT NULL DEFAULT 0,
    `position_y`    DOUBLE          NOT NULL DEFAULT 0,
    `width`         DOUBLE          NOT NULL DEFAULT 100,
    `height`        DOUBLE          NOT NULL DEFAULT 100,
    `rotation`      DOUBLE          NOT NULL DEFAULT 0,
    `z_index`       INT             NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_deco_record` FOREIGN KEY (`record_id`) REFERENCES `record` (`id`) ON DELETE CASCADE
) COMMENT='캔버스 장식 요소 (2단계)';


CREATE TABLE `favorite_scene` (
    `id`            BIGINT          NOT NULL AUTO_INCREMENT COMMENT 'PK',
    `record_id`     BIGINT          NOT NULL COMMENT 'FK → record',
    `image_url`     VARCHAR(500)    NOT NULL COMMENT '명장면 이미지 URL',
    `order_index`   INT             NOT NULL DEFAULT 0 COMMENT '정렬 순서',
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_favscene_record` FOREIGN KEY (`record_id`) REFERENCES `record` (`id`) ON DELETE CASCADE
) COMMENT='명장면 (2단계)';


CREATE TABLE `album` (
    `id`            BIGINT          NOT NULL AUTO_INCREMENT COMMENT '앨범 PK',
    `user_id`       BIGINT          NOT NULL COMMENT 'FK → user',
    `name`          VARCHAR(100)    NOT NULL COMMENT '앨범명',
    `description`   TEXT            NOT NULL DEFAULT '' COMMENT '앨범 설명',
    `cover_image`   VARCHAR(500)    NOT NULL DEFAULT '' COMMENT '커버 이미지 URL (HTTPS 필수)',
    `visibility`    VARCHAR(20)     NOT NULL DEFAULT 'private' COMMENT 'public | friends | private',
    `created_at`    DATETIME        NOT NULL COMMENT '생성일',
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_album_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) COMMENT='기록 컬렉션 앨범';


CREATE TABLE `album_record` (
    `id`            BIGINT          NOT NULL AUTO_INCREMENT COMMENT 'PK',
    `album_id`      BIGINT          NOT NULL COMMENT 'FK → album',
    `record_id`     BIGINT          NOT NULL COMMENT 'FK → record',
    `added_at`      DATETIME        NOT NULL COMMENT '앨범에 추가된 시각',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_album_record` (`album_id`, `record_id`),
    CONSTRAINT `fk_ar_album`  FOREIGN KEY (`album_id`)  REFERENCES `album` (`id`)  ON DELETE CASCADE,
    CONSTRAINT `fk_ar_record` FOREIGN KEY (`record_id`) REFERENCES `record` (`id`) ON DELETE CASCADE
) COMMENT='Album-Record M:N 중간 테이블';
