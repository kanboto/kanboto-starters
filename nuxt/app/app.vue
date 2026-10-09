<script setup lang="ts">
const { appName } = useRuntimeConfig().public

useHead({
  title: appName,
  htmlAttrs: { lang: 'en' },
  link: [{ rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
})
</script>

<template>
  <NuxtPage />
</template>

<style>
html,
body {
  margin: 0;
  color: #1f2328;
  background: #fff;
  font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}

@media (prefers-color-scheme: dark) {
  html,
  body {
    color: #e6e6e6;
    background: #111;
  }
}
</style>
