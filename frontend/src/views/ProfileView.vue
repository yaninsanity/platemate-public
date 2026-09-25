<!-- File: src/views/ProfileView.vue -->
<template>
  <v-app class="profile-view">
    <!-- 🎮 AAA游戏化左右分栏布局 - 零tab，零点击成本 -->
    <div class="game-dual-layout">
      
      <!-- 🎮 左侧 35%：Couple信息展示区 -->
      <div class="left-panel">
        <!-- 🎯 隐藏式截图功能组件 -->
                <ScreenshotShare 
                  ref="screenshotComponent"
                  context="profile"
                  :buttonText="'📷 Share Our Story'"
                  :successTitle="'Couple Story Captured!'"
                  :successMessage="'Your beautiful story is ready to share!'"
                  :shareTitle="'🏆 Our PlateMate Journey'"
                  :shareText="'Check out our amazing culinary journey together! 👫🍽️✨'"
                  :fileName="'platemate-couple-story.png'"
                  class="share-target hidden-screenshot"
                  @capture-start="onCaptureStart"
                  @capture-success="onCaptureSuccess"
                  @capture-error="onCaptureError"
                  @share-success="onShareSuccess"
                  @share-error="onShareError"
                >
                  <div class="couple-view">
                    <!-- � AAA级头像编辑区 - 极致清晰引导 -->
                    <section class="avatar-edit-aaa">
                      <div class="avatar-display-zone">
                        <v-avatar size="70" class="avatar-preview">
                          <img :src="avatarPreview" class="avatar-image" @error="onImageError"
                              :alt="`Avatar of ${form.username}`"/>
                        </v-avatar>
                        <v-btn v-if="showRemove"
                              icon density="compact" size="x-small"
                              class="remove-avatar" :disabled="submitting"
                              @click="removeAvatar">
                          <v-icon size="14">mdi-close</v-icon>
                        </v-btn>
                        <div class="avatar-hint">Your Avatar</div>
                      </div>
                      
                      <div class="upload-action-zone">
                        <label class="upload-trigger-btn" tabindex="0">
                          <input
                            type="file"
                            accept="image/jpeg,image/png,image/webp,image/gif"
                            @change="handleFileSelect"
                            class="hidden-file-input"
                          />
                          <span class="upload-icon">📸</span>
                          <span class="upload-text">
                            <strong>Upload Avatar</strong>
                            <small>Click to choose image</small>
                          </span>
                        </label>
                      </div>
                    </section>
                    
                    <!-- 已配对 -->
                    <template v-if="isCoupled">
                      <!-- ① 头像 & SVG 心形 -->
                      <header class="faces-row">
                        <figure class="face" tabindex="0">
                          <img :src="meAvatar" alt="You" class="face-img" />
                          <figcaption>{{ meName }}<br /><span>(You)</span></figcaption>
                        </figure>

                        <svg class="connector" viewBox="0 0 100 50" preserveAspectRatio="none">
                          <path
                            d="M0,25 C25,0 75,50 100,25"
                            stroke="#ff6fa5" stroke-width="4" fill="none"
                          />
                        </svg>

                        <figure class="face" tabindex="0">
                          <img :src="paAvatar" alt="Partner" class="face-img" />
                          <figcaption>{{ paName }}<br /><span>(Partner)</span></figcaption>
                        </figure>
                      </header>

                      <!-- ② 宠物区 -->
                      <section class="pet-zone">
                        <!-- 蛋未孵化 -->
                        <template v-if="!hasPet">
                          <div class="egg-wrapper" @click="bounceEgg" role="button" aria-label="Hatch Egg">
                            <PetRenderer
                              ref="egg"
                              class="egg"
                              :base="ASSET_DIR"
                              :initial-anim="eggFile"
                            />
                            <div class="egg-glow"></div>
                          </div>
                          <p class="tap-tip">🎮 Tap the egg to hatch your companion!</p>
                        </template>

                        <!-- 已孵化 -->
                        <template v-else>
                          <div class="pet-wrapper">
                            <div :class="['pet-card', { celebrating }]" @animationend="celebrating = false">
                              <PetStage :status="petStatus" :size="200" bg="#e9f3ff" />
                              <!-- 庆祝动画 -->
                              <div v-if="celebrating" class="sparkle"></div>
                            </div>

                            <!-- 宠物名称 & 等级 -->
                            <div class="pet-info">
                              <h3 class="pet-name">{{ petNickname }}</h3>
                              <p class="pet-level">Lv {{ petLevel }}</p>
                            </div>

                            <!-- XP 进度条 -->
                            <div class="xp-bar">
                              <div class="xp-fill" :style="{ width: xpPercent + '%' }"></div>
                            </div>

                            <!-- 心情 -->
                            <p class="mood">{{ moodEmoji }} Feeling {{ moodText }}</p>
                          </div>
                        </template>
                      </section>

                      <!-- ③ 情侣信息卡 -->
                      <section class="couple-card">
                        <h2>{{ coupleName }}</h2>
                        <p class="code">Code · <strong>{{ coupleCode }}</strong></p>
                        <p class="since">🕒 {{ hoursSince }}h together</p>

                        <div class="btn-row">
                          <button class="btn copy" :disabled="copying" @click="copyCode">
                            <span v-if="!copying">✂️ Copy</span>
                            <span v-else class="loader"></span>
                          </button>
                          <button class="btn share" :disabled="screenshotComponent?.isCapturing" @click="handleShare">
                            <span v-if="!screenshotComponent?.isCapturing">📷 Share</span>
                            <span v-else class="loader"></span>
                          </button>
                          <button class="btn memory" @click="goMemories">📖 Memories</button>
                        </div>

                        <p class="encourage">
                          Keep unlocking memories together—cook up the next level! 🍳
                        </p>
                      </section>
                    </template>

                    <!-- 未配对 -->
                    <template v-else>
                      <div class="couple-invite">
                        <h3>🥰 Find Your Cooking Partner!</h3>
                        <p>Connect with someone special and start your culinary journey together!</p>
                        <button class="btn invite-btn" @click="router.push('/couple')">
                          💕 Start Pairing
                        </button>
                      </div>
                    </template>
                  </div>
                </ScreenshotShare>
      </div><!-- .left-panel -->
      
      <!-- 🎮 右侧 65%：Profile编辑区 -->
      <div class="right-panel">
        <div class="profile-edit-container">
          <!-- 🎯 简洁页面标题 -->
          <div class="page-header">
            <div class="header-content">
              <h2 class="page-title">⚡ Your Profile</h2>
              <p class="page-subtitle">Manage your personal information</p>
            </div>
            <v-btn 
              icon 
              variant="text"
              :disabled="loading||submitting"
              @click="onReset" 
              aria-label="Reset"
              class="reset-btn"
            >
              <v-icon color="rgba(168, 230, 207, 0.8)">mdi-refresh</v-icon>
            </v-btn>
          </div>

                <!-- ── skeleton / error ─────────────────────────── -->
                <v-skeleton-loader
                  v-if="loading"
                  type="avatar, heading, paragraph@4"
                  class="ma-6"
                />
                <v-alert
                  v-else-if="errorMsg"
                  type="error" variant="tonal" color="red-lighten-4"
                  class="mx-6 mt-4" border="start" border-color="red-accent-2"
                  dismissible
                  @click:close="errorMsg=''"
                >
                  {{ errorMsg }}
                </v-alert>

                <!-- ── main form ────────────────────────────────── -->
                <v-form
                  v-else
                  ref="formRef"
                  v-model="valid"
                  lazy-validation
                  @submit.prevent="onSubmit"
                >

                  <!-- 🎮 单列清晰表单 - HCI最佳实践 -->
                  <div class="profile-fields-single">
                    
                    <!-- 引导提示卡片 -->
                    <div class="welcome-prompt">
                      <div class="prompt-icon">✨</div>
                      <div class="prompt-content">
                        <h4>Complete Your Profile!</h4>
                        <p>Tell us about yourself to unlock full features</p>
                      </div>
                    </div>

                    <!-- Basic Info Section -->
                    <div class="field-group">
                      <div class="group-header">
                        <span class="group-icon">👤</span>
                        <h3 class="group-title">Basic Information</h3>
                      </div>
                      
                      <div class="field-row">
                        <div class="field-item">
                          <label class="field-label">
                            Username <span class="required">*</span>
                          </label>
                          <v-text-field 
                            v-model="form.username" 
                            placeholder="Enter your username (e.g., john_doe)"
                            :rules="[rules.required]" 
                            variant="outlined"
                            density="comfortable"
                            hide-details="auto"
                            clearable
                          />
                        </div>

                        <div class="field-item">
                          <label class="field-label">
                            Email <span class="required">*</span>
                          </label>
                          <v-text-field 
                            v-model="form.email" 
                            placeholder="your.email@example.com"
                            :rules="[rules.email]"
                            variant="outlined"
                            density="comfortable"
                            hide-details="auto"
                            clearable
                          />
                        </div>
                      </div>

                      <div class="field-row">
                        <div class="field-item">
                          <label class="field-label">First Name</label>
                          <v-text-field 
                            v-model="form.first_name" 
                            placeholder="John"
                            variant="outlined"
                            density="comfortable"
                            hide-details="auto"
                            clearable
                          />
                        </div>
                        <div class="field-item">
                          <label class="field-label">Last Name</label>
                          <v-text-field 
                            v-model="form.last_name" 
                            placeholder="Doe"
                            variant="outlined"
                            density="comfortable"
                            hide-details="auto"
                            clearable
                          />
                        </div>
                      </div>

                      <div class="field-item">
                        <label class="field-label">Bio</label>
                        <v-textarea 
                          v-model="form.bio" 
                          placeholder="Tell us a bit about yourself... 🌟"
                          rows="2" 
                          auto-grow
                          variant="outlined"
                          density="comfortable"
                          hide-details="auto"
                          clearable
                        />
                      </div>
                    </div>

                    <!-- Additional Info Section -->
                    <div class="field-group">
                      <div class="group-header">
                        <span class="group-icon">📋</span>
                        <h3 class="group-title">Additional Information</h3>
                      </div>

                      <div class="field-row">
                        <div class="field-item">
                          <label class="field-label">Birth Date</label>
                          <v-dialog v-model="birthDlg" width="290" persistent>
                            <template #activator="{ props }">
                              <v-text-field
                                v-bind="props" 
                                readonly 
                                variant="outlined"
                                placeholder="Select your birth date"
                                prepend-inner-icon="mdi-calendar"
                                :model-value="formattedBirth"
                                density="comfortable"
                                hide-details="auto"
                              />
                            </template>
                            <v-card>
                              <v-date-picker v-model="birthTemp" color="green" />
                              <v-card-actions class="justify-end">
                                <v-btn text @click="confirmBirth">Done</v-btn>
                              </v-card-actions>
                            </v-card>
                          </v-dialog>
                        </div>

                        <div class="field-item">
                          <label class="field-label">Phone</label>
                          <v-text-field 
                            v-model="form.phone" 
                            placeholder="+1 (555) 123-4567"
                            :rules="[rules.phone]" 
                            variant="outlined"
                            density="comfortable"
                            hide-details="auto"
                            clearable
                          />
                        </div>
                      </div>

                      <div class="field-row">
                        <div class="field-item">
                          <label class="field-label">Address</label>
                          <v-text-field 
                            v-model="form.address" 
                            placeholder="123 Main St, City, Country"
                            variant="outlined"
                            density="comfortable"
                            hide-details="auto"
                            clearable
                          />
                        </div>

                        <div class="field-item">
                          <label class="field-label">Timezone</label>
                          <v-select 
                            v-model="form.timezone" 
                            :items="timezones"
                            placeholder="Select your timezone"
                            variant="outlined"
                            density="comfortable"
                            hide-details="auto"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- save btn -->
                                    <!-- 🎮 游戏化提交按钮 -->
                  <div class="profile-actions">
                    <button 
                      type="submit" 
                      class="game-submit-btn"
                      :disabled="!canSave || submitting"
                    >
                      <span v-if="!submitting">💾 Save Profile</span>
                      <span v-else>⚡ Saving...</span>
                    </button>
                  </div>
                </v-form>
        </div><!-- .profile-edit-container -->
      </div><!-- .right-panel -->
      
    </div><!-- .game-dual-layout -->

    <!-- 🎮 游戏化Toast -->
    <div v-if="snackbar.show" :class="['game-toast', snackbar.color]">
      {{ snackbar.text }}
    </div>
  </v-app>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { useRouter } from 'vue-router'
