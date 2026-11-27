<script setup lang="ts">
import { computed } from 'vue'
import KbAction from '../KbAction.vue'
import KbSectionHeader from '../KbSectionHeader.vue'
import { useVariant } from '../lib/block'
import { items, link, text } from '../lib/fields'
import type { KbBlock } from '../lib/types'
import { cn } from '../lib/utils'
import { Card } from '../ui/card'
import KbSection from './KbSection.vue'

const props = defineProps<{
  block: KbBlock
}>()

const variant = useVariant(() => props.block, ['card', 'columns'])
const fields = computed(() => props.block.props)
const list = computed(() => items(fields.value, 'items').filter(item => text(item, 'label')))
const actions = computed(() => link(fields.value, 'primary') || link(fields.value, 'secondary'))
</script>

<template>
  <KbSection
    :block="block"
    :data-kb-variant="variant"
  >
    <component
      :is="variant === 'card' ? Card : 'div'"
      class="flex flex-col gap-6"
    >
      <KbSectionHeader
        :block="block"
        compact
      />
      <dl
        v-if="list.length"
        :class="variant === 'card' ? 'flex flex-col divide-y divide-border border-y border-border' : 'grid gap-x-10 gap-y-6 @2xl:grid-cols-2'"
      >
        <div
          v-for="(item, index) in list"
          :key="index"
          data-kb-field="items"
          :data-kb-item="index"
          :class="variant === 'card' ? 'flex flex-col gap-1 py-3 @2xl:grid @2xl:grid-cols-3 @2xl:gap-6' : 'flex flex-col gap-1 border-t border-border pt-4'"
        >
          <dt
            data-kb-field="label"
            class="text-sm text-muted-foreground"
          >
            {{ text(item, 'label') }}
          </dt>
          <dd
            data-kb-field="value"
            :class="cn('font-medium', variant === 'card' && '@2xl:col-span-2')"
          >
            {{ text(item, 'value') }}
          </dd>
        </div>
      </dl>
      <div
        v-if="actions"
        class="flex flex-wrap gap-3"
      >
        <KbAction
          :link="link(fields, 'primary')"
          field="primary"
        />
        <KbAction
          :link="link(fields, 'secondary')"
          field="secondary"
          variant="outline"
        />
      </div>
    </component>
  </KbSection>
</template>
