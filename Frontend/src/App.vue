<script setup lang="ts">
import { onMounted } from 'vue'
import { useWebSocket } from '@/composables/useWebSocket'

const wsProtocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsUrl = `${wsProtocol}//${location.host}/ws/devices`
const { connect } = useWebSocket(wsUrl)

onMounted(() => {
  connect()
})
</script>

<template>
  <RouterView />
</template>
