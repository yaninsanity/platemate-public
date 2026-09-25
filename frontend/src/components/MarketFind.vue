<template>
  <main class="market-game-hub">
    <!-- 游戏化标题 -->
    <div class="quest-header">
      <div class="quest-icon">
        <img :src="shoppingImg" alt="Shopping Companion" class="shopping-mascot" />
      </div>
      <h1 class="quest-title">Market Adventure</h1>
      <p class="quest-subtitle">Find ingredients with your cute companion</p>
    </div>

    <!-- 游戏化扫描按钮 -->
    <button class="scout-btn" @click="scan" :disabled="loading">
      <div class="btn-content">
        <span v-if="!loading" class="btn-text">
          <span class="btn-icon">🛒</span>
          <span>Scout Stores</span>
        </span>
        <span v-else class="btn-spinner"></span>
      </div>
      <div class="btn-glow"></div>
    </button>

    <p v-if="error" class="error-message">⚠️ {{ error }}</p>

    <!-- 游戏化弹窗 - 改善高度 -->
    <Teleport to="body">
      <div v-if="showModal" class="modal-overlay" @click="closeModal">
        <div class="treasure-modal" @click.stop>
          <!-- 弹窗头部 -->
          <div class="modal-header">
            <h2 class="modal-title">
              <img :src="shoppingImg" alt="Shopping Companion" class="header-companion" />
              Stores Discovered!
            </h2>
            <button class="close-btn" @click="closeModal">✕</button>
          </div>

          <!-- 加载状态 -->
          <div v-if="loading" class="loading-area">
            <div class="quest-loader">
              <img :src="shoppingImg" alt="Loading" class="loader-companion" />
              <p>Exploring nearby stores...</p>
            </div>
          </div>

          <!-- 结果列表 -->
          <div v-else-if="stores.length" class="treasure-list">
            <div v-for="store in stores" :key="store.id" 
                 class="treasure-card" @click="openMap(store)">
              <div class="card-badge">{{ store.distance?.toFixed(1) || 0 }}km</div>
              <div class="card-content">
                <h3 class="store-name">{{ store.name }}</h3>
                <p class="store-address">{{ store.address }}</p>
                <div class="store-meta" v-if="store.brand || store.opening_hours">
                  <span v-if="store.brand" class="meta-tag">{{ store.brand }}</span>
                  <span v-if="store.opening_hours" class="meta-hours">{{ store.opening_hours }}</span>
                </div>
              </div>
              <div class="card-action">📍</div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-else class="empty-state">
            <img :src="shoppingImg" alt="No stores" class="empty-companion" />
            <p>No stores found nearby</p>
            <p class="empty-tip">Try expanding your search radius!</p>
          </div>
        </div>
      </div>
    </Teleport>
  </main>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import shoppingImg from '/assets/shopping.png'
import type { Store, OverpassElement } from '@/models/market'

interface ExtendedStore extends Store {
  brand?: string
  branch?: string
  opening_hours?: string
  phone?: string
  website?: string
}

const stores=ref<ExtendedStore[]>([])
const loading=ref(false)
const error=ref('')
const showModal=ref(false)

const toRad=(d:number)=>d*Math.PI/180
const haversine=(a:number,b:number,c:number,d:number)=>{
  const R=6371, dLat=toRad(c-a), dLon=toRad(d-b)
  const x=Math.sin(dLat/2)**2+Math.cos(toRad(a))*Math.cos(toRad(c))*Math.sin(dLon/2)**2
  return R*2*Math.atan2(Math.sqrt(x),Math.sqrt(1-x))
}

const buildAddress=(t:Record<string,string>,lat:number,lon:number)=>{
  const l1=[t['addr:housenumber'],t['addr:street']].filter(Boolean).join(' ')
  const city=[t['addr:city'],t['addr:state']].filter(Boolean).join(' ')
  const l2=[city,t['addr:postcode']].filter(Boolean).join(' ')
  return [l1,l2].filter(Boolean).join(', ')||`${lat.toFixed(4)}, ${lon.toFixed(4)}`
}

const getPos=()=>new Promise<GeolocationPosition>((r,j)=>
  navigator.geolocation.getCurrentPosition(r,j,{enableHighAccuracy:true,timeout:8000}))

const openMap=(s:Store)=>{
  const q=encodeURIComponent(`${s.name} ${s.address}`)
  window.open(`https://www.google.com/maps/search/?api=1&query=${q}`,'_blank')
}

const closeModal = () => {
  showModal.value = false
}

