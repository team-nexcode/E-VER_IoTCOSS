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
    </div>

    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="text-gray-400">불러오는 중...</div>
    </div>

    <div v-else-if="devices.length > 0" class="space-y-4">
      <div class="bg-gray-900/50 border border-gray-800 rounded-2xl overflow-hidden">
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
            <tr v-for="device in devices" :key="device.id" class="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div class="p-2 bg-blue-500/10 text-blue-400 rounded-lg"><Plug class="w-4 h-4" /></div>
                  <span class="text-white font-medium">{{ device.deviceName }}</span>
                </div>
              </td>
              <td class="px-6 py-4"><code class="text-sm text-gray-300 bg-gray-800 px-2 py-1 rounded">{{ device.deviceMac }}</code></td>
              <td class="px-6 py-4"><div class="flex items-center gap-1 text-gray-400 text-sm"><MapPin class="w-3.5 h-3.5" />{{ device.location }}</div></td>
              <td class="px-6 py-4 text-gray-400 text-sm">{{ formatDate(device.createdAt) }}</td>
              <td class="px-6 py-4">
                <div class="flex items-center justify-end gap-2">
                  <button @click="openEditModal(device)" class="p-2 text-gray-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors"><Pencil class="w-4 h-4" /></button>
                  <button @click="handleDelete(device.id, device.deviceName)" class="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"><Trash2 class="w-4 h-4" /></button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

     <div class="flex justify-center" style="width: 100%; padding-top: 80px; padding-bottom: 40px;">
  <button
    @click="openAddModal"
    style="
      display: flex;
      align-items: center;
      
      /* 상하 12px, 오른쪽 28px, 왼쪽 20px로 오른쪽만 좀 더 여유 있게 */
      padding: 6px 28px 6px 20px; 
      gap: 10px;
      
      background: linear-gradient(135deg, #374151 0%, #111827 100%) !important;
      border: 1px solid #4b5563 !important;
      border-radius: 8px !important;
      color: #ffffff !important;
      font-size: 15px !important;
      font-weight: 600 !important;
      cursor: pointer !important;
    "
  >
    <Plus style="width: 18px; height: 18px; color: #60a5fa;" />
    <span>새 디바이스 추가하기</span>
  </button>
</div>
    </div>

    <div v-else class="flex flex-col items-center justify-center h-64 bg-gray-900/50 border border-gray-800 rounded-2xl">
      <Plug class="w-12 h-12 text-gray-700 mb-3" />
      <p class="text-gray-500 mb-4">등록된 디바이스가 없습니다.</p>
      <button
        @click="openAddModal"
        class="flex items-center gap-2 px-6 py-3 text-white font-bold"
        style="background-color: #374151 !important; border-radius: 8px !important; cursor: pointer;"
      >
        <Plus class="w-5 h-5" />
        첫 번째 기기 등록
      </button>
    </div>

    <div v-if="isAddModalOpen" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 9999;" @click.self="isAddModalOpen = false">
      <div style="background: #111827; border: 1px solid #374151; width: 90%; max-width: 400px; padding: 24px; border-radius: 16px;">
        <h3 style="font-size: 1.25rem; font-weight: 700; color: white; margin-bottom: 20px;">디바이스 등록</h3>
        <div style="display: flex; flex-direction: column; gap: 16px;">
          <div>
            <label style="display: block; font-size: 0.875rem; color: #9ca3af; margin-bottom: 4px;">이름</label>
            <input v-model="addForm.deviceName" type="text" placeholder="예: 거실 TV" style="width: 100%; background: #1f2937; border: 1px solid #374151; border-radius: 8px; padding: 10px; color: white; outline: none;">
          </div>
          <div>
            <label style="display: block; font-size: 0.875rem; color: #9ca3af; margin-bottom: 4px;">MAC 주소</label>
            <input v-model="addForm.deviceMac" type="text" placeholder="AA:BB:CC:DD:EE:FF" style="width: 100%; background: #1f2937; border: 1px solid #374151; border-radius: 8px; padding: 10px; color: white; outline: none;">
          </div>
          <div>
            <label style="display: block; font-size: 0.875rem; color: #9ca3af; margin-bottom: 4px;">위치</label>
            <input v-model="addForm.location" type="text" placeholder="예: 거실" style="width: 100%; background: #1f2937; border: 1px solid #374151; border-radius: 8px; padding: 10px; color: white; outline: none;">
          </div>
        </div>
        <p v-if="addError" style="color: #f87171; font-size: 0.875rem; margin-top: 12px;">{{ addError }}</p>
        <div style="display: flex; gap: 12px; margin-top: 24px;">
          <button @click="isAddModalOpen = false" style="flex: 1; padding: 10px; background: #374151; color: white; border-radius: 8px; border: none; cursor: pointer;">취소</button>
          <button @click="handleAdd" style="flex: 1; padding: 10px; background: #2563eb; color: white; border-radius: 8px; border: none; cursor: pointer; font-weight: 700;">등록</button>
        </div>
      </div>
    </div>
    </div> </template>