import { usePetStore } from '@/stores/petStore'
import PetRenderer from '@/components/PetRenderer.vue'
import PetStage from '@/components/PetStage.vue'
import ScreenshotShare from '@/components/ScreenshotShare.vue'

const ORIGIN = import.meta.env.VITE_API_BASE_URL?.replace('/api', '') || location.origin
const fix = (u?: string) => {
  if (!u) return ''
  if (u.startsWith('http')) {
    // Handle various source URLs:
    // - web:911 (docker container)
    // - localhost:911 (local dev)
    // - <PRODUCTION_HOST>:911 (production)
    return u.replace(
      /^https?:\/\/(web|localhost|45\.79\.163\.242):\d+/i, 
      ORIGIN
    )
  }
  // For relative URLs, prepend with correct origin
  return ORIGIN + u
}

/* ╭─ constants ───────────────────────────────╮ */
const MAX_AVATAR = 5 * 1024 * 1024
const maxMB      = (MAX_AVATAR/1048576).toFixed(0)
const MIME       = ['image/jpeg','image/png','image/webp','image/gif']
const fmtChips   = ['JPG','PNG','WEBP','GIF']
import defaultAvatar from '@/assets/default-avatar.png'
const MS_PER_HOUR = 60 * 60 * 1000

/* ╭─ stores / state ───────────────────────────╮ */
const userStore = useUserStore()
const avatarFile = ref<File|null>(null)
const avatarPreview = ref<string>(defaultAvatar)
const previewURL   = ref<string|null>(null)
const router    = useRouter()
const petStore  = usePetStore()

// Couple
const couple     = computed(() => userStore.couple)
const isCoupled  = computed(() => !!couple.value &&
  (couple.value.is_complete || (couple.value.members?.length || 0) >= 2)
)
const meAvatar   = computed(() => fix(userStore.user?.avatar_url ?? undefined) || defaultAvatar)
const meName     = computed(() => userStore.user?.username || 'You')
const partnerUser= computed(() => couple.value?.members?.find(m => m.id !== userStore.user?.id))
const paAvatar   = computed(() => fix(partnerUser.value?.avatar_url ?? undefined) || defaultAvatar)
const paName     = computed(() => partnerUser.value?.username || 'Partner')
const coupleCode = computed(() => couple.value?.code || '')
const coupleName = computed(() => couple.value?.name || '')
const hoursSince = computed(() => {
  const t = couple.value?.created_at
  return t ? Math.floor((Date.now() - Date.parse(t)) / MS_PER_HOUR) : 0
})

// Pet
const ASSET_DIR   = '/biped/'
const eggFile     = 'egg.glb'
const pet         = computed(() => petStore.pet!)
const petStatus   = computed(() => petStore.petStatus)
const petNickname = computed(() => pet.value?.nickname || 'Your Pet')
const petLevel    = computed(() => pet.value?.level || 0)
const hasPet      = computed(() => !!petStore.pet)
const celebrating = ref(false)

// XP 百分比
const xpPercent = computed(() => {
  const p = pet.value
  if (!p) return 0
  // Calculate next level XP based on current level (100 XP per level)
  const nextLevelXp = (p.level + 1) * 100
  const currentLevelXp = p.level * 100
  const xpInCurrentLevel = p.xp - currentLevelXp
  return Math.min(100, Math.floor((xpInCurrentLevel / (nextLevelXp - currentLevelXp)) * 100))
})

// 心情
const moodValue = computed(() => (petStatus.value as any)?.happiness ?? 0)
const moodEmoji = computed(() => {
  const h = moodValue.value
  return h >= 80 ? '😄'
       : h >= 60 ? '🙂'
       : h >= 40 ? '😐'
       : h >= 20 ? '🙁'
       : '😢'
})
const moodText  = computed(() => {
  const h = moodValue.value
  return h >= 80 ? 'Awesome'
       : h >= 60 ? 'Good'
       : h >= 40 ? 'Okay'
       : h >= 20 ? 'Sad'
       : 'Down'
})

const form = reactive({
  username:'', email:'', first_name:'', last_name:'',
  bio:'', birth_date:null as string|null,
  phone:'', address:'', timezone:'UTC',
})

/* ui */
const loading   = ref(true)
const submitting= ref(false)
const valid     = ref(false)
const dirty     = ref(false)
const errorMsg  = ref('')
const mainTab   = ref<'couple'|'profile'>('couple') // Main tab for switching between couple and profile view
const tab       = ref<'basic'|'more'>('basic')
const snackbar  = reactive({show:false,text:'',color:'success'})
const birthDlg  = ref(false)
const birthTemp = ref<string|null>(null)
const formRef   = ref<any>()

