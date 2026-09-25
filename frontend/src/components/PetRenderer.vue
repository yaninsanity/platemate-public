<!-- PetRenderer.vue – de-ghosted switching & clean disposal (v2.2) -->
<template>
  <div ref="wrap" class="pet-renderer">
    <transition name="fade">
      <div v-if="!ready" class="loader">
        <v-progress-circular :value="progress"
                             size="48"
                             width="4"
                             color="primary"/>
        <p>{{ Math.round(progress) }} %</p>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment'

/* props / emits */
const props = defineProps<{ initialAnim: string; base?: string; bg?: string }>()
const emit  = defineEmits(['loaded', 'error'])
const ASSET = props.base ?? '/biped/'

/* reactivity */
const wrap     = ref<HTMLElement | null>(null)
const ready    = ref(false)
const progress = ref(0)

/* three core */
let scene: THREE.Scene,
    renderer: THREE.WebGLRenderer,
    cam: THREE.PerspectiveCamera,
    ctl: OrbitControls,
    mixer: THREE.AnimationMixer | null = null,
    raf = 0,
    ro: ResizeObserver

/* loaders */
const draco = new DRACOLoader().setDecoderPath('https://www.gstatic.com/draco/versioned/decoders/1.5.6/')
const gltf  = new GLTFLoader().setDRACOLoader(draco)

/* ───── life-cycle ───── */
onMounted(() => { init(); load(props.initialAnim); loop() })
onBeforeUnmount(cleanup)
watch(() => props.initialAnim, v => load(v))

/* ───── init scene ───── */
function init () {
  scene = new THREE.Scene()
  scene.background = new THREE.Color(props.bg ?? '#dfeaff')

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
  wrap.value!.appendChild(renderer.domElement)

  cam = new THREE.PerspectiveCamera(40, 1, 0.05, 200)

  ctl = new OrbitControls(cam, renderer.domElement)
  ctl.enableDamping = true
  ctl.enablePan     = false

  scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 1))
  scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment()).texture

  resize()
  ro = new ResizeObserver(resize)
  ro.observe(wrap.value!)
  window.addEventListener('resize', resize)
}

/* ───── load / switch model ───── */
let loadId = 0           // ▲ 用于取消过期加载
function load (file: string) {
  const id = ++loadId
  ready.value    = false
  progress.value = 0
  clear()

  gltf.load(
    ASSET + file,
    res => {
      if (id !== loadId) return              // ▲ 忽略过期结果
      res.scene.userData.pet = true          // ▲ 标记给 clear() 用
      scene.add(res.scene)

      if (res.animations.length) {
        mixer = new THREE.AnimationMixer(res.scene)
        mixer.clipAction(res.animations[0]).play()
      }

      fit(res.scene)
      ready.value = true
      emit('loaded', res.scene)
    },
    e   => progress.value = e.loaded / (e.total || 1) * 100,
    err => { emit('error', err); ready.value = true }
  )
}

/* ───── clear previous model ───── */
function clear () {
  mixer?.stopAllAction()
  mixer = null

  scene.children
       .filter(o => o.userData?.pet)
       .forEach(o => { disposeHierarchy(o); o.parent?.remove(o) })

  renderer.renderLists?.dispose?.()
}

/* ▲ dispose geometry, material and texture in turn */
function disposeHierarchy (root: THREE.Object3D) {
  root.traverse((obj: any) => {
    if (obj.geometry) obj.geometry.dispose()
    if (obj.material) {
      const mats = Array.isArray(obj.material) ? obj.material : [obj.material]
      mats.forEach((m: any) => {
        Object.keys(m).forEach(k => {
          const v = m[k]
          if (v && v.isTexture) v.dispose()
        })
        m.dispose?.()
      })
    }
  })
}

/* ───── framing ───── */
function fit (root: THREE.Object3D) {
  const s = new THREE.Sphere()
  new THREE.Box3().setFromObject(root).getBoundingSphere(s)

  const { clientWidth: w, clientHeight: h } = wrap.value!
  cam.aspect = w / h
  cam.updateProjectionMatrix()

  const vFov = THREE.MathUtils.degToRad(cam.fov)
  const hFov = 2 * Math.atan(Math.tan(vFov / 2) * cam.aspect)
  const fill = 0.45
  const dist = Math.max(
    s.radius / Math.sin(vFov / 2) / fill,
    s.radius / Math.sin(hFov / 2) / fill,
    s.radius * 1.3
  )

  cam.near = dist * 0.02
  cam.far  = dist * 40
  cam.updateProjectionMatrix()

  ctl.target.copy(s.center)
  cam.position.set(s.center.x, s.center.y + s.radius * 0.05, s.center.z + dist)
  ctl.update()
}

/* ───── render loop ───── */
function loop () {
  const clk = new THREE.Clock()
  ;(function tick () {
    raf = requestAnimationFrame(tick)
    mixer?.update(clk.getDelta())
    ctl.update()

    const { clientWidth: w, clientHeight: h } = wrap.value!
    renderer.setSize(w, h, false)
    renderer.render(scene, cam)
  })()
}

/* ───── resize ───── */
function resize () {
  if (!wrap.value) return
  const { clientWidth: w, clientHeight: h } = wrap.value
  cam.aspect = w / h
  cam.updateProjectionMatrix()
  renderer.setSize(w, h, false)
}

/* ───── cleanup ───── */
function cleanup () {
  cancelAnimationFrame(raf)
  ro?.disconnect()
  window.removeEventListener('resize', resize)
  clear()
  renderer.dispose()
  ctl.dispose()
}

/* external api */
function play (file: string) { load(file) }
defineExpose({ play })
</script>

<style scoped>
.pet-renderer{
  position:relative;
  width:100%;
  height:100%;
  overflow:hidden;
  border-radius:12px;
  background:#fff;
}
.pet-renderer canvas{
  width:100%;
  height:100%;
  display:block;
}
.loader{
  position:absolute;
  inset:0;
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  gap:6px;
  background:rgba(255,255,255,.9);
  backdrop-filter:blur(4px);
}
.fade-enter-active,
.fade-leave-active{transition:opacity .25s;}
.fade-enter-from,
.fade-leave-to{opacity:0;}
</style>
