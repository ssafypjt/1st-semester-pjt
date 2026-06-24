<template>
  <div v-cloak>
    <div class="shell-bg">
      <span class="tape tape-a"></span>
      <span class="tape tape-b"></span>
      <span class="spark s1">*</span>
      <span class="spark s2">*</span>
      <span class="spark s3">*</span>
      <span class="polaroid polaroid-left"></span>
      <span class="memo memo-right">Today's log<br />감상<br />명장면<br />공유</span>
    </div>

    <!-- ── 로그인 / 회원가입 (미인증 시) ── -->
    <section v-if="!isCheckingAuth && !currentUser" class="login-stage">
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

    <section v-if="!isCheckingAuth && currentUser" class="workspace">
      <sidebar
        :simple-logo-url="simpleLogoUrl"
        :nav="nav"
        :active-page="activePage"
        :recent-tags="recentTags"
        :nav-icon="navIcon"
        :my-page-icon-url="myPageIconUrl"
        :review-icon-url="reviewIconUrl"
        :add-record-icon-url="addRecordIconUrl"
        :album-icon-url="albumIconUrl"
        :home-icon-url="homeIconUrl"
        :has-record-in-progress="hasRecordInProgress"
        @navigate="navigatePage"
      />

      <main class="main">
        <topbar
          ref="profileMenu"
          v-model:query="query"
          :current-user="currentUser"
          :show-profile-menu="showProfileMenu"
          :profile-initial="profileInitial"
          :activity-stats="activityStats"
          @open-record="openRecordModal"
          @toggle-profile="toggleProfileMenu"
          @view-profile="openProfilePageFromDropdown"
          @logout="logout"
        />

        <div v-if="activePage === '기록 작성'" class="content-grid">
          <section class="editor-zone">
            <div class="section-head">
              <div>
                <input
                  class="record-title-input"
                  type="text"
                  v-model="recordTitle"
                  placeholder="기록 제목을 입력하세요"
                  maxlength="100"
                />
              </div>
              <div class="toolset">
                <button
                  class="tool-action close-record-action"
                  type="button"
                  title="기록 닫기"
                  @click="confirmCloseRecord"
                >
                  <span>✕</span><b>닫기</b>
                </button>
                <button
                  class="tool-action"
                  type="button"
                  :disabled="!canUndo"
                  title="이전 작업으로 되돌리기"
                  @click="undoLastCanvasChange"
                >
                  <span>↶</span><b>실행 취소</b>
                </button>
                <button class="tool-action memo-action" type="button" title="메모 추가" @click="addTextMemo">
                  <span>T</span><b>메모 추가</b>
                </button>
                <fieldset class="visibility-toggle" aria-label="공개 설정">
                  <legend>공개 설정</legend>
                  <label :class="{ active: recordVisibility === 'public' }">
                    <input type="radio" value="public" v-model="recordVisibility" />
                    <span>
                      <b>공개</b>
                      <small>홈 피드에 다른 사용자도 볼 수 있어요</small>
                    </span>
                  </label>
                  <label :class="{ active: recordVisibility === 'private' }">
                    <input type="radio" value="private" v-model="recordVisibility" />
                    <span>
                      <b>비공개</b>
                      <small>내 앨범에서만 볼 수 있어요</small>
                    </span>
                  </label>
                </fieldset>
                <button class="primary small tool-action save-action" type="button" title="저장" @click="saveCard">
                  <span class="save-icon"></span><b>저장</b>
                </button>
                <button class="tool-action share-action" type="button" title="공유하기" @click="openShareModal">
                  <span>✂</span><b>공유하기</b>
                </button>
              </div>
            </div>

            <article class="scrapbook blank-scrapbook" @click.self="clearDecorationSelection">
              <div class="page left-page" @click="clearDecorationSelection">
                <button class="record-title-edit" type="button" title="기록 정보 수정" @click.stop="openRecordModal('edit')">
                  <small>{{ selectedView.date }}</small>
                  <strong>{{ selectedView.title }}</strong>
                  <span class="stars">{{ selectedViewStars }}</span>
                </button>
                <div v-if="isCanvasEmpty" class="blank-guide">
                  <strong>빈 다이어리</strong>
                  <span>오른쪽 도구에서 이미지, 메모, 스티커를 붙여 자유롭게 꾸며보세요.</span>
                </div>
              </div>
              <div class="binder" aria-hidden="true"><span v-for="ring in 7" :key="ring"></span></div>
              <div class="page right-page" @click="clearDecorationSelection">
                <div v-if="isCanvasEmpty" class="blank-guide right">
                  <strong>꾸미기 영역</strong>
                  <span>텍스트 메모는 입력, 이동, 삭제, 크기 조절이 가능합니다.</span>
                </div>
              </div>

              <div class="decoration-layer" ref="canvasLayer" @click.self="clearDecorationSelection">
                <div
                  v-for="item in placedItems"
                  :key="item.id"
                  class="placed-decoration"
                  :class="{ selected: selectedDecorationId === item.id }"
                  :style="placementStyle(item)"
                  role="button"
                  tabindex="0"
                  title="드래그로 이동"
                  @click.stop="selectDecoration(item.id)"
                  @pointerdown="startDrag($event, item)"
                >
                  <div class="placed-sticker" :class="item.tone" :style="stickerStyle(item)">
                    <div v-if="item.type === 'bubble'" class="bubble-editor" :class="item.bubbleType"
                      :style="bubbleEditorStyle(item)">
                      <textarea
                        v-model="item.text"
                        :style="{ fontSize: `${item.fontSize || 14}px`, color: item.textColor || '#342a3f' }"
                        placeholder="내용을 입력하세요"
                        @click.stop="selectDecoration(item.id)"
                      ></textarea>
                    </div>
                    <div v-else-if="item.type === 'text'" class="memo-editor">
                      <textarea
                        v-model="item.text"
                        :style="{ fontSize: `${item.fontSize || 15}px` }"
                        placeholder="메모를 입력하세요"
                        @click.stop="selectDecoration(item.id)"
                      ></textarea>
                      <label v-if="selectedDecorationId === item.id" class="memo-font-control" @pointerdown.stop @click.stop>
                        <span>글자</span>
                        <input type="range" min="11" max="34" step="1" v-model.number="item.fontSize" title="글자 크기 조절" />
                      </label>
                    </div>
                    <img v-else-if="item.imageSrc" :src="item.imageSrc" alt="첨부 이미지" />
                    <span v-else>{{ item.icon }}</span>
                  </div>
                  <button
                    v-if="selectedDecorationId === item.id"
                    class="rotate-decoration"
                    type="button"
                    title="기울기 조절"
                    @pointerdown.stop="startRotate($event, item)"
                    @click.stop
                  >
                    ↻
                  </button>
                  <button
                    v-if="selectedDecorationId === item.id"
                    class="resize-decoration"
                    type="button"
                    title="크기 조절"
                    aria-label="크기 조절"
                    @pointerdown.stop="startResize($event, item)"
                    @click.stop
                  ></button>
                  <button
                    v-if="selectedDecorationId === item.id"
                    class="delete-decoration"
                    type="button"
                    title="삭제"
                    @pointerdown.stop
                    @click.stop="removeSticker(item.id)"
                  >
                    ×
                  </button>
                </div>
              </div>
            </article>

            <div class="canvas-tools">
              <button v-for="tool in canvasTools" :key="tool.label" type="button" @click="runCanvasTool(tool)">
                {{ tool.icon }} {{ tool.label }}
              </button>
              <span></span>
              <button type="button">－</button>
              <b>100%</b>
              <button type="button">＋</button>
            </div>

            <!-- 말풍선 편집 툴바 -->
            <div v-if="selectedBubbleItem" class="bubble-toolbar">
              <div class="bt-section">
                <span class="bt-label">글꼴 크기</span>
                <div class="bt-font-size">
                  <button type="button" @click="changeBubbleFontSize(-1)">−</button>
                  <span>{{ selectedBubbleItem.fontSize || 14 }}px</span>
                  <button type="button" @click="changeBubbleFontSize(1)">+</button>
                </div>
              </div>
              <div class="bt-section">
                <span class="bt-label">배경색</span>
                <div class="bt-colors">
                  <button
                    v-for="c in bubblePresetColors"
                    :key="'bg-'+c"
                    class="bt-swatch"
                    :class="{ active: (selectedBubbleItem.bgColor || '#ffffff') === c }"
                    :style="{ background: c }"
                    type="button"
                    @click="selectedBubbleItem.bgColor = c"
                  ></button>
                  <label class="bt-custom-color">
                    <input type="color" :value="selectedBubbleItem.bgColor || '#ffffff'" @input="selectedBubbleItem.bgColor = $event.target.value" />
                    <span class="bt-swatch custom" :style="{ background: selectedBubbleItem.bgColor || '#ffffff' }">⋯</span>
                  </label>
                </div>
              </div>
              <div class="bt-section">
                <span class="bt-label">테두리색</span>
                <div class="bt-colors">
                  <button
                    v-for="c in bubblePresetBorders"
                    :key="'bd-'+c"
                    class="bt-swatch"
                    :class="{ active: (selectedBubbleItem.borderColor || '#b49cd8') === c }"
                    :style="{ background: c }"
                    type="button"
                    @click="selectedBubbleItem.borderColor = c"
                  ></button>
                  <label class="bt-custom-color">
                    <input type="color" :value="selectedBubbleItem.borderColor || '#b49cd8'" @input="selectedBubbleItem.borderColor = $event.target.value" />
                    <span class="bt-swatch custom" :style="{ background: selectedBubbleItem.borderColor || '#b49cd8' }">⋯</span>
                  </label>
                </div>
              </div>
            </div>
          </section>

          <aside class="right-rail">
            <sticker-panel
              :sticker-categories="stickerCategories"
              :active-sticker-category="activeStickerCategory"
              :visible-decorations="visibleDecorations"
              @change-category="activeStickerCategory = $event"
              @add-decoration="addDecoration"
              @upload-sticker="handleStickerUpload"
            />

            <image-upload-panel @image-upload="handleImageUpload" />

            <section class="panel-card">
              <header>
                <h3>감상평</h3>
                <span>메모</span>
              </header>
              <textarea
                class="content-textarea"
                v-model="currentRecord.memo"
                placeholder="작품에 대한 감상평을 자유롭게 작성하세요..."
                rows="5"
              ></textarea>
            </section>

            <section class="panel-card">
              <header>
                <h3>추천 키워드</h3>
                <span>AI 추천</span>
              </header>
              <div class="keyword-list">
                <button v-for="tag in ai.tags" :key="tag" type="button">#{{ tag }}</button>
              </div>
            </section>
          </aside>
        </div>

        <section v-else class="detail-page">
          <header>
            <img v-if="activePage === nav[4]" class="detail-page-icon-image" :src="myPageIconUrl" alt="" />
            <img v-else-if="activePage === nav[3]" class="detail-page-icon-image" :src="reviewIconUrl" alt="" />
            <img v-else-if="activePage === nav[1]" class="detail-page-icon-image" :src="albumIconUrl" alt="" />
            <img v-else-if="activePage === nav[0]" class="detail-page-icon-image" :src="homeIconUrl" alt="" />
            <span v-else>{{ navIcon(activePage) }}</span>
            <div>
              <h2>{{ activePage }}</h2>
              <p>{{ pageDescription }}</p>
            </div>
          </header>
          <my-page-dashboard
            v-if="activePage === nav[4]"
            :current-user="currentUser"
            :profile-preview-url="profilePreviewUrl"
            :profile-initial="profileInitial"
            :joined-date="currentUser?.created_at ? formatProfileDate(currentUser.created_at) : ''"
            :profile-stats="profileStats"
            :featured-badges="featuredBadges"
            @edit-profile="openProfileModal"
            @open-badges="openBadgeModal"
          />

          <div v-if="activePage !== nav[0] && activePage !== nav[1] && activePage !== nav[4]" class="detail-grid">
            <article
              v-for="card in detailCards"
              :key="card.title"
              class="detail-card"
              :class="{ clickable: card.action }"
              :role="card.action ? 'button' : null"
              :tabindex="card.action ? 0 : null"
              @click="card.action && navigatePage(card.action)"
              @keydown.enter.prevent="card.action && navigatePage(card.action)"
              @keydown.space.prevent="card.action && navigatePage(card.action)"
            >
              <span v-if="card.icon" class="detail-card-icon">{{ card.icon }}</span>
              <b>{{ card.title }}</b>
              <p>{{ card.body }}</p>
            </article>
          </div>
          <!-- 홈 피드: public 게시글 -->
          <div v-if="activePage === '홈'" class="home-feed">
            <p v-if="isFeedLoading" class="feed-empty">불러오는 중...</p>
            <p v-else-if="feedRecords.length === 0" class="feed-empty">아직 공유된 기록이 없습니다.</p>
            <article
              v-for="rec in feedRecords"
              :key="rec.id"
              class="feed-card"
              role="button"
              tabindex="0"
              @click="openFeedDiaryPreview(rec)"
              @keydown.enter.prevent="openFeedDiaryPreview(rec)"
              @keydown.space.prevent="openFeedDiaryPreview(rec)"
            >
              <header class="feed-card-header">
                <div class="feed-user">
                  <b>{{ rec.user_nickname || '익명' }}님의 기록</b>
                </div>
                <time>{{ formatFeedDate(rec.created_at) }}</time>
              </header>
              <div class="record-preview" :class="recordPreviewClass(rec)">
                <img
                  v-if="currentRecordPreviewImage(rec)"
                  class="record-preview-image"
                  :src="currentRecordPreviewImage(rec)"
                  :alt="recordDisplayTitle(rec)"
                  @error="handleRecordPreviewImageError(rec)"
                />
                <div v-else class="record-preview-empty-copy">
                  <small>다이어리 기록</small>
                  <b>{{ recordDisplayTitle(rec) }}</b>
                </div>
                <span class="record-preview-sticker sticker-a">✦</span>
                <span class="record-preview-sticker sticker-b">♡</span>
                <span class="record-preview-sticker sticker-c">✧</span>
                <div class="preview-memo-note">
                  <b>{{ rec.rating ? `${rec.rating} / 10` : '감상 기록' }}</b>
                  <p>{{ recordPreviewText(rec) }}</p>
                </div>
              </div>
              <div class="feed-card-body">
                <div class="feed-info">
                  <h3>{{ recordDisplayTitle(rec) }}</h3>
                  <p v-if="rec.work_title" class="feed-work">{{ rec.work_title }}</p>
                  <span v-if="rec.rating" class="feed-rating">{{ stars(rec.rating) }} {{ rec.rating }}</span>
                  <p v-if="rec.content" class="feed-content">{{ rec.content.length > 120 ? rec.content.slice(0, 120) + '…' : rec.content }}</p>
                </div>
                <footer class="feed-card-footer">
                  <button type="button" class="feed-action" :class="{ liked: rec.is_liked }" @click.stop="toggleFeedLike(rec)" @keydown.enter.stop @keydown.space.stop>{{ rec.is_liked ? '♥' : '♡' }} {{ rec.like_count || 0 }}</button>
                  <button type="button" class="feed-action" @click.stop @keydown.enter.stop @keydown.space.stop>💬 {{ rec.comment_count || 0 }}</button>
                  <button v-if="rec.is_mine" type="button" class="feed-action feed-edit" @click.stop="openFeedRecord(rec)" @keydown.enter.stop @keydown.space.stop>✎ 편집</button>
                </footer>
              </div>
            </article>
          </div>

          <saved-album-grid
            v-if="activePage === '내 앨범'"
            :saved-cards="savedCards"
            :stars="stars"
            @open-card="openSavedCard"
            @delete-card="deleteSavedCard"
          />

          <!-- 공유 페이지 안내 (기존 nav 연결 유지) -->
          <div v-if="activePage === '공유 페이지'" class="share-page-section">
            <p class="share-page-hint">기록 작성 화면에서 <b>공유하기</b> 버튼을 눌러 공유 카드를 만들 수 있습니다.</p>
          </div>
        </section>

        <record-modal
          v-if="isRecordModalOpen"
          v-model:record-form="recordForm"
          :mode="recordModalMode"
          :stars="stars"
          :api-fetch="apiFetch"
          @close="closeRecordModal"
          @submit="createBlankRecord"
        />

        <save-toast
          v-if="toastMessage"
          :message="toastMessage"
          @close="toastMessage = ''"
          @view-album="openAlbumFromToast"
        />

        <profile-modal
          v-if="isProfileModalOpen"
          v-model:profile-form="profileForm"
          :profile-preview-url="profilePreviewUrl"
          :profile-initial="profileInitial"
          :profile-status="profileStatus"
          :current-user="currentUser"
          :is-profile-saving="isProfileSaving"
          @close="closeProfileModal"
          @submit="updateProfile"
          @image-change="handleProfileImageChange"
        />

        <badge-modal
          v-if="isBadgeModalOpen"
          :available-badges="availableBadges"
          :selected-badge-ids="selectedBadgeIds"
          @close="closeBadgeModal"
          @toggle-badge="toggleRepresentativeBadge"
        />

        <div v-if="isDiaryPreviewOpen" class="diary-preview-overlay" @click.self="closeFeedDiaryPreview">
          <section class="diary-preview-modal" role="dialog" aria-modal="true" aria-label="다이어리 원본 보기">
            <header class="diary-preview-header">
              <div>
                <small>DIARY PREVIEW</small>
                <h3>{{ previewRecord.title || '제목 없는 기록' }}</h3>
                <p v-if="previewRecord.author">{{ previewRecord.author }}님의 기록</p>
              </div>
              <button class="diary-preview-close" type="button" @click="closeFeedDiaryPreview">✕</button>
            </header>

            <div v-if="previewError" class="diary-preview-state error">{{ previewError }}</div>
            <article class="scrapbook blank-scrapbook diary-preview-book" :class="{ loading: previewLoading }">
              <div class="page left-page">
                <div class="record-title-edit diary-preview-title">
                  <small>{{ previewRecord.date }}</small>
                  <strong>{{ previewRecord.title || '제목 없는 기록' }}</strong>
                  <span class="stars">{{ previewStars }}</span>
                </div>
                <div v-if="isPreviewDiaryEmpty" class="blank-guide">
                  <strong>{{ previewRecord.title || '다이어리 기록' }}</strong>
                  <span>{{ previewRecord.memo || '저장된 꾸미기 요소가 없어 기본 기록 정보로 표시합니다.' }}</span>
                </div>
              </div>
              <div class="binder" aria-hidden="true"><span v-for="ring in 7" :key="'preview-ring-' + ring"></span></div>
              <div class="page right-page">
                <div v-if="isPreviewDiaryEmpty" class="blank-guide right">
                  <strong>감상 메모</strong>
                  <span>{{ previewRecord.memo || '작성된 감상평이 없습니다.' }}</span>
                </div>
              </div>

              <div class="decoration-layer diary-preview-layer">
                <div
                  v-for="item in previewPlacedItems"
                  :key="item.id"
                  class="placed-decoration diary-preview-decoration"
                  :style="placementStyle(item)"
                >
                  <div class="placed-sticker" :class="item.tone" :style="stickerStyle(item)">
                    <div
                      v-if="item.type === 'bubble'"
                      class="bubble-editor diary-preview-note"
                      :class="item.bubbleType"
                      :style="bubbleEditorStyle(item)"
                    >
                      <p :style="previewTextStyle(item)">{{ item.text }}</p>
                    </div>
                    <div v-else-if="item.type === 'text'" class="memo-editor diary-preview-note">
                      <p :style="previewTextStyle(item)">{{ item.text }}</p>
                    </div>
                    <img v-else-if="item.imageSrc" :src="item.imageSrc" alt="다이어리 이미지" />
                    <span v-else>{{ item.icon }}</span>
                  </div>
                </div>
              </div>
            </article>
            <div v-if="previewLoading" class="diary-preview-loading">다이어리를 불러오는 중...</div>
          </section>
        </div>

        <!-- ── 공유 카드 모달 ── -->
        <div v-if="isShareModalOpen" class="share-modal-overlay" @click.self="closeShareModal">
          <div class="share-modal">
            <div class="share-modal-header">
              <div>
                <small>SHARE PREVIEW</small>
                <h3>공유 카드 만들기</h3>
              </div>
              <button class="share-modal-close" type="button" @click="closeShareModal">✕</button>
            </div>

            <div class="share-modal-body">
              <!-- 카드 미리보기 -->
              <div class="share-preview-card">
                <div v-if="latestShareCard" class="share-preview-image">
                  <img :src="latestShareCard.image_url" alt="공유 카드" />
                </div>
                <div v-else-if="isGeneratingCard" class="share-preview-placeholder">
                  <div class="spinner"></div>
                  <p>AI가 배치 중...</p>
                </div>
                <div v-else class="share-preview-placeholder">
                  <p>아래 버튼을 눌러 공유 카드를 생성하세요.</p>
                </div>

                <div class="share-preview-info">
                  <b>{{ currentRecord.title }}</b>
                  <span v-if="currentRecord.rating" class="share-preview-rating">{{ currentRecord.rating }} / 10</span>
                  <div v-if="currentRecord.tags && currentRecord.tags.length" class="share-preview-tags">
                    <span v-for="tag in currentRecord.tags" :key="tag">#{{ tag }}</span>
                  </div>
                </div>
              </div>

              <!-- 우측 액션 영역 -->
              <div class="share-actions">
                <p v-if="shareCardError" class="share-error">{{ shareCardError }}</p>

                <p v-if="latestShareCard" class="share-result-desc">
                  {{ latestShareCard.template_name || '이미지 폴라로이드' }}
                </p>
                <p v-if="latestShareCard" class="share-result-sub">AI가 자동으로 배치한 공유 카드입니다.</p>

                <div class="share-btn-group">
                  <button
                    class="share-btn outline"
                    type="button"
                    :disabled="isGeneratingCard"
                    @click="generateShareCard"
                  >
                    {{ latestShareCard ? '다시 만들기' : (isGeneratingCard ? 'AI 생성 중...' : 'AI 카드 생성') }}
                  </button>
                  <button
                    v-if="latestShareCard"
                    class="share-btn primary"
                    type="button"
                    @click="downloadShareImage"
                  >
                    이미지 저장
                  </button>
                  <button class="share-btn" type="button" @click="closeShareModal">닫기</button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </section>
  </div>
