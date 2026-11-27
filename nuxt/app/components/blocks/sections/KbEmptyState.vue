<script setup lang="ts">
import { computed } from 'vue'
import { Inbox } from 'lucide-vue-next'
import KbAction from '../KbAction.vue'
import { useHeading, useVariant } from '../lib/block'
import { link, text } from '../lib/fields'
import type { KbBlock } from '../lib/types'
import { cn } from '../lib/utils'
import KbSection from './KbSection.vue'

const props = defineProps<{
  block: KbBlock
}>()

const variant = useVariant(() => props.block, ['centered', 'card'])
const heading = useHeading(() => props.block)
const fields = computed(() => props.block.props)
</script>

<template>
  <KbSection
    :block="block"
    :data-kb-variant="variant"
  >
    <div :class="cn('mx-auto flex max-w-xl flex-col items-center gap-4 text-center', variant === 'card' && 'max-w-none rounded-(--radius-lg) border border-dashed border-border px-6 py-12')">
      <span class="flex size-12 items-center justify-center rounded-(--radius-pill) bg-muted text-muted-foreground">
        <Inbox
          class="size-6"
          aria-hidden="true"
        />
      </span>
      <component
        :is="heading"
        v-if="text(fields, 'title')"
        data-kb-field="title"
        class="text-xl leading-tight"
      >
        {{ text(fields, 'title') }}
      </component>
      <p
        v-if="text(fields, 'text')"
        data-kb-field="text"
        class="max-w-prose text-muted-foreground"
      >
        {{ text(fields, 'text') }}
      </p>
      <KbAction
        :link="link(fields, 'primary')"
        field="primary"
        class="mt-2"
      />
    </div>
  </KbSection>
</template>
