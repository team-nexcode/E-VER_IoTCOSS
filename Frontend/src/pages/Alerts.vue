<script setup lang="ts">
import { ref } from 'vue'
import { Bell, AlertTriangle, Info, CheckCircle2, Trash2 } from 'lucide-vue-next'

// 알림 더미 데이터
const notifications = ref([
  {
    id: 1,
    type: 'danger', // 위험: 빨간색
    title: '이상 전력 소모 감지',
    message: "'거실 에어컨'이 설정된 임계치보다 40% 많은 전력을 소비하고 있습니다. 기기 상태를 확인하세요.",
    time: '방금 전',
    isRead: false
  },
  {
    id: 2,
    type: 'warning', // 경고: 주황색
    title: '기기 연결 끊김',
    message: "'침실 공기청정기'의 네트워크 연결이 불안정하여 오프라인 상태로 전환되었습니다.",
    time: '12분 전',
    isRead: false
  },
  {
    id: 3,
    type: 'success', // 성공/정보: 초록색
    title: '주간 에너지 리포트',
    message: '지난주 대비 전체 전력 사용량이 12% 감소했습니다. 훌륭합니다! 👏',
    time: '2시간 전',
    isRead: true
  },
  {
    id: 4,
    type: 'info', // 일반: 파란색
    title: '스케줄 실행 완료',
    message: "'외출 모드' 스케줄에 따라 모든 스마트 플러그가 차단되었습니다.",
    time: '5시간 전',
    isRead: true
  }
])

// 알림 삭제 함수
const deleteNotification = (id: number) => {
  notifications.value = notifications.value.filter(n => n.id !== id)
}

// 모두 읽음 처리
const markAllAsRead = () => {
  notifications.value.forEach(n => n.isRead = true)
}
</script>

<template>
  <div class="space-y-8 p-8"> <div class="flex justify-between items-end">
      <div>
        <h2 class="text-3xl font-bold text-white">알림 센터</h2> <p class="text-base text-gray-500 mt-2">시스템에서 발생한 중요한 소식을 확인하세요</p> </div>
      <button 
        @click="markAllAsRead"
        class="text-sm text-blue-400 hover:text-blue-300 transition-colors font-medium"
      >
        모두 읽음으로 표시
      </button>
    </div>

    <div v-if="notifications.length > 0" class="space-y-4">
      <div 
        v-for="n in notifications" 
        :key="n.id"
        class="group relative border rounded-2xl p-6 transition-all" 
        :style="{
          backgroundColor: n.isRead ? '#111827' : '#1f2937',
          borderColor: n.isRead ? '#1f2937' : '#374151',
          opacity: n.isRead ? 0.7 : 1
        }"
      >
        <div class="flex items-center gap-6"> 
          <div class="flex-shrink-0 flex items-center justify-center">
            <AlertTriangle v-if="n.type === 'danger'" class="w-7 h-7 text-red-500" />
            <AlertTriangle v-else-if="n.type === 'warning'" class="w-7 h-7 text-orange-500" />
            <CheckCircle2 v-else-if="n.type === 'success'" class="w-7 h-7 text-emerald-500" />
            <Info v-else class="w-7 h-7 text-blue-500" />
          </div>

          <div class="flex-1">
            <div class="flex justify-between items-center">
              <h4 class="font-bold text-lg" :class="n.isRead ? 'text-gray-400' : 'text-white'">
                {{ n.title }}
                <span v-if="!n.isRead" class="ml-2 inline-block w-2 h-2 bg-blue-500 rounded-full"></span>
              </h4>
              <span class="text-sm text-gray-500">{{ n.time }}</span>
            </div>
            <p class="text-base mt-1.5 leading-relaxed" :class="n.isRead ? 'text-gray-500' : 'text-gray-400'">
              {{ n.message }}
            </p>
          </div>

          <div class="flex items-center">
            <button 
              @click="deleteNotification(n.id)"
              class="opacity-0 group-hover:opacity-100 p-2 text-gray-500 hover:text-red-400 transition-all"
            >
              <Trash2 class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="flex flex-col items-center justify-center h-80 bg-gray-900/30 border border-dashed border-gray-800 rounded-3xl">
      <Bell class="w-16 h-16 text-gray-700 mb-4" />
      <p class="text-lg text-gray-500">새로운 알림이 없습니다.</p>
    </div>
  </div>
</template>