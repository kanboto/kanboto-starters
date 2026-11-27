<script setup lang="ts">
import { computed } from 'vue'
import { ChevronRight } from 'lucide-vue-next'
import KbSectionHeader from '../KbSectionHeader.vue'
import { useVariant } from '../lib/block'
import { items, lines, text } from '../lib/fields'
import type { KbBlock } from '../lib/types'
import { cn, focusRing, touchTarget } from '../lib/utils'
import KbSection from './KbSection.vue'

// Native `details`: closed answers stay findable in the page, the keyboard works without script. The
// question is not a heading (screen readers drop a heading inside `summary`); the marker sits before it.
const props = defineProps<{
  block: KbBlock
}>()

const variant = useVariant(() => props.block, ['accordion', 'columns'])
const list = computed(() => items(props.block.props, 'items').filter(item => text(item, 'question')))
</script>

<template>
  <KbSection
    :block="block"
    :data-kb-variant="variant"
  >
    <div :class="cn('flex flex-col gap-10', variant === 'accordion' && 'mx-auto max-w-3xl')">
      <KbSectionHeader
        :block="block"
        :center="variant === 'accordion'"
      />
      <div
        v-if="list.length"
        :class="variant === 'columns' ? 'grid items-start gap-x-10 @3xl:grid-cols-2' : 'flex flex-col'"
      >
        <details
          v-for="(item, index) in list"
          :key="index"
          :name="`kb-faq-${block.id}`"
          data-kb-field="items"
          :data-kb-item="index"
          class="group border-b border-border"
        >
          <summary :class="cn('flex cursor-pointer list-none items-start gap-3 rounded-(--radius-sm) py-4 font-medium [&::-webkit-details-marker]:hidden', focusRing, touchTarget)">
            <ChevronRight
              class="mt-1 size-4 shrink-0 text-muted-foreground transition-transform duration-(--duration-fast) ease-(--easing) group-open:rotate-90"
              aria-hidden="true"
            />
            <span data-kb-field="question">{{ text(item, 'question') }}</span>
          </summary>
          <div
            v-if="text(item, 'answer')"
            data-kb-field="answer"
            class="flex max-w-prose flex-col gap-3 pb-5 pl-7 text-muted-foreground"
          >
            <p
              v-for="(paragraph, at) in lines(text(item, 'answer'))"
              :key="at"
            >
              {{ paragraph }}
            </p>
          </div>
        </details>
      </div>
    </div>
  </KbSection>
</template>
