<!-- src/views/RegisterView.vue -->
<template>
  <div class="register-screen">
    <!-- ▍LEFT ─ Clean Mobile Stage ─────────────────────────────── -->
    <section class="stage" ref="stageRef">
      <!-- Desktop: Pet Renderer -->
      <PetRenderer
        v-if="!mobile"
        ref="pet"
        :initial-anim="danceAnim"
        class="stage__pet"
      />

      <!-- Mobile: Clean Cooking Experience -->
      <div v-else class="stage__mobile-clean">
        <!-- Main Cooking Hero -->
        <div class="cooking-main">
          <div class="cooking-container">
            <img 
              src="/assets/gifs/cooking.gif" 
              alt="Platemate Cooking" 
              class="cooking-gif-main"
              loading="eager"
            />
            <div class="cooking-glow"></div>
          </div>
          <div class="cooking-title">
            <span class="title-emoji">👨‍🍳</span>
            <span class="title-text">JOIN PLATEMATE</span>
            <span class="title-emoji">📱</span>
          </div>
        </div>

        <!-- Side Dice -->
        <div class="dice-side">
          <img 
            src="/assets/dice-roll.gif" 
            alt="Dice" 
            class="dice-gif-side"
            loading="eager"
          />
        </div>

        <!-- Simple Floating Elements -->
        <div class="simple-floats">
          <div class="float f1">🍳</div>
          <div class="float f2">💕</div>
          <div class="float f3">🍅</div>
          <div class="float f4">📱</div>
        </div>
      </div>

      <!-- Desktop Dance Button -->
      <BaseButton
        v-if="!mobile"
        class="btn-dance"
        @click="startDance"
      >
        Dance&nbsp;With&nbsp;Me 💞
      </BaseButton>

      <!-- 心形粒子 · 简单浪漫彩蛋 (Desktop Only) -->
      <div v-if="playing && !mobile" class="hearts">
        <span v-for="n in 12" :key="n" class="heart"/>
      </div>
    </section>

    <!-- ▍RIGHT ─ 注册表单 ─────────────────────────────── -->
    <section class="form-wrap">
      <BaseCard class="form-card">
        <!-- Loading Overlay -->
        <transition name="fade">
          <div v-if="loading" class="loading-overlay">
            <v-progress-circular indeterminate size="40" color="pink-lighten-2"/>
          </div>
        </transition>

        <!-- 页面标题 -->
        <h2 class="form-title">Create&nbsp;Your&nbsp;Love&nbsp;Nest&nbsp;💖</h2>

        <!-- 表单 -->
        <v-form ref="formRef" @submit.prevent="onSubmit">
          <!-- Username -->
          <BaseFormField label="Username" :error="errors.username">
            <BaseInput v-model="form.username"
                       :rules="usernameRules"
                       placeholder="Your nickname"
                       clearable
                       prepend-inner-icon="mdi-account-heart"
                       required/>
          </BaseFormField>

          <!-- Email -->
          <BaseFormField label="Email" :error="errors.email">
            <BaseInput v-model="form.email"
                       :rules="emailRules"
                       placeholder="you@example.com"
                       clearable
                       prepend-inner-icon="mdi-email-heart"
                       required/>
          </BaseFormField>

          <!-- Password -->
          <BaseFormField label="Password" :error="errors.password">
            <BaseInput v-model="form.password"
                       :type="showPass ? 'text' : 'password'"
                       :rules="passwordRules"
                       :append-inner-icon="showPass ? 'mdi-eye-off' : 'mdi-eye'"
                       @click:append-inner="showPass = !showPass"
                       placeholder="Create a secret"
                       prepend-inner-icon="mdi-lock-heart"
                       required/>
          </BaseFormField>

          <!-- Confirm -->
          <BaseFormField label="Confirm Password" :error="errors.confirmPassword">
            <BaseInput v-model="form.confirmPassword"
                       :type="showConfirm ? 'text' : 'password'"
                       :rules="confirmRules"
                       :append-inner-icon="showConfirm ? 'mdi-eye-off' : 'mdi-eye'"
                       @click:append-inner="showConfirm = !showConfirm"
                       placeholder="Repeat your secret"
                       prepend-inner-icon="mdi-lock-check"
                       required/>
          </BaseFormField>

          <!-- 全局错误 -->
          <p v-if="errors.global" class="err-global">{{ errors.global }}</p>

          <BaseButton type="submit"
                      :disabled="!isFormValid || loading"
                      block
                      class="btn-submit">
            Sign&nbsp;Up
          </BaseButton>
        </v-form>

        <!-- 已有账号 -->
        <p class="alt-link">
          Already linked hearts?
          <RouterLink to="/login">Reconnect&nbsp;here</RouterLink>
        </p>
      </BaseCard>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useDisplay } from 'vuetify'
