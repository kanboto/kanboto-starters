<script setup lang="ts">
import type { Ref } from 'vue'
import { computed, inject, resolveComponent, unref } from 'vue'

// The kit's only tie to Nuxt: a link inside the site goes through `NuxtLink` when the host has one. In the
// page workshop (`kb:editing`), a link is inert: clicking it selects, it never navigates.
const props = defineProps<{
  href?: string
}>()

const editing = inject<boolean | Ref<boolean>>('kb:editing', false)
const NuxtLink = resolveComponent('NuxtLink')

const target = computed(() => props.href || '#')
const internal = computed(() => typeof NuxtLink !== 'string' && /^\/(?!\/)/.test(target.value))
</script>

<template>
  <a
    v-if="unref(editing)"
    :href="target"
    @click.prevent
  ><slot /></a>
  <component
    :is="NuxtLink"
    v-else-if="internal"
    :to="target"
  >
    <slot />
  </component>
  <a
    v-else
    :href="target"
  ><slot /></a>
</template>
