<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn } from '../../lib/utils'
import { controlClass } from '../input'

const props = defineProps<{
  class?: HTMLAttributes['class']
}>()

const model = defineModel<string>()
</script>

<template>
  <select
    v-model="model"
    data-slot="native-select"
    :class="cn(controlClass, 'min-h-9', props.class)"
  >
    <slot />
  </select>
</template>
