<script setup lang="ts">
import { computed } from 'vue'
import { useHeading } from '../lib/block'
import { lines, text } from '../lib/fields'
import { useLabels } from '../lib/labels'
import type { KbBlock } from '../lib/types'
import { Badge } from '../ui/badge'
import KbSection from './KbSection.vue'

// What the block library does not have: the place is held, with what the block must do and show, until a component
// written for the project replaces it. Also renders a block whose type the block library does not know.
const props = defineProps<{
  block: KbBlock
}>()

const labels = useLabels()
const heading = useHeading(() => props.block)
const title = computed(() => text(props.block.props, 'title'))
const description = computed(() => lines(text(props.block.props, 'description')))
</script>

<template>
  <KbSection
    :block="block"
    data-kb-variant="placeholder"
  >
    <div class="flex flex-col items-start gap-4 rounded-(--radius-lg) border border-dashed border-border p-6 @3xl:p-10">
      <Badge variant="outline">
        {{ labels.custom }} · {{ block.type }}
      </Badge>
      <component
        :is="heading"
        v-if="title"
        data-kb-field="title"
        class="text-xl leading-tight"
      >
        {{ title }}
      </component>
      <div
        v-if="description.length"
        data-kb-field="description"
        class="flex max-w-prose flex-col gap-3 text-muted-foreground"
      >
        <p
          v-for="(paragraph, index) in description"
          :key="index"
        >
          {{ paragraph }}
        </p>
      </div>
    </div>
  </KbSection>
</template>
