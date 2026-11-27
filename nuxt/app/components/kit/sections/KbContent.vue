<script setup lang="ts">
import { computed } from 'vue'
import { ArrowRight } from 'lucide-vue-next'
import KbImage from '../KbImage.vue'
import KbLink from '../KbLink.vue'
import KbSectionHeader from '../KbSectionHeader.vue'
import { useVariant } from '../lib/block'
import { image, lines, link, text } from '../lib/fields'
import type { KbBlock } from '../lib/types'
import { cn, textLink } from '../lib/utils'
import KbSection from './KbSection.vue'

const props = defineProps<{
  block: KbBlock
}>()

const variant = useVariant(() => props.block, ['text', 'media-right', 'media-left'])
const fields = computed(() => props.block.props)
const picture = computed(() => (variant.value === 'text' ? undefined : image(fields.value, 'image')))
const paragraphs = computed(() => lines(text(fields.value, 'body')))
const more = computed(() => link(fields.value, 'link'))
</script>

<template>
  <KbSection
    :block="block"
    :data-kb-variant="variant"
  >
    <div :class="picture ? 'grid items-center gap-10 @4xl:grid-cols-2 @4xl:gap-16' : 'mx-auto max-w-prose'">
      <KbImage
        v-if="picture && variant === 'media-left'"
        :image="picture"
      />
      <div class="flex flex-col gap-6">
        <KbSectionHeader :block="block" />
        <div
          v-if="paragraphs.length"
          data-kb-field="body"
          class="flex max-w-prose flex-col gap-4 text-muted-foreground"
        >
          <p
            v-for="(paragraph, index) in paragraphs"
            :key="index"
          >
            {{ paragraph }}
          </p>
        </div>
        <KbLink
          v-if="more"
          :href="more.href"
          data-kb-field="link"
          :class="cn('inline-flex w-fit items-center gap-2 font-medium', textLink)"
        >
          {{ more.label }}
          <ArrowRight
            class="size-4"
            aria-hidden="true"
          />
        </KbLink>
      </div>
      <KbImage
        v-if="picture && variant === 'media-right'"
        :image="picture"
      />
    </div>
  </KbSection>
</template>
