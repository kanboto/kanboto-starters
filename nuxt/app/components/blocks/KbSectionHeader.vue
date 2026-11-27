<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { computed } from 'vue'
import { centred, useHeading } from './lib/block'
import KbMarked from './KbMarked'
import { text } from './lib/fields'
import type { KbBlock } from './lib/types'
import { cn } from './lib/utils'

// The head most sections share: an eyebrow, the title (the page's `h1` when this block is the one that
// titles it) and a sentence. Renders nothing when the block has none of them.
const props = defineProps<{
  block: KbBlock
  center?: boolean
  /** Key of the sentence under the title: `subtitle` for most blocks, `text` for some. */
  lead?: string
  /** A quieter title, for the blocks of an application screen. */
  compact?: boolean
  class?: HTMLAttributes['class']
}>()

const heading = useHeading(() => props.block)
const eyebrow = computed(() => text(props.block.props, 'eyebrow'))
const title = computed(() => text(props.block.props, 'title'))
const middle = computed(() => centred(props.block, !!props.center))
const leadKey = computed(() => props.lead ?? 'subtitle')
const leadText = computed(() => text(props.block.props, leadKey.value))
</script>

<template>
  <header
    v-if="eyebrow || title || leadText"
    :class="cn('flex max-w-2xl flex-col gap-3', middle && 'mx-auto items-center text-center', props.class)"
  >
    <p
      v-if="eyebrow"
      data-kb-field="eyebrow"
      class="text-sm font-medium tracking-(--tracking-caps) text-muted-foreground uppercase"
    >
      {{ eyebrow }}
    </p>
    <component
      :is="heading"
      v-if="title"
      :id="`kb-title-${block.id}`"
      data-kb-field="title"
      :class="cn('leading-tight', compact ? 'text-lg @3xl:text-xl' : 'text-xl @3xl:text-2xl')"
    >
      <KbMarked :text="title" />
    </component>
    <p
      v-if="leadText"
      :data-kb-field="leadKey"
      class="text-lg text-muted-foreground"
    >
      {{ leadText }}
    </p>
  </header>
</template>
