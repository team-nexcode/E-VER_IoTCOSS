<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Bell, Search, User, Zap } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const router = useRouter() // 라우터 사용
const hasNotification = ref(false) // 알람 여부
const unreadCount = ref(0) // 읽지 않은 알람 개수

// 서버에서 알람 상태 가져오기
async function fetchNotifications() {
  try {
    const res = await fetch('/api/notifications/unread-count') // 실제 API 주소로 변경
    if (res.ok) {
      const data = await res.json()
      unreadCount.value = data.unreadCount
      hasNotification.value = unreadCount.value > 0
    } else {
      hasNotification.value = false
      unreadCount.value = 0
    }
  } catch (error) {
    console.error('알람 가져오기 실패:', error)
    hasNotification.value = false
    unreadCount.value = 0
  }
}

onMounted(() => {
  fetchNotifications()
  // 10초마다 새로고침
  setInterval(fetchNotifications, 10000)
})
</script>

<template>
  <header class="fixed top-0 left-0 right-0 h-[60px] bg-[#111827] border-b border-gray-800 flex items-center justify-between px-6 z-50">
    <!-- 좌측: 로고 + 시스템 이름 (클릭 시 대시보드로 이동) -->
    <button
      type="button"
      class="flex items-center gap-3 text-left hover:opacity-95 active:opacity-90 transition-opacity"
      @click="router.push('/')"
      aria-label="대시보드로 이동"
    >
      <div class="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center">
        <Zap class="w-5 h-5 text-white" />
      </div>
      <div>
        <h1 class="text-base font-bold text-white leading-tight">E-VER</h1>
        <p class="text-[10px] text-gray-500 leading-tight">Energy Saver</p>
      </div>
    </button>

    <!-- 우측: 검색, 알림, 프로필 -->
    <div class="flex items-center gap-4">
      <!-- 검색 -->
      <div class="hidden md:flex items-center bg-gray-800 rounded-lg px-3 py-3 gap-2">
        <Search class="w-5 h-5 text-gray-500" />
        <input
          type="text"
          placeholder="검색..."
          class="bg-transparent text-sm text-gray-300 outline-none w-48 placeholder-gray-600 h-8"
        />
      </div>

      <!-- 알림 벨 -->
      <button
        class="relative p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
        @click="router.push('/alerts')"
      >
        <Bell class="w-5 h-5" />
        <span
          v-if="hasNotification"
          class="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full"
        />
      </button>

      <!-- 사용자 프로필 -->
      <button class="flex items-center gap-2 px-3 py-1.5 hover:bg-gray-800 rounded-lg transition-colors">
        <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
          <User class="w-4 h-4 text-white" />
        </div>
        <span class="text-sm text-gray-300 hidden sm:block">관리자</span>
      </button>
    </div>
  </header>
</template>
