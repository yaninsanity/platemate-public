<!-- LoginView.vue — “Native Dice Throw v2 (logo injected)” -->
<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useDisplay } from 'vuetify'
import { useUserStore } from '@/stores/userStore'

/* components */
import BaseCard      from '@/components/BaseCard.vue'
import BaseFormField from '@/components/BaseFormField.vue'
import BaseInput     from '@/components/BaseInput.vue'
import PetRenderer   from '@/components/PetRenderer.vue'
/* ⚠️ nothing to do if BaseButton is globally registered; otherwise import it */
// import BaseButton    from '@/components/BaseButton.vue'

/* ——— form ——— */
interface Form { username:string; password:string }
const form   = reactive<Form>({ username:'', password:'' })
const errors = reactive<{ username?:string; password?:string; global?:string }>({})
const loading  = ref(false)
const showPass = ref(false)
const formRef  = ref<any>()

/* ——— responsive detection ——— */
const { mobile } = useDisplay()

/* ——— pet (desktop only) ——— */
const renderer  = ref<InstanceType<typeof PetRenderer>>()
const ASSET_DIR = '/biped/'
const statusMap = {
  egg:'egg.glb',
  idle:'Animation_You_Groove_withSkin.glb',
  dance:'Animation_Boom_Dance_withSkin.glb'
}
function play(k:'egg'|'idle'|'dance'){ renderer.value?.play(statusMap[k]??statusMap.egg) }
onMounted(()=>{
  if (!mobile.value) {
    play('idle')
  }
})

/* ——— dice button state ——— */
const faces = ['\u2680','\u2681','\u2682','\u2683','\u2684','\u2685']
const diceFace = ref('\u2685')   // initial ⚅
function nextFace(){ diceFace.value = faces[Math.floor(Math.random()*faces.length)] }

/* ——— stage & throw ——— */
const stageRef = ref<HTMLElement>()

function throwDice(){
  /* 1) update button face */
  nextFace()

  if(!stageRef.value) return

  /* 2) create flying dice */
  const rect = stageRef.value.getBoundingClientRect()
  const sx = rect.width - 70,  sy = rect.height - 70
  const ex = 60 + Math.random()*(rect.width-120)
  const ey = 50 + Math.random()*(rect.height*0.35)
  const g  = 1.15
  let vx = (ex-sx)/40, vy = -(ey-sy)/40
  let x=sx, y=sy, frame=0

  const flying = document.createElement('div')
  flying.className = 'dice-fx'
  flying.textContent = diceFace.value
  stageRef.value.appendChild(flying)

  const loop = ()=> {
    frame++
    x += vx; vy += g; y += vy
    flying.style.transform = `translate(${x}px,${y}px) rotate(${frame*24}deg)`
    if(y>sy){
      flying.style.transition='opacity .4s, transform .4s'
      flying.style.opacity='0'
      flying.style.transform += ' scale(.7)'
      setTimeout(()=> flying.remove(), 400)
    }else requestAnimationFrame(loop)
  }
  requestAnimationFrame(loop)

  /* 3) pet reacts */
  play('dance')
  setTimeout(()=>play('idle'),1200)
}

/* ——— cert download ——— */
function downloadCert(){
  window.open('http://localhost:911/certs/cert.pem', '_blank')
}

/* ——— discord community ——— */
function joinDiscord(){
  window.open('https://discord.gg/PgnxX24T', '_blank')
}

/* ——— auth ——— */
const router = useRouter()
const userStore = useUserStore()
async function onSubmit(){
  if(!(await formRef.value.validate())) return
  loading.value=true; errors.global=undefined
  try{
    // 🎯 精准改善：直接登录，无额外等待
    await userStore.login(form.username,form.password)
    
    // Enhanced visual feedback based on device
    if (!mobile.value) {
      // Desktop: Dice throw + pet dance
      throwDice()
      play('dance')
      setTimeout(()=>play('idle'),1200)
    }
    
    // 🎯 精准改善：立即跳转，最佳游戏体验
    // router.replace is already handled inside userStore.login
  }catch(e:any){
    errors.global = e.response?.data?.detail || 'Login failed.'
  }finally{ loading.value=false }
}
const required = (v:string)=>!!v||'Required'
</script>

