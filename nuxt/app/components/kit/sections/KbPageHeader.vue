<script setup lang="ts">
import { computed, inject } from 'vue'
import { ArrowLeft } from 'lucide-vue-next'
import KbAction from '../KbAction.vue'
import KbLink from '../KbLink.vue'
import { PAGE_PATH, useHeading, useVariant } from '../lib/block'
import { link, text } from '../lib/fields'
import { useLabels } from '../lib/labels'
import type { KbBlock } from '../lib/types'
import { cn, textLink } from '../lib/utils'
import KbSection from './KbSection.vue'

const props = defineProps<{
  block: KbBlock
}>()

const labels = useLabels()
const variant = useVariant(() => props.block, ['simple', 'with-back'])
const heading = useHeading(() => props.block)
const fields = computed(() => props.block.props)
const path = inject(PAGE_PATH, undefined)
/** One level up from the page: `/app/items/new` goes back to `/app/items`. */
const parent = computed(() => (path?.value ?? '/').replace(/\/[^/]*\/?$/, '') || '/')
</script>

<template>
  <KbSection
    :block="block"
    :data-kb-variant="variant"
  >
    <div class="flex flex-col gap-4">
      <KbLink
        v-if="variant === 'with-back'"
        :href="parent"
        :class="cn('inline-flex w-fit items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground pointer-coarse:min-h-11', textLink)"
      >
        <ArrowLeft
          class="size-4"
          aria-hidden="true"
        />
        {{ labels.back }}
      </KbLink>
      <div class="flex flex-col gap-4 @3xl:flex-row @3xl:items-end @3xl:justify-between @3xl:gap-8">
        <div class="flex flex-col gap-2">
          <component
            :is="heading"
            v-if="text(fields, 'title')"
            data-kb-field="title"
            class="text-xl leading-tight @3xl:text-2xl"
          >
            {{ text(fields, 'title') }}
          </component>
          <p
            v-if="text(fields, 'text')"
            data-kb-field="text"
            class="max-w-prose text-muted-foreground"
          >
            {{ text(fields, 'text') }}
          </p>
        </div>
        <div
          v-if="link(fields, 'primary') || link(fields, 'secondary')"
          class="flex shrink-0 flex-wrap gap-3"
        >
          <KbAction
            :link="link(fields, 'secondary')"
            field="secondary"
            variant="outline"
          />
          <KbAction
            :link="link(fields, 'primary')"
            field="primary"
          />
        </div>
      </div>
    </div>
  </KbSection>
</template>
