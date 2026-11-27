<script setup lang="ts">
import { computed } from 'vue'
import KbSectionHeader from '../KbSectionHeader.vue'
import { useVariant } from '../lib/block'
import { items, text } from '../lib/fields'
import type { KbBlock } from '../lib/types'
import { Card } from '../ui/card'
import KbSection from './KbSection.vue'

const props = defineProps<{
  block: KbBlock
}>()

const variant = useVariant(() => props.block, ['grid', 'single'])
const list = computed(() => items(props.block.props, 'items').filter(item => text(item, 'quote')))
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
      <div
        v-if="list.length"
        :class="variant === 'grid' ? 'grid gap-6 @3xl:grid-cols-[repeat(auto-fit,minmax(min(100%,calc(var(--spacing)*64)),1fr))]' : 'mx-auto flex max-w-3xl flex-col gap-12'"
      >
        <component
          :is="variant === 'grid' ? Card : 'figure'"
          v-for="(item, index) in list"
          :key="index"
          as="figure"
          data-kb-field="items"
          :data-kb-item="index"
          :class="variant === 'grid' ? 'justify-between gap-6' : 'flex flex-col items-center gap-6 text-center'"
        >
          <blockquote
            data-kb-field="quote"
            :class="variant === 'grid' ? 'text-base' : 'font-(family-name:--font-display) text-xl leading-tight @3xl:text-2xl'"
          >
            <p>{{ text(item, 'quote') }}</p>
          </blockquote>
          <figcaption
            v-if="text(item, 'author') || text(item, 'role')"
            class="flex flex-col text-sm"
          >
            <span
              v-if="text(item, 'author')"
              data-kb-field="author"
              class="font-semibold"
            >{{ text(item, 'author') }}</span>
            <span
              v-if="text(item, 'role')"
              data-kb-field="role"
              class="text-muted-foreground"
            >{{ text(item, 'role') }}</span>
          </figcaption>
        </component>
      </div>
    </div>
  </KbSection>
</template>
