<template>
  <canvas ref="canvasRef" class="fixed inset-0 pointer-events-none" style="z-index: 0;" />
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const canvasRef = ref(null)
let animId = null
let particles = []

const PARTICLE_COUNT = 80
const MAX_CONNECT_DIST = 120
const SPEED = 0.35

function rand(min, max) {
  return Math.random() * (max - min) + min
}

function initParticles(w, h) {
  particles = Array.from({ length: PARTICLE_COUNT }, () => ({
    x: rand(0, w),
    y: rand(0, h),
    vx: rand(-SPEED, SPEED),
    vy: rand(-SPEED, SPEED),
    r: rand(1, 2.2),
    opacity: rand(0.2, 0.6),
  }))
}

function draw(ctx, w, h) {
  ctx.clearRect(0, 0, w, h)

  // Update + wrap positions
  for (const p of particles) {
    p.x += p.vx
    p.y += p.vy
    if (p.x < 0) p.x = w
    else if (p.x > w) p.x = 0
    if (p.y < 0) p.y = h
    else if (p.y > h) p.y = 0
  }

  // Draw connections
  for (let i = 0; i < particles.length; i++) {
    for (let j = i + 1; j < particles.length; j++) {
      const a = particles[i]
      const b = particles[j]
      const dx = a.x - b.x
      const dy = a.y - b.y
      const dist = Math.sqrt(dx * dx + dy * dy)
      if (dist < MAX_CONNECT_DIST) {
        const alpha = (1 - dist / MAX_CONNECT_DIST) * 0.12
        ctx.strokeStyle = `rgba(96, 165, 250, ${alpha})`
        ctx.lineWidth = 0.8
        ctx.beginPath()
        ctx.moveTo(a.x, a.y)
        ctx.lineTo(b.x, b.y)
        ctx.stroke()
      }
    }
  }

  // Draw dots
  for (const p of particles) {
    ctx.beginPath()
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2)
    ctx.fillStyle = `rgba(148, 163, 184, ${p.opacity})`
    ctx.fill()
  }
}

let raf = null

function loop(ctx, w, h) {
  draw(ctx, w, h)
  raf = requestAnimationFrame(() => loop(ctx, w, h))
}

function resize(canvas) {
  canvas.width = window.innerWidth
  canvas.height = window.innerHeight
  initParticles(canvas.width, canvas.height)
}

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  resize(canvas)
  loop(ctx, canvas.width, canvas.height)

  window.addEventListener('resize', () => {
    cancelAnimationFrame(raf)
    resize(canvas)
    loop(ctx, canvas.width, canvas.height)
  })
})

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
})
</script>
