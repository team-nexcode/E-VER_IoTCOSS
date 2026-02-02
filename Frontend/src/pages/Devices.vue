<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plug, Plus, Trash2, MapPin, Pencil } from 'lucide-vue-next'
import { useDeviceMacStore } from '@/stores/deviceMac'
import { storeToRefs } from 'pinia'
import type { DeviceMac } from '@/types/deviceMac'

/** ===== 로직 (기능 유지) ===== */
const store = useDeviceMacStore()
const { deviceMacs, loading } = storeToRefs(store)

const isAddModalOpen = ref(false)
const addForm = ref({ deviceName: '', deviceMac: '', location: '' })
const addError = ref('')

const isEditModalOpen = ref(false)
const editForm = ref({ id: 0, deviceName: '', deviceMac: '', location: '' })
const editError = ref('')

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
    deviceName: device.device_name,
    deviceMac: device.device_mac,
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
  try { await store.deleteDevice(id) } catch { /* silent */ }
}

onMounted(() => { store.fetchDeviceMacs() })
</script>

<template>
  <div class="space-y-8 p-8">
    <div class="flex justify-between items-end">
      <div>
        <h2 class="text-3xl font-bold text-white">디바이스 관리</h2>
        <p class="text-base text-gray-500 mt-2">등록된 {{ deviceMacs.length }}개의 기기를 관리하세요</p>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center h-64 text-xl text-gray-400">
      불러오는 중...
    </div>

    <div v-else-if="deviceMacs.length > 0" class="rounded-2xl border border-white/10 bg-white/[0.03] overflow-hidden">
      <div class="divide-y divide-white/10">
        <div
          v-for="device in deviceMacs"
          :key="device.id"
          class="px-8 py-6 flex items-center justify-between gap-6 hover:bg-white/[0.04] transition group"
        >
          <div class="flex items-center gap-6 min-w-0">
            <div class="p-4 bg-blue-500/15 text-blue-400 rounded-xl">
              <Plug class="w-7 h-7" />
            </div>
            <div class="min-w-0">
              <div class="flex items-center gap-3">
                <span class="text-xl font-bold text-white truncate">{{ device.device_name }}</span>
              </div>
              <div class="flex items-center gap-2 text-base text-white/40 mt-1.5">
                <MapPin class="w-4 h-4" />
                <span>{{ device.location }}</span>
                <span class="mx-1 text-white/20">|</span>
                <span class="font-mono text-sm tracking-tight">{{ device.device_mac }}</span>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-2">
            <button @click="openEditModal(device)" class="p-3 rounded-xl text-white/30 hover:text-blue-400 hover:bg-white/10 transition">
              <Pencil class="w-6 h-6" />
            </button>
            <button @click="handleDelete(device.id, device.device_name)" class="p-3 rounded-xl text-white/30 hover:text-red-400 hover:bg-white/10 transition">
              <Trash2 class="w-6 h-6" />
            </button>
          </div>
        </div>
      </div>

      <button
        type="button"
        @click="openAddModal"
        class="w-full h-14 border-t border-white/10 hover:bg-white/[0.05] active:bg-white/[0.08] transition flex items-center justify-center gap-2"
      >
        <span class="w-7 h-7 grid place-items-center rounded-full bg-white/[0.06] border border-white/10">
          <Plus class="w-4 h-4 text-blue-400" />
        </span>
        <span class="text-sm font-semibold text-white">새 디바이스 추가하기</span>
      </button>
    </div>

    <div v-if="isAddModalOpen || isEditModalOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-md" @click.self="isAddModalOpen = false; isEditModalOpen = false">
      <div class="w-full max-w-md mx-4 bg-[#0b1220] ring-1 ring-white/12 rounded-lg overflow-hidden shadow-2xl">
        <div class="px-8 pt-8 pb-6 flex items-center justify-between border-b border-white/10">
          <button @click="isAddModalOpen = false; isEditModalOpen = false" class="text-sky-300 text-lg font-semibold hover:opacity-70 transition">취소</button>
          <div class="text-white text-xl font-bold">{{ isAddModalOpen ? '디바이스 등록' : '정보 수정' }}</div>
          <button @click="isAddModalOpen ? handleAdd() : handleEdit()" class="text-sky-300 text-lg font-semibold hover:opacity-70 transition">완료</button>
        </div>

        <div class="p-8 space-y-6">
          <div class="space-y-4">
            <div class="bg-white/[0.04] p-4 rounded-md ring-1 ring-white/10 focus-within:ring-white/20 transition">
              <label class="text-xs text-white/40 block mb-2 px-1 uppercase font-black tracking-widest">Device Name</label>
              <input v-model="(isAddModalOpen ? addForm : editForm).deviceName" type="text" class="w-full bg-transparent border-none text-white focus:ring-0 p-1 text-lg outline-none" placeholder="거실 에어컨">
            </div>
            <div class="bg-white/[0.04] p-4 rounded-md ring-1 ring-white/10 focus-within:ring-white/20 transition">
              <label class="text-xs text-white/40 block mb-2 px-1 uppercase font-black tracking-widest">Mac Address</label>
              <input v-model="(isAddModalOpen ? addForm : editForm).deviceMac" type="text" class="w-full bg-transparent border-none text-white focus:ring-0 p-1 text-lg outline-none font-mono" placeholder="AA:BB:CC:DD:EE:FF">
            </div>
            <div class="bg-white/[0.04] p-4 rounded-md ring-1 ring-white/10 focus-within:ring-white/20 transition">
              <label class="text-xs text-white/40 block mb-2 px-1 uppercase font-black tracking-widest">Location</label>
              <input v-model="(isAddModalOpen ? addForm : editForm).location" type="text" class="w-full bg-transparent border-none text-white focus:ring-0 p-1 text-lg outline-none" placeholder="거실">
            </div>
          </div>
          <p v-if="addError || editError" class="text-red-400 text-sm text-center font-medium">{{ addError || editError }}</p>
        </div>
      </div>
    </div>
  </div>
</template>