</template>

<script>
import simpleLogoUrl from "./assets/images/simple_logo.png";
import mainLogoUrl from "./assets/images/main-logo.png";
import basicProfileUrl from "./assets/images/basic_profile.png";
import myPageIconUrl from "./assets/images/my_page_icon.png";
import reviewIconUrl from "./assets/images/card_icon.png";
import addRecordIconUrl from "./assets/images/add_record_icon.png";
import albumIconUrl from "./assets/images/album_icon.png";
import homeIconUrl from "./assets/images/home_icon.png";
import SavedAlbumGrid from "./components/album/SavedAlbumGrid.vue";
import Sidebar from "./components/layout/Sidebar.vue";
import Topbar from "./components/layout/Topbar.vue";
import BadgeModal from "./components/modal/BadgeModal.vue";
import ProfileModal from "./components/modal/ProfileModal.vue";
import RecordModal from "./components/modal/RecordModal.vue";
import SaveToast from "./components/modal/SaveToast.vue";
import MyPageDashboard from "./components/profile/MyPageDashboard.vue";
import ImageUploadPanel from "./components/record/ImageUploadPanel.vue";
import StickerPanel from "./components/record/StickerPanel.vue";
import { canvasTools, nav, recentTags } from "./constants/navigation";
import { decorations, stickerCategories } from "./constants/stickers";
import { defaultAnalysis } from "./constants/defaultAnalysis";

