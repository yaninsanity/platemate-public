<template>
  <div class="badge-view p-6 bg-white rounded-2xl shadow-md max-w-5xl mx-auto my-8">
    <!-- 标题 -->
    <h1 class="text-3xl font-bold mb-6 text-center">🏅 My Badges</h1>

    <!-- 加载中 -->
    <div v-if="loading" class="text-center text-gray-500 animate-pulse py-8">
      Loading your badges…
    </div>

    <!-- 空状态 -->
    <div v-else-if="!badges.length" class="text-center text-gray-500 py-8">
      You haven’t earned any badges yet.
    </div>

    <!-- 徽章网格 -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
      <div
        v-for="badge in badges"
        :key="badge.slug"
        class="badge-card p-4 bg-gray-50 rounded-lg shadow hover:shadow-lg transition"
      >
        <!-- 徽章代码/标识 -->
        <div class="text-xl font-mono text-center mb-2">{{ badge.slug }}</div>
        <!-- 描述 -->
        <p class="text-center font-medium text-gray-800">{{ badge.desc }}</p>
        <!-- 获得时间 -->
        <p class="text-center text-sm text-gray-500 mt-2">
          Earned: {{ formatDate(badge.added) }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { usePetStore } from '@/stores/petStore'
import type { Badge } from '@/models/pet'

const store = usePetStore()
const loading = ref(true)

// 触发拉取
onMounted(async () => {
  await store.fetchBadges()
  loading.value = false
})

// 从 store 取 badges
const badges = computed(() => store.badges)

// 简单的日期格式化
function formatDate(iso: string) {
  const d = new Date(iso)
  return d.toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric'
  })
}
</script>

<style scoped>
.badge-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  transition: transform 0.2s, box-shadow 0.2s;
}
.badge-card:hover {
  transform: translateY(-2px);
}
</style>
