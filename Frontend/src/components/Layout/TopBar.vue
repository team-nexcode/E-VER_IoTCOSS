<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Bell, Search, User } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const router = useRouter()
const hasNotification = ref(false)
const unreadCount = ref(0)

// 알림 기능 로직 (기존과 동일)
async function fetchNotifications() {
  return;
  try {
    const res = await fetch('/api/notifications/unread-count')
    if (res.ok) {
      const data = await res.json()
      unreadCount.value = data.unreadCount
      hasNotification.value = unreadCount.value > 0
    }
  } catch (error) {
    console.error('알람 가져오기 실패:', error)
  }
}

onMounted(() => {
  fetchNotifications()
  setInterval(fetchNotifications, 10000)
})
</script>

<template>
  <header class="fixed top-0 left-0 right-0 h-[60px] bg-[#111827] border-b border-gray-800 flex items-center justify-between px-20 z-50">
    <button
      type="button"
      class="flex items-center gap-3 text-left hover:opacity-80 transition-opacity"
      @click="router.push('/')"
    >
      <div class="w-13 h-13 flex items-center justify-center overflow-hidden">
        <img 
          src="/logo.png" 
          alt="E-VER Logo" 
          class="w-full h-full object-contain" 
        />
      </div>
      
      <div>
        <h1 class="text-base font-bold text-white leading-tight">E-VER</h1>
        <p class="text-[10px] text-gray-500 leading-tight">Energy Saver</p>
      </div>
    </button>

    <div class="flex items-center gap-6 mr-10 md:mr-20 lg:mr-32 transition-all">
  <div class="hidden md:flex items-center bg-gray-800 rounded-lg px-3 py-1.5 gap-2">
    <Search class="w-4 h-4 text-gray-500" />
    <input type="text" placeholder="검색..." class="bg-transparent text-sm text-gray-300 outline-none w-48" />
  </div>

  <button class="relative p-2 text-gray-400 hover:text-white" @click="router.push('/alerts')">
    <Bell class="w-5 h-5" />
    <span v-if="hasNotification" class="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
  </button>

  <button class="flex items-center gap-2 px-3 py-1.5 hover:bg-gray-800 rounded-lg transition-colors">
    <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
      <User class="w-4 h-4 text-white" />
    </div>
    <span class="text-sm text-gray-300 hidden sm:block">관리자</span>
  </button>
</div>
  </header>
</template>