/* select list */
const timezones=['UTC','America/Phoenix','America/New_York','Europe/London','Asia/Shanghai']

/* ╭─ validation ───────────────────────────────╮ */
const rules = {
  required:(v:any)=>!!v||'Required',
  email   :(v: string) => !v || /^\S+@\S+\.\S+$/.test(v) || 'Invalid email',
  phone   :(v:string)=>!v||/^\+?[0-9\- ]{7,15}$/.test(v)||'Invalid phone',
  avatar  :(f:File|null)=>{
    if(!f) return true
    if(f.size > MAX_AVATAR)        return `≤${maxMB} MB`
    if(!MIME.includes(f.type))     return 'Unsupported format'
    return true
  },
}

/* ╭─ computed ────────────────────────────────╮ */
const showRemove   = computed(()=> !!avatarFile.value || avatarPreview.value!==defaultAvatar)
const avatarHint   = computed(()=> avatarFile.value
  ? `${avatarFile.value.name} • ${(avatarFile.value.size/1048576).toFixed(1)} MB`
  : `≤${maxMB} MB • ${fmtChips.join('/')}`)

const formattedBirth = computed(()=> form.birth_date ?? '—')
const canSave = computed(()=> valid.value && dirty.value && !submitting.value)

/* hearts progress */
const progressColor = (n:number)=> n <= (dirty.value ? 3 : 1)
  ? 'pink-accent-2' : 'grey-lighten-1'

/* ╭─ watchers ────────────────────────────────╮ */
watch(form, ()=>{ dirty.value=true }, {deep:true})
watch(avatarFile, ()=>{ dirty.value=true })

/* ╭─ helpers ─────────────────────────────────╮ */
function toast(t:string,c='success'){ Object.assign(snackbar,{show:true,text:t,color:c}) }
function revoke(){ if(previewURL.value){ URL.revokeObjectURL(previewURL.value); previewURL.value=null }}

// Copy / Share - 现在使用新的ScreenshotShare组件
const copying = ref(false)
const screenshotComponent = ref<InstanceType<typeof ScreenshotShare>>()

async function copyCode() {
  if (!coupleCode.value) return
  copying.value = true
  addClickEffect('copy')
  
  await navigator.clipboard.writeText(coupleCode.value)
  copying.value = false
  toast('Code copied! 🎉')
}

// 🎯 mobile tuning的截图事件处理
function onCaptureStart() {
  console.log('📸 Screenshot capture started')
}

function onCaptureSuccess(data: any) {
  console.log('✅ Screenshot captured successfully:', data)
  toast('Screenshot captured! 📸✨')
}

function onCaptureError(error: any) {
  console.error('❌ Screenshot failed:', error)
  toast('Screenshot failed 😢', 'error')
}

function onShareSuccess(data: any) {
  console.log('📤 Share successful:', data)
  toast('Shared successfully! 🔗')
}

function onShareError(error: any) {
  console.error('📤 Share failed:', error)
  toast('Share failed, but image is saved! 💾', 'warning')
}

// 🎯 集成到游戏按钮的分享功能
async function handleShare() {
  if (!screenshotComponent.value) {
    toast('Screenshot feature not available', 'error')
    return
  }
  
  try {
    // 添加点击反馈
    addClickEffect('share')
    
    // 使用ScreenshotShare组件的截图功能
    await screenshotComponent.value.captureAndShare()
  } catch (error) {
    console.error('Share failed:', error)
    toast('Share failed 😢', 'error')
  }
}

// 🎯 增强按钮点击反馈
function addClickEffect(buttonType: string) {
  const button = document.querySelector(`.btn.${buttonType}`)
  if (button) {
    button.classList.add('clicked')
    setTimeout(() => {
      button.classList.remove('clicked')
    }, 300)
  }
}

// 增强其他按钮的反馈
// copyCode 和 goMemories 函数已在上面定义，不需要重复

// onShare is gone; the ScreenshotShare component handles it
// async function onShare() { ... } // 已移除

// 蛋抖动
import type { ComponentPublicInstance } from 'vue'
const egg = ref<ComponentPublicInstance>()
function bounceEgg() {
  const el = (egg.value as any)?.$el as HTMLElement
  if (!el) return
  el.classList.add('bounce')
  setTimeout(() => el.classList.remove('bounce'), 600)
}

// 跳转 Memories
function goMemories() {
  addClickEffect('memory')
  router.push('/battle_history')
}

// 🎯 performance: the duplicate onMounted is gone; loadProfile below covers it
// line 702 already has onMounted(loadProfile)

/* avatar events */
function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0] || null
  onAvatarChange(file)
}

function onAvatarChange(file:File|null){
  revoke()
  avatarFile.value = file
  if(!file){
    avatarPreview.value = fix(userStore.avatar) || defaultAvatar
    return
  }
  const chk = rules.avatar(file)
  if(chk!==true){ toast(chk as string,'error'); avatarFile.value=null; return }
  previewURL.value    = URL.createObjectURL(file)
  avatarPreview.value = previewURL.value
}
function removeAvatar(){ avatarFile.value=null; revoke(); avatarPreview.value=defaultAvatar }
function onImageError(){ avatarPreview.value = defaultAvatar }

/* date */
function confirmBirth(){
  form.birth_date = birthTemp.value
  birthDlg.value  = false
  dirty.value     = true
}

/* load profile */
async function loadProfile(){
  loading.value = true
  try{
    await userStore.fetchProfile()
    const u=userStore.user!
    Object.assign(form,{
      username:u.username,email:u.email,
      first_name:u.first_name||'',last_name:u.last_name||'',
      bio:u.bio||'',birth_date:u.birth_date,
      phone:u.phone||'',address:u.address||'',timezone:u.timezone||'UTC',
    })
    avatarPreview.value = fix(userStore.avatar) || defaultAvatar
    avatarFile.value    = null
    dirty.value         = false
    errorMsg.value      = ''
  }catch{ errorMsg.value='Failed to load profile.' }
  finally{ loading.value=false }
}
onMounted(loadProfile)

/* reset */
function onReset(){
  formRef.value?.resetValidation(); removeAvatar(); loadProfile()
}

/* submit */
async function onSubmit(){
  if(!formRef.value.validate()){ toast('Fix validation errors','error'); return }
  submitting.value=true; errorMsg.value=''

  try{
    /* 1. prepare body; ''→null */
    const bodyObj:Record<string,any> = {}
    Object.entries(form).forEach(([k,v])=>{
      bodyObj[k]=v===''?null:v
    })

    /* 2. choose FormData if avatar chosen */
    let payload:FormData|Record<string,any>
    if(avatarFile.value){
      payload=new FormData()
      payload.append('avatar',avatarFile.value)
      Object.entries(bodyObj).forEach(([k,v])=>{
        if(v!==null && v!==undefined) payload.append(k,String(v))
      })
    }else{
      payload=bodyObj
    }

    /* 3. call API */
    await userStore.updateProfile(payload)
    
    // 🎯 performance: updateProfile has already refreshed userStore.user
    // read the latest state from the store; no need to fetch the profile again
    const u = userStore.user!
    Object.assign(form, {
      username: u.username, email: u.email,
      first_name: u.first_name || '', last_name: u.last_name || '',
      bio: u.bio || '', birth_date: u.birth_date,
      phone: u.phone || '', address: u.address || '', timezone: u.timezone || 'UTC',
    })
    avatarPreview.value = fix(userStore.avatar) || defaultAvatar
    avatarFile.value = null
    dirty.value = false
    
    toast('Saved! Your profile looks delicious 🍑')
    await nextTick(() => window.scrollTo({ top: 0, behavior: 'smooth' }))
  }catch(e){
    console.error(e); errorMsg.value='Update failed. Please retry.'
    toast('Update failed','error')
  }finally{ submitting.value=false }
}
</script>

<style scoped>
/* 🎮 ===============================================
   AAA游戏化布局 - HCItuning + 美工精准调整
   =============================================== */

/* 全局背景 - 固定高度，消除滚动 */
.profile-view {
  background: linear-gradient(
    135deg,
    #0f172a 0%,
    #1e1b4b 25%,
    #312e81 50%,
    #1e293b 75%,
    #0f172a 100%
  );
  background-size: 400% 400%;
  animation: gameArenaFlow 20s ease infinite;
  height: 100vh;
  overflow: hidden; /* 消除整体滚动 */
  position: relative;
}

