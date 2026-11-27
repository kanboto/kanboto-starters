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
  <textarea
    v-model="model"
    data-slot="textarea"
    :class="cn(controlClass, 'field-sizing-content min-h-24 resize-y', props.class)"
  />
</template>
