<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '../../lib/utils'
import { controlClass } from '.'

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()

const model = defineModel<string | number>()
</script>

<template>
  <input
    v-model="model"
    data-slot="input"
    :class="cn(controlClass, 'min-h-9', props.class)"
  >
</template>