@keyframes gameArenaFlow {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* 🎮 HCItuning：超紧凑的左右功能分区 */
.game-dual-layout {
  display: grid;
  grid-template-columns: 28% 71%; /* tuning比例：左侧更紧凑 */
  gap: 0.6rem;
  height: 100vh;
  padding: 0.4rem;
  max-width: 100%;
  margin: 0;
  box-sizing: border-box;
  
  /* 🌟 游戏一体化视觉 */
  background: linear-gradient(
    135deg,
    rgba(15, 23, 42, 0.6) 0%,
    rgba(30, 27, 75, 0.6) 50%,
    rgba(15, 23, 42, 0.6) 100%
  );
  border: 5px solid rgba(168, 230, 207, 0.4);
  border-radius: 0;
  box-shadow: 
    inset 0 0 120px rgba(168, 230, 207, 0.12),
    inset 0 0 50px rgba(168, 230, 207, 0.08),
    0 0 140px rgba(0, 0, 0, 0.8),
    0 0 100px rgba(168, 230, 207, 0.25);
}

/* 🎮 左侧面板：展示区 - 固定高度 */
.left-panel {
  height: calc(100vh - 1.4rem);
  overflow-y: hidden;
  overflow-x: hidden;
  
  /* 🌟 统一背景和边框 */
  background: rgba(20, 20, 30, 0.75);
  border: 3px solid rgba(168, 230, 207, 0.35);
  border-radius: 10px;
  box-shadow: 
    inset 0 0 70px rgba(168, 230, 207, 0.05),
    0 4px 30px rgba(0, 0, 0, 0.5);
  
  /* tuning滚动条 - 更细更优雅 */
  scrollbar-width: thin;
  scrollbar-color: rgba(168, 230, 207, 0.5) rgba(20, 20, 30, 0.3);
}

.left-panel::-webkit-scrollbar {
  width: 5px;
}

.left-panel::-webkit-scrollbar-track {
  background: rgba(20, 20, 30, 0.3);
  border-radius: 10px;
}

.left-panel::-webkit-scrollbar-thumb {
  background: rgba(168, 230, 207, 0.4);
  border-radius: 10px;
  transition: background 0.3s ease;
}

.left-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(168, 230, 207, 0.7);
}

/* 🎮 右侧面板：编辑区 - 固定高度 */
.right-panel {
  height: calc(100vh - 1.4rem);
  overflow-y: auto;
  overflow-x: hidden;
  
  /* 🌟 统一背景和边框 - 与左侧呼应 */
  background: rgba(20, 20, 30, 0.75);
  border: 3px solid rgba(168, 230, 207, 0.35);
  border-radius: 10px;
  box-shadow: 
    inset 0 0 70px rgba(168, 230, 207, 0.05),
    0 4px 30px rgba(0, 0, 0, 0.5);
  
  /* tuning滚动条 */
  scrollbar-width: thin;
  scrollbar-color: rgba(168, 230, 207, 0.5) rgba(20, 20, 30, 0.3);
}

.right-panel::-webkit-scrollbar {
  width: 5px;
}

.right-panel::-webkit-scrollbar-track {
  background: rgba(20, 20, 30, 0.3);
  border-radius: 10px;
}

.right-panel::-webkit-scrollbar-thumb {
  background: rgba(168, 230, 207, 0.4);
  border-radius: 10px;
  transition: background 0.3s ease;
}

.right-panel::-webkit-scrollbar-thumb:hover {
  background: rgba(168, 230, 207, 0.7);
}

.profile-edit-container {
  background: transparent;
  backdrop-filter: none;
  border: none;
  border-radius: 0;
  padding: 0.6rem 1rem;
  box-shadow: none;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* 🎯 页面标题区 - 超紧凑 */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 0.5rem;
  margin-bottom: 0.8rem;
  border-bottom: 2px solid rgba(168, 230, 207, 0.3);
}

.header-content {
  flex: 1;
}

.page-title {
  font-size: 1.4rem;
  font-weight: 800;
  color: rgba(168, 230, 207, 0.95);
  text-shadow: 
    0 0 20px rgba(168, 230, 207, 0.4),
    0 0 40px rgba(168, 230, 207, 0.2);
  margin: 0;
  letter-spacing: 0.3px;
  line-height: 1.2;
}

.page-subtitle {
  font-size: 0.8rem;
  color: rgba(168, 230, 207, 0.6);
  margin: 0.2rem 0 0 0;
  line-height: 1.2;
}

.reset-btn {
  transition: all 0.3s ease;
}

.reset-btn:hover {
  transform: rotate(180deg);
  background: rgba(168, 230, 207, 0.1) !important;
}

/* 🎮 响应式：移动端垂直堆叠 */
@media (max-width: 1024px) {
  .game-dual-layout {
    grid-template-columns: 1fr;
    gap: 1rem;
    padding: 0.5rem;
    height: auto;
    min-height: 100vh;
    overflow-y: auto;
  }
  
  .left-panel,
  .right-panel {
    height: auto;
    overflow-y: visible;
  }
  
  .field-row {
    grid-template-columns: 1fr !important; /* 移动端所有字段单列 */
  }
  
  .profile-fields-single {
    max-width: 100%;
  }
}

/* 🎮 平板tuning */
@media (min-width: 1024px) and (max-width: 1400px) {
  .game-dual-layout {
    grid-template-columns: 32% 67%;
  }
}

/* 🎮 大屏tuning */
@media (min-width: 1600px) {
  .game-dual-layout {
    grid-template-columns: 28% 71%; /* 大屏tuning比例 */
    gap: 1.2rem;
  }
  
  .profile-fields-single {
    max-width: 900px;
  }
}

/* 🎮 ===============================================
   左侧：Couple区域样式 - 紧凑tuning
   =============================================== */

.couple-view {
  background: transparent;
  backdrop-filter: none;
  border: none;
  border-radius: 0;
  padding: 0.5rem;
  box-shadow: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  height: 100%;
  justify-content: space-between;
}

/* � AAA级头像编辑区 - 高级感层次 */
.avatar-edit-aaa {
  display: flex;
  align-items: center;
  gap: 1rem;
  width: 100%;
  max-width: 100%;
  padding: 1rem 1.2rem;
  background: linear-gradient(135deg,
    rgba(5, 10, 20, 0.6) 0%,
    rgba(10, 15, 25, 0.5) 100%);
  border-radius: 14px;
  border: 1.5px solid rgba(168, 230, 207, 0.25);
  box-shadow: 
    0 4px 16px rgba(0, 0, 0, 0.3),
    inset 0 1px 1px rgba(168, 230, 207, 0.05);
  backdrop-filter: blur(30px) saturate(150%);
  transition: all 0.3s ease;
}

.avatar-edit-aaa:hover {
  border-color: rgba(168, 230, 207, 0.35);
  box-shadow: 
    0 6px 20px rgba(0, 0, 0, 0.35),
    inset 0 1px 1px rgba(168, 230, 207, 0.08),
    0 0 30px rgba(168, 230, 207, 0.08);
}

.avatar-display-zone {
  position: relative;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3rem;
}

.avatar-hint {
  font-size: 0.7rem;
  color: rgba(168, 230, 207, 0.65);
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.avatar-edit-aaa .avatar-preview {
  border: 2.5px solid rgba(168, 230, 207, 0.4) !important;
  box-shadow: 
    0 4px 20px rgba(168, 230, 207, 0.25),
    0 0 30px rgba(168, 230, 207, 0.15),
    inset 0 0 20px rgba(168, 230, 207, 0.08) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  animation: avatarGlowSubtle 3s ease-in-out infinite;
}

/* 🎮 头像微妙呼吸光效 - 高级感 */
@keyframes avatarGlowSubtle {
  0%, 100% {
    box-shadow: 
      0 4px 20px rgba(168, 230, 207, 0.25),
      0 0 30px rgba(168, 230, 207, 0.15),
      inset 0 0 20px rgba(168, 230, 207, 0.08);
    border-color: rgba(168, 230, 207, 0.4);
  }
  50% {
    box-shadow: 
      0 6px 28px rgba(168, 230, 207, 0.35),
      0 0 45px rgba(168, 230, 207, 0.25),
      inset 0 0 28px rgba(168, 230, 207, 0.12);
    border-color: rgba(168, 230, 207, 0.55);
  }
}

.avatar-edit-aaa .avatar-preview:hover {
  transform: scale(1.08);
  animation: none;
  box-shadow: 
    0 8px 40px rgba(168, 230, 207, 0.45),
    0 0 60px rgba(168, 230, 207, 0.35),
    inset 0 0 40px rgba(168, 230, 207, 0.15) !important;
  border-color: rgba(168, 230, 207, 0.7) !important;
}

.remove-avatar {
  position: absolute;
  top: -6px;
  right: -6px;
  background: rgba(239, 68, 68, 0.95) !important;
  z-index: 2;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
}

/* 🎮 AAA级上传按钮区域 */
.upload-action-zone {
  flex: 1;
  min-width: 0;
}

.hidden-file-input {
  display: none;
}

.upload-trigger-btn {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  width: 100%;
  padding: 0.75rem 1.1rem;
  background: linear-gradient(135deg,
    rgba(168, 230, 207, 0.12) 0%,
    rgba(134, 239, 172, 0.08) 100%);
  border: 1.5px solid rgba(168, 230, 207, 0.3);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.15),
    inset 0 1px 1px rgba(168, 230, 207, 0.05);
}

