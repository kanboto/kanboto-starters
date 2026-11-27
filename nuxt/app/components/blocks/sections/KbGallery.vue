<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, useTemplateRef } from 'vue'
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
// script. The buttons bring the previous or the next slide to the start and loop at the ends; one marker per
// slide goes straight to it; once the scroll settles, the current slide is announced.
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

/** Scrolls by one slide, measured on the slides themselves: a fixed distance drifts from where they snap. */
function page(direction: 1 | -1): void {
  const scroller = track.value
  if (!scroller) return
  const edge = scroller.getBoundingClientRect().left
  const slides = [...scroller.children] as HTMLElement[]
  const offset = (slide: HTMLElement) => slide.getBoundingClientRect().left - edge
  const current = slides.reduce((best, slide) => (Math.abs(offset(slide)) < Math.abs(offset(best)) ? slide : best), slides[0]!)
  const last = Math.abs(scroller.scrollLeft) + scroller.clientWidth >= scroller.scrollWidth - 1
  const first = Math.abs(scroller.scrollLeft) <= 1
  // At an end, the same button loops to the other one.
  const target = direction === 1 && last ? slides[0] : direction === -1 && first ? slides.at(-1) : slides[slides.indexOf(current) + direction]
  if (target) scroller.scrollBy({ left: offset(target) - offset(current) })
}

function go(index: number): void {
  const scroller = track.value
  const target = scroller?.children[index] as HTMLElement | undefined
  if (scroller && target) scroller.scrollBy({ left: target.getBoundingClientRect().left - scroller.getBoundingClientRect().left })
}

// The slide at the start of the scroller, read once the scroll has settled.
const current = ref(0)
const status = ref('')
let settle: ReturnType<typeof setTimeout> | undefined
function settled(): void {
  const scroller = track.value
  if (!scroller) return
  const edge = scroller.getBoundingClientRect().left
  const distances = [...scroller.children].map(slide => Math.abs(slide.getBoundingClientRect().left - edge))
  const index = distances.indexOf(Math.min(...distances))
  if (index !== current.value) status.value = `${index + 1} / ${distances.length}`
  current.value = index
}
function onScroll(): void {
  clearTimeout(settle)
  settle = setTimeout(settled, 150)
}
onMounted(() => {
  if (variant.value === 'carousel') track.value?.addEventListener('scroll', onScroll, { passive: true })
})
onBeforeUnmount(() => {
  clearTimeout(settle)
  track.value?.removeEventListener('scroll', onScroll)
})
</script>

<template>
  <KbSection
    :block="block"
    :data-kb-variant="variant"
  >
    <div
      class="flex flex-col gap-10"
      :role="variant === 'carousel' ? 'region' : undefined"
      :aria-roledescription="variant === 'carousel' ? 'carousel' : undefined"
      :aria-labelledby="variant === 'carousel' && title ? `kb-title-${block.id}` : undefined"
      :aria-label="variant === 'carousel' && !title ? labels.gallery : undefined"
    >
      <div
        v-if="title || (variant === 'carousel' && list.length > 1)"
        class="flex items-end justify-between gap-6"
      >
        <KbSectionHeader :block="block" />
        <div
          v-if="variant === 'carousel' && list.length > 1"
          class="ms-auto flex gap-2"
        >
          <Button
            variant="outline"
            size="icon"
            class="touch-manipulation"
            :aria-label="labels.previous"
            @click="page(-1)"
          >
            <ChevronLeft aria-hidden="true" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            class="touch-manipulation"
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
        :role="variant === 'carousel' ? 'group' : 'list'"
        :aria-label="variant === 'carousel' ? labels.slides : undefined"
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
      <template v-if="variant === 'carousel' && list.length > 1">
        <div class="flex flex-wrap justify-center">
          <button
            v-for="(item, index) in list"
            :key="index"
            type="button"
            :aria-label="`${index + 1} / ${list.length}`"
            :aria-current="index === current ? 'true' : undefined"
            :class="cn('group/marker flex size-6 items-center justify-center rounded-(--radius-pill) touch-manipulation pointer-coarse:size-11', focusRing)"
            @click="go(index)"
          >
            <span class="size-2 rounded-(--radius-pill) border border-foreground group-aria-[current=true]/marker:bg-foreground" />
          </button>
        </div>
        <div
          role="status"
          class="sr-only"
        >
          {{ status }}
        </div>
      </template>
    </div>
  </KbSection>
</template>
