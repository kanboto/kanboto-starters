<script setup lang="ts">
import { computed } from 'vue'
import KbSectionHeader from '../KbSectionHeader.vue'
import { useItemHeading, useVariant } from '../lib/block'
import { items, text } from '../lib/fields'
import type { KbBlock } from '../lib/types'
import { cn } from '../lib/utils'
import KbSection from './KbSection.vue'

const props = defineProps<{
  block: KbBlock
}>()

const variant = useVariant(() => props.block, ['row', 'column'])
const list = computed(() => items(props.block.props, 'items'))
const itemHeading = useItemHeading(() => props.block)
</script>

<template>
  <KbSection
    :block="block"
    :data-kb-variant="variant"
  >
    <div class="flex flex-col gap-10 @3xl:gap-14">
      <KbSectionHeader
        :block="block"
        center
      />
      <ol
        v-if="list.length"
        role="list"
        :class="variant === 'row' ? 'grid gap-8 @3xl:grid-cols-[repeat(auto-fit,minmax(min(100%,calc(var(--spacing)*52)),1fr))]' : 'mx-auto flex w-full max-w-2xl flex-col'"
      >
        <li
          v-for="(item, index) in list"
          :key="index"
          data-kb-field="items"
          :data-kb-item="index"
          :class="variant === 'row' ? 'flex flex-col gap-4 border-t border-border pt-6' : 'flex gap-5'"
        >
          <div :class="cn('flex shrink-0 flex-col items-center gap-2', variant === 'row' && 'items-start')">
            <span
              class="flex min-h-8 min-w-8 items-center justify-center rounded-(--radius-pill) bg-primary text-sm font-semibold text-primary-foreground"
              aria-hidden="true"
            >{{ index + 1 }}</span>
            <span
              v-if="variant === 'column' && index < list.length - 1"
              class="flex-1 border-s border-border"
            />
          </div>
          <div :class="cn('flex min-w-0 flex-col gap-2', variant === 'column' && 'pb-10')">
            <component
              :is="itemHeading"
              v-if="text(item, 'title')"
              data-kb-field="title"
              class="text-lg"
            >
              {{ text(item, 'title') }}
            </component>
            <p
              v-if="text(item, 'text')"
              data-kb-field="text"
              class="max-w-prose text-muted-foreground"
            >
              {{ text(item, 'text') }}
            </p>
          </div>
        </li>
      </ol>
    </div>
  </KbSection>
</template>
