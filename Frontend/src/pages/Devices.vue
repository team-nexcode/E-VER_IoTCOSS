<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plug, Plus, Trash2, MapPin, Pencil } from 'lucide-vue-next'
import { useDeviceMacStore } from '@/stores/deviceMac'
import { storeToRefs } from 'pinia'
import type { DeviceMac } from '@/types/deviceMac'

const store = useDeviceMacStore()
const { devices, loading } = storeToRefs(store)

// 등록 모달
const isAddModalOpen = ref(false)
const addForm = ref({ deviceName: '', deviceMac: '', location: '' })
const addError = ref('')

// 수정 모달
const isEditModalOpen = ref(false)
const editForm = ref({ id: 0, deviceName: '', deviceMac: '', location: '' })
const editError = ref('')

function formatDate(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

function openAddModal() {
  addForm.value = { deviceName: '', deviceMac: '', location: '' }
  addError.value = ''
  isAddModalOpen.value = true
}

async function handleAdd() {
  if (!addForm.value.deviceName || !addForm.value.deviceMac || !addForm.value.location) {
    addError.value = '모든 필드를 입력해주세요.'
    return
  }
  try {
    addError.value = ''
    await store.addDevice(addForm.value)
    isAddModalOpen.value = false
  } catch (e: unknown) {
    addError.value = e instanceof Error ? e.message : '등록 실패'
  }
}

function openEditModal(device: DeviceMac) {
  editForm.value = {
    id: device.id,
    deviceName: device.deviceName,
    deviceMac: device.deviceMac,
    location: device.location,
  }
  editError.value = ''
  isEditModalOpen.value = true
}

async function handleEdit() {
  if (!editForm.value.deviceName || !editForm.value.deviceMac || !editForm.value.location) {
    editError.value = '모든 필드를 입력해주세요.'
    return
  }
  try {
    editError.value = ''
    await store.updateDevice(editForm.value.id, {
      deviceName: editForm.value.deviceName,
      deviceMac: editForm.value.deviceMac,
      location: editForm.value.location,
    })
    isEditModalOpen.value = false
  } catch (e: unknown) {
    editError.value = e instanceof Error ? e.message : '수정 실패'
  }
}

async function handleDelete(id: number, name: string) {
  if (!confirm(`'${name}' 디바이스를 삭제하시겠습니까?`)) return
  try {
    await store.deleteDevice(id)
  } catch {
    // silent
  }
}

onMounted(() => {
  store.fetchDevices()
})
</script>

<template>
  <div class="space-y-6 p-6">
    <div class="flex justify-between items-end">
      <div>
        <h2 class="text-2xl font-bold text-white">디바이스 관리</h2>
        <p class="text-sm text-gray-500 mt-1">등록된 {{ devices.length }}개의 IoT 디바이스를 관리하세요</p>
      </div>
      <button
        @click="openAddModal"
        class="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition-all font-semibold"
      >
        <Plus class="w-5 h-5" />
        새 기기 등록
      </button>
    </div>

    <!-- 로딩 -->
    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="text-gray-400">불러오는 중...</div>
    </div>

    <!-- 테이블 -->
    <div v-else-if="devices.length > 0" class="bg-gray-900/50 border border-gray-800 rounded-2xl overflow-hidden">
      <table class="w-full">
        <thead>
          <tr class="border-b border-gray-800 text-gray-400 text-sm">
            <th class="text-left px-6 py-4 font-medium">이름</th>
            <th class="text-left px-6 py-4 font-medium">MAC 주소</th>
            <th class="text-left px-6 py-4 font-medium">위치</th>
            <th class="text-left px-6 py-4 font-medium">등록일</th>
            <th class="text-right px-6 py-4 font-medium">액션</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="device in devices"
            :key="device.id"
            class="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors"
          >
            <td class="px-6 py-4">
              <div class="flex items-center gap-3">
                <div class="p-2 bg-blue-500/10 text-blue-400 rounded-lg">
                  <Plug class="w-4 h-4" />
                </div>
                <span class="text-white font-medium">{{ device.deviceName }}</span>
              </div>
            </td>
            <td class="px-6 py-4">
              <code class="text-sm text-gray-300 bg-gray-800 px-2 py-1 rounded">{{ device.deviceMac }}</code>
            </td>
            <td class="px-6 py-4">
              <div class="flex items-center gap-1 text-gray-400 text-sm">
                <MapPin class="w-3.5 h-3.5" />
                {{ device.location }}
              </div>
            </td>
            <td class="px-6 py-4 text-gray-400 text-sm">
              {{ formatDate(device.createdAt) }}
            </td>
            <td class="px-6 py-4">
              <div class="flex items-center justify-end gap-2">
                <button
                  @click="openEditModal(device)"
                  class="p-2 text-gray-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors"
                  title="수정"
                >
                  <Pencil class="w-4 h-4" />
                </button>
                <button
                  @click="handleDelete(device.id, device.deviceName)"
                  class="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                  title="삭제"
                >
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 빈 상태 -->
    <div v-else class="flex flex-col items-center justify-center h-64 bg-gray-900/50 border border-gray-800 rounded-2xl">
      <Plug class="w-12 h-12 text-gray-700 mb-3" />
      <p class="text-gray-500">등록된 디바이스가 없습니다.</p>
    </div>

    <!-- 등록 모달 -->
    <div v-if="isAddModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div class="bg-gray-900 border border-gray-800 w-full max-w-sm rounded-2xl p-6">
        <h3 class="text-xl font-bold text-white mb-4">디바이스 등록</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm text-gray-400 mb-1">이름</label>
            <input v-model="addForm.deviceName" type="text" placeholder="예: 거실 TV" class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white outline-none focus:border-blue-500 transition-colors" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">MAC 주소</label>
            <input v-model="addForm.deviceMac" type="text" placeholder="예: AA:BB:CC:DD:EE:FF" class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white outline-none focus:border-blue-500 transition-colors" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">위치</label>
            <input v-model="addForm.location" type="text" placeholder="예: 거실" class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white outline-none focus:border-blue-500 transition-colors" />
          </div>
          <p v-if="addError" class="text-red-400 text-sm">{{ addError }}</p>
          <div class="flex gap-2">
            <button @click="isAddModalOpen = false" class="flex-1 py-3 bg-gray-800 text-white rounded-xl hover:bg-gray-700 transition-colors">취소</button>
            <button @click="handleAdd" class="flex-1 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-500 transition-colors">등록</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 수정 모달 -->
    <div v-if="isEditModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div class="bg-gray-900 border border-gray-800 w-full max-w-sm rounded-2xl p-6">
        <h3 class="text-xl font-bold text-white mb-4">디바이스 수정</h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm text-gray-400 mb-1">이름</label>
            <input v-model="editForm.deviceName" type="text" class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white outline-none focus:border-blue-500 transition-colors" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">MAC 주소</label>
            <input v-model="editForm.deviceMac" type="text" class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white outline-none focus:border-blue-500 transition-colors" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">위치</label>
            <input v-model="editForm.location" type="text" class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white outline-none focus:border-blue-500 transition-colors" />
          </div>
          <p v-if="editError" class="text-red-400 text-sm">{{ editError }}</p>
          <div class="flex gap-2">
            <button @click="isEditModalOpen = false" class="flex-1 py-3 bg-gray-800 text-white rounded-xl hover:bg-gray-700 transition-colors">취소</button>
            <button @click="handleEdit" class="flex-1 py-3 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-500 transition-colors">저장</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