.upload-trigger-btn:hover {
  background: linear-gradient(135deg,
    rgba(168, 230, 207, 0.18) 0%,
    rgba(134, 239, 172, 0.12) 100%);
  border-color: rgba(168, 230, 207, 0.5);
  transform: translateY(-1px);
  box-shadow: 
    0 4px 16px rgba(168, 230, 207, 0.15),
    0 0 20px rgba(168, 230, 207, 0.08),
    inset 0 1px 2px rgba(168, 230, 207, 0.08);
}

.upload-trigger-btn:active {
  transform: translateY(0) scale(0.98);
  filter: brightness(0.95);
}

.upload-trigger-btn:focus-visible {
  outline: 2px solid rgba(168, 230, 207, 0.8);
  outline-offset: 2px;
}

.upload-icon {
  font-size: 1.8rem;
  flex-shrink: 0;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.upload-text {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  text-align: left;
  flex: 1;
}

.upload-text strong {
  display: block;
  font-size: 0.88rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.2px;
}

.upload-text small {
  display: block;
  font-size: 0.7rem;
  font-weight: 500;
  color: rgba(168, 230, 207, 0.7);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
  letter-spacing: 0.1px;
}

.avatar-image {
  object-fit: cover;
  width: 100%;
  height: 100%;
}

/* 头像 & 连线 - 超紧凑 */
.faces-row {
  width: 100%;
  max-width: 100%;
  position: relative; 
  z-index: 2;
  display: flex; 
  align-items: center; 
  gap: 0.5rem;
  margin-bottom: 0.6rem;
}

.face { text-align: center; font-size: 0.75rem; flex: 1; }
.face-img {
  width: 48px; height: 48px; border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
  transition: transform .3s;
}
.face:hover .face-img { transform: scale(1.05) }
.face figcaption { margin-top: 0.2rem; line-height: 1.2; }
.connector {
  flex: 0 0 60px; height: 30px; overflow: visible;
  animation: wave 3s infinite ease-in-out;
}
@keyframes wave {
  0%,100%{transform: translateY(0)}50%{transform: translateY(1px)}
}
.connector-path { stroke-linecap: round; }
.connector path { stroke-width: 3; }

/* 蛋 / 宠物 - 超紧凑 */
.pet-zone { 
  text-align: center; 
  margin-bottom: 0.6rem;
  width: 100%;
  max-width: 100%;
}
.egg-wrapper { 
  position: relative; 
  width: 100px; 
  height: 100px; 
  cursor: pointer;
  margin: 0 auto;
}
.tap-tip { 
  font-size: 0.75rem; 
  margin-top: 0.4rem; 
  line-height: 1.2;
}
.egg-glow {
  position:absolute; inset:0;
  box-shadow: 0 0 20px 8px rgba(255,111,165,0.5);
  border-radius:50%; opacity:0;
  animation: glow 0.8s ease-out forwards;
}
@keyframes glow { from{opacity:1} to{opacity:0} }
.egg { width:100%; height:100%; }
.egg.bounce { animation:bounce 0.6s; }
@keyframes bounce { 0%,100%{transform:translateY(0)}50%{transform:translateY(-12px)} }
.pet-wrapper { 
  display: flex; 
  flex-direction: column; 
  align-items: center; 
  width: 100%;
}
.pet-card {
  width: 140px;
  height: 140px;
  background: #e9f3ff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative; 
  overflow: hidden;
  animation: float 4s ease-in-out infinite;
}
@keyframes float { 0%,100%{transform: translateY(0)}50%{transform: translateY(-5px)} }
.pet-card.celebrating { animation: celebrate 0.8s ease-in-out; }
@keyframes celebrate { 0%{transform:scale(1)}50%{transform:scale(1.07)}100%{transform:scale(1)} }
.sparkle {
  position:absolute; inset:0;
  background:url('https://cdn.jsdelivr.net/gh/niklasvh/html2canvas-tests@main/assets/fireworks.gif')
    center/cover no-repeat; mix-blend-mode: screen; pointer-events:none;
}
.pet-info { margin-top:0.3rem; text-align:center; }
.pet-name { font-size:0.9rem; font-weight:700; color:rgba(168, 230, 207, 0.85); line-height:1.2; }
.pet-level { font-size:0.75rem; color:rgba(255, 255, 255, 0.95); margin-top:0.1rem; line-height:1.2; }
.xp-bar {
  width:120px; height:5px; background:#ddd; border-radius:2px;
  overflow:hidden; margin:0.25rem auto 0;
}
.xp-fill { height:100%; background:#4cafef; }
.mood { margin-top:0.2rem; font-size:0.75rem; color:rgba(255, 255, 255, 0.85); line-height:1.2; }

/* 🎮 AAA情侣卡片 - 优雅克制的层次感 */
.couple-card {
  width: 100%; 
  max-width: 100%;
  background: linear-gradient(135deg,
    rgba(5, 10, 20, 0.65) 0%,
    rgba(10, 15, 25, 0.55) 100%);
  padding: 1rem;
  border-radius: 14px; 
  text-align: center;
  border: 1.5px solid rgba(168, 230, 207, 0.25);
  box-shadow: 
    0 4px 16px rgba(0, 0, 0, 0.3),
    inset 0 1px 1px rgba(168, 230, 207, 0.05);
  margin-top: auto;
  backdrop-filter: blur(30px) saturate(150%);
  transition: all 0.3s ease;
}

.couple-card:hover {
  border-color: rgba(168, 230, 207, 0.35);
  box-shadow: 
    0 6px 20px rgba(0, 0, 0, 0.35),
    inset 0 1px 1px rgba(168, 230, 207, 0.08),
    0 0 30px rgba(168, 230, 207, 0.08);
}

.couple-card h2 { 
  font-size: 1.05rem; 
  font-weight: 700; 
  margin-bottom: 0.5rem;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 
    0 2px 6px rgba(0, 0, 0, 0.4),
    0 0 15px rgba(168, 230, 207, 0.15);
  line-height: 1.35;
  letter-spacing: 0.3px;
}

.code, .since { 
  margin: 0.35rem 0; 
  color: rgba(255, 255, 255, 0.85); 
  font-size: 0.82rem;
  line-height: 1.45;
  font-weight: 500;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.code strong {
  color: rgba(168, 230, 207, 0.85);
  text-shadow: 0 0 6px rgba(168, 230, 207, 0.15);
  letter-spacing: 0.8px;
  font-weight: 600;
}
.btn-row {
  display: flex; 
  gap: 0.5rem; 
  justify-content: center; 
  margin: 0.6rem 0;
  flex-wrap: wrap;
}

.btn {
  flex: 1; 
  min-width: 80px;
  padding: 0.6rem 0.85rem; 
  border: 1.5px solid rgba(168, 230, 207, 0.3);
  border-radius: 9px;
  color: rgba(15, 23, 42, 0.95);
  background: rgba(30, 27, 75, 0.3);
  font-weight: 650; 
  font-size: 0.78rem;
  cursor: pointer; 
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex; 
  justify-content: center; 
  align-items: center;
  min-height: 38px;
  box-shadow: 
    0 2px 8px rgba(0, 0, 0, 0.25),
    inset 0 1px 1px rgba(255, 255, 255, 0.05);
  line-height: 1.35;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}
/* 🎮 AAA级按钮 - 优雅的渐进式绿色主题 */
.btn.copy { 
  background: linear-gradient(135deg, 
    rgba(168, 230, 207, 0.75), 
    rgba(134, 239, 172, 0.7));
  border-color: rgba(168, 230, 207, 0.5);
  color: rgba(15, 23, 42, 0.95);
  font-weight: 700;
  box-shadow: 
    0 3px 12px rgba(168, 230, 207, 0.2),
    inset 0 -1px 2px rgba(0, 0, 0, 0.15);
}
.btn.share { 
  background: linear-gradient(135deg, 
    rgba(168, 230, 207, 0.65), 
    rgba(134, 239, 172, 0.6));
  border-color: rgba(168, 230, 207, 0.4);
  color: rgba(15, 23, 42, 0.95);
  font-weight: 700;
  box-shadow: 
    0 3px 12px rgba(168, 230, 207, 0.15),
    inset 0 -1px 2px rgba(0, 0, 0, 0.15);
}
.btn.memory { 
  background: linear-gradient(135deg, 
    rgba(168, 230, 207, 0.55), 
    rgba(134, 239, 172, 0.5));
  border-color: rgba(168, 230, 207, 0.35);
  color: rgba(15, 23, 42, 0.95);
  font-weight: 700;
  box-shadow: 
    0 3px 12px rgba(168, 230, 207, 0.12),
    inset 0 -1px 2px rgba(0, 0, 0, 0.15);
}
.btn:disabled { opacity:0.5; cursor:not-allowed }
.btn:hover:not(:disabled){ 
  transform: translateY(-2px) scale(1.02);
  filter: brightness(1.12) saturate(1.05);
  border-color: rgba(168, 230, 207, 0.6);
}

.btn.copy:hover:not(:disabled) {
  box-shadow: 
    0 5px 20px rgba(168, 230, 207, 0.28),
    0 0 25px rgba(168, 230, 207, 0.15),
    inset 0 -1px 2px rgba(0, 0, 0, 0.15);
}

.btn.share:hover:not(:disabled) {
  box-shadow: 
    0 5px 20px rgba(168, 230, 207, 0.25),
    0 0 25px rgba(168, 230, 207, 0.12),
    inset 0 -1px 2px rgba(0, 0, 0, 0.15);
}

.btn.memory:hover:not(:disabled) {
  box-shadow: 
    0 5px 20px rgba(168, 230, 207, 0.22),
    0 0 25px rgba(168, 230, 207, 0.1),
    inset 0 -1px 2px rgba(0, 0, 0, 0.15);
}

.btn:active:not(:disabled) {
  transform: translateY(0) scale(0.99);
  filter: brightness(0.95);
  transition: transform 0.1s ease;
}
.loader {
  width:1em; height:1em;
  border:3px solid rgba(255,255,255,0.3);
  border-top-color:#fff; 
  border-radius:50%;
  animation:spin .8s linear infinite;
  display: inline-block;
}

@keyframes spin { 
  to{transform:rotate(360deg)} 
}

/* 🎯 游戏感按钮脉冲效果 */
@keyframes buttonPulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.02); }
  100% { transform: scale(1); }
}

.btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  animation: buttonPulse 1.5s ease-in-out infinite;
}

/* 🎯 按钮点击反馈 */
.btn.clicked {
  animation: clickEffect 0.3s ease;
}

@keyframes clickEffect {
  0% { transform: scale(1); }
  50% { transform: scale(0.95); }
  100% { transform: scale(1); }
}
.encourage { 
  margin-top: 0.7rem; 
  font-size: 0.8rem; 
  color: rgba(255, 255, 255, 0.75); 
  line-height: 1.45;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
  letter-spacing: 0.15px;
}

/* 🎯 AAA未配对状态 - 优雅邀请感 */
.couple-invite {
  text-align: center;
  padding: 1.8rem 1.4rem;
  background: linear-gradient(135deg,
    rgba(5, 10, 20, 0.65) 0%,
    rgba(10, 15, 25, 0.55) 100%);
  border-radius: 14px;
  border: 1.5px solid rgba(168, 230, 207, 0.3);
  box-shadow: 
    0 4px 16px rgba(0, 0, 0, 0.3),
    inset 0 1px 1px rgba(168, 230, 207, 0.05);
  margin: auto;
  max-width: 100%;
  width: 100%;
  backdrop-filter: blur(30px) saturate(150%);
  transition: all 0.3s ease;
}

.couple-invite:hover {
  border-color: rgba(168, 230, 207, 0.4);
  box-shadow: 
    0 6px 20px rgba(0, 0, 0, 0.35),
    inset 0 1px 1px rgba(168, 230, 207, 0.08),
    0 0 30px rgba(168, 230, 207, 0.08);
}

.couple-invite h3 {
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 0.7rem;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 
    0 2px 6px rgba(0, 0, 0, 0.4),
    0 0 15px rgba(168, 230, 207, 0.15);
  line-height: 1.35;
  letter-spacing: 0.3px;
}

.couple-invite p {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.82);
  margin-bottom: 1.2rem;
  font-weight: 500;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  line-height: 1.5;
  line-height: 1.3;
}

.invite-btn {
  background: linear-gradient(135deg, 
    rgba(168, 230, 207, 0.7), 
    rgba(134, 239, 172, 0.65));
  color: rgba(15, 23, 42, 0.95);
  border: 1.5px solid rgba(168, 230, 207, 0.5);
  border-radius: 11px;
  padding: 0.75rem 2rem;
  font-size: 0.88rem;
  font-weight: 700;
  cursor: pointer;
  line-height: 1.35;
  letter-spacing: 0.3px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 
    0 3px 16px rgba(168, 230, 207, 0.2),
    inset 0 -1px 2px rgba(0, 0, 0, 0.15);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.15);
  
  /* 🎯 touch tuning for mobile */
  min-height: 50px;
  -webkit-tap-highlight-color: transparent;
  touch-action: manipulation;
}

.invite-btn:hover {
  transform: translateY(-2px) scale(1.02);
  filter: brightness(1.12) saturate(1.05);
  border-color: rgba(168, 230, 207, 0.65);
  box-shadow: 
    0 5px 24px rgba(168, 230, 207, 0.28),
    0 0 30px rgba(168, 230, 207, 0.15),
    inset 0 -1px 2px rgba(0, 0, 0, 0.15);
}

.invite-btn:active {
  transform: translateY(0) scale(0.99);
  filter: brightness(0.95);
}

/* � ===============================================
   右侧：Profile编辑区游戏化样式
   =============================================== */

/* Profile标题栏 */
:deep(.v-toolbar) {
  background: transparent !important;
  border-bottom: 2px solid rgba(168, 230, 207, 0.2);
  margin-bottom: 1rem;
}

.gradient-text {
  font-size: 1.5rem !important;
  font-weight: 700;
  background: linear-gradient(135deg, #ffffff 0%, #a8e6cf 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: 0 0 20px rgba(168, 230, 207, 0.3);
}

/* 🎯 HCItuning：超紧凑单列表单布局 */
.profile-fields-single {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  max-width: 800px; /* 最佳阅读宽度 */
  margin: 0 auto;
}

/* 🌟 引导提示卡片 - 游戏化增强 */
.welcome-prompt {
  position: relative;
  background: linear-gradient(135deg, 
    rgba(168, 230, 207, 0.2) 0%, 
    rgba(134, 239, 172, 0.15) 100%);
  border: 2px solid rgba(168, 230, 207, 0.5);
  border-radius: 8px;
  padding: 0.6rem 0.8rem;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  box-shadow: 
    inset 0 0 40px rgba(168, 230, 207, 0.08),
    0 4px 20px rgba(168, 230, 207, 0.15),
    0 0 40px rgba(168, 230, 207, 0.1);
  overflow: hidden;
  animation: promptGlow 3s ease-in-out infinite;
}

/* 🎮 背景光效 */
.welcome-prompt::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, 
    transparent 30%, 
    rgba(168, 230, 207, 0.1) 50%, 
    transparent 70%);
  animation: shimmer 3s linear infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
  100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
}

@keyframes promptGlow {
  0%, 100% { 
    box-shadow: 
      inset 0 0 40px rgba(168, 230, 207, 0.08),
      0 4px 20px rgba(168, 230, 207, 0.15),
      0 0 40px rgba(168, 230, 207, 0.1);
  }
  50% { 
    box-shadow: 
      inset 0 0 40px rgba(168, 230, 207, 0.12),
      0 6px 30px rgba(168, 230, 207, 0.25),
      0 0 60px rgba(168, 230, 207, 0.2);
  }
}

.prompt-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
  animation: pulse 2s ease-in-out infinite;
  filter: drop-shadow(0 0 8px rgba(168, 230, 207, 0.5));
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.08); opacity: 0.85; }
}

.prompt-content {
  position: relative;
  z-index: 1;
}

