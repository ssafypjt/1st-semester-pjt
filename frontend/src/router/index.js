import { createRouter, createWebHistory } from "vue-router";

/**
 * 라우트 정의
 * - 백엔드 Django urls.py 패턴과 일치하도록 설계
 * - /deokkku/ 접두사 계열과 / 직접 접근 모두 지원
 */
const routes = [
  // ── 인증 ──
  {
    path: "/login",
    name: "login",
    meta: { guest: true },
    // LoginPage는 App.vue에서 직접 렌더링 (router-view 밖)
    // 이 라우트는 URL 매핑용
    component: { render: () => null },
  },
  {
    path: "/signup",
    name: "signup",
    meta: { guest: true },
    component: { render: () => null },
  },
  // Django 호환 경로
  { path: "/deokkku/login", redirect: "/login" },
  { path: "/deokkku/join", redirect: "/signup" },

  // ── 메인 페이지들 (인증 필요) ──
  {
    path: "/",
    redirect: "/home",
  },
  {
    path: "/home",
    name: "home",
    meta: { auth: true, navPage: "홈" },
    component: { render: () => null },
  },
  {
    path: "/diaries",
    name: "diaries",
    meta: { auth: true, navPage: "내 앨범" },
    component: { render: () => null },
  },
  {
    path: "/diaries/:id",
    name: "diary-detail",
    meta: { auth: true, navPage: "기록 작성" },
    component: { render: () => null },
    props: true,
  },
  {
    path: "/record/new",
    name: "record-new",
    meta: { auth: true, navPage: "기록 작성" },
    component: { render: () => null },
  },
  {
    path: "/cardbox",
    name: "cardbox",
    meta: { auth: true, navPage: "카드함" },
    component: { render: () => null },
  },
  {
    path: "/mypage",
    name: "mypage",
    meta: { auth: true, navPage: "마이페이지" },
    component: { render: () => null },
  },
  {
    path: "/share/:id",
    name: "share",
    meta: { auth: true, navPage: "공유 페이지" },
    component: { render: () => null },
    props: true,
  },

  // Django 호환 경로
  { path: "/deokkku", redirect: "/home" },
  { path: "/deokkku/home", redirect: "/home" },
  { path: "/deokkku/my_album", redirect: "/diaries" },
  { path: "/reviews", redirect: "/cardbox" },

  // ── 404 fallback ──
  {
    path: "/:pathMatch(.*)*",
    redirect: "/home",
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;
