<script setup lang="ts">
// The page is data (`app/content/pages/home.json`), rendered block by block by the block library.
const page = usePageContent('home')

useSeoMeta({
  title: page.title,
  description: page.description,
  ogTitle: page.title,
  ogDescription: page.description,
})
</script>

<template>
  <KbPage :page="page" />
</template>