import { useUserStore } from '@/stores/userStore'
import BaseCard from '@/components/BaseCard.vue'
import BaseFormField from '@/components/BaseFormField.vue'
import BaseInput from '@/components/BaseInput.vue'
import BaseButton from '@/components/BaseButton.vue'
import PetRenderer from '@/components/PetRenderer.vue'

/* ---------- 表单数据 ---------- */
interface Form { username:string; email:string; password:string; confirmPassword:string }
const form    = reactive<Form>({ username:'', email:'', password:'', confirmPassword:'' })
const errors  = reactive<Partial<Record<keyof Form|'global', string>>>({})
const loading = ref(false)

/* 响应式检测 */
const { mobile } = useDisplay()

/* 密码显隐 */
const showPass    = ref(false)
const showConfirm = ref(false)

/* v-form 引用 */
const formRef = ref<any>(null)

/* ---------- 校验 ---------- */
const usernameRules = [(v:string)=>!!v||'Required', (v:string)=>v.length>=3||'≥3 chars']
const emailRules    = [(v:string)=>!!v||'Required', (v:string)=>/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)||'Invalid']
const passwordRules = [(v:string)=>!!v||'Required', (v:string)=>v.length>=6||'≥6 chars']
const confirmRules  = [(v:string)=>!!v||'Required', (v:string)=>v===form.password||'Mismatch']
const isFormValid   = computed(()=>form.username&&form.email&&form.password.length>=6&&form.password===form.confirmPassword)

/* ---------- Pet 动画 ---------- */
const danceAnims = ['Animation_Boom_Dance_withSkin.glb','Animation_All_Night_Dance_withSkin.glb']
const danceAnim  = ref(danceAnims[0])
const pet        = ref<InstanceType<typeof PetRenderer>>()

onMounted(() => {
  pet.value?.play('Animation_You_Groove_withSkin.glb')
})

const playing = ref(false)   // 控制心形粒子显示

function startDance () {
  danceAnim.value = danceAnims[Math.floor(Math.random()*danceAnims.length)]
  pet.value?.play(danceAnim.value)
  playing.value = true
  setTimeout(()=>playing.value=false, 1800)
}

/* ---------- 提交 ---------- */
const router     = useRouter()
const userStore  = useUserStore()

async function onSubmit () {
  if (!(await formRef.value.validate())) return
  loading.value = true
  Object.keys(errors).forEach(k=>delete errors[k as keyof typeof errors])

  try {
    await userStore.register({ username:form.username, email:form.email, password:form.password })
    startDance()
    await new Promise(r=>setTimeout(r, 800))
    router.push({ name:'Home' })
    window.dispatchEvent(new Event('auth-changed')) // TODO temporary fix
  } catch (err:any) {
    const data = err.response?.data
    if (data && typeof data==='object') {
      for (const [field,msg] of Object.entries(data)) {
        const text = Array.isArray(msg)?msg.join(' '):String(msg)
        field in form ? (errors[field as keyof Form]=text) : (errors.global=text)
      }
    } else errors.global='Registration failed. Please try again.'
  } finally { loading.value=false }
}
</script>

<style scoped>
/* ▍总体布局 ▍*/
.register-screen{
  display:flex;
  flex-direction:column;
  height:100%;
}
@media(min-width:768px){
  .register-screen{ flex-direction:row; }
}

