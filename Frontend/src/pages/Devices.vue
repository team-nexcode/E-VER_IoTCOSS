<script setup lang="ts">
import { ref } from 'vue'
import { Plug, Plus, Trash2, MapPin, Power, X } from 'lucide-vue-next'
import { useDeviceStore } from '@/stores/device'
import { storeToRefs } from 'pinia'

const store = useDeviceStore()
const { devices } = storeToRefs(store)

// 모달 및 입력 상태
const isModalOpen = ref(false)
const newName = ref('')
const newLocation = ref('')

const handleAdd = () => {
  if (!newName.value || !newLocation.value) return
  store.addDevice(newName.value, newLocation.value)
  // 입력 필드 초기화
  newName.value = ''
  newLocation.value = ''
  isModalOpen.value = false
}

const handleDelete = (id: number, name: string) => {
  if (confirm(`'${name}' 디바이스를 삭제하시겠습니까?`)) {
    store.removeDevice(id)
  }
}
</script>

<template>
  <div class="space-y-6 p-6">
    <div class="flex justify-between items-end">
      <div>
        <h2 class="text-2xl font-bold text-white">디바이스 관리</h2>
        <p class="text-sm text-gray-500 mt-1">연결된 {{ devices.length }}개의 IoT 디바이스를 관리하세요</p>
      </div>
      <button 
        @click="isModalOpen = true"
        class="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-all font-semibold"
      >
        <Plus class="w-5 h-5" />
        새 기기 등록
      </button>
    </div>

    <div v-if="devices.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div 
        v-for="device in devices" 
        :key="device.id"
        class="bg-gray-900/50 border border-gray-800 rounded-2xl p-5 hover:border-gray-700 transition-all group relative"
      >
        <button 
          @click="handleDelete(device.id, device.name)"
          class="absolute top-4 right-4 p-2 text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <Trash2 class="w-4 h-4" />
        </button>

        <div class="flex items-center gap-4 mb-4">
          <div :class="['p-3 rounded-xl', device.isOnline ? 'bg-blue-500/10 text-blue-400' : 'bg-gray-800 text-gray-600']">
            <Plug class="w-6 h-6" />
          </div>
          <div>
            <h3 class="font-bold text-white">{{ device.name }}</h3>
            <div class="flex items-center gap-1 text-xs text-gray-500">
              <MapPin class="w-3 h-3" /> {{ device.location }}
            </div>
          </div>
        </div>

        <div class="flex items-center justify-between pt-4 border-t border-gray-800">
          <span :class="['text-sm font-medium', device.isActive ? 'text-green-400' : 'text-gray-400']">
            {{ device.isActive ? '작동 중' : '중지됨' }}
          </span>
          <button @click="store.toggleDevice(device.id)" class="p-2 bg-gray-800 rounded-lg text-gray-400 hover:text-white">
            <Power class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <div v-else class="flex flex-col items-center justify-center h-64 bg-gray-900/50 border border-gray-800 rounded-2xl">
      <Plug class="w-12 h-12 text-gray-700 mb-3" />
      <p class="text-gray-500">등록된 디바이스가 없습니다.</p>
    </div>

    <div v-if="isModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div class="bg-gray-900 border border-gray-800 w-full max-w-sm rounded-2xl p-6">
        <h3 class="text-xl font-bold text-white mb-4">디바이스 등록</h3>
        <div class="space-y-4">
          <input v-model="newName" type="text" placeholder="이름 (예: 거실 TV)" class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white outline-none" />
          <input v-model="newLocation" type="text" placeholder="위치 (예: 거실)" class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white outline-none" />
          <div class="flex gap-2">
            <button @click="isModalOpen = false" class="flex-1 py-3 bg-gray-800 text-white rounded-xl">취소</button>
            <button @click="handleAdd" class="flex-1 py-3 bg-blue-600 text-white rounded-xl font-bold">등록</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>