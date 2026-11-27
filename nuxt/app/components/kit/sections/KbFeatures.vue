<script setup lang="ts">
import { computed } from 'vue'
import KbSectionHeader from '../KbSectionHeader.vue'
import { columnsClass, useVariant } from '../lib/block'
import { items, text } from '../lib/fields'
import { icon } from '../lib/icons'
import type { KbBlock } from '../lib/types'
import { cn } from '../lib/utils'
import { Card } from '../ui/card'
import KbSection from './KbSection.vue'

const props = defineProps<{
  block: KbBlock
}>()

const variant = useVariant(() => props.block, ['grid', 'list', 'cards'])
const list = computed(() => items(props.block.props, 'items'))
</script>

<template>
  <KbSection
    :block="block"
    :data-kb-variant="variant"
  >
    <div :class="variant === 'list' ? 'grid gap-10 @4xl:grid-cols-5 @4xl:gap-16' : 'flex flex-col gap-10 @3xl:gap-14'">
      <KbSectionHeader
        :block="block"
        :center="variant !== 'list'"
        :class="variant === 'list' && '@4xl:col-span-2'"
      />
      <ul
        v-if="list.length"
        :class="variant === 'list' ? 'flex flex-col divide-y divide-border @4xl:col-span-3' : cn(columnsClass(block), variant === 'grid' && 'gap-x-8 gap-y-10')"
      >
        <component
          :is="variant === 'cards' ? Card : 'li'"
          v-for="(item, index) in list"
          :key="index"
          as="li"
          data-kb-field="items"
          :data-kb-item="index"
          :class="variant === 'list' ? 'flex gap-4 py-6 first:pt-0 last:pb-0' : 'flex flex-col gap-4'"
        >
          <span
            v-if="text(item, 'icon')"
            data-kb-field="icon"
            class="flex size-10 shrink-0 items-center justify-center rounded-(--radius-md) bg-muted text-foreground"
            :class="variant === 'cards' && 'bg-background'"
          >
            <component
              :is="icon(text(item, 'icon'))"
              class="size-5"
              aria-hidden="true"
            />
          </span>
          <div class="flex flex-col gap-2">
            <h3
              v-if="text(item, 'title')"
              data-kb-field="title"
              class="text-lg"
            >
              {{ text(item, 'title') }}
            </h3>
            <p
              v-if="text(item, 'text')"
              data-kb-field="text"
              class="text-muted-foreground"
            >
              {{ text(item, 'text') }}
            </p>
          </div>
        </component>
      </ul>
    </div>
  </KbSection>
</template>