<template>
  <div class="login-screen">
    <!-- Stage -->
    <section class="stage" ref="stageRef">
      <!-- Desktop: 3D Pet Renderer -->
      <PetRenderer
        v-if="!mobile"
        ref="renderer"
        :base="ASSET_DIR"
        :initial-anim="statusMap.idle"
        class="stage__pet"
        @error="play('egg')"/>

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
            <span class="title-text">PLATEMATE</span>
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
          <div class="float f2">🥕</div>
          <div class="float f3">🍅</div>
          <div class="float f4">📱</div>
        </div>
      </div>

      <!-- Dice Button (Desktop Only - since mobile shows gif) -->
      <div v-if="!mobile" class="dice-btn" @click="throwDice">
        {{ diceFace }}
      </div>
    </section>

    <!-- Login Card -->
    <section class="form-wrap">
      <BaseCard class="form-card">
        <transition name="fade">
          <div v-if="loading" class="loading-overlay">
            <v-progress-circular indeterminate size="40" color="primary"/>
          </div>
        </transition>

        <!-- ★ NEW: Brand Logo -->
        <img
          class="brand-logo"
          src="/assets/logo4.png"
          alt="Platemate Logo"
          loading="lazy"
          decoding="async"
        />

        <h2 class="title">Welcome&nbsp;Home&nbsp;🍳</h2>
        <p class="subtitle">Sign in & start cooking memories together.</p>

        <v-form ref="formRef" @submit.prevent="onSubmit">
          <BaseFormField label="Username" :error="errors.username">
            <BaseInput v-model="form.username"
                       prepend-inner-icon="mdi-account"
                       :rules="[required]"
                       placeholder="Foodie-handle" clearable/>
          </BaseFormField>
          <BaseFormField label="Password" :error="errors.password">
            <BaseInput v-model="form.password"
                       :type="showPass?'text':'password'"
                       :append-inner-icon="showPass?'mdi-eye-off':'mdi-eye'"
                       @click:append-inner="showPass=!showPass"
                       prepend-inner-icon="mdi-lock"
                       :rules="[required]"
                       placeholder="Secret recipe"/>
          </BaseFormField>

          <p v-if="errors.global" class="err-global">{{errors.global}}</p>
          <BaseButton type="submit" block class="btn-submit" :disabled="loading">
            Let’s&nbsp;Cook&nbsp;❤️
          </BaseButton>
          <!-- download cert -->
          <BaseButton 
            @click="downloadCert" 
            block 
            variant="secondary" 
            class="btn-cert"
            prepend-icon="mdi-certificate">
            Download SSL Certificate
          </BaseButton>

          <!-- discord community -->
          <BaseButton 
            @click="joinDiscord" 
            block 
            variant="info" 
            class="btn-discord"
            prepend-icon="mdi-discord">
            Join Discord Community
          </BaseButton>

        </v-form>
      </BaseCard>
    </section>
  </div>
</template>

<style scoped>
/* — Layout — */
.login-screen{display:flex;flex-direction:column;height:100vh}
@media(min-width:768px){.login-screen{flex-direction:row;padding-top:0}}

