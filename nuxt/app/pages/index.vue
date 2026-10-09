<script setup lang="ts">
const { appName } = useRuntimeConfig().public
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
  padding: 0 16px;
  box-sizing: border-box;
  text-align: center;
}

h1 {
  margin: 0;
  font-size: clamp(2rem, 6vw, 3.5rem);
  font-weight: 600;
  letter-spacing: -0.02em;
}

p {
  margin: 0.75rem 0 0;
  font-size: 1.125rem;
  opacity: 0.6;
}
</style>
