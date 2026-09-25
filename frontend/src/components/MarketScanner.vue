<template>
  <div class="market-scanner">
    <h3 class="scanner-title">🥕Find Ingredients Nearby</h3>

    <button class="btn-scan" @click="scanStores" :disabled="loading">
      <span v-if="!loading">🧭 Start Scouting</span>
      <span v-else class="spinner"></span>
    </button>

    <p v-if="error" class="error">⚠️ {{ error }}</p>

    <!-- skeleton while loading -->
    <ul v-if="loading" class="list">
      <li v-for="i in 4" :key="i" class="skeleton">
        <div class="bar short"></div><div class="bar long"></div>
      </li>
    </ul>

    <!-- results -->
    <transition-group name="fade" tag="ul" class="list" v-else>
      <li v-for="s in stores" :key="s.id" class="card" @click="openMap(s)">
        <div class="stripe"></div>
        <h4>{{ s.name }}</h4>
        <p class="addr">{{ s.address }}</p>
        <p class="dist">📍 {{ s.distance?.toFixed(1) || 0 }} km</p>
      </li>
    </transition-group>

    <p v-if="!loading && !stores.length && !error" class="empty">
      No tasty loot nearby… try again!
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { Store } from '@/models/market'

const stores  = ref<Store[]>([])
const loading = ref(false)
const error   = ref('')

// Haversine & helpers
const toRad = (d: number) => d * Math.PI / 180
function haversine(lat1: number, lon1: number, lat2: number, lon2: number) {
  const R = 6371
  const dLat = toRad(lat2 - lat1)
  const dLon = toRad(lon2 - lon1)
  const a = Math.sin(dLat/2)**2
          + Math.cos(toRad(lat1))*Math.cos(toRad(lat2))
            * Math.sin(dLon/2)**2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a))
}
function buildAddress(tags: Record<string,string>, lat: number, lon: number) {
  const line1 = [tags['addr:housenumber'], tags['addr:street']].filter(Boolean).join(' ')
  const line2 = [tags['addr:city'], tags['addr:state'], tags['addr:postcode']].filter(Boolean).join(', ')
  return (line1 || line2)
    ? [line1, line2].filter(Boolean).join(', ')
    : `${lat.toFixed(4)}, ${lon.toFixed(4)}`
}

function getPosition(): Promise<GeolocationPosition> {
  return new Promise((res, rej) =>
    navigator.geolocation.getCurrentPosition(res, rej, {
      enableHighAccuracy: true, timeout: 8000
    })
  )
}

function openMap(s: Store) {
  const q = encodeURIComponent(`${s.name} ${s.address}`)
  window.open(`https://www.google.com/maps/search/?api=1&query=${q}`, '_blank')
}

async function scanStores() {
  loading.value = true
  error.value   = ''
  stores.value  = []

  try {
    const { coords: { latitude: lat, longitude: lon } } = await getPosition()
    const query = `[out:json][timeout:15];
      node["shop"~"supermarket|grocery"](around:5000,${lat},${lon});
      out;`
    const resp = await fetch('https://overpass-api.de/api/interpreter', {
      method: 'POST', body: query
    })
    if (!resp.ok) throw new Error('Network error')
    const json = await resp.json() as { elements: any[] }
    stores.value = json.elements.map(el => {
      const tags = el.tags || {}
      return {
        id: `${el.id}`,
        name: tags.name || 'Unnamed',
        lat: el.lat, lon: el.lon,
        address: buildAddress(tags, el.lat, el.lon),
        distance: haversine(lat, lon, el.lat, el.lon)
      }
    })
    .sort((a,b) => a.distance - b.distance)
    .slice(0, 5)
    if (!stores.value.length) error.value = 'No stores found within 5 km.'
  } catch (e: any) {
    if (e.code === 1) error.value = 'Permission denied.'
    else if (e.code === 2) error.value = 'Position unavailable.'
    else if (e.code === 3) error.value = 'Location timeout.'
    else error.value = e.message || 'Scan failed.'
  } finally {
    setTimeout(() => loading.value = false, 300)
  }
}
</script>

<style scoped>
.market-scanner {
  padding: 1rem;
  background: #fff;
  border-radius: 1rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
}
.scanner-title {
  font-weight: bold;
  margin-bottom: .75rem;
  color: #0f83d7;
}
.btn-scan {
  background: #0f83d7; color: #fff;
  padding: .6rem 1.2rem; border:none; border-radius:6px;
  cursor: pointer; transition: .2s;
}
.btn-scan:disabled { background: #9ac8f8; cursor: not-allowed }
.spinner {
  width: 1em; height: 1em;
  border: 2px solid rgba(255,255,255,.6);
  border-top-color: #fff; border-radius: 50%;
  animation: spin .8s linear infinite;
}
@keyframes spin{ to{ transform: rotate(360deg) } }

.list {
  list-style:none; padding: 0; margin:1rem 0 0;
}
.card {
  position: relative;
  margin-bottom: 1rem;
  padding: .8rem;
  background: #fdfcff;
  border-radius: 8px;
  cursor: pointer;
  transition: transform .2s, box-shadow .2s;
}
.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 6px 16px rgba(0,0,0,0.12);
}
.stripe {
  height: 4px;
  background: linear-gradient(90deg,#0f83d7,#76b7ff);
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
  position: absolute; top: 0; left: 0; right: 0;
}
.addr, .dist {
  margin: 0;
  font-size: .85rem;
  color: #4c5868;
}
.empty {
  color: #64748b;
  margin-top: 1rem;
}
.skeleton {
  display: flex;
  flex-direction: column;
  gap: .5rem;
  padding: .75rem;
  background: #f1f5f9;
  border-radius: 6px;
  overflow:hidden;
  margin-bottom: .75rem;
}
.bar {
  height: .8em;
  background: #e2e8f0;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}
.bar::before {
  content: '';
  position: absolute; top: 0; left: -100%;
  width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, #f1f5f9 50%, transparent);
  animation: shimmer 1s infinite;
}
.short { width: 40% }
.long  { width: 75% }
@keyframes shimmer { to{ left:100% } }
.fade-enter-active { transition: .4s }
.fade-enter-from   { opacity: 0; transform: translateY(10px) }
.fade-enter-to     { opacity: 1; transform: translateY(0) }
</style>