async function scan(){
  error.value=''
  stores.value=[]
  loading.value=true
  showModal.value=true
  
  try{
    const {coords:{latitude:lat,longitude:lon}}=await getPos()
    const q=`[out:json][timeout:15];node["shop"~"supermarket|grocery"](around:5000,${lat},${lon});out;`
    const resp=await fetch('https://overpass-api.de/api/interpreter',{method:'POST',body:q})
    if(!resp.ok) throw new Error('Network error')
    const data=await resp.json() as {elements:OverpassElement[]}
    
    stores.value=data.elements.map(el=>{
      const t=el.tags||{}
      return{
        id:String(el.id),name:t.name||'Unnamed Store',
        lat:el.lat,lon:el.lon,
        address:buildAddress(t,el.lat,el.lon),
        brand:t.brand,branch:t.branch,opening_hours:t.opening_hours,
        phone:t.phone||t['contact:phone'],website:t.website||t['contact:website'],
        distance:haversine(lat,lon,el.lat,el.lon)
      }
    }).sort((a,b)=>a.distance-b.distance).slice(0,8)
    
    if(!stores.value.length) {
      error.value='No stores found within 5 km.'
    }
  }catch(e:any){
    showModal.value = false
    if(e.code===1) error.value='Location permission denied.'
    else if(e.code===2) error.value='Position unavailable.'
    else if(e.code===3) error.value='Location timeout.'
    else error.value=e.message||'Scout mission failed.'
  }finally{
    setTimeout(()=>loading.value=false,800)
  }
}
</script>

<style scoped>
/* ===== 游戏化主容器 - 温柔情侣风格 ===== */
.market-game-hub {
  max-width: 420px;
  margin: 2rem auto;
  padding: 2rem;
  background: linear-gradient(135deg, 
    #fdf2f8 0%, 
    #fce7f3 30%,
    #fbcfe8 70%, 
    #f9a8d4 100%);
  border-radius: 20px;
  box-shadow: 
    0 10px 30px rgba(236, 72, 153, 0.15),
    0 0 40px rgba(244, 114, 182, 0.1);
  text-align: center;
  color: #be185d;
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(244, 114, 182, 0.2);
}

.market-game-hub::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(244, 114, 182, 0.15) 0%, transparent 70%);
  animation: bgPulse 6s ease-in-out infinite;
  pointer-events: none;
}

@keyframes bgPulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.05); }
}

/* ===== 购物伙伴图标 ===== */
.shopping-mascot {
  width: 80px;
  height: 80px;
  object-fit: contain;
  filter: drop-shadow(0 4px 12px rgba(244, 114, 182, 0.3));
  animation: companionFloat 3s ease-in-out infinite;
}

@keyframes companionFloat {
  0%, 100% { transform: translateY(0px) scale(1); }
  50% { transform: translateY(-6px) scale(1.03); }
}

.header-companion {
  width: 32px;
  height: 32px;
  object-fit: contain;
  filter: drop-shadow(0 2px 6px rgba(244, 114, 182, 0.3));
}

.loader-companion {
  width: 60px;
  height: 60px;
  object-fit: contain;
  animation: companionExplore 2s ease-in-out infinite;
  filter: drop-shadow(0 4px 8px rgba(244, 114, 182, 0.25));
}

@keyframes companionExplore {
  0%, 100% { transform: translateX(-8px) rotate(-3deg); }
  50% { transform: translateX(8px) rotate(3deg); }
}

.empty-companion {
  width: 64px;
  height: 64px;
  object-fit: contain;
  opacity: 0.6;
  filter: grayscale(0.2) drop-shadow(0 2px 8px rgba(0, 0, 0, 0.1));
}

/* ===== 任务头部 ===== */
.quest-header {
  margin-bottom: 0.5rem;
  position: relative;
  z-index: 1;
}

.quest-icon {
  margin-bottom: 0rem;
}

