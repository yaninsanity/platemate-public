<!-- src/components/ModelViewer.vue -->
<template>
  <div ref="container" class="model-viewer" />
</template>

<script setup lang="ts">
// 3D GLTF 模型渲染组件
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'

const props = defineProps<{ src: string }>()

const container = ref<HTMLDivElement | null>(null)
let renderer: THREE.WebGLRenderer
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let controls: OrbitControls
let mixer: THREE.AnimationMixer
const clock = new THREE.Clock()
let frameId: number

function initThree() {
  const width  = container.value!.clientWidth
  const height = container.value!.clientHeight

  // 渲染器
  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  container.value!.appendChild(renderer.domElement)

  // 场景 & 相机
  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100)
  camera.position.set(0, 1.5, 3)

  // 灯光
  const hemi = new THREE.HemisphereLight(0xffffff, 0x444444, 1.2)
  hemi.position.set(0, 1, 0)
  scene.add(hemi)

  // 控制器
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.autoRotate = true
  controls.autoRotateSpeed = 1.2

  // 加载模型
  const loader = new GLTFLoader()
  loader.load(props.src, gltf => {
    const model = gltf.scene
    model.scale.setScalar(1)
    scene.add(model)
    if (gltf.animations && gltf.animations.length) {
      mixer = new THREE.AnimationMixer(model)
      gltf.animations.forEach(clip => mixer.clipAction(clip).play())
    }
  })

  window.addEventListener('resize', onResize)
  animate()
}

function animate() {
  frameId = requestAnimationFrame(animate)
  if (mixer) mixer.update(clock.getDelta())
  controls.update()
  renderer.render(scene, camera)
}

function onResize() {
  if (!container.value) return
  const w = container.value.clientWidth
  const h = container.value.clientHeight
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h)
}

onMounted(initThree)
onBeforeUnmount(() => {
  cancelAnimationFrame(frameId)
  controls.dispose()
  renderer.dispose()
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
.model-viewer {
  width: 100%;
  height: 100%;
  position: relative;
}
</style>
