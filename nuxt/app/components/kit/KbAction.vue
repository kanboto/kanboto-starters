<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import KbLink from './KbLink.vue'
import type { KbLinkField } from './lib/types'
import type { ButtonVariants } from './ui/button'
import { Button } from './ui/button'

// A link field shown as a button: renders nothing without a label.
defineProps<{
  link?: KbLinkField
  field: string
  variant?: ButtonVariants['variant']
  size?: ButtonVariants['size']
  class?: HTMLAttributes['class']
}>()
</script>

<template>
  <Button
    v-if="link?.label"
    as-child
    :variant="variant"
    :size="size"
    :class="$props.class"
  >
    <KbLink
      :href="link.href"
      :data-kb-field="field"
    >
      {{ link.label }}
    </KbLink>
  </Button>
</template>
