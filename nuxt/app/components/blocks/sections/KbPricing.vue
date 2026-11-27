<script setup lang="ts">
import { computed } from 'vue'
import { Check } from 'lucide-vue-next'
import KbAction from '../KbAction.vue'
import KbSectionHeader from '../KbSectionHeader.vue'
import { useItemHeading, useVariant } from '../lib/block'
import { flag, items, lines, link, text } from '../lib/fields'
import type { KbBlock } from '../lib/types'
import { useLabels } from '../lib/labels'
import { cn } from '../lib/utils'
import { Badge } from '../ui/badge'
import { Card } from '../ui/card'
import KbSection from './KbSection.vue'

const props = defineProps<{
  block: KbBlock
}>()

const variant = useVariant(() => props.block, ['cards', 'single'])
const list = computed(() => items(props.block.props, 'items'))
const itemHeading = useItemHeading(() => props.block)
const labels = useLabels()
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
      <ul
        v-if="list.length"
        role="list"
        :class="variant === 'cards' ? 'grid items-stretch gap-6 @3xl:grid-cols-[repeat(auto-fit,minmax(min(100%,calc(var(--spacing)*60)),1fr))]' : 'mx-auto flex w-full max-w-4xl flex-col gap-6'"
      >
        <Card
          v-for="(item, index) in list"
          :key="index"
          as="li"
          data-kb-field="items"
          :data-kb-item="index"
          :class="cn(
            'gap-6 p-6 @3xl:p-8',
            // Side by side, the offers share their rows: names, prices and actions line up across cards.
            variant === 'cards' && '@3xl:row-span-4 @3xl:grid @3xl:grid-rows-subgrid',
            variant === 'single' && '@3xl:grid @3xl:grid-cols-2 @3xl:gap-10',
            flag(item, 'featured') && 'border-primary shadow-(--shadow-md) outline-1 outline-primary',
          )"
        >
          <div :class="variant === 'cards' ? 'flex flex-col gap-6 @3xl:contents' : 'flex flex-col gap-6'">
            <div class="flex flex-col gap-2">
              <!-- The recommended offer says so in words: a border alone is lost on a screen reader. -->
              <Badge
                v-if="flag(item, 'featured')"
                class="w-fit"
              >
                {{ labels.featured }}
              </Badge>
              <component
                :is="itemHeading"
                v-if="text(item, 'name')"
                data-kb-field="name"
                class="text-lg"
              >
                {{ text(item, 'name') }}
              </component>
              <p
                v-if="text(item, 'description')"
                data-kb-field="description"
                class="text-sm text-muted-foreground"
              >
                {{ text(item, 'description') }}
              </p>
            </div>
            <p
              v-if="text(item, 'price')"
              class="flex flex-wrap items-baseline gap-x-2"
            >
              <span
                data-kb-field="price"
                class="font-(family-name:--font-display) text-2xl leading-tight font-semibold"
              >{{ text(item, 'price') }}</span>
              <span
                v-if="text(item, 'period')"
                data-kb-field="period"
                class="text-sm text-muted-foreground"
              >{{ text(item, 'period') }}</span>
            </p>
            <KbAction
              :link="link(item, 'cta')"
              field="cta"
              :variant="flag(item, 'featured') || variant === 'single' ? 'default' : 'outline'"
              :class="variant === 'single' && 'w-fit'"
            />
          </div>
          <ul
            v-if="lines(text(item, 'features')).length"
            role="list"
            data-kb-field="features"
            :class="cn('flex flex-col gap-3 text-sm', variant === 'cards' && 'border-t border-border pt-6')"
          >
            <li
              v-for="(feature, at) in lines(text(item, 'features'))"
              :key="at"
              class="flex gap-3"
            >
              <Check
                class="mt-0.5 size-4 shrink-0 text-muted-foreground"
                aria-hidden="true"
              />
              <span class="min-w-0">{{ feature }}</span>
            </li>
          </ul>
        </Card>
      </ul>
    </div>
  </KbSection>
</template>
