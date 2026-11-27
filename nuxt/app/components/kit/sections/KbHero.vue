<script setup lang="ts">
import { computed } from 'vue'
import KbAction from '../KbAction.vue'
import KbImage from '../KbImage.vue'
import { useHeading, useVariant } from '../lib/block'
import { image, link, text } from '../lib/fields'
import type { KbBlock } from '../lib/types'
import { cn } from '../lib/utils'
import KbSection from './KbSection.vue'

const props = defineProps<{
  block: KbBlock
}>()

const variant = useVariant(() => props.block, ['centered', 'media-right', 'media-left', 'media-below'])
const heading = useHeading(() => props.block)
const fields = computed(() => props.block.props)
const picture = computed(() => image(fields.value, 'image'))
const beside = computed(() => variant.value === 'media-right' || variant.value === 'media-left')
const centered = computed(() => variant.value === 'centered')
</script>

<template>
  <KbSection
    :block="block"
    :data-kb-variant="variant"
  >
    <div :class="beside && picture ? 'grid items-center gap-10 @4xl:grid-cols-2 @4xl:gap-16' : 'flex flex-col gap-10 @3xl:gap-14'">
      <KbImage
        v-if="picture && variant === 'media-left'"
        :image="picture"
        priority
      />
      <div :class="cn('flex flex-col gap-6', centered ? 'mx-auto max-w-3xl items-center text-center' : 'max-w-3xl')">
        <p
          v-if="text(fields, 'eyebrow')"
          data-kb-field="eyebrow"
          class="text-sm font-medium tracking-(--tracking-caps) text-muted-foreground uppercase"
        >
          {{ text(fields, 'eyebrow') }}
        </p>
        <component
          :is="heading"
          v-if="text(fields, 'title')"
          data-kb-field="title"
          class="text-2xl leading-tight tracking-tight @3xl:text-3xl"
        >
          {{ text(fields, 'title') }}
        </component>
        <p
          v-if="text(fields, 'subtitle')"
          data-kb-field="subtitle"
          class="max-w-prose text-lg text-muted-foreground @3xl:text-xl"
        >
          {{ text(fields, 'subtitle') }}
        </p>
        <div
          v-if="link(fields, 'primary') || link(fields, 'secondary')"
          :class="cn('flex flex-wrap gap-3 pt-2', centered && 'justify-center')"
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
      <KbImage
        v-if="picture && variant !== 'media-left'"
        :image="picture"
        priority
        :class="centered && 'mx-auto max-w-4xl'"
      />
    </div>
  </KbSection>
</template>