.prompt-content h4 {
  font-size: 0.95rem;
  font-weight: 800;
  color: rgba(168, 230, 207, 1);
  margin: 0;
  text-shadow: 
    0 0 15px rgba(168, 230, 207, 0.5),
    0 2px 4px rgba(0, 0, 0, 0.3);
  line-height: 1.2;
  letter-spacing: 0.3px;
}

.prompt-content p {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(168, 230, 207, 0.85);
  margin: 0.15rem 0 0 0;
  line-height: 1.2;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

/* 📦 字段组 - 游戏化增强 */
.field-group {
  background: linear-gradient(135deg, 
    rgba(30, 27, 75, 0.4) 0%,
    rgba(20, 30, 50, 0.35) 100%);
  border: 2px solid rgba(168, 230, 207, 0.3);
  border-radius: 8px;
  padding: 0.7rem;
  box-shadow: 
    inset 0 0 40px rgba(168, 230, 207, 0.05),
    0 2px 15px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.field-group:hover {
  border-color: rgba(168, 230, 207, 0.4);
  box-shadow: 
    inset 0 0 40px rgba(168, 230, 207, 0.08),
    0 4px 20px rgba(168, 230, 207, 0.1);
}

.group-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.6rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid rgba(168, 230, 207, 0.25);
}

.group-icon {
  font-size: 1.2rem;
  flex-shrink: 0;
  filter: drop-shadow(0 0 6px rgba(168, 230, 207, 0.4));
}

.group-title {
  font-size: 0.95rem;
  font-weight: 800;
  color: rgba(168, 230, 207, 1);
  text-shadow: 
    0 0 15px rgba(168, 230, 207, 0.5),
    0 2px 4px rgba(0, 0, 0, 0.3);
  margin: 0;
  line-height: 1.2;
  letter-spacing: 0.3px;
}

/* 🎨 字段项 - 超紧凑label + input结构 */
.field-item {
  margin-bottom: 0.6rem;
}

.field-item:last-child {
  margin-bottom: 0;
}

.field-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 700;
  color: rgba(168, 230, 207, 0.95);
  margin-bottom: 0.25rem;
  letter-spacing: 0.3px;
  line-height: 1.2;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.field-label .required {
  color: rgba(239, 68, 68, 0.8);
  margin-left: 0.15rem;
}

/* 双列字段行（first name + last name等）*/
.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem;
  margin-bottom: 0.6rem;
}

.field-row:last-child {
  margin-bottom: 0;
}

.field-row .field-item {
  margin-bottom: 0;
}

/* 🎨 输入框HCItuning - 精准渲染 */
:deep(.v-text-field),
:deep(.v-textarea),
:deep(.v-select),
:deep(.v-file-input) {
  background: transparent !important;
  border-radius: 8px;
}

/* 🎮 AAA级输入框 - 优雅克制的层次 */
:deep(.v-field) {
  font-size: 0.93rem !important;
  background: linear-gradient(135deg, 
    rgba(5, 10, 20, 0.6) 0%,
    rgba(10, 15, 25, 0.5) 100%) !important;
  border-radius: 10px !important;
  backdrop-filter: blur(30px) saturate(150%) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: 
    0 2px 10px rgba(0, 0, 0, 0.2),
    inset 0 1px 1px rgba(168, 230, 207, 0.03) !important;
}

/* 输入框文字 - AAA级对比度 */
:deep(.v-field__input) {
  min-height: 42px !important;
  padding: 10px 16px !important;
  color: rgba(255, 255, 255, 0.98) !important;
  font-size: 0.95rem !important;
  font-weight: 600 !important;
  line-height: 1.6 !important;
  letter-spacing: 0.3px !important;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5) !important;
  -webkit-font-smoothing: antialiased !important;
  -moz-osx-font-smoothing: grayscale !important;
  text-rendering: optimizeLegibility !important;
}

/* Placeholder - 优雅对比 */
:deep(.v-field__input::placeholder),
:deep(input::placeholder),
:deep(textarea::placeholder) {
  color: rgba(168, 230, 207, 0.4) !important;
  opacity: 1 !important;
  font-size: 0.88rem !important;
  font-weight: 500 !important;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
}

/* 边框 - 微妙光效 */
:deep(.v-field__outline) {
  border-color: rgba(168, 230, 207, 0.25) !important;
  border-width: 1.5px !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  filter: drop-shadow(0 0 2px rgba(168, 230, 207, 0.08)) !important;
}

/* Focus状态 - 优雅激活 */
:deep(.v-field--focused) {
  background: linear-gradient(135deg, 
    rgba(5, 10, 20, 0.7) 0%,
    rgba(10, 15, 25, 0.65) 100%) !important;
  transform: translateY(-0.5px) !important;
  box-shadow: 
    0 4px 16px rgba(168, 230, 207, 0.12),
    0 2px 6px rgba(0, 0, 0, 0.3),
    inset 0 0 15px rgba(168, 230, 207, 0.04) !important;
}

:deep(.v-field--focused .v-field__outline) {
  border-color: rgba(168, 230, 207, 0.55) !important;
  border-width: 2px !important;
  filter: drop-shadow(0 0 8px rgba(168, 230, 207, 0.15)) !important;
}

:deep(.v-field--focused .v-field__input) {
  color: rgba(255, 255, 255, 1) !important;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4), 0 0 6px rgba(168, 230, 207, 0.1) !important;
}

/* Hover - 微妙预览 */
:deep(.v-field:hover:not(.v-field--focused)) {
  background: linear-gradient(135deg, 
    rgba(5, 10, 20, 0.65) 0%,
    rgba(10, 15, 25, 0.55) 100%) !important;
  box-shadow: 
    0 3px 12px rgba(0, 0, 0, 0.25),
    inset 0 1px 1px rgba(168, 230, 207, 0.05) !important;
}

:deep(.v-field:hover .v-field__outline) {
  border-color: rgba(168, 230, 207, 0.35) !important;
  filter: drop-shadow(0 0 4px rgba(168, 230, 207, 0.12)) !important;
}

/* 图标 - 优雅可见性 */
:deep(.v-field__prepend-inner),
:deep(.v-field__append-inner) {
  padding-top: 10px !important;
  color: rgba(168, 230, 207, 0.5) !important;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3)) !important;
}

:deep(.v-field--focused .v-field__prepend-inner),
:deep(.v-field--focused .v-field__append-inner) {
  color: rgba(168, 230, 207, 0.75) !important;
  filter: drop-shadow(0 0 4px rgba(168, 230, 207, 0.2)) !important;
}

/* Textarea - AAA可读性 */
:deep(.v-textarea .v-field__input) {
  padding: 12px 16px !important;
  line-height: 1.6 !important;
}

/* Select - AAA可读性 */
:deep(.v-select .v-field__input) {
  padding: 10px 16px !important;
}

/* 输入提示隐藏（已移到外部label）*/
:deep(.v-input__details) {
  min-height: 0 !important;
  padding-top: 0 !important;
  margin-top: 4px !important;
}

:deep(.v-messages) {
  font-size: 0.85rem !important;
  color: rgba(239, 68, 68, 0.8) !important;
}

/* 🎯 提交按钮 - CTA突出设计（紧凑版）*/
.profile-actions {
  display: flex;
  justify-content: center;
  margin-top: 0.6rem;
}

.game-submit-btn {
  min-width: 200px;
  padding: 0.75rem 2.5rem;
  font-size: 1rem;
  font-weight: 800;
  letter-spacing: 0.5px;
  border-radius: 10px;
  background: linear-gradient(135deg, 
    rgba(168, 230, 207, 1) 0%, 
    rgba(134, 239, 172, 1) 100%);
  border: 3px solid rgba(168, 230, 207, 0.8);
  color: rgba(15, 23, 42, 0.95);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 
    0 6px 20px rgba(168, 230, 207, 0.5),
    0 0 40px rgba(168, 230, 207, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.5),
    inset 0 -1px 0 rgba(0, 0, 0, 0.1);
  text-shadow: 
    0 1px 2px rgba(0, 0, 0, 0.2),
    0 0 10px rgba(255, 255, 255, 0.5);
  position: relative;
  overflow: hidden;
  animation: buttonPulse 2s ease-in-out infinite;
}

/* 🎮 呼吸光效 */
@keyframes buttonPulse {
  0%, 100% {
    box-shadow: 
      0 6px 20px rgba(168, 230, 207, 0.5),
      0 0 40px rgba(168, 230, 207, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.5);
  }
  50% {
    box-shadow: 
      0 8px 30px rgba(168, 230, 207, 0.7),
      0 0 60px rgba(168, 230, 207, 0.5),
      inset 0 1px 0 rgba(255, 255, 255, 0.6);
  }
}