export default {
  name: "App",
  components: {
    BadgeModal,
    ImageUploadPanel,
    MyPageDashboard,
    ProfileModal,
    RecordModal,
    SavedAlbumGrid,
    SaveToast,
    Sidebar,
    StickerPanel,
    Topbar,
  },
  data() {
    return {
      simpleLogoUrl,
      mainLogoUrl,
      basicProfileUrl,
      myPageIconUrl,
      reviewIconUrl,
      addRecordIconUrl,
      albumIconUrl,
      homeIconUrl,
      query: "",
      activePage: localStorage.getItem("deokkku:activePage") || "내 앨범",
      _dirty: false,
      activeStickerCategory: "전체",
      isRecordModalOpen: false,
      selectedDecorationId: null,
      mainImageSrc: "",
      currentRecord: {
        title: "새 감상 기록",
        date: "2026.05.18",
        rating: 0,
        memo: "좋아하는 장면과 감정을 자유롭게 남겨보세요.",
        tags: [],
      },
      recordForm: {
        title: "",
        date: new Date().toISOString().slice(0, 10),
        rating: 0,
        workId: null,
      },
      recordModalMode: "create",
      savedCards: [],
      feedRecords: [],
      isFeedLoading: false,
      recordPreviewCandidateIndexes: {},
      brokenRecordPreviewImages: {},
      isDiaryPreviewOpen: false,
      previewLoading: false,
      previewError: "",
      previewRecord: {},
      previewPlacedItems: [],
      previewMainImageSrc: "",
      recordVisibility: "public",
      recordTitle: "",
      bubblePresetColors: ['#ffffff', '#fff5f5', '#fff8e1', '#e8f5e9', '#e3f2fd', '#f3e5f5', '#fce4ec', '#ede7f6'],
      bubblePresetBorders: ['#b49cd8', '#e57373', '#ffb74d', '#81c784', '#64b5f6', '#ba68c8', '#f06292', '#333333'],
      undoHistory: [],
      layerZIndex: 0,
      lastSaveAt: 0,
      toastMessage: "",
      isCheckingAuth: true,
      currentUser: null,
      isLoggingOut: false,
      isProfileSaving: false,
      showProfileMenu: false,
      isProfileModalOpen: false,
      isBadgeModalOpen: false,
      csrfToken: "",
      profileForm: {
        nickname: "",
        profileImage: null,
        removeProfileImage: false,
      },
      profilePreviewLocalUrl: "",
      profileStatus: {
        type: "",
        message: "",
      },
      selectedBadgeIds: [],
      dragging: null,
      resizing: null,
      rotating: null,
      nav,
      recentTags,
      canvasTools,
      stickerCategories,
      decorations,           // 하드코딩 폴백
      userStickers: [],      // API에서 가져온 유저 보유 스티커
      stickersLoaded: false, // API 로드 완료 여부
      placedItems: [],
      ai: defaultAnalysis,
      currentRecordId: null,  // 현재 편집 중인 백엔드 Record ID (null이면 신규)
      isSaving: false,         // 저장 중 중복 요청 방지

      // ── 로그인 폼 ──
      loginForm: {
        email: '',
        password: '',
        nickname: '',
        error: '',
        loading: false,
        mode: 'login',  // 'login' | 'signup'
      },

      // ── 공유 카드 ──
      isShareModalOpen: false,   // 공유 모달 열림
      shareCards: [],            // 생성된 공유 카드 목록
      isGeneratingCard: false,   // AI 카드 생성 중
      shareCardError: '',        // 에러 메시지
    };
  },
  watch: {
    placedItems: { handler() { this._dirty = true; }, deep: true },
    mainImageSrc() { this._dirty = true; },
    currentRecord: { handler() { this._dirty = true; }, deep: true },
  },
  computed: {
    selectedView() {
      return this.currentRecord;
    },
    selectedViewStars() {
      return this.stars(this.selectedView.rating);
    },
    previewStars() {
      return this.stars(this.previewRecord.rating || 0);
    },
    isPreviewDiaryEmpty() {
      return this.previewPlacedItems.length === 0 && !this.previewMainImageSrc;
    },
    isCanvasEmpty() {
      return this.placedItems.length === 0 && !this.mainImageSrc;
    },
    hasRecordInProgress() {
      return this.placedItems.length > 0 || !!this.mainImageSrc || !!this.currentRecordId;
    },
    canUndo() {
      return this.undoHistory.length > 0;
    },
    latestShareCard() {
      return this.shareCards.length > 0 ? this.shareCards[0] : null;
    },
    profilePreviewUrl() {
      return this.profilePreviewLocalUrl || this.currentUser?.profile_image || this.basicProfileUrl;
    },
    profileInitial() {
      const source = this.currentUser?.nickname || this.currentUser?.email || "?";
      return source.trim().slice(0, 1).toUpperCase();
    },
    activityStats() {
      return this.getActivityStats();
    },
    profileStats() {
      const stats = this.activityStats;
      const unlockedBadges = this.availableBadges.filter((badge) => badge.unlocked).length;
      return [
        { icon: "🏅", label: "수집한 뱃지", value: unlockedBadges, action: "badges" },
        { icon: "▣", label: "내 앨범", value: stats.albums },
        { icon: "↗", label: "공유 카드", value: stats.shares },
        { icon: "⭐", label: "대표 뱃지", value: this.featuredBadges.length },
      ];
    },
    availableBadges() {
      return this.getUserBadges();
    },
    featuredBadges() {
      const unlocked = this.availableBadges.filter((badge) => badge.unlocked);
      const selected = this.selectedBadgeIds
        .map((id) => unlocked.find((badge) => badge.id === id))
        .filter(Boolean);
      return selected.slice(0, 3);
    },
    recentActivities() {
      return (this.savedCards || []).slice(0, 5).map((card) => ({
        id: `saved-${card.id}`,
        icon: "▣",
        title: card.title || "저장한 다이어리",
        description: "내 앨범에 저장한 감상 카드",
        date: card.date || "최근",
      }));
    },
    visibleDecorations() {
      // 기본 스티커 + 유저 업로드 스티커 합산
      var source = this.decorations.slice();
      if (this.stickersLoaded && this.userStickers.length > 0) {
        // 기본 스티커와 중복되지 않는 유저 스티커만 추가
        var existingIds = {};
        for (var i = 0; i < source.length; i++) {
          if (source[i].id) existingIds[source[i].id] = true;
        }
        for (var j = 0; j < this.userStickers.length; j++) {
          if (!existingIds[this.userStickers[j].id]) {
            source.push(this.userStickers[j]);
          }
        }
      }
      if (this.activeStickerCategory === "전체") {
        return source;
      }
      return source.filter(function(item) { return item.category === this.activeStickerCategory; }.bind(this));
    },
    selectedBubbleItem() {
      if (!this.selectedDecorationId) return null;
      var item = this.placedItems.find(function(i) { return i.id === this.selectedDecorationId; }.bind(this));
      return (item && item.type === 'bubble') ? item : null;
    },
    pageDescription() {
      const descriptions = {
        홈: "다른 사람들의 감상 기록을 둘러보세요.",
        "내 앨범": "저장한 다이어리 카드를 모아보는 공간입니다.",
        리뷰: "작품별 감상과 별점을 정리합니다.",
        마이페이지: "내 취향과 활동 기록을 확인합니다.",
        "공유 페이지": "다이어리 기록을 공유용 이미지로 생성하고 저장합니다.",
      };
      return descriptions[this.activePage] || "선택한 기록 모음을 다이어리 카드로 미리 봅니다.";
    },
    detailCards() {
      if (this.activePage === this.nav[4]) {
        return [
          { icon: "✏", title: "기록 작성", body: "새 감상 다이어리를 작성합니다.", action: this.nav[2] },
          { icon: "▣", title: "내 앨범", body: "작성한 기록을 확인합니다.", action: this.nav[1] },
          { icon: "↗", title: "공유 페이지", body: "공유 이미지를 생성하고 저장합니다.", action: "공유 페이지" },
        ];
      }
      return [
        { title: "기록 작성", body: "이미지, 스티커, 메모를 붙여 새 감상 다이어리를 만듭니다.", action: "기록 작성" },
        { title: "내 앨범", body: "저장한 다이어리 카드를 다시 열고 편집할 수 있습니다.", action: "내 앨범" },
        { title: "공유 페이지", body: "완성한 기록을 이미지로 생성하고 저장합니다.", action: "공유 페이지" },
      ];
    },
  },
  mounted() {
    window.addEventListener("pointermove", this.handlePointerMove);
    window.addEventListener("pointerup", this.stopPointerWork);
    document.addEventListener("click", this.handleProfileOutsideClick);
    document.addEventListener("keydown", this.handleGlobalKeydown);

    // 새로고침/탭 닫기 시 임시저장 + 확인 다이얼로그 (기록 작성 중 + 미저장 변경 있을 때만)
    this._isEditing = () =>
      this.activePage === "기록 작성" && this._dirty && (this.placedItems.length > 0 || this.mainImageSrc);
    this._beforeUnloadHandler = (e) => {
      if (this._isEditing()) {
        this._autosaveDraft();
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", this._beforeUnloadHandler);
    window.addEventListener("pagehide", () => {
      if (this._isEditing()) {
        this._autosaveDraft();
      }
    });

    this.loadRepresentativeBadges();
    this.checkAuth();
    this.loadFeedRecords();
    this.loadSavedCards().then(() => {
      this._checkAutosaveRestore();
      this.$nextTick(() => { this._dirty = false; });
    });
  },
  beforeUnmount() {
    window.removeEventListener("pointermove", this.handlePointerMove);
    window.removeEventListener("pointerup", this.stopPointerWork);
    document.removeEventListener("click", this.handleProfileOutsideClick);
    document.removeEventListener("keydown", this.handleGlobalKeydown);
    window.removeEventListener("beforeunload", this._beforeUnloadHandler);
  },
  methods: {
    async toggleFeedLike(record) {
      if (!this.currentUser) return;
      try {
        const data = await this.apiFetch(`/api/records/${record.id}/like/`, { method: "POST" });
        record.is_liked = data.liked;
        record.like_count = data.like_count;
      } catch (error) {
        console.error("좋아요 실패:", error);
      }
    },
    async openFeedRecord(record) {
      if (!record?.id) {
        console.error("피드 기록 열기 실패: record id가 없습니다.", record);
        return;
      }
      this.closeFeedDiaryPreview();
      try {
        const detail = await this.apiFetch(`/api/records/${record.id}/`);
        const card = this.apiRecordToSavedCard(this.mergePreviewRecord(record, detail));
        this.openSavedCard(card);
      } catch (error) {
        console.error("피드 기록 열기 실패:", error);
        const card = this.apiRecordToSavedCard(record);
        this.openSavedCard(card);
      }
    },
    async openFeedDiaryPreview(record) {
      this.isDiaryPreviewOpen = true;
      this.previewError = "";
      this.previewLoading = false;

      try {
        this.setDiaryPreviewFromRecord(record);
      } catch (error) {
        console.error("다이어리 미리보기 초기화 실패:", error);
        this.previewRecord = {
          title: this.recordDisplayTitle(record),
          author: record?.user_nickname || "",
          date: this.formatDisplayDate(record?.watched_date || ""),
          rating: record?.rating ?? 0,
          memo: record?.content || "",
        };
        this.previewPlacedItems = this.previewFallbackItems(this.previewRecord, "");
        this.previewMainImageSrc = "";
      }

      try {
        const detail = await this.apiFetch(`/api/records/${record.id}/`);
        this.setDiaryPreviewFromRecord(this.mergePreviewRecord(record, detail));
      } catch (error) {
        console.error("다이어리 미리보기 불러오기 실패:", error);
        this.previewLoading = false;
      }
    },
    closeFeedDiaryPreview() {
      this.isDiaryPreviewOpen = false;
      this.previewLoading = false;
      this.previewError = "";
      this.previewRecord = {};
      this.previewPlacedItems = [];
      this.previewMainImageSrc = "";
    },
    setDiaryPreviewFromRecord(record) {
      const cd = record?.canvas_data || {};
      const watchedDate = record?.watched_date ? this.formatDisplayDate(record.watched_date) : "";
      const previewImage = this.normalizeImageUrl(
        cd.main_image_src ||
        cd.mainImageSrc ||
        cd.imageSrc ||
        record?.work_poster ||
        record?.work?.poster_image ||
        record?.work?.cover_image ||
        record?.poster ||
        record?.image ||
        record?.imageSrc
      );
      const rawItems = Array.isArray(cd.placed_items) ? cd.placed_items : cd.placedItems;
      const baseItems = Array.isArray(rawItems) ? this.cloneForSave(rawItems) : [];

      this.previewRecord = {
        title: this.recordDisplayTitle(record),
        author: record?.user_nickname || "",
        date: watchedDate,
        rating: record?.rating ?? 0,
        memo: record?.content || cd.memo || cd.record?.memo || cd.analysis?.phrase || "",
      };
      this.previewMainImageSrc = previewImage;
      this.previewPlacedItems = baseItems.length > 0
        ? baseItems
        : this.previewFallbackItems(this.previewRecord, previewImage);
    },
    mergePreviewRecord(listRecord, detailRecord) {
      const listCanvas = listRecord?.canvas_data || {};
      const detailCanvas = detailRecord?.canvas_data || {};
      return {
        ...listRecord,
        ...detailRecord,
        work_title: detailRecord?.work_title || listRecord?.work_title,
        work_poster: detailRecord?.work_poster || listRecord?.work_poster,
        display_title: detailRecord?.display_title || listRecord?.display_title,
        title: detailRecord?.title || listRecord?.title,
        content: detailRecord?.content || listRecord?.content,
        user_nickname: detailRecord?.user_nickname || listRecord?.user_nickname,
        watched_date: detailRecord?.watched_date || listRecord?.watched_date,
        rating: detailRecord?.rating ?? listRecord?.rating,
        canvas_data: {
          ...listCanvas,
          ...detailCanvas,
          title: detailCanvas.title || listCanvas.title,
          anime_title: detailCanvas.anime_title || detailCanvas.animeTitle || listCanvas.anime_title || listCanvas.animeTitle,
          animeTitle: detailCanvas.animeTitle || detailCanvas.anime_title || listCanvas.animeTitle || listCanvas.anime_title,
          main_image_src: detailCanvas.main_image_src || detailCanvas.mainImageSrc || listCanvas.main_image_src || listCanvas.mainImageSrc,
          mainImageSrc: detailCanvas.mainImageSrc || detailCanvas.main_image_src || listCanvas.mainImageSrc || listCanvas.main_image_src,
          placed_items: detailCanvas.placed_items || detailCanvas.placedItems || listCanvas.placed_items || listCanvas.placedItems,
          placedItems: detailCanvas.placedItems || detailCanvas.placed_items || listCanvas.placedItems || listCanvas.placed_items,
        },
      };
    },
    previewFallbackItems(record, imageSrc) {
      const items = [];
      if (imageSrc) {
        items.push({
          id: "preview-main-image",
          type: "image",
          imageSrc,
          tone: "custom-image",
          x: 24,
          y: 24,
          width: 220,
          rotate: -3,
          scale: 1,
          zIndex: 1,
        });
      }
      const memoText = record.memo || `${record.title || "기록"}\n${record.rating ? `${record.rating} / 10` : ""}`.trim();
      items.push({
        id: "preview-memo",
        type: "text",
        text: memoText.length > 140 ? `${memoText.slice(0, 140)}…` : memoText,
        tone: "memo-text",
        x: imageSrc ? 56 : 32,
        y: imageSrc ? 32 : 34,
        width: 220,
        height: 150,
        rotate: 2,
        fontSize: 15,
        scale: 1,
        zIndex: 2,
      });
      return items;
    },
    formatFeedDate(dateStr) {
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
    },
    async checkAuth() {
      try {
        this.currentUser = await this.apiFetch("/api/auth/me/");
        this.resetProfileForm();
        this.loadRepresentativeBadges();
        this.loadUserStickers();
      } catch (error) {
        console.error("인증 확인 실패 — 로그인 필요:", error);
        this.currentUser = null;
      } finally {
        this.isCheckingAuth = false;
      }
    },
    loginRedirectUrl() {
      const { protocol, hostname, port } = window.location;
      const isViteDevServer = ["5173", "5174"].includes(port);
      if (isViteDevServer) {
        return `${protocol}//${hostname}:8000/deokkku/login/`;
      }
      return "/deokkku/login/";
    },
    async getCsrfToken(forceRefresh = false) {
      if (this.csrfToken && !forceRefresh) return this.csrfToken;
      const response = await fetch("/api/auth/csrf/", {
        credentials: "include",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) {
        const errorBody = await response.text();
        console.error("CSRF token request failed:", response.status, errorBody);
        throw new Error(`CSRF token request failed: ${response.status}`);
      }
      const data = await response.json();
      this.csrfToken = data.csrfToken || "";
      return this.csrfToken;
    },
    toggleProfileMenu() {
      this.showProfileMenu = !this.showProfileMenu;
    },
    closeProfileMenu() {
      this.showProfileMenu = false;
    },
    handleProfileOutsideClick(event) {
      if (!this.showProfileMenu) return;
      const menu = this.$refs.profileMenu;
      if (menu && !menu.contains(event.target)) {
        this.closeProfileMenu();
      }
    },
    handleGlobalKeydown(event) {
      if (event.key !== "Escape") return;
      this.closeProfileMenu();
      if (this.isProfileModalOpen) {
        this.closeProfileModal();
      }
      if (this.isBadgeModalOpen) {
        this.closeBadgeModal();
      }
      if (this.isDiaryPreviewOpen) {
        this.closeFeedDiaryPreview();
      }
    },
    openProfileModal() {
      this.resetProfileForm();
      this.isProfileModalOpen = true;
    },
    closeProfileModal() {
      this.isProfileModalOpen = false;
      this.resetProfileForm();
    },
    openBadgeModal() {
      this.isBadgeModalOpen = true;
    },
    closeBadgeModal() {
      this.isBadgeModalOpen = false;
    },
    badgeStorageKey() {
      return `deokkkuRepresentativeBadges:${this.currentUser?.email || "guest"}`;
    },
    loadRepresentativeBadges() {
      try {
        const stored = JSON.parse(localStorage.getItem(this.badgeStorageKey()) || "[]");
        this.selectedBadgeIds = Array.isArray(stored) ? stored.slice(0, 3) : [];
      } catch (error) {
        this.selectedBadgeIds = [];
      }
    },
    persistRepresentativeBadges() {
      try {
        localStorage.setItem(this.badgeStorageKey(), JSON.stringify(this.selectedBadgeIds.slice(0, 3)));
      } catch (error) {
        // 대표 뱃지는 화면 표시용이므로 저장 실패 시 현재 세션 상태만 유지합니다.
      }
    },
    toggleRepresentativeBadge(badge) {
      if (!badge.unlocked) return;
      if (this.selectedBadgeIds.includes(badge.id)) {
        this.selectedBadgeIds = this.selectedBadgeIds.filter((id) => id !== badge.id);
      } else {
        this.selectedBadgeIds = [...this.selectedBadgeIds, badge.id].slice(-3);
      }
      this.persistRepresentativeBadges();
    },
    getActivityStats() {
      const albums = Array.isArray(this.savedCards) ? this.savedCards.length : 0;
      const shares = Array.isArray(this.shareCards) ? this.shareCards.length : 0;
      return {
        records: albums,
        albums,
        shares,
        recent: Math.min(albums + shares, 9),
      };
    },
    getFavoriteGenres() {
      return [];
    },
    getUserBadges() {
      const stats = this.getActivityStats();
      const ratedCount = (this.savedCards || []).filter((card) => Number(card.rating || 0) > 0).length;
      return [
        {
          id: "first-record",
          icon: "🏆",
          label: "첫 기록 작성",
          description: "기록 1개 이상",
          unlocked: stats.records + stats.albums >= 1,
        },
        {
          id: "archive-collector",
          icon: "📚",
          label: "기록 수집가",
          description: "기록 5개 이상",
          unlocked: stats.records + stats.albums >= 5,
        },
        {
          id: "rating-master",
          icon: "⭐",
          label: "별점 마스터",
          description: "별점 기록 3개 이상",
          unlocked: ratedCount >= 3,
        },
        {
          id: "decoration-starter",
          icon: "🎨",
          label: "다꾸 입문자",
          description: "저장한 다이어리 1개 이상",
          unlocked: stats.albums >= 1,
        },
        {
          id: "steady-logger",
          icon: "📝",
          label: "꾸준한 기록러",
          description: "기록 10개 이상",
          unlocked: stats.records + stats.albums >= 10,
        },
      ];
    },
    resetProfileForm() {
      if (this.profilePreviewLocalUrl) {
        URL.revokeObjectURL(this.profilePreviewLocalUrl);
      }
      this.profilePreviewLocalUrl = "";
      this.profileForm = {
        nickname: this.currentUser?.nickname || "",
        profileImage: null,
        removeProfileImage: false,
      };
      this.profileStatus = { type: "", message: "" };
    },
    handleProfileImageChange(event) {
      const file = event.target.files?.[0] || null;
      if (this.profilePreviewLocalUrl) {
        URL.revokeObjectURL(this.profilePreviewLocalUrl);
      }
      this.profilePreviewLocalUrl = file ? URL.createObjectURL(file) : "";
      this.profileForm.profileImage = file;
      if (file) {
        this.profileForm.removeProfileImage = false;
      }
      this.profileStatus = { type: "", message: "" };
    },
    formatProfileDate(value) {
      if (!value) return "";
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return "";
      return date.toLocaleDateString("ko-KR", {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    },
    async updateProfile() {
      const nickname = this.profileForm.nickname.trim();
      if (!nickname) {
        this.profileStatus = { type: "error", message: "닉네임을 입력해주세요." };
        return;
      }

      this.isProfileSaving = true;
      this.profileStatus = { type: "", message: "" };
      try {
        const csrfToken = await this.getCsrfToken();
        const formData = new FormData();
        formData.append("nickname", nickname);
        formData.append("remove_profile_image", this.profileForm.removeProfileImage ? "true" : "false");
        if (this.profileForm.profileImage && !this.profileForm.removeProfileImage) {
          formData.append("profile_image", this.profileForm.profileImage);
        }

        const response = await fetch("/api/auth/me/update/", {
          method: "PATCH",
          credentials: "include",
          headers: { "X-CSRFToken": csrfToken },
          body: formData,
        });
        if (!response.ok) {
          const responseBody = await response.text();
          let detail = responseBody;
          try {
            const errorData = JSON.parse(responseBody);
            detail = errorData.detail || JSON.stringify(errorData);
          } catch (error) {
            // Keep the raw response body when the server does not return JSON.
          }
          throw new Error(`프로필 저장에 실패했습니다. (${response.status}) ${detail}`);
        }

        this.currentUser = await response.json();
        this.resetProfileForm();
        this.profileStatus = { type: "success", message: "프로필이 저장되었습니다." };
      } catch (error) {
        this.profileStatus = { type: "error", message: error.message || "프로필 저장에 실패했습니다." };
      } finally {
        this.isProfileSaving = false;
      }
    },
    async apiFetch(url, options = {}, _retried = false) {
      const method = (options.method || "GET").toUpperCase();
      const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      };
      const needsCsrf = !["GET", "HEAD", "OPTIONS", "TRACE"].includes(method);
      if (needsCsrf) {
        headers["X-CSRFToken"] = await this.getCsrfToken();
      }

      const response = await fetch(url, {
        credentials: "include",
        ...options,
        headers,
      });

      if (!response.ok) {
        const responseBody = await response.text();

        // CSRF 403 → 토큰 갱신 후 1회 재시도
        if (response.status === 403 && needsCsrf && !_retried && responseBody.includes("CSRF")) {
          this.csrfToken = "";
          return this.apiFetch(url, options, true);
        }

        let detail = responseBody;
        try {
          const errorData = JSON.parse(responseBody);
          detail = errorData.detail || JSON.stringify(errorData);
        } catch (error) {
          // Keep the raw response body when the server does not return JSON.
        }
        console.error("API request failed:", response.status, detail);
        throw new Error(`API request failed: ${response.status} ${detail}`);
      }
      // 204 No Content (DELETE 등) — 본문 없음
      if (response.status === 204) return null;
      return response.json();
    },
    async logout() {
      if (this.isLoggingOut) return;
      this.isLoggingOut = true;
      try {
        // CSRF 토큰 강제 갱신 후 로그아웃
        this.csrfToken = "";
        await this.apiFetch("/api/auth/logout/", {
          method: "POST",
          body: JSON.stringify({}),
        });
      } catch (error) {
        console.error("로그아웃 요청 실패 (무시):", error);
      }
      // 성공/실패 관계없이 로컬 상태 초기화
      this.currentUser = null;
      this.csrfToken = "";
      this.loginForm = { email: '', password: '', nickname: '', error: '', loading: false, mode: 'login' };
      this.isLoggingOut = false;
    },
    navigatePage(page) {
      // "기록 작성" 클릭 시: 작성 중인 내용이 없으면 새 기록 모달 열기
      if (page === "기록 작성" && !this.hasRecordInProgress) {
        this.openRecordModal("create");
        return;
      }
      this.activePage = page;
      try { localStorage.setItem("deokkku:activePage", page); } catch (e) { /* ignore */ }
    },
    openProfilePageFromDropdown() {
      this.navigatePage(this.nav[4]);
      this.closeProfileMenu();
    },
    openAlbumFromToast() {
      this.navigatePage("내 앨범");
      this.toastMessage = "";
    },
    navIcon(item) {
      const icons = {
        홈: "⌂",
        "내 앨범": "▣",
        "기록 작성": "✎",
        리뷰: "★",
        마이페이지: "◉",
        "공유 페이지": "↗",
      };
      return icons[item] || "•";
    },
    stars(score) {
      const filled = Math.max(0, Math.min(5, Math.round(score / 2)));
      return "★".repeat(filled) + "☆".repeat(5 - filled);
    },
    placementStyle(item) {
      return {
        left: `${item.x}%`,
        top: `${item.y}%`,
        width: item.width ? `${item.width}px` : null,
        height: item.height ? `${item.height}px` : null,
        zIndex: item.zIndex || 1,
        "--item-scale": (item.type === "text" || item.type === "image" || item.type === "bubble") ? 1 : item.scale || 1,
      };
    },
    stickerStyle(item) {
      const scale = (item.type === "text" || item.type === "image" || item.type === "bubble") ? 1 : item.scale || 1;
      return {
        transform: `rotate(${item.rotate || 0}deg) scale(${scale})`,
      };
    },
    previewTextStyle(item) {
      return {
        fontSize: `${item.fontSize || 15}px`,
        color: item.textColor || "#342a3f",
      };
    },
    canvasRect() {
      return this.$refs.canvasLayer.getBoundingClientRect();
    },
    clamp(value, min, max) {
      return Math.max(min, Math.min(max, value));
    },
    cloneForSave(value) {
      return JSON.parse(JSON.stringify(value));
    },
    normalizeImageUrl(value) {
      const rawValue = String(value || "").trim();
      if (!rawValue) return "";
      if (rawValue.startsWith("/") || rawValue.startsWith("data:image/")) return rawValue;

      const markdownMatch = rawValue.match(/\[[^\]]*\]\((https?:\/\/[^)]+)\)/);
      if (markdownMatch) return markdownMatch[1];

      const urlMatch = rawValue.match(/https?:\/\/[^\s)]+/);
      return urlMatch ? urlMatch[0] : "";
    },
    recordPreviewShareImage(record) {
      return this.normalizeImageUrl(
        record?.share_card_image ||
        record?.share_image_url ||
        record?.share_card_url ||
        record?.latest_share_card?.image_url ||
        record?.share_card?.image_url
      );
    },
    recordPreviewImage(record) {
      return this.recordPreviewCandidates(record)[0] || "";
    },
    recordPreviewCandidates(record) {
      const canvasData = record?.canvas_data || {};
      return [
        this.recordPreviewShareImage(record),
        canvasData.main_image_src,
        record?.work_poster,
        record?.work?.poster_image,
        record?.work?.cover_image,
        record?.poster,
        record?.image,
      ]
        .map((value) => this.normalizeImageUrl(value))
        .filter(Boolean)
        .filter((value, index, list) => list.indexOf(value) === index);
    },
    currentRecordPreviewImage(record) {
      if (this.brokenRecordPreviewImages[record.id]) return "";
      const candidates = this.recordPreviewCandidates(record);
      const index = this.recordPreviewCandidateIndexes[record.id] || 0;
      return candidates[index] || "";
    },
    handleRecordPreviewImageError(record) {
      const candidates = this.recordPreviewCandidates(record);
      const currentIndex = this.recordPreviewCandidateIndexes[record.id] || 0;
      const nextIndex = currentIndex + 1;
      if (nextIndex < candidates.length) {
        this.recordPreviewCandidateIndexes = {
          ...this.recordPreviewCandidateIndexes,
          [record.id]: nextIndex,
        };
        return;
      }
      this.brokenRecordPreviewImages = {
        ...this.brokenRecordPreviewImages,
        [record.id]: true,
      };
    },
    recordPreviewClass(record) {
      if (this.recordPreviewShareImage(record)) return "record-preview--share";
      const canvasData = record?.canvas_data || {};
      if ((Array.isArray(canvasData.placed_items) && canvasData.placed_items.length > 0) || canvasData.main_image_src) {
        return "record-preview--diary";
      }
      if (this.recordPreviewCandidates(record).length > 0) return "record-preview--poster";
      return "record-preview--empty";
    },
    isPlaceholderTitle(value) {
      const title = String(value || "").trim();
      return !title || title === "제목 없는 기록";
    },
    recordDisplayTitle(record) {
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
      const title = candidates.find((value) => !this.isPlaceholderTitle(value));
      return title || "제목 없는 기록";
    },
    recordPreviewText(record) {
      const source = record?.content || record?.memo || record?.canvas_data?.analysis?.phrase || record?.work_title || "기록의 분위기를 담은 미리보기입니다.";
      return String(source).replace(/\s+/g, " ").trim();
    },
    canvasSnapshot() {
      return {
        placedItems: this.cloneForSave(this.placedItems),
        mainImageSrc: this.mainImageSrc,
        selectedDecorationId: this.selectedDecorationId,
      };
    },
    pushUndoState() {
      this.undoHistory.push(this.canvasSnapshot());
      if (this.undoHistory.length > 50) {
        this.undoHistory.shift();
      }
    },
    undoLastCanvasChange() {
      const previousState = this.undoHistory.pop();
      if (!previousState) return;
      this.placedItems = this.cloneForSave(previousState.placedItems);
      this.mainImageSrc = previousState.mainImageSrc || "";
      this.selectedDecorationId = previousState.selectedDecorationId || null;
      this.syncLayerZIndex();
    },
    currentMaxLayerZIndex() {
      return this.placedItems.reduce((maxZIndex, item) => Math.max(maxZIndex, item.zIndex || 0), 0);
    },
    nextLayerZIndex() {
      this.layerZIndex = Math.max(this.layerZIndex, this.currentMaxLayerZIndex()) + 1;
      return this.layerZIndex;
    },
    syncLayerZIndex() {
      this.layerZIndex = this.currentMaxLayerZIndex();
    },
    bringDecorationToFront(id) {
      const item = this.placedItems.find((decoration) => decoration.id === id);
      if (!item) return;
      item.zIndex = this.nextLayerZIndex();
    },
    selectDecoration(id) {
      this.selectedDecorationId = id;
      this.bringDecorationToFront(id);
    },
    clearDecorationSelection() {
      this.selectedDecorationId = null;
    },
    _findNextGridSlot() {
      // 기존 스티커들이 차지하는 그리드 슬롯을 파악하고 비어있는 첫 슬롯 반환
      var cols = 8;
      var cellW = 8;    // % 단위
      var cellH = 8;
      var startX = 6;
      var startY = 18;
      var stickers = this.placedItems.filter(function(i) { return i.type !== 'text'; });
      var occupied = {};
      for (var i = 0; i < stickers.length; i++) {
        var s = stickers[i];
        // 현재 위치에서 가장 가까운 그리드 슬롯 계산
        var c = Math.round((s.x - startX) / cellW);
        var r = Math.round((s.y - startY) / cellH);
        if (c >= 0 && c < cols && r >= 0) {
          occupied[r + ',' + c] = true;
        }
      }
      // 비어있는 첫 슬롯 찾기
      for (var slot = 0; slot < 200; slot++) {
        var col = slot % cols;
        var row = Math.floor(slot / cols);
        if (!occupied[row + ',' + col]) {
          return { x: startX + col * cellW, y: startY + row * cellH };
        }
      }
      return { x: startX, y: startY };
    },
    bubbleEditorStyle(item) {
      var style = {};
      if (item.bgColor) style.background = item.bgColor;
      if (item.borderColor) {
        style.borderColor = item.borderColor;
        style['--bubble-border'] = item.borderColor;
      }
      return style;
    },
    changeBubbleFontSize(delta) {
      var item = this.selectedBubbleItem;
      if (!item) return;
      var size = (item.fontSize || 14) + delta;
      if (size < 10) size = 10;
      if (size > 36) size = 36;
      item.fontSize = size;
    },
    addDecoration(sticker) {
      console.log('[DEBUG] addDecoration called:', sticker, 'placedItems before:', this.placedItems.length);
      this.pushUndoState();
      const nextId = Date.now();
      var pos = this._findNextGridSlot();

      // 말풍선 타입: 텍스트 편집 가능
      if (sticker.bubbleType) {
        const nextItem = {
          id: nextId,
          type: "bubble",
          bubbleType: sticker.bubbleType,  // "normal" or "thought"
          tone: sticker.tone,
          text: "",
          icon: sticker.icon,
          x: pos.x,
          y: pos.y,
          rotate: 0,
          scale: 1,
          width: 180,
          height: 100,
          fontSize: 14,
          zIndex: this.nextLayerZIndex(),
        };
        this.placedItems.push(nextItem);
        this.selectedDecorationId = nextId;
        return;
      }

      const nextItem = {
        id: nextId,
        icon: sticker.icon,
        tone: sticker.tone,
        imageSrc: sticker.imageSrc || null,
        x: pos.x,
        y: pos.y,
        rotate: 0,
        scale: sticker.imageSrc ? 0.72 : sticker.icon.length > 1 ? 0.86 : 1.08,
        zIndex: this.nextLayerZIndex(),
      };
      this.placedItems.push(nextItem);
      this.selectedDecorationId = nextId;
    },
    addTextMemo() {
      this.pushUndoState();
      const nextId = Date.now();
      this.placedItems.push({
        id: nextId,
        type: "text",
        text: "새 메모",
        tone: "memo-text",
        x: 38 + (this.placedItems.length * 9) % 35,
        y: 34 + (this.placedItems.length * 7) % 36,
        rotate: -4 + (this.placedItems.length * 3) % 9,
        scale: 1,
        fontSize: 15,
        width: 190,
        height: 150,
        zIndex: this.nextLayerZIndex(),
      });
      this.selectedDecorationId = nextId;
    },
    async handleImageUpload(event) {
      const file = event.target.files?.[0];
      if (!file) return;
      event.target.value = "";

      try {
        const csrfToken = await this.getCsrfToken();
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch("/api/records/upload/", {
          method: "POST",
          credentials: "include",
          headers: { "X-CSRFToken": csrfToken },
          body: formData,
        });
        if (!response.ok) {
          const err = await response.text();
          throw new Error(`이미지 업로드 실패: ${response.status} ${err}`);
        }
        const data = await response.json();

        this.pushUndoState();
        const nextId = Date.now();
        const nextItem = {
          id: nextId,
          type: "image",
          icon: "",
          imageSrc: data.url,  // 백엔드 protected URL
          tone: "custom-image",
          x: 31 + (this.placedItems.length * 7) % 38,
          y: 24 + (this.placedItems.length * 9) % 44,
          width: 200,
          rotate: 0,
          scale: 1,
          zIndex: this.nextLayerZIndex(),
        };
        this.placedItems.push(nextItem);
        this.mainImageSrc = data.url;
        this.selectedDecorationId = nextId;
      } catch (error) {
        console.error(error);
        alert("이미지 업로드에 실패했습니다. 다시 시도해주세요.");
      }
    },
    removeSticker(id) {
      this.pushUndoState();
      this.placedItems = this.placedItems.filter((sticker) => sticker.id !== id);
      if (this.selectedDecorationId === id) {
        this.selectedDecorationId = null;
      }
    },
    runCanvasTool(tool) {
      if (tool.action === "memo") {
        this.addTextMemo();
      }
    },
    startDrag(event, item) {
      if (!event.target.closest("textarea")) {
        event.preventDefault();
      }
      this.selectDecoration(item.id);
      const rect = this.canvasRect();
      this.dragging = {
        item,
        rect,
        offsetX: event.clientX - (rect.left + (item.x / 100) * rect.width),
        offsetY: event.clientY - (rect.top + (item.y / 100) * rect.height),
      };
    },
    startResize(event, item) {
      event.preventDefault();
      this.selectDecoration(item.id);
      if (item.type === "text" || item.type === "bubble") {
        this.resizing = {
          item, mode: "box",
          startX: event.clientX, startY: event.clientY,
          startWidth: item.width || (item.type === "bubble" ? 180 : 190),
          startHeight: item.height || (item.type === "bubble" ? 100 : 150),
        };
      } else if (item.type === "image") {
        this.resizing = {
          item, mode: "image-width",
          startX: event.clientX, startWidth: item.width || 200,
        };
      } else {
        this.resizing = {
          item, mode: "scale",
          startX: event.clientX, startY: event.clientY,
          startScale: item.scale || 1,
        };
      }
    },
    startRotate(event, item) {
      event.preventDefault();
      this.selectDecoration(item.id);
      const rect = event.currentTarget.parentElement.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      this.rotating = {
        item,
        centerX,
        centerY,
        startAngle: Math.atan2(event.clientY - centerY, event.clientX - centerX),
        startRotate: item.rotate || 0,
      };
    },
    angleToDegrees(radians) {
      return radians * 180 / Math.PI;
    },
    handlePointerMove(event) {
      if (this.dragging) {
        const { item, rect, offsetX, offsetY } = this.dragging;
        const nextX = ((event.clientX - offsetX - rect.left) / rect.width) * 100;
        const nextY = ((event.clientY - offsetY - rect.top) / rect.height) * 100;
        item.x = this.clamp(nextX, 2, 94);
        item.y = this.clamp(nextY, 3, 90);
      }

      if (this.resizing) {
        const { item, mode, startX, startY } = this.resizing;
        if (mode === "box") {
          item.width = this.clamp(this.resizing.startWidth + event.clientX - startX, 120, 440);
          item.height = this.clamp(this.resizing.startHeight + event.clientY - startY, 100, 380);
        } else if (mode === "image-width") {
          item.width = this.clamp(this.resizing.startWidth + event.clientX - startX, 60, 500);
        } else {
          const delta = Math.max(event.clientX - startX, event.clientY - startY);
          item.scale = this.clamp(this.resizing.startScale + delta / 140, 0.45, 2.8);
        }
      }

      if (this.rotating) {
        const { item, centerX, centerY, startAngle, startRotate } = this.rotating;
        const currentAngle = Math.atan2(event.clientY - centerY, event.clientX - centerX);
        item.rotate = Math.round(startRotate + this.angleToDegrees(currentAngle - startAngle));
      }
    },
    stopPointerWork() {
      this.dragging = null;
      this.resizing = null;
      this.rotating = null;
    },
    openRecordModal(mode = "create") {
      this.recordModalMode = mode;
      this.recordForm = {
        title: mode === "edit" ? this.currentRecord.title : "",
        date: mode === "edit" ? this.formatInputDate(this.currentRecord.date) : new Date().toISOString().slice(0, 10),
        rating: mode === "edit" ? this.currentRecord.rating : 0,
        workId: mode === "edit" ? (this.currentRecord.workId || null) : null,
      };
      this.isRecordModalOpen = true;
    },
    closeRecordModal() {
      this.isRecordModalOpen = false;
    },
    formatDisplayDate(value) {
      if (!value) return "";
      return value.replaceAll("-", ".");
    },
    formatInputDate(value) {
      if (!value) return new Date().toISOString().slice(0, 10);
      return value.replaceAll(".", "-");
    },
    createBlankRecord() {
      this.currentRecord = {
        title: this.recordForm.title || "제목 없는 기록",
        date: this.formatDisplayDate(this.recordForm.date),
        rating: this.recordForm.rating,
        memo: "새롭게 작성한 감상 기록입니다.",
        tags: [],
      };
      if (this.recordModalMode !== "edit") {
        // 신규 기록이면 백엔드 ID 초기화 (저장 시 POST)
        this.currentRecordId = null;
        this.recordVisibility = "public";
        this.recordTitle = "";
        this.placedItems = [];
        this.mainImageSrc = "";
        this.selectedDecorationId = null;
        this.undoHistory = [];
        this.syncLayerZIndex();
      }
      this.activePage = "기록 작성";
      this.isRecordModalOpen = false;
    },

    // ── 백엔드 Record → 프론트 savedCard 포맷 변환 헬퍼 ──────────────────
    apiRecordToSavedCard(record) {
      const cd = record.canvas_data || {};
      const placedItems = Array.isArray(cd.placed_items)
        ? cd.placed_items
        : (Array.isArray(cd.placedItems) ? cd.placedItems : []);
      const recordTitle = (cd.title || "").trim();
      const workTitle = record.work?.title_ko || record.work?.title || record.work_title || "";
      const title = (cd.anime_title || cd.animeTitle || "").trim()
        || workTitle
        || this.recordDisplayTitle(record);
      const watchedDate = record.watched_date
        ? record.watched_date.replaceAll("-", ".")
        : "";
      const imageCandidates = [
        record.work_poster,
        record.work?.poster_image,
        record.work?.cover_image,
      ]
        .map((value) => this.normalizeImageUrl(value))
        .filter(Boolean)
        .filter((value, index, list) => list.indexOf(value) === index);
      const imageSrc = imageCandidates[0] || "";

      return {
        id: record.id,
        title,
        recordTitle,
        date: watchedDate,
        rating: record.rating ?? 0,
        imageSrc,
        imageCandidates,
        workId: record.work?.id || record.work || null,
        visibility: record.visibility || "private",
        memoCount: placedItems.filter((i) => i.type === "text").length,
        stickerCount: placedItems.filter((i) => i.type !== "text").length,
        savedAt: record.created_at,
        snapshot: {
          record: {
            title,
            date: watchedDate,
            rating: record.rating ?? 0,
            memo: record.content || cd.memo || cd.record?.memo || "",
            tags: [],
            workId: record.work?.id || record.work || null,
          },
          placedItems,
          mainImageSrc: this.normalizeImageUrl(cd.main_image_src || cd.mainImageSrc),
          analysis: cd.analysis || null,
        },
      };
    },

    // ── 기록 목록 불러오기 (GET /api/records/) ────────────────────────────
    async loadSavedCards() {
      try {
        const data = await this.apiFetch("/api/records/?mine=1");
        const results = Array.isArray(data) ? data : (data.results || []);
        this.savedCards = results.map((r) => this.apiRecordToSavedCard(r));
      } catch (error) {
        console.error("기록 목록 불러오기 실패:", error);
        this.savedCards = [];
      }
    },

    // ── 홈 피드: public 게시글 불러오기 ──
    async loadFeedRecords() {
      this.isFeedLoading = true;
      try {
        const data = await this.apiFetch("/api/records/");
        const results = Array.isArray(data) ? data : (data.results || []);
        this.recordPreviewCandidateIndexes = {};
        this.brokenRecordPreviewImages = {};
        this.feedRecords = results;
      } catch (error) {
        console.error("피드 불러오기 실패:", error);
        this.feedRecords = [];
      } finally {
        this.isFeedLoading = false;
      }
    },

    // ── 저장 (신규: POST / 수정: PATCH) ──────────────────────────────────
    async confirmCloseRecord() {
      // 내용이 없으면 바로 닫기
      if (this.isCanvasEmpty && !this.currentRecordId) {
        this.closeRecord();
        return;
      }
      // 저장 확인 다이얼로그
      var choice = confirm("저장하시겠습니까?\n\n확인: 저장 후 내 앨범으로 이동\n취소: 저장하지 않고 내 앨범으로 이동");
      if (choice) {
        await this.saveCard();
      }
      this.closeRecord();
    },
    closeRecord() {
      this.placedItems = [];
      this.mainImageSrc = "";
      this.selectedDecorationId = null;
      this.currentRecordId = null;
      this.recordTitle = "";
      this.undoHistory = [];
      this._dirty = false;
      this.currentRecord = {
        title: "새 감상 기록",
        date: "2026.05.18",
        rating: 0,
        memo: "좋아하는 장면과 감정을 자유롭게 남겨보세요.",
        tags: [],
      };
      this.navigatePage("내 앨범");
    },
    async saveCard() {
      const now = Date.now();
      if (now - this.lastSaveAt < 350 || this.isSaving) return;
      this.lastSaveAt = now;
      this.isSaving = true;

      try {
        const animeTitle = (this.currentRecord.title || this.recordForm.title || "").trim() || "제목 없는 기록";
        const payload = {
          ...(this.recordForm.workId ? { work_id: this.recordForm.workId } : {}),
          title: this.recordTitle.trim() || animeTitle,
          work_title: animeTitle,
          anime_title: animeTitle,
          rating: this.currentRecord.rating ?? null,
          watched_date: this.formatInputDate(this.currentRecord.date) || null,
          content: this.currentRecord.memo || "",
          canvas_data: {
            title: this.recordTitle,
            anime_title: animeTitle,
            placed_items: this.cloneForSave(this.placedItems),
            main_image_src: this.mainImageSrc,
            analysis: this.cloneForSave(this.ai),
          },
          status: "published",
          visibility: this.recordVisibility,
        };

        let record;
        if (this.currentRecordId) {
          // 기존 기록 수정 (PATCH)
          record = await this.apiFetch(`/api/records/${this.currentRecordId}/`, {
            method: "PATCH",
            body: JSON.stringify(payload),
          });
          const updated = this.apiRecordToSavedCard(record);
          const idx = this.savedCards.findIndex((c) => c.id === this.currentRecordId);
          if (idx !== -1) this.savedCards.splice(idx, 1, updated);
          else this.savedCards.unshift(updated);
        } else {
          // 새 기록 생성 (POST)
          record = await this.apiFetch("/api/records/", {
            method: "POST",
            body: JSON.stringify(payload),
          });
          this.currentRecordId = record.id;
          this.savedCards.unshift(this.apiRecordToSavedCard(record));
        }

        this.toastMessage = "저장되었습니다";
        this._dirty = false;
        this._clearAutosave();
        this.loadFeedRecords();
      } catch (error) {
        console.error("저장 실패:", error);
        this.toastMessage = "저장에 실패했습니다. 다시 시도해주세요.";
      } finally {
        this.isSaving = false;
      }
    },

    // ── 저장된 카드 열기 ──────────────────────────────────────────────────
    openSavedCard(card) {
      this.currentRecord = this.cloneForSave(
        card.snapshot?.record || {
          title: card.title,
          date: card.date,
          rating: card.rating,
          memo: "",
          tags: [],
        }
      );
      this.placedItems = this.cloneForSave(card.snapshot?.placedItems || []);
      this.mainImageSrc = card.snapshot?.mainImageSrc || "";
      this.selectedDecorationId = null;
      this.currentRecordId = card.id;  // 수정 모드 — 저장 시 PATCH
      this.recordVisibility = card.visibility || "private";
      this.recordTitle = card.recordTitle || card.title || "";
      this.activePage = "기록 작성";
      this.toastMessage = "";
      this.undoHistory = [];
      this.syncLayerZIndex();
      if (card.snapshot?.analysis) {
        this.ai = this.cloneForSave(card.snapshot.analysis);
      }
      this.$nextTick(() => { this._dirty = false; });
    },

    // ── 기록 삭제 (DELETE /api/records/{id}/) ────────────────────────────
    async deleteSavedCard(cardId) {
      try {
        await this.apiFetch(`/api/records/${cardId}/`, { method: "DELETE" });
      } catch (error) {
        // 404 = 이미 DB에서 삭제된 레코드 → 프론트에서도 제거
        if (!error.message?.includes("404")) {
          console.error("삭제 실패:", error);
          alert("삭제에 실패했습니다. 다시 시도해주세요.");
          return;
        }
      }
      this.savedCards = this.savedCards.filter((card) => card.id !== cardId);
      if (this.currentRecordId === cardId) {
        this.currentRecordId = null;
      }
    },

    // ── 스티커 API ────────────────────────────────────────────────────────

    async loadUserStickers() {
      try {
        const data = await this.apiFetch('/api/records/stickers/');
        const categoryMap = {
          sticker: '스티커', frame: '프레임', bubble: '말풍선',
        };
        this.userStickers = data.map((item) => {
          var tone = item.sticker.tone || '';
          // 이미지가 있고 tone에 sticker-image가 없으면 추가 (포토카드 프레임 방지)
          if (item.sticker.image_url && tone.indexOf('sticker-image') === -1) {
            tone = ('sticker-image ' + tone).trim();
          }
          return {
            id: item.sticker.id,
            icon: item.sticker.emoji_fallback || '⬡',
            label: item.sticker.name,
            tone: tone,
            category: categoryMap[item.sticker.category] || '스티커',
            imageSrc: item.sticker.image_url || null,
          };
        });
        this.stickersLoaded = true;
      } catch (error) {
        console.error('스티커 로드 실패:', error);
        this.stickersLoaded = false;
      }
    },

    async handleStickerUpload({ file, category }) {
      var formData = new FormData();
      formData.append('image', file);
      formData.append('category', category);
      formData.append('name', file.name.replace(/\.[^.]+$/, ''));
      try {
        var csrfToken = await this.getCsrfToken();
        var resp = await fetch('/api/records/stickers/upload/', {
          method: 'POST',
          headers: { 'X-CSRFToken': csrfToken },
          credentials: 'include',
          body: formData,
        });
        if (!resp.ok) throw new Error('업로드 실패');
        await this.loadUserStickers();
        this.toastMessage = '스티커가 추가되었습니다!';
      } catch (error) {
        console.error('스티커 업로드 실패:', error);
        this.toastMessage = '스티커 업로드에 실패했습니다.';
      }
    },

    // ── 공유 카드 ─────────────────────────────────────────────────────────

    // 공유 모달 열기
    openShareModal() {
      if (!this.currentRecordId) {
        this.toastMessage = '먼저 기록을 저장한 뒤 공유할 수 있습니다.';
        return;
      }
      this.shareCardError = '';
      this.isShareModalOpen = true;
      this.loadShareCards(this.currentRecordId);
    },

    // 공유 모달 닫기
    closeShareModal() {
      this.isShareModalOpen = false;
    },

    // AI 공유 카드 생성
    async generateShareCard() {
      if (!this.currentRecordId) {
        this.shareCardError = '기록을 먼저 저장해주세요.';
        return;
      }
      this.isGeneratingCard = true;
      this.shareCardError = '';
      try {
        const data = await this.apiFetch(
          `/api/shares/${this.currentRecordId}/generate/`,
          { method: 'POST', body: JSON.stringify({}) }
        );
        this.shareCards.unshift(data);
      } catch (error) {
        console.error('공유 카드 생성 실패:', error);
        this.shareCardError = '카드 생성에 실패했습니다. 다시 시도해주세요.';
      } finally {
        this.isGeneratingCard = false;
      }
    },

    // 기존 공유 카드 목록 조회
    async loadShareCards(recordId) {
      try {
        const data = await this.apiFetch(`/api/shares/${recordId}/`);
        this.shareCards = Array.isArray(data) ? data : (data.results || []);
      } catch (error) {
        console.error('공유 카드 목록 조회 실패:', error);
        this.shareCards = [];
      }
    },
    // 공유 카드 이미지를 파일로 다운로드
    async downloadShareImage() {
      if (!this.latestShareCard?.image_url) return;
      try {
        const resp = await fetch(this.latestShareCard.image_url);
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        const title = (this.currentRecord.title || 'deokkku').replace(/[\\/:*?"<>|]/g, '').replace(/\s+/g, '_');
        link.href = url;
        link.download = `${title}_sharecard.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
      } catch (err) {
        console.error('이미지 다운로드 실패:', err);
        alert('이미지 다운로드에 실패했습니다.');
      }
    },

    // ── SPA 로그인 / 회원가입 ──
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
        this.currentUser = user;
        this.resetProfileForm();
        this.loadRepresentativeBadges();
        this.loadUserStickers();
        this.loadSavedCards();
        this.loadFeedRecords();
        this.loginForm = { email: '', password: '', nickname: '', error: '', loading: false, mode: 'login' };
      } catch (error) {
        this.loginForm.error = error.message || '회원가입에 실패했습니다.';
      } finally {
        this.loginForm.loading = false;
      }
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
        this.currentUser = user;
        this.resetProfileForm();
        this.loadRepresentativeBadges();
        this.loadUserStickers();
        this.loadSavedCards();
        this.loadFeedRecords();
        this.loginForm = { email: '', password: '', error: '', loading: false, mode: 'login' };
      } catch (error) {
        this.loginForm.error = '이메일 또는 비밀번호가 올바르지 않습니다.';
      } finally {
        this.loginForm.loading = false;
      }
    },

    // ── 임시저장 (새로고침/브라우저 종료 대비) ──
    _autosaveKey() {
      return `deokkkuAutosave:${this.currentUser?.email || "guest"}`;
    },
    _autosaveDraft() {
      try {
        const data = {
          currentRecord: JSON.parse(JSON.stringify(this.currentRecord)),
          placedItems: JSON.parse(JSON.stringify(this.placedItems)),
          mainImageSrc: this.mainImageSrc,
          currentRecordId: this.currentRecordId,
          activePage: this.activePage,
          savedAt: new Date().toISOString(),
        };
        localStorage.setItem(this._autosaveKey(), JSON.stringify(data));
      } catch (e) {
        console.warn("임시저장 실패:", e);
      }
    },
    _clearAutosave() {
      try { localStorage.removeItem(this._autosaveKey()); } catch (e) { /* ignore */ }
    },
    _checkAutosaveRestore() {
      try {
        const raw = localStorage.getItem(this._autosaveKey());
        if (!raw) return;
        const saved = JSON.parse(raw);
        if (!saved?.currentRecord) { this._clearAutosave(); return; }

        // 기록 작성 중이 아니었으면 복원 불필요
        if (saved.activePage !== "기록 작성") { this._clearAutosave(); return; }

        // placedItems가 비어있으면 복원할 의미 없음
        const hasWork = (saved.placedItems?.length > 0) || saved.mainImageSrc;
        if (!hasWork) { this._clearAutosave(); return; }

        const title = saved.currentRecord.title || "제목 없음";
        const when = saved.savedAt ? new Date(saved.savedAt).toLocaleString("ko-KR") : "";

        if (confirm(`작성 중이던 기록이 있습니다.\n\n"${title}" (${when})\n\n복원하시겠습니까?\n[확인] 복원  /  [취소] 삭제`)) {
          this.currentRecord = saved.currentRecord;
          this.placedItems = Array.isArray(saved.placedItems) ? saved.placedItems : [];
          this.mainImageSrc = saved.mainImageSrc || "";
          this.currentRecordId = saved.currentRecordId || null;
          this.activePage = "기록 작성";
          this.$nextTick(() => { this._dirty = true; });
        }
        this._clearAutosave();
      } catch (e) {
        console.warn("임시저장 복원 실패:", e);
        this._clearAutosave();
      }
    },
  },
};
</script>