.quest-title {
  font-size: 1.2rem;
  font-weight: 900;
  margin: 0.2rem 0;
  background: linear-gradient(45deg, #be185d, #db2777, #ec4899);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 2px 4px rgba(190, 24, 93, 0.2);
  letter-spacing: 1px;
}

.quest-subtitle {
  color: #be185d;
  font-size: 0.9rem;
  margin: 0;
  opacity: 0.8;
  font-weight: 600;
}

/* ===== 游戏化按钮 - 柔和粉色 ===== */
.scout-btn {
  position: relative;
  background: linear-gradient(135deg, #ec4899, #db2777);
  border: none;
  border-radius: 16px;
  padding: 1rem 2rem;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 
    0 8px 20px rgba(236, 72, 153, 0.3),
    0 0 30px rgba(236, 72, 153, 0.15);
  z-index: 1;
}

.scout-btn:disabled {
  background: linear-gradient(135deg, #d1d5db, #9ca3af);
  cursor: not-allowed;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.scout-btn:not(:disabled):hover {
  transform: translateY(-2px);
  box-shadow: 
    0 12px 25px rgba(236, 72, 153, 0.4),
    0 0 40px rgba(236, 72, 153, 0.2);
}

.btn-content {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #fff;
  font-weight: 700;
  font-size: 1rem;
}

.btn-icon {
  font-size: 1.2rem;
}

.btn-glow {
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.25), transparent);
  transition: left 0.5s ease;
}

.scout-btn:not(:disabled):hover .btn-glow {
  left: 100%;
}

.btn-spinner {
  width: 1.2rem;
  height: 1.2rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ===== 错误消息 ===== */
.error-message {
  margin-top: 1rem;
  color: #dc2626;
  font-size: 0.9rem;
  background: rgba(239, 68, 68, 0.08);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

/* ===== 弹窗样式 - 温柔配色 ===== */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.treasure-modal {
  background: linear-gradient(135deg, #fdf2f8, #fce7f3);
  border-radius: 20px;
  max-width: 520px;
  width: 100%;
  max-height: 85vh;
  box-shadow: 
    0 20px 50px rgba(236, 72, 153, 0.2),
    0 0 100px rgba(244, 114, 182, 0.15);
  overflow: hidden;
  animation: modalSlideIn 0.4s ease;
  border: 2px solid rgba(244, 114, 182, 0.2);
}

@keyframes modalSlideIn {
  from { 
    opacity: 0; 
    transform: translateY(50px) scale(0.9); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0) scale(1); 
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 2px solid rgba(244, 114, 182, 0.2);
  background: rgba(253, 242, 248, 0.9);
}

.modal-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #be185d;
  font-size: 1.4rem;
  font-weight: 800;
  margin: 0;
}

.close-btn {
  background: rgba(239, 68, 68, 0.15);
  border: 1px solid rgba(239, 68, 68, 0.25);
  color: #dc2626;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  transition: all 0.3s ease;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.25);
  transform: scale(1.1);
}

/* ===== 加载状态 ===== */
.loading-area {
  padding: 3rem;
  text-align: center;
}

.quest-loader {
  color: #be185d;
}

/* ===== 商店列表 - 改善高度 ===== */
.treasure-list {
  max-height: calc(85vh - 200px);
  overflow-y: auto;
  padding: 1rem;
}

.treasure-list::-webkit-scrollbar {
  width: 8px;
}

.treasure-list::-webkit-scrollbar-track {
  background: rgba(244, 114, 182, 0.08);
  border-radius: 4px;
}

.treasure-list::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #ec4899, #db2777);
  border-radius: 4px;
  box-shadow: 0 0 10px rgba(236, 72, 153, 0.2);
}

.treasure-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: rgba(255, 255, 255, 0.9);
  border: 2px solid rgba(244, 114, 182, 0.15);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 0.75rem;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.treasure-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(244, 114, 182, 0.15), transparent);
  transition: left 0.3s ease;
}

.treasure-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(244, 114, 182, 0.25);
  border-color: rgba(244, 114, 182, 0.3);
  background: rgba(255, 255, 255, 0.95);
}

.treasure-card:hover::before {
  left: 100%;
}

.card-badge {
  background: linear-gradient(135deg, #ec4899, #db2777);
  color: #fff;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
  box-shadow: 0 2px 6px rgba(236, 72, 153, 0.2);
}

.card-content {
  flex: 1;
}

.store-name {
  color: #be185d;
  font-size: 1rem;
  font-weight: 700;
  margin: 0 0 0.25rem 0;
}

.store-address {
  color: #db2777;
  font-size: 0.8rem;
  margin: 0 0 0.5rem 0;
}

.store-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.meta-tag, .meta-hours {
  background: rgba(244, 114, 182, 0.15);
  color: #be185d;
  padding: 0.125rem 0.5rem;
  border-radius: 12px;
  font-size: 0.7rem;
  border: 1px solid rgba(244, 114, 182, 0.2);
}

.card-action {
  font-size: 1.2rem;
  color: #ec4899;
  flex-shrink: 0;
}

/* ===== 空状态 ===== */
.empty-state {
  padding: 3rem 2rem;
  text-align: center;
  color: #be185d;
}

.empty-tip {
  font-size: 0.8rem;
  opacity: 0.7;
  margin-top: 0.5rem;
}

/* ===== 响应式 ===== */
@media (max-width: 640px) {
  .market-game-hub {
    margin: 0.5rem;
    padding: 0.5rem;
  }
  
  .treasure-modal {
    margin: 0.5rem;
    max-height: 90vh;
  }
  
  .treasure-list {
    max-height: calc(90vh - 180px);
  }
  
  .treasure-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .card-action {
    align-self: flex-end;
  }
}
</style>