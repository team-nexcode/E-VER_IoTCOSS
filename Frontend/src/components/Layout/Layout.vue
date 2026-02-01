<script setup lang="ts">
import TopBar from './TopBar.vue'
import Sidebar from './Sidebar.vue'
</script>

<template>
  <div class="h-screen w-screen overflow-hidden">
    <TopBar />
    <Sidebar />
    <main class="fixed top-[60px] left-[250px] right-0 bottom-0 bg-[#0f172a] p-8 overflow-y-auto overflow-x-hidden">
      <RouterView />
    </main>
  </div>
</template>
