<script setup lang="ts">
import { computed, useTemplateRef } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import KbImage from '../KbImage.vue'
import KbSectionHeader from '../KbSectionHeader.vue'
import { columnsClass, useVariant } from '../lib/block'
import { image, items, text } from '../lib/fields'
import { useLabels } from '../lib/labels'
import type { KbBlock } from '../lib/types'
import { cn, focusRing } from '../lib/utils'
import { Button } from '../ui/button'
import KbSection from './KbSection.vue'

// The carousel is a native scroller that snaps to its slides: swipe, wheel and keyboard work without
// script; the two buttons only scroll it by a page.
const props = defineProps<{
  block: KbBlock
}>()

const SLIDES: Record<string, string> = {
  2: '@3xl:basis-[calc(50%_-_var(--spacing)_*_2)]',
  3: '@3xl:basis-[calc(100%_/_3_-_var(--spacing)_*_8_/_3)]',
  4: '@3xl:basis-[calc(25%_-_var(--spacing)_*_3)]',
}

const labels = useLabels()
const variant = useVariant(() => props.block, ['grid', 'carousel'])
const list = computed(() => items(props.block.props, 'items').filter(item => image(item, 'image')))
const title = computed(() => text(props.block.props, 'title'))
const track = useTemplateRef<HTMLElement>('track')

function page(direction: 1 | -1): void {
  track.value?.scrollBy({ left: direction * track.value.clientWidth })
}
</script>

<template>
  <KbSection
    :block="block"
    :data-kb-variant="variant"
  >
    <div class="flex flex-col gap-10">
      <div
        v-if="title || (variant === 'carousel' && list.length > 1)"
        class="flex items-end justify-between gap-6"
      >
        <KbSectionHeader :block="block" />
        <div
          v-if="variant === 'carousel' && list.length > 1"
          class="ml-auto flex gap-2"
        >
          <Button
            variant="outline"
            size="icon"
            :aria-label="labels.previous"
            @click="page(-1)"
          >
            <ChevronLeft aria-hidden="true" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            :aria-label="labels.next"
            @click="page(1)"
          >
            <ChevronRight aria-hidden="true" />
          </Button>
        </div>
      </div>
      <component
        :is="variant === 'carousel' ? 'div' : 'ul'"
        v-if="list.length"
        ref="track"
        :role="variant === 'carousel' ? 'region' : undefined"
        :aria-roledescription="variant === 'carousel' ? 'carousel' : undefined"
        :aria-label="variant === 'carousel' ? title || labels.gallery : undefined"
        :tabindex="variant === 'carousel' ? 0 : undefined"
        :class="variant === 'carousel'
          ? cn('flex snap-x snap-mandatory gap-4 overflow-x-auto overscroll-x-contain rounded-(--radius-lg) pb-2 touch-manipulation motion-safe:scroll-smooth', focusRing)
          : columnsClass(block)"
      >
        <component
          :is="variant === 'carousel' ? 'div' : 'li'"
          v-for="(item, index) in list"
          :key="index"
          :role="variant === 'carousel' ? 'group' : undefined"
          :aria-roledescription="variant === 'carousel' ? 'slide' : undefined"
          :aria-label="variant === 'carousel' ? `${index + 1} / ${list.length}` : undefined"
          data-kb-field="items"
          :data-kb-item="index"
          :class="variant === 'carousel' && cn('shrink-0 basis-5/6 snap-start', SLIDES[block.options?.columns ?? '3'] ?? SLIDES[3])"
        >
          <figure class="flex flex-col gap-3">
            <KbImage :image="image(item, 'image')!" />
            <figcaption
              v-if="text(item, 'caption')"
              data-kb-field="caption"
              class="text-sm text-muted-foreground"
            >
              {{ text(item, 'caption') }}
            </figcaption>
          </figure>
        </component>
      </component>
    </div>
  </KbSection>
</template>
