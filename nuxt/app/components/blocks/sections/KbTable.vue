<script setup lang="ts">
import { computed } from 'vue'
import KbSectionHeader from '../KbSectionHeader.vue'
import { useVariant } from '../lib/block'
import { lines, text } from '../lib/fields'
import { useLabels } from '../lib/labels'
import type { KbBlock } from '../lib/types'
import { cn, focusRing } from '../lib/utils'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/table'
import KbSection from './KbSection.vue'

// A real table, which scrolls sideways inside its own region when the container is too narrow: the region
// is focusable and named, so the keyboard reaches it; the first cell of a row is its header.
const props = defineProps<{
  block: KbBlock
}>()

const labels = useLabels()
const variant = useVariant(() => props.block, ['simple', 'striped'])
const columns = computed(() => lines(text(props.block.props, 'columns')))
const rows = computed(() => lines(text(props.block.props, 'rows')).map(row => row.split('|').map(cell => cell.trim())))
const title = computed(() => text(props.block.props, 'title'))
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
      <div
        v-if="columns.length || rows.length"
        role="region"
        tabindex="0"
        :aria-label="title || labels.table"
        :class="cn('overflow-x-auto rounded-(--radius-lg) border border-border', focusRing)"
      >
        <Table>
          <TableHeader
            v-if="columns.length"
            data-kb-field="columns"
          >
            <TableRow>
              <TableHead
                v-for="(column, index) in columns"
                :key="index"
                scope="col"
              >
                {{ column }}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody
            v-if="rows.length"
            data-kb-field="rows"
          >
            <TableRow
              v-for="(row, index) in rows"
              :key="index"
              :class="cn('bg-background', variant === 'striped' && 'even:bg-muted')"
            >
              <component
                :is="at === 0 ? TableHead : TableCell"
                v-for="(cell, at) in row"
                :key="at"
                :scope="at === 0 ? 'row' : undefined"
                :class="at === 0 && 'sticky start-0 bg-inherit text-foreground'"
              >
                {{ cell }}
              </component>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </div>
  </KbSection>
</template>