/* — Stage — */
.stage{flex:1;position:relative;overflow:hidden;display:flex;align-items:center;justify-content:center;
       background:linear-gradient(135deg,#e4f1ff 0%,#f0e8ff 100%);min-height:38vh}

/* — Pet (Desktop) — */
.stage__pet{width:170px;height:170px}@media(min-width:768px){.stage__pet{width:210px;height:210px}}
@media(min-width:1200px){.stage__pet{width:250px;height:250px}}

/* ======= CLEAN MOBILE DESIGN ======= */
.stage__mobile-clean{
  position:relative;width:100%;height:100%;
  background:linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
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
    rgba(78,205,196,0.1) 50%, 
    rgba(255,255,255,0.05) 100%);
  padding:8px;
  box-shadow:0 20px 60px rgba(0,0,0,0.3), 0 0 40px rgba(78,205,196,0.2);
  backdrop-filter:blur(20px);
  animation:heroFloat 4s ease-in-out infinite;
  border:2px solid rgba(78,205,196,0.3);
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
  background:radial-gradient(circle, rgba(78,205,196,0.3) 0%, transparent 70%);
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
  border:1px solid rgba(78,205,196,0.3);
}

.title-emoji{
  font-size:20px;
  animation:emojiFloat 2s ease-in-out infinite;
}

.title-text{
  color:#4ecdc4;font-weight:800;font-size:16px;
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

/* — Responsive — */
@media(max-width:480px){
  .cooking-container{width:200px;height:200px;}
  .dice-gif-side{width:60px;height:60px;}
  .title-text{font-size:14px;letter-spacing:1.5px;}
  .float{font-size:20px;}
}

/* — Dice Button — */
.dice-btn{position:absolute;bottom:1.3rem;right:1.3rem;width:60px;height:60px;border-radius:14px;
          background:linear-gradient(145deg,#fff 0%,#f2f4ff 100%);
          box-shadow:0 4px 12px rgba(0,0,0,.22),inset 0 2px 4px rgba(255,255,255,.6);
          display:flex;align-items:center;justify-content:center;font-size:34px;user-select:none;
          cursor:pointer;transition:transform .15s cubic-bezier(.17,.67,.42,1.27)}
.dice-btn:hover{transform:scale(1.08) rotate(-3deg)}
.dice-btn:active{transform:scale(.94) rotate(1deg)}

/* — Flying dice effect — */
.dice-fx{position:absolute;width:50px;height:50px;border-radius:12px;font-size:32px;
         display:flex;align-items:center;justify-content:center;
         background:linear-gradient(145deg,#fff 0%,#f3f5ff 100%);
         box-shadow:0 4px 12px rgba(0,0,0,.18),inset 0 2px 4px rgba(255,255,255,.6);
         pointer-events:none;will-change:transform,opacity;}

/* — Card & misc (同前) — */
.form-wrap{flex:1;display:flex;align-items:center;justify-content:center;padding:1rem;background:#fff}
.form-card{position:relative;width:100%;max-width:22rem;border-radius:20px;
           box-shadow:0 10px 28px rgba(26,33,42,.08);padding:1.4rem 1.2rem}
.loading-overlay{position:absolute;inset:0;background:rgba(255,255,255,.7);
                 display:flex;align-items:center;justify-content:center;z-index:10}
.title{margin:.4rem 0 .15rem;text-align:center;font-size:1.6rem;font-weight:800;color:#1e88e5}
.subtitle{margin:0 0 1rem;text-align:center;font-size:.94rem;color:#60708a}
.btn-submit{margin-top:.35rem;font-weight:700}
.btn-cert{margin-top:.5rem;font-weight:600;opacity:0.9}  /* 精准调整按钮间距 */
.btn-discord{margin-top:.45rem;font-weight:600;opacity:0.95}  /* Discord按钮样式 */
.alt-link{text-align:center;font-size:.83rem;margin-top:1.2rem}
.alt-link a{color:#1e88e5;font-weight:600;text-decoration:none}
.alt-link a:hover{text-decoration:underline}
.err-global{color:#d32f2f;margin:.4rem 0 .6rem;font-size:.88rem}
.fade-enter-active,.fade-leave-active{transition:opacity .25s}.fade-enter-from,.fade-leave-to{opacity:0}

/* ★ NEW: Logo style (mobile-friendly) */
.brand-logo{
  display:block;
  margin:0 auto .6rem;
  width:96px;
  max-width:38vw;
  height:auto;
  object-fit:contain;
}
@media(min-width:768px){
  .brand-logo{width:110px;max-width:110px;margin-bottom:.8rem}
}
</style>
