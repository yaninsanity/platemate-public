<template>
  <v-card class="battle-card rounded-xl" elevation="3">

    <!-- ╭── 顶栏：作者 + 心情 + 日期 ╮ -->
    <div class="flex items-center gap-2 px-4 pt-3">
      <v-icon size="20" :icon="MOOD_ICON[entry.mood]" />
      <span class="font-semibold tracking-wide">{{ entry.author_username }}</span>
      <v-spacer/>
      <span class="text-xs text-gray-500">{{ entry.created_at.slice(0, 10) }}</span>
    </div>

    <!-- ╭── 主体：4图 + 分数 + 4图 ╮ -->
    <div
      class="grid gap-2 p-4"
      :class="gridCls"
    >
      <!-- ◀ 左 4 张 / 上传框 -->
      <ImgBox
        v-for="i in 4" :key="'l'+i"
        :src="media[i-1]"
        @add="chooseFile"
      />

      <!-- ◎ 分数面板 -->
      <ScorePanel
        :score="entry.ai_score === null ? undefined : entry.ai_score"
        @set="$emit('set-score', entry.id)"
      />

      <!-- ▶ 右 4 张 / 上传框 -->
      <ImgBox
        v-for="i in 4" :key="'r'+i"
        :src="media[i+3]"
        @add="chooseFile"
      />
    </div>

    <!-- ╭── 评论折叠 ╮ -->
    <v-expansion-panels flat density="compact" class="border-t">
      <v-expansion-panel>
        <v-expansion-panel-title>
          <v-icon size="18" start icon="mdi-comment-text-multiple-outline" />
          Comments&nbsp;({{ entry.comments.length }})
        </v-expansion-panel-title>

        <v-expansion-panel-text>
          <!-- 列表 -->
          <v-list density="compact" nav>
            <v-list-item
              v-for="c in entry.comments" :key="c.id"
              :title="c.author_username || c.author"
              :subtitle="c.content"
            >
              <template #append>
                <v-btn
                  icon size="x-small" color="red"
                  @click="$emit('delete-comment', c.id)"
                ><v-icon size="14">mdi-delete</v-icon></v-btn>
              </template>
            </v-list-item>
          </v-list>

          <!-- 新评论 -->
          <div class="flex gap-2 mt-2">
            <v-text-field
              v-model="draft"
              density="compact"
              variant="outlined"
              placeholder="Add a comment…"
              class="flex-grow-1"
              hide-details
            />
            <v-btn
              color="primary"
              :disabled="!draft.trim()"
              @click="sendComment"
            >Send</v-btn>
          </div>

        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, defineComponent, h } from 'vue'
import type { MemoryEntry } from '@/models/couplememory'

/* ───── props / emits ───── */
const props = defineProps<{ entry: MemoryEntry }>()
const emit  = defineEmits<{
  /** 上传 1~多文件  */
  (e:'upload', files: File[], entryId: number): void
  /** 手动设置 AI 分数  */
  (e:'set-score', entryId: number): void
  /** 新评论  */
  (e:'post-comment', entryId: number, text: string): void
  /** 删除评论  */
  (e:'delete-comment', commentId: number): void
}>()

/* ───── mood → icon ───── */
const MOOD_ICON = {
  happy: 'mdi-emoticon-happy-outline',
  proud: 'mdi-emoticon-cool-outline',
  fail : 'mdi-emoticon-cry-outline',
  nailed: 'mdi-emoticon-excited-outline',
  grind: 'mdi-emoticon-neutral-outline',
  love: 'mdi-heart-outline',
  lucky: 'mdi-emoticon-wink-outline',
  chaos: 'mdi-emoticon-confused-outline',
} as const

/* ───── 取前 8 张图 ───── */
const media = computed(() => props.entry.media.map(m => m.media).slice(0, 8))

/* ───── 上传文件 ───── */
function chooseFile() {
  const input = document.createElement('input')
  input.type = 'file'
  input.multiple = true
  input.onchange = e => {
    const files = Array.from((e.target as HTMLInputElement).files || [])
    if (files.length) emit('upload', files, props.entry.id)
  }
  input.click()
}

/* ───── 评论 ───── */
const draft = ref('')
function sendComment() {
  const txt = draft.value.trim()
  if (txt) emit('post-comment', props.entry.id, txt)
  draft.value = ''
}

/* ───── 小组件：图片方块 ───── */
const ImgBox = defineComponent({
  name: 'ImgBox',
  props: { src: String },
  emits: ['add'],
  setup(p, { emit }) {
    const isEmpty = computed(() => !p.src)
    return () => {
      if (isEmpty.value) {
        return h('label', { class: 'img-box add' }, [
          h('input', { 
            type: 'file', 
            hidden: true, 
            onChange: () => emit('add') 
          }),
          h('v-icon', { size: '28' }, 'mdi-plus')
        ])
      } else {
        return h('img', { 
          class: 'img-box', 
          src: p.src 
        })
      }
    }
  },
})

/* ───── 小组件：分数面板 ───── */
const ScorePanel = defineComponent({
  name: 'ScorePanel',
  props: { 
    score: {
      type: Number,
      default: undefined,
      validator: (val) => val === null || typeof val === 'number' || val === undefined
    } 
  },
  emits: ['set'],
  setup(p, { emit }) {
    return () => {
      return h('div', { class: 'score-panel flex flex-col items-center justify-center gap-1 rounded-lg' }, [
        h('v-icon', { size: '26', color: 'deep-purple' }, 'mdi-brain'),
        h('span', { class: 'text-lg font-bold' }, p.score ?? '—'),
        p.score == null ? h('v-btn', {
          size: 'x-small',
          variant: 'text',
          onClick: () => emit('set')
        }, 'Set') : null
      ])
    }
  },
})

/* ───── 响应式列宽 class ───── */
const gridCls = 'grid-cols-[repeat(4,70px)_auto_repeat(4,70px)] sm:grid-cols-[repeat(4,90px)_auto_repeat(4,90px)]'
</script>

<style scoped>
.battle-card { transition: .25s; }
@media (hover:hover) { .battle-card:hover { transform: translateY(-4px); } }

/* 方图 */
.img-box {
  width: 70px;
  height: 70px;
  object-fit: cover;
  border-radius: .5rem;
  box-shadow: 0 2px 6px rgba(0,0,0,.15);
}
@media (min-width: 640px) { .img-box { width: 90px; height: 90px; } }
.img-box.add {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed #d1d5db;
  color: #9ca3af;
  cursor: pointer;
}

/* 分数 */
.score-panel {
  width: 78px;
  height: 78px;
  background: #f3f4f6;
}
@media (min-width: 640px) { .score-panel { width: 90px; height: 90px; } }
</style>
