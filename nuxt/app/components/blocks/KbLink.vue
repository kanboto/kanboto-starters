<script setup lang="ts">
import type { Ref } from 'vue'
import { computed, inject, resolveComponent, unref } from 'vue'
import { PAGE_PATH } from './lib/block'

// The library's only tie to Nuxt: a link inside the site goes through `NuxtLink` when the host has one. In the
// page workshop (`kb:editing`), a link is inert: clicking it selects, it never navigates.
const props = defineProps<{
  href?: string
}>()

const editing = inject<boolean | Ref<boolean>>('kb:editing', false)
const NuxtLink = resolveComponent('NuxtLink')

// Without an address there is nowhere to go: the anchor keeps its place and stays out of the tab order.
const target = computed(() => props.href || undefined)
const internal = computed(() => typeof NuxtLink !== 'string' && /^\/(?!\/)/.test(target.value ?? ''))
// `NuxtLink` marks the current page itself; a plain anchor gets the same mark here.
const path = inject(PAGE_PATH, undefined)
const current = computed(() => (target.value && target.value === unref(path) ? 'page' : undefined))
</script>

<template>
  <a
    v-if="unref(editing)"
    :href="target"
    :aria-current="current"
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
    :aria-current="current"
  ><slot /></a>
</template>