/* ▍LEFT 舞台 ▍*/
/* ▍LEFT 舞台 ▍*/
.stage{
  flex:1;
  position:relative;
  overflow:hidden;
  display:flex;
  align-items:center;
  justify-content:center;
  background:linear-gradient(135deg,#ffd6e8 0%,#ffcfe1 40%,#dcd3ff 100%);
  min-height:38vh
}

/* Desktop Pet */
.stage__pet{
  position:absolute; inset:0; margin:auto;
  width:170px;height:170px
}
@media(min-width:768px){.stage__pet{width:210px;height:210px}}
@media(min-width:1200px){.stage__pet{width:250px;height:250px}}

/* ======= CLEAN MOBILE DESIGN (Register) ======= */
.stage__mobile-clean{
  position:relative;width:100%;height:100%;
  background:linear-gradient(135deg, #2d1b69 0%, #11998e 100%);
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:20px;min-height:45vh;
}

/* — Main Cooking Area — */
.cooking-main{
  position:relative;display:flex;flex-direction:column;align-items:center;
  z-index:10;
}

.cooking-container{
  position:relative;
  width:240px;height:240px;
  border-radius:50%;
  background:linear-gradient(145deg, 
    rgba(255,255,255,0.1) 0%, 
    rgba(253,121,168,0.1) 50%, 
    rgba(255,255,255,0.05) 100%);
  padding:8px;
  box-shadow:0 20px 60px rgba(0,0,0,0.3), 0 0 40px rgba(253,121,168,0.2);
  backdrop-filter:blur(20px);
  animation:heroFloat 4s ease-in-out infinite;
  border:2px solid rgba(253,121,168,0.3);
}

.cooking-gif-main{
  width:100%;height:100%;
  border-radius:50%;
  object-fit:cover;
  box-shadow:0 10px 30px rgba(0,0,0,0.4);
}

.cooking-glow{
  position:absolute;top:-15px;left:-15px;right:-15px;bottom:-15px;
  border-radius:50%;
  background:radial-gradient(circle, rgba(253,121,168,0.3) 0%, transparent 70%);
  animation:glowPulse 3s ease-in-out infinite alternate;
  filter:blur(10px);
}

/* — Clean Title — */
.cooking-title{
  display:flex;align-items:center;gap:12px;
  margin-top:16px;
  background:rgba(0,0,0,0.7);
  padding:10px 20px;border-radius:25px;
  backdrop-filter:blur(15px);
  border:1px solid rgba(253,121,168,0.3);
}

.title-emoji{
  font-size:20px;
  animation:emojiFloat 2s ease-in-out infinite;
}

.title-text{
  color:#fd79a8;font-weight:800;font-size:14px;
  letter-spacing:2px;text-transform:uppercase;
  text-shadow:0 2px 8px rgba(0,0,0,0.8);
}

/* — Side Dice — */
.dice-side{
  position:absolute;top:30px;right:30px;
  z-index:5;
}

.dice-gif-side{
  width:70px;height:70px;
  border-radius:12px;
  box-shadow:0 8px 20px rgba(0,0,0,0.3);
  animation:diceFloat 3s ease-in-out infinite;
  background:rgba(255,255,255,0.1);
  padding:4px;
  border:1px solid rgba(255,255,255,0.2);
}

/* — Simple Floating Elements — */
.simple-floats{
  position:absolute;top:0;left:0;right:0;bottom:0;
  pointer-events:none;z-index:2;
}

.float{
  position:absolute;font-size:24px;
  animation:simpleFloat 8s linear infinite;
  opacity:0.7;
  filter:drop-shadow(0 2px 4px rgba(0,0,0,0.5));
}

.f1{top:20%;left:15%;animation-delay:0s;animation-duration:10s;}
.f2{top:60%;right:20%;animation-delay:2s;animation-duration:12s;}
.f3{bottom:30%;left:20%;animation-delay:4s;animation-duration:9s;}
.f4{bottom:60%;right:15%;animation-delay:6s;animation-duration:11s;}

/* ======= CLEAN ANIMATIONS ======= */
@keyframes heroFloat {
  0%, 100% { transform: translateY(0px) scale(1); }
  50% { transform: translateY(-8px) scale(1.02); }
}

@keyframes glowPulse {
  0% { opacity: 0.3; transform: scale(0.95); }
  100% { opacity: 0.6; transform: scale(1.05); }
}

@keyframes emojiFloat {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@keyframes diceFloat {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-6px); }
}

@keyframes simpleFloat {
  0%, 100% { 
    transform: translateX(0px) translateY(0px) scale(1); 
    opacity: 0.7; 
  }
  25% { 
    transform: translateX(10px) translateY(-15px) scale(1.1); 
    opacity: 0.9; 
  }
  50% { 
    transform: translateX(-5px) translateY(-10px) scale(0.9); 
    opacity: 0.8; 
  }
  75% { 
    transform: translateX(8px) translateY(10px) scale(1.05); 
    opacity: 0.85; 
  }
}

/* Desktop Dance Button */
.btn-dance{
  position:absolute; bottom:2.2rem; left:50%; transform:translateX(-50%);
  background:rgba(255,255,255,.8); color:#d6336c; font-weight:600;
  backdrop-filter:blur(4px);
}

/* 心形粒子 */
.hearts{ pointer-events:none; position:absolute; inset:0; overflow:hidden; }
.heart{
  position:absolute; top:100%; left:50%;
  width:18px; height:18px; background:url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox=\"0 0 32 29.6\"><path fill=\"%23ff6b9e\" d=\"M23.6,0c-2.9,0-5.4,1.4-7,3.6C14.8,1.4,12.3,0,9.4,0C4.2,0,0,4.2,0,9.4 c0,5.2,4.2,9.4,9.4,9.4c7.5,0,9.4-9.4,9.4-9.4S22.3,18.8,29.8,18.8c5.2,0,9.4-4.2,9.4-9.4C39.2,4.2,35,0,29.8,0 C26.9,0,24.4,1.4,23.6,3.6C22.8,1.4,20.3,0,17.4,0z\"/></svg>') center/contain no-repeat;
  animation: float 1.8s ease-in-out forwards;
  opacity:.8;
}
@keyframes float{
  0%{ transform:translate(-50%,0) scale(.6); opacity:.8; }
  100%{ transform:translate(-50%,-120vh) scale(1.2); opacity:0; }
}

/* — Responsive — */
@media(max-width:480px){
  .cooking-container{width:200px;height:200px;}
  .dice-gif-side{width:60px;height:60px;}
  .title-text{font-size:12px;letter-spacing:1.5px;}
  .float{font-size:20px;}
}

/* ▍RIGHT 表单 ▍*/
.form-wrap{
  flex:1;
  display:flex; align-items:center; justify-content:center;
  padding:1rem; background:rgba(255,255,255,.9); backdrop-filter:blur(3px);
}
.form-card{ width:100%; max-width:22rem; position:relative; overflow:hidden; border-radius:18px; }

/* Loading */
.loading-overlay{
  position:absolute; inset:0;
  background:rgba(255,255,255,.7);
  display:flex; align-items:center; justify-content:center; z-index:10;
}

/* Title */
.form-title{
  text-align:center; margin-bottom:1rem;
  font-size:1.5rem; font-weight:700; color:#d6336c;
}

/* Buttons & Links */
.btn-submit{ margin-top:.25rem; }
.alt-link{ margin-top:1.2rem; text-align:center; font-size:.875rem; }
.alt-link a{ color:#d6336c; text-decoration:none; }
.alt-link a:hover{ text-decoration:underline; }

/* Errors */
.err-global{ color:#d32f2f; margin:.25rem 0 .5rem; font-size:.9rem; }

/* 过渡 */
.fade-enter-active,.fade-leave-active{ transition:opacity .25s; }
.fade-enter-from,.fade-leave-to{ opacity:0; }
</style>
