<script setup lang="ts">
import KbNavBar from '../KbNavBar.vue'
import { useVariant } from '../lib/block'
import type { KbBlock } from '../lib/types'

// `sidebar` needs room beside the page: `KbPage` lays the other blocks next to it in a wide container.
const props = defineProps<{
  block: KbBlock
}>()

const variant = useVariant(() => props.block, ['sidebar', 'topbar'])
</script>

<template>
  <KbNavBar
    :block="block"
    :layout="variant === 'sidebar' ? 'side' : 'start'"
    :data-kb-variant="variant"
  />
</template>
