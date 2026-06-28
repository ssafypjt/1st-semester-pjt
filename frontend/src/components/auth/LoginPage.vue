<template>
  <section class="login-stage">
    <article class="login-card">
      <div class="login-panel">
        <h1><span>덕꾸</span>{{ loginForm.mode === 'signup' ? ' 회원가입' : '에 로그인' }}</h1>
        <p v-if="loginForm.mode === 'login'">좋아하는 순간을 기록하고,<br />나만의 다꾸 앨범을 만들어보세요 ✨</p>
        <p v-else>좋아하는 애니 기록을 모으고,<br />나만의 다꾸 아카이브를 시작해보세요 ✨</p>

        <form @submit.prevent="loginForm.mode === 'signup' ? handleSignup() : handleLogin()">
          <label class="field">
            <span>♙</span>
            <input type="email" placeholder="이메일 주소" v-model="loginForm.email" required />
            <b>✉</b>
          </label>
          <label v-if="loginForm.mode === 'signup'" class="field">
            <span>◇</span>
            <input type="text" placeholder="닉네임" v-model="loginForm.nickname" />
            <b>✎</b>
          </label>
          <label class="field">
            <span>▣</span>
            <input type="password" placeholder="비밀번호" v-model="loginForm.password" required />
            <b>◌</b>
          </label>

          <div v-if="loginForm.mode === 'login'" class="login-options">
            <label><input type="checkbox" /> 로그인 상태 유지</label>
            <button type="button">비밀번호 찾기</button>
          </div>

          <p v-if="loginForm.error" class="auth-error">{{ loginForm.error }}</p>
          <button class="primary full" type="submit" :disabled="loginForm.loading">
            {{ loginForm.loading ? '확인 중...' : (loginForm.mode === 'signup' ? '회원가입' : '로그인') }}
          </button>
        </form>

        <div class="divider"><span>또는</span></div>
        <button class="oauth" type="button"><b>G</b> Google로 계속하기</button>
        <button class="oauth" type="button"><b>●</b> 카카오로 계속하기</button>
        <button class="oauth" type="button"><b></b> Apple로 계속하기</button>

        <p v-if="loginForm.mode === 'login'" class="join">계정이 없으신가요? <button type="button" @click="loginForm.mode = 'signup'; loginForm.error = ''">회원가입</button></p>
        <p v-else class="join">이미 계정이 있으신가요? <button type="button" @click="loginForm.mode = 'login'; loginForm.error = ''">로그인</button></p>
      </div>

      <div class="brand-panel">
        <img class="main-logo-img" :src="mainLogoUrl" alt="덕꾸 Deokkku 대표 로고" />
        <p class="brand-copy">
          애니를 보고 설레였던 그 순간,<br />
          좋아하는 장면, 캐릭터, 대사까지<br />
          나만의 다꾸로 예쁘게 기록해보세요!
        </p>
        <div class="feature-row">
          <div><span>♡</span><b>나만의 앨범</b><small>애니별로 정리</small></div>
          <div><span>✧</span><b>자유로운 꾸미기</b><small>스티커와 메모</small></div>
          <div><span>↗</span><b>쉽게 공유하기</b><small>링크와 이미지</small></div>
        </div>
      </div>
    </article>
  </section>
</template>

<script>
export default {
  name: 'LoginPage',
  props: {
    mainLogoUrl: {
      type: String,
      required: true,
    },
  },
  emits: ['login', 'signup'],
  data() {
    return {
      loginForm: {
        email: '',
        password: '',
        nickname: '',
        error: '',
        loading: false,
        mode: 'login',
      },
      csrfToken: '',
    };
  },
  methods: {
    async getCsrfToken(forceRefresh = false) {
      if (this.csrfToken && !forceRefresh) return this.csrfToken;
      const response = await fetch('/api/auth/csrf/', {
        credentials: 'include',
        cache: 'no-store',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!response.ok) throw new Error(`CSRF token request failed: ${response.status}`);
      const data = await response.json();
      this.csrfToken = data.csrfToken || '';
      return this.csrfToken;
    },
    async apiFetch(url, options = {}, _retried = false) {
      const method = (options.method || 'GET').toUpperCase();
      const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
      const needsCsrf = !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method);
      if (needsCsrf) headers['X-CSRFToken'] = await this.getCsrfToken();
      const response = await fetch(url, { credentials: 'include', ...options, headers });
      if (!response.ok) {
        const responseBody = await response.text();
        if (response.status === 403 && needsCsrf && !_retried && responseBody.includes('CSRF')) {
          this.csrfToken = '';
          return this.apiFetch(url, options, true);
        }
        let detail = responseBody;
        try {
          const errorData = JSON.parse(responseBody);
          detail = errorData.detail || JSON.stringify(errorData);
        } catch (e) { /* ignore parse error */ }
        throw new Error(`API request failed: ${response.status} ${detail}`);
      }
      if (response.status === 204) return null;
      return response.json();
    },
    async handleLogin() {
      this.loginForm.error = '';
      this.loginForm.loading = true;
      try {
        const user = await this.apiFetch('/api/auth/login/', {
          method: 'POST',
          body: JSON.stringify({
            email: this.loginForm.email,
            password: this.loginForm.password,
          }),
        });
        this.$emit('login', user);
        this.loginForm = { email: '', password: '', nickname: '', error: '', loading: false, mode: 'login' };
      } catch (error) {
        this.loginForm.error = '이메일 또는 비밀번호가 올바르지 않습니다.';
      } finally {
        this.loginForm.loading = false;
      }
    },
    async handleSignup() {
      this.loginForm.error = '';
      this.loginForm.loading = true;
      try {
        const user = await this.apiFetch('/api/auth/signup/', {
          method: 'POST',
          body: JSON.stringify({
            email: this.loginForm.email,
            password: this.loginForm.password,
            nickname: this.loginForm.nickname || this.loginForm.email.split('@')[0],
          }),
        });
        this.$emit('signup', user);
        this.loginForm = { email: '', password: '', nickname: '', error: '', loading: false, mode: 'login' };
      } catch (error) {
        this.loginForm.error = error.message || '회원가입에 실패했습니다.';
      } finally {
        this.loginForm.loading = false;
      }
    },
  },
};
</script>
