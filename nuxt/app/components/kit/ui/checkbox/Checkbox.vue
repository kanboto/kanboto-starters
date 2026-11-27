<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { cn, focusRing } from '../../lib/utils'

// A native checkbox: it validates, submits and reads like one, without script.
const props = defineProps<{
  class?: HTMLAttributes['class']
}>()

const model = defineModel<boolean>()
</script>

<template>
  <input
    v-model="model"
    type="checkbox"
    data-slot="checkbox"
    :class="cn('size-4 shrink-0 rounded-(--radius-sm) accent-primary user-invalid:outline-2 user-invalid:outline-destructive', focusRing, props.class)"
  >
</template>
