/**
 * 순수 유틸리티 함수 모음
 * App.vue에서 추출한 재사용 가능한 헬퍼 함수들
 */

/** 10점 만점 → ★☆ 5개 변환 */
export function stars(score) {
  const filled = Math.max(0, Math.min(5, Math.round(score / 2)));
  return "★".repeat(filled) + "☆".repeat(5 - filled);
}

/** "2026-05-18" → "2026.05.18" */
export function formatDisplayDate(value) {
  if (!value) return "";
  return value.replaceAll("-", ".");
}

/** "2026.05.18" → "2026-05-18" (input[type=date] 용) */
export function formatInputDate(value) {
  if (!value) return new Date().toISOString().slice(0, 10);
  return value.replaceAll(".", "-");
}

/** 피드 날짜 상대 표시 ("3분 전", "2일 전" 등) */
export function formatFeedDate(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  const now = new Date();
  const diff = now - d;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "방금 전";
  if (mins < 60) return `${mins}분 전`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}시간 전`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}일 전`;
  return d.toLocaleDateString("ko-KR");
}

/** 댓글 시간 상대 표시 */
export function formatCommentTime(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  const now = new Date();
  const diff = Math.floor((now - d) / 1000);
  if (diff < 60) return "방금 전";
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}일 전`;
  return d.toLocaleDateString("ko-KR");
}

/** 프로필 가입일 포맷 ("2026년 5월 18일") */
export function formatProfileDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

/** 이미지 URL 정규화 (마크다운 링크, 빈 값 처리) */
export function normalizeImageUrl(value) {
  const rawValue = String(value || "").trim();
  if (!rawValue) return "";
  if (rawValue.startsWith("/") || rawValue.startsWith("data:image/")) return rawValue;

  const markdownMatch = rawValue.match(/\[[^\]]*\]\((https?:\/\/[^)]+)\)/);
  if (markdownMatch) return markdownMatch[1];

  const urlMatch = rawValue.match(/https?:\/\/[^\s)]+/);
  return urlMatch ? urlMatch[0] : "";
}

/** 깊은 복사 (JSON 직렬화) */
export function cloneForSave(value) {
  return JSON.parse(JSON.stringify(value));
}

/** 값을 min~max 사이로 제한 */
export function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

/** 제목이 플레이스홀더인지 판별 */
export function isPlaceholderTitle(value) {
  const title = String(value || "").trim();
  return !title || title === "제목 없는 기록";
}

/** record 객체에서 표시용 제목 추출 */
export function recordDisplayTitle(record) {
  const candidates = [
    record?.work_title,
    record?.canvas_data?.work_title,
    record?.canvas_data?.anime_title,
    record?.canvas_data?.record?.title,
    record?.work?.title_ko,
    record?.work?.title,
    record?.work?.name,
    record?.anime_title,
    record?.display_title,
    record?.title,
    record?.canvas_data?.title,
  ];
  const title = candidates.find((v) => !isPlaceholderTitle(v));
  return title || "제목 없는 기록";
}

/** record 미리보기 텍스트 */
export function recordPreviewText(record) {
  const source =
    record?.content ||
    record?.memo ||
    record?.canvas_data?.analysis?.phrase ||
    record?.work_title ||
    "기록의 분위기를 담은 미리보기입니다.";
  return String(source).replace(/\s+/g, " ").trim();
}

/** 라디안 → 도 */
export function angleToDegrees(radians) {
  return (radians * 180) / Math.PI;
}

/** 네비게이션 아이콘 매핑 */
export function navIcon(item) {
  const icons = {
    홈: "⌂",
    "내 앨범": "▣",
    "기록 작성": "✎",
    리뷰: "★",
    마이페이지: "◉",
    "공유 페이지": "↗",
  };
  return icons[item] || "•";
}

/** 페이지 설명 텍스트 */
export function pageDescription(activePage) {
  const descriptions = {
    홈: "다른 사람들의 감상 기록을 둘러보세요.",
    "내 앨범": "저장한 다이어리 카드를 모아보는 공간입니다.",
    리뷰: "작품별 감상과 별점을 정리합니다.",
    마이페이지: "내 취향과 활동 기록을 확인합니다.",
    "공유 페이지": "다이어리 기록을 공유용 이미지로 생성하고 저장합니다.",
  };
  return descriptions[activePage] || "선택한 기록 모음을 다이어리 카드로 미리 봅니다.";
}
