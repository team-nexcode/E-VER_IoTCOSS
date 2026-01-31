<script setup lang="ts">
import { Bell, Search, User, Zap } from 'lucide-vue-next'
</script>

<template>
  <header class="fixed top-0 left-0 right-0 h-[60px] bg-[#111827] border-b border-gray-800 flex items-center justify-between px-6 z-50">
    <!-- 좌측: 로고 + 시스템 이름 -->
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center">
        <Zap class="w-5 h-5 text-white" />
      </div>
      <div>
        <h1 class="text-base font-bold text-white leading-tight">E-VER</h1>
        <p class="text-[10px] text-gray-500 leading-tight">Energy Saver</p>
      </div>
    </div>

    <!-- 우측: 검색, 알림, 프로필 -->
    <div class="flex items-center gap-4">
      <!-- 검색 -->
      <div class="hidden md:flex items-center bg-gray-800 rounded-lg px-3 py-2 gap-2">
        <Search class="w-4 h-4 text-gray-500" />
        <input
          type="text"
          placeholder="검색..."
          class="bg-transparent text-sm text-gray-300 outline-none w-48 placeholder-gray-600"
        />
      </div>

      <!-- 알림 벨 -->
      <button class="relative p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors">
        <Bell class="w-5 h-5" />
        <span class="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
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
