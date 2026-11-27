<script setup lang="ts">
// A page of the signed-in area: rendered in the browser, never indexed. Its list shows the examples of the
// document until the page passes it the items of the backend API.
const page = usePageContent('app-items')

useSeoMeta({
  title: page.title,
  description: page.description,
})
</script>

<template>
  <KbPage :page="page" />
</template>
