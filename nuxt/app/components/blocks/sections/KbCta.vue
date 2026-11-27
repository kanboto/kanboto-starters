<script setup lang="ts">
import { computed } from 'vue'
import KbAction from '../KbAction.vue'
import { useHeading, useVariant } from '../lib/block'
import { link, text } from '../lib/fields'
import type { KbBlock } from '../lib/types'
import { cn } from '../lib/utils'
import KbSection from './KbSection.vue'

const props = defineProps<{
  block: KbBlock
}>()

const variant = useVariant(() => props.block, ['banner', 'centered'])
const heading = useHeading(() => props.block)
const fields = computed(() => props.block.props)
</script>

<template>
  <KbSection
    :block="block"
    :data-kb-variant="variant"
  >
    <div
      :class="variant === 'banner'
        ? 'flex flex-col gap-6 rounded-(--radius-lg) border border-border bg-card p-6 text-card-foreground @3xl:flex-row @3xl:items-center @3xl:justify-between @3xl:gap-10 @3xl:p-10'
        : 'mx-auto flex max-w-2xl flex-col items-center gap-6 text-center'"
    >
      <div class="flex flex-col gap-3">
        <component
          :is="heading"
          v-if="text(fields, 'title')"
          data-kb-field="title"
          class="text-xl leading-tight @3xl:text-2xl"
        >
          {{ text(fields, 'title') }}
        </component>
        <p
          v-if="text(fields, 'text')"
          data-kb-field="text"
          class="max-w-prose text-lg text-muted-foreground"
        >
          {{ text(fields, 'text') }}
        </p>
      </div>
      <div
        v-if="link(fields, 'primary') || link(fields, 'secondary')"
        :class="cn('flex shrink-0 flex-wrap gap-3', variant === 'centered' && 'justify-center')"
      >
        <KbAction
          :link="link(fields, 'primary')"
          field="primary"
          size="lg"
        />
        <KbAction
          :link="link(fields, 'secondary')"
          field="secondary"
          variant="outline"
          size="lg"
        />
      </div>
    </div>
  </KbSection>
</template>
