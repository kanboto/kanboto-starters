<script setup lang="ts">
import KbNavBar from '../KbNavBar.vue'
import { useVariant } from '../lib/block'
import type { KbBlock } from '../lib/types'

const props = defineProps<{
  block: KbBlock
}>()

const variant = useVariant(() => props.block, ['simple', 'centered'])
</script>

<template>
  <KbNavBar
    :block="block"
    :layout="variant === 'centered' ? 'center' : 'start'"
    :data-kb-variant="variant"
  />
</template>
