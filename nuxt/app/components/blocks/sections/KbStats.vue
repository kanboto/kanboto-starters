<script setup lang="ts">
import { computed } from 'vue'
import KbSectionHeader from '../KbSectionHeader.vue'
import { useVariant } from '../lib/block'
import { items, text } from '../lib/fields'
import type { KbBlock } from '../lib/types'
import { cn } from '../lib/utils'
import { Card } from '../ui/card'
import KbSection from './KbSection.vue'

const props = defineProps<{
  block: KbBlock
}>()

const variant = useVariant(() => props.block, ['row', 'cards'])
const list = computed(() => items(props.block.props, 'items'))
</script>

<template>
  <KbSection
    :block="block"
    :data-kb-variant="variant"
  >
    <div class="flex flex-col gap-10">
      <KbSectionHeader
        :block="block"
        center
      />
      <ul
        v-if="list.length"
        role="list"
        :class="cn('grid grid-cols-2 @3xl:grid-cols-[repeat(auto-fit,minmax(min(100%,calc(var(--spacing)*40)),1fr))]', variant === 'cards' ? 'gap-4' : 'gap-y-8 @3xl:divide-x @3xl:divide-border')"
      >
        <component
          :is="variant === 'cards' ? Card : 'li'"
          v-for="(item, index) in list"
          :key="index"
          as="li"
          data-kb-field="items"
          :data-kb-item="index"
          :class="cn('flex flex-col gap-1', variant === 'row' && 'items-center px-4 text-center')"
        >
          <strong
            v-if="text(item, 'value')"
            data-kb-field="value"
            class="font-(family-name:--font-display) text-2xl leading-tight font-semibold"
          >{{ text(item, 'value') }}</strong>
          <span
            v-if="text(item, 'label')"
            data-kb-field="label"
            class="text-sm text-muted-foreground"
          >{{ text(item, 'label') }}</span>
        </component>
      </ul>
    </div>
  </KbSection>
</template>
