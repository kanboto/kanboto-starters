<script setup lang="ts">
const { appName } = useRuntimeConfig().public

useSeoMeta({
  title: appName,
  description: 'Hello world',
  ogTitle: appName,
  ogDescription: 'Hello world',
})
</script>

<template>
  <main class="home">
    <h1>{{ appName }}</h1>
    <p>Hello world</p>
  </main>
</template>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  min-height: 100dvh;
  padding: 0 var(--gutter);
  box-sizing: border-box;
  text-align: center;
}

h1 {
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(var(--text-2xl), 8vw, var(--text-3xl));
  font-weight: var(--weight-bold);
  line-height: var(--leading-tight);
}

p {
  margin: var(--space-3) 0 0;
  font-size: var(--text-lg);
  color: var(--color-muted);
}
</style>
