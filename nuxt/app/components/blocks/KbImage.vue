<script setup lang="ts">
import type { HTMLAttributes, Ref } from 'vue'
import { computed, inject, resolveComponent, unref } from 'vue'
import { Image as ImageIcon } from 'lucide-vue-next'
import type { KbImageField } from './lib/types'
import { cn } from './lib/utils'

// An image always reserves its place (`width`, `height`, ratio). Without a file yet, a tinted placeholder of
// the same ratio says what will stand there. An image of the site goes through the host's `NuxtImg` when it
// has one: the file stays at its original definition in the repository, the visitor receives a WebP at the
// width of their screen. In the page workshop (`kb:editing`) and for a file hosted elsewhere, a plain `img`.
const props = withDefaults(defineProps<{
  image: KbImageField
  /** The page's main image: loaded first, never lazily. */
  priority?: boolean
  field?: string
  /** Width the image takes on the page, by screen size, for `NuxtImg` (`sm:100vw lg:50vw`). */
  sizes?: string
  class?: HTMLAttributes['class']
}>(), {
  field: 'image',
  sizes: 'sm:100vw md:100vw lg:50vw',
})

const editing = inject<boolean | Ref<boolean>>('kb:editing', false)
const NuxtImg = resolveComponent('NuxtImg')
const optimised = computed(() => typeof NuxtImg !== 'string' && !unref(editing) && /^\/(?!\/)/.test(props.image.src ?? ''))

const RATIOS: Record<string, { class: string, value: number }> = {
  '1:1': { class: 'aspect-square', value: 1 },
  '4:3': { class: 'aspect-4/3', value: 4 / 3 },
  '3:2': { class: 'aspect-3/2', value: 3 / 2 },
  '16:9': { class: 'aspect-video', value: 16 / 9 },
  '3:4': { class: 'aspect-3/4', value: 3 / 4 },
  '21:9': { class: 'aspect-21/9', value: 21 / 9 },
}
const DEFAULT_WIDTH = 1200

const ratio = computed(() => RATIOS[props.image.ratio ?? ''] ?? RATIOS['4:3']!)
const width = computed(() => props.image.width ?? DEFAULT_WIDTH)
const height = computed(() => props.image.height ?? Math.round(width.value / ratio.value.value))
const caption = computed(() => props.image.alt || props.image.prompt || '')
</script>

<template>
  <component
    :is="NuxtImg"
    v-if="image.src && optimised"
    :src="image.src"
    :alt="image.alt ?? ''"
    :width="width"
    :height="height"
    format="webp"
    :sizes="sizes"
    :loading="priority ? 'eager' : 'lazy'"
    :fetchpriority="priority ? 'high' : undefined"
    decoding="async"
    :data-kb-field="field"
    :class="cn('h-auto w-full rounded-(--radius-lg) bg-muted object-cover', ratio.class, props.class)"
  />
  <img
    v-else-if="image.src"
    :src="image.src"
    :alt="image.alt ?? ''"
    :width="width"
    :height="height"
    :loading="priority ? 'eager' : 'lazy'"
    :fetchpriority="priority ? 'high' : undefined"
    decoding="async"
    :data-kb-field="field"
    :class="cn('h-auto w-full rounded-(--radius-lg) bg-muted object-cover', ratio.class, props.class)"
  >
  <div
    v-else
    role="img"
    :aria-label="caption"
    :data-kb-field="field"
    :class="cn('flex w-full flex-col items-center justify-center gap-3 rounded-(--radius-lg) border border-dashed border-border bg-muted p-6 text-center text-muted-foreground', ratio.class, props.class)"
  >
    <ImageIcon
      class="size-6"
      aria-hidden="true"
    />
    <span
      v-if="caption"
      class="line-clamp-3 max-w-prose text-sm"
    >{{ caption }}</span>
  </div>
</template>
