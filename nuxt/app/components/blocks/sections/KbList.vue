<script setup lang="ts">
import { computed } from 'vue'
import { Inbox } from 'lucide-vue-next'
import KbSectionHeader from '../KbSectionHeader.vue'
import { columnsClass, useVariant } from '../lib/block'
import { items, text } from '../lib/fields'
import type { KbBlock } from '../lib/types'
import { cn } from '../lib/utils'
import { Badge } from '../ui/badge'
import { Card } from '../ui/card'
import KbSection from './KbSection.vue'

// The items of the document are examples: the page that uses the block passes the real ones the same way.
// Without any, the block shows its own empty state.
const props = defineProps<{
  block: KbBlock
}>()

const variant = useVariant(() => props.block, ['rows', 'cards'])
const fields = computed(() => props.block.props)
const list = computed(() => items(fields.value, 'items'))
</script>

<template>
  <KbSection
    :block="block"
    :data-kb-variant="variant"
  >
    <div class="flex flex-col gap-6">
      <KbSectionHeader
        :block="block"
        compact
      />
      <ul
        v-if="list.length"
        role="list"
        :class="variant === 'rows' ? 'flex flex-col divide-y divide-border rounded-(--radius-lg) border border-border' : cn(columnsClass(block), 'gap-4')"
      >
        <component
          :is="variant === 'cards' ? Card : 'li'"
          v-for="(item, index) in list"
          :key="index"
          as="li"
          data-kb-field="items"
          :data-kb-item="index"
          :class="variant === 'rows' ? 'flex flex-col gap-3 px-4 py-4 @2xl:flex-row @2xl:items-center @2xl:justify-between @2xl:gap-6' : 'justify-between'"
        >
          <div class="flex min-w-0 flex-col gap-1">
            <h3
              v-if="text(item, 'title')"
              data-kb-field="title"
              class="text-base"
            >
              {{ text(item, 'title') }}
            </h3>
            <p
              v-if="text(item, 'text')"
              data-kb-field="text"
              class="text-sm text-muted-foreground"
            >
              {{ text(item, 'text') }}
            </p>
          </div>
          <div
            v-if="text(item, 'meta') || text(item, 'status')"
            class="flex shrink-0 items-center gap-3"
          >
            <span
              v-if="text(item, 'meta')"
              data-kb-field="meta"
              class="text-sm text-muted-foreground"
            >{{ text(item, 'meta') }}</span>
            <Badge
              v-if="text(item, 'status')"
              variant="secondary"
              data-kb-field="status"
            >
              {{ text(item, 'status') }}
            </Badge>
          </div>
        </component>
      </ul>
      <div
        v-else-if="text(fields, 'empty_title') || text(fields, 'empty_text')"
        class="flex flex-col items-center gap-2 rounded-(--radius-lg) border border-dashed border-border px-6 py-12 text-center"
      >
        <Inbox
          class="size-6 text-muted-foreground"
          aria-hidden="true"
        />
        <p
          v-if="text(fields, 'empty_title')"
          data-kb-field="empty_title"
          class="font-medium"
        >
          {{ text(fields, 'empty_title') }}
        </p>
        <p
          v-if="text(fields, 'empty_text')"
          data-kb-field="empty_text"
          class="max-w-prose text-sm text-muted-foreground"
        >
          {{ text(fields, 'empty_text') }}
        </p>
      </div>
    </div>
  </KbSection>
</template>