.game-submit-btn::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.game-submit-btn:hover:not(:disabled)::before {
  width: 300px;
  height: 300px;
}

.game-submit-btn:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  filter: brightness(1.12) saturate(1.05);
  box-shadow: 
    0 6px 28px rgba(168, 230, 207, 0.35),
    0 0 50px rgba(168, 230, 207, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  border-color: rgba(168, 230, 207, 0.7);
  animation: none; /* 停止呼吸动画 */
}

.game-submit-btn:active:not(:disabled) {
  transform: translateY(-1px) scale(1);
}

.game-submit-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  background: linear-gradient(135deg, 
    rgba(100, 100, 100, 0.5) 0%, 
    rgba(80, 80, 80, 0.5) 100%);
  border-color: rgba(100, 100, 100, 0.3);
}

/* 🎮 游戏化Toast */
.game-toast {
  position: fixed;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10000;
  padding: 1rem 2rem;
  border-radius: 12px;
  background: rgba(20, 20, 30, 0.95);
  backdrop-filter: blur(12px);
  border: 2px solid rgba(168, 230, 207, 0.5);
  color: rgba(168, 230, 207, 0.95);
  font-weight: 600;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translate(-50%, 20px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

/* �🎯 隐藏式截图组件样式 */
.hidden-screenshot {
  position: relative;
}

.hidden-screenshot :deep(.screenshot-controls) {
  display: none !important;
}

.hidden-screenshot :deep(.screenshot-btn) {
  display: none !important;
}

/* � 统一游戏化光效动画 */
.btn {
  position: relative;
  overflow: hidden;
}

.btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
  transition: left 0.6s ease;
}

.btn:hover::before {
  left: 100%;
}

/* 🎯 移动设备按钮触摸tuning */
@media (max-width: 768px) {
  .btn-row {
    gap: 0.8rem; /* 增加移动设备间距 */
    padding: 0 0.5rem; /* 确保按钮不会碰到边缘 */
  }
  
  .btn {
    flex: 1;
    min-height: 48px; /* iOS推荐触摸目标 */
    font-size: 0.9rem;
    border-radius: 12px; /* 更适合移动设备的圆角 */
    
    /* touch tuning for mobile */
    -webkit-tap-highlight-color: transparent;
    touch-action: manipulation;
    -webkit-user-select: none;
    user-select: none;
  }
  
  /* 移动设备按钮按下效果 */
  .btn:active {
    transform: scale(0.95) translateY(1px);
    transition: transform 0.1s ease;
  }
  
  /* 移动设备禁用hover效果 */
  @media (hover: none) {
    .btn::before {
      display: none;
    }
    
    .btn:hover {
      transform: none;
      box-shadow: none;
    }
  }
}

/* 🎯 小屏device-specific tuning */
@media (max-width: 480px) {
  .btn-row {
    flex-direction: column;
    gap: 0.6rem;
  }
  
  .btn {
    width: 100%;
    min-height: 52px; /* 小屏设备更大的触摸目标 */
    font-size: 1rem;
  }
  
  .couple-card {
    margin: 0 0.5rem;
    padding: 1rem;
  }
}

/* Mobile */
@media (max-width:480px) {
  .face-img { width: 70px; height: 70px; }
  .pet-card { width: 200px; height: 200px; }
  .xp-bar { width: 180px; }
  
  .couple-view {
    padding: 0.5rem 0.8rem 0.8rem;
    min-height: calc(100vh - 150px);
  }
  
  .faces-row {
    width: 90%;
    gap: 1rem;
  }
  
  .couple-card {
    margin: 1rem auto 0;
    padding: 1rem;
  }
  
  /* 🎯 移动设备performance tuning */
  .couple-view {
    /* GPU加速tuning */
    -webkit-transform: translateZ(0);
    transform: translateZ(0);
    will-change: transform;
    backface-visibility: hidden;
    -webkit-backface-visibility: hidden;
  }
  
  /* 减少移动设备上的复杂动画 */
  .connector {
    animation-duration: 4s; /* 减慢动画频率 */
  }
  
  .pet-card {
    animation-duration: 6s; /* 减慢浮动动画 */
  }
  
  /* tuning滚动性能 */
  .profile-view {
    -webkit-overflow-scrolling: touch;
  }
}

/* 🎯 移动device-specific tuning */
@media (max-width: 768px) {
  .couple-view {
    padding: 0.8rem;
    min-height: calc(100vh - 180px);
  }
  
  .faces-row {
    width: 88%;
  }
  
  .pet-zone {
    margin-bottom: 1.5rem;
  }
  
  .couple-card {
    max-width: 100%;
    margin: 0.5rem;
  }
  
  /* 减少移动设备上的视觉效果复杂度 */
  .profile-card {
    backdrop-filter: blur(5px); /* 减少模糊强度 */
  }
  
  /* touch tuning for mobile */
  .btn {
    min-height: 44px; /* iOS推荐的最小触摸目标 */
    -webkit-tap-highlight-color: transparent;
    touch-action: manipulation;
  }
  
  /* 确保SVG在移动设备上正常渲染 */
  .connector {
    -webkit-transform: translateZ(0);
    transform: translateZ(0);
  }
  
  /* font rendering tuned for mobile */
  * {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
}

/* 🎯 iOSdevice-specific tuning */
@supports (-webkit-touch-callout: none) {
  .couple-view {
    /* iOS Safarispecific tuning */
    -webkit-overflow-scrolling: touch;
    isolation: isolate;
  }
  
  .pet-card {
    /* iOS 3D渲染tuning */
    -webkit-transform: translate3d(0, 0, 0);
    transform: translate3d(0, 0, 0);
  }
}

/* 🎯 用户偏好：减少动画（移动设备电池tuning） */
@media (prefers-reduced-motion: reduce) {
  .connector,
  .pet-card,
  .face-img,
  .avatar-preview {
    animation: none !important;
    transition: none !important;
  }
  
  .celebrating {
    animation: none !important;
  }
}

/* 🎯 大屏设备tuning */
@media (min-width: 1200px) {
  .couple-view {
    padding: 1.5rem 2rem 2rem;
    max-width: 800px;
    margin: 0 auto;
  }
  
  .faces-row {
    width: 75%;
    max-width: 500px;
  }
  
  .pet-card {
    width: 200px;
    height: 200px;
  }
  
  .couple-card {
    max-width: 600px;
    padding: 1rem;
  }
  
  .btn-row {
    gap: 1.5rem;
  }
  
  .btn {
    min-width: 100px;
    padding: 0.5rem 0.5rem;
    font-size: 0.8rem;
  }
}

/* monkey patch for full‐height background & remove white gap */
html, body, #app, .v-application {
  height: 100%;
  margin: 0;
  padding: 0;
}

/* drop the white background from v-main */
.v-application .v-main {
  background: transparent !important;
}

/* couple-setup-screen 拉伸到底部 */
.couple-setup-screen {
  position: absolute;
  top: var(--nav-mobile);    /* both variables are already defined in the component */
  bottom: 0;
  left: 0;
  right: 0;
  overflow-y: auto;
}

/* —— background —— */
.profile-view{
  min-height: 100vh;
  background: linear-gradient(145deg,#ffe0ec 0%,#ffd3e0 50%,#fff 100%);
}

/* —— card —— */
.profile-card{
  backdrop-filter:blur(10px);
  background:rgba(255,255,255,.65);
  border:2px solid rgba(255,192,203,.4);
}

/* —— gradient text —— */
.gradient-text{
  background:linear-gradient(90deg,#ff6ec7 0%,#ff9a9e 50%,#fecfef 100%);
  -webkit-background-clip:text;
  background-clip:text;
  -webkit-text-fill-color:transparent;
}

/* —— avatar —— */
.avatar-block{
  border-bottom:1px dashed rgba(255,105,135,.3);
  display: flex;
  flex-direction: column;
  align-items: center;
}
.avatar-preview{
  border:4px solid #fff;
  transition:transform .25s; border-radius:50%;
}
@media(hover:hover){
  .avatar-preview:hover{transform:scale(1.05);}
}
.profile-card .remove-avatar{
  position:absolute;top:-6px;right:-6px;
  background:rgba(255,105,135,.85);
}
.avatar-image{
  width:100%; height:100%;
  object-fit:cover;
}

/* —— tabs —— */
.peach-tabs .v-tab--selected{color:#ff5e9c!important}
.peach-tabs .v-tabs-slider{background:#ff8ab2!important}
</style>
