<script setup lang="ts">
import { computed } from 'vue'
import KbLink from '../KbLink.vue'
import { containerClass, useVariant } from '../lib/block'
import { items, text } from '../lib/fields'
import { useLabels } from '../lib/labels'
import type { KbBlock } from '../lib/types'
import { cn, textLink } from '../lib/utils'
import KbSection from './KbSection.vue'

const props = defineProps<{
  block: KbBlock
}>()

const labels = useLabels()
const variant = useVariant(() => props.block, ['simple', 'columns'])
const fields = computed(() => props.block.props)
const links = computed(() => items(fields.value, 'links').filter(item => text(item, 'label')))
</script>

<template>
  <KbSection
    :block="block"
    as="footer"
    bare
    class="border-t border-border"
    :data-kb-variant="variant"
  >
    <div :class="cn('flex flex-col gap-8 py-10', containerClass(block))">
      <div :class="variant === 'columns' ? 'grid gap-8 @3xl:grid-cols-2' : 'flex flex-col gap-6 @3xl:flex-row @3xl:items-center @3xl:justify-between'">
        <div
          v-if="text(fields, 'brand') || text(fields, 'text')"
          class="flex max-w-sm flex-col gap-2"
        >
          <p
            v-if="text(fields, 'brand')"
            data-kb-field="brand"
            class="font-(family-name:--font-display) text-lg font-semibold"
          >
            {{ text(fields, 'brand') }}
          </p>
          <p
            v-if="text(fields, 'text')"
            data-kb-field="text"
            class="text-sm text-muted-foreground"
          >
            {{ text(fields, 'text') }}
          </p>
        </div>
        <nav
          v-if="links.length"
          :aria-label="labels.footerNav"
        >
          <ul :class="variant === 'columns' ? 'grid grid-cols-2 gap-x-8 gap-y-1 @xl:grid-cols-3' : 'flex flex-wrap gap-x-6 gap-y-1'">
            <li
              v-for="(item, index) in links"
              :key="index"
              data-kb-field="links"
              :data-kb-item="index"
            >
              <KbLink
                :href="text(item, 'href')"
                :class="cn('inline-flex items-center py-1 text-sm text-muted-foreground hover:text-foreground pointer-coarse:min-h-11', textLink)"
              >
                <span data-kb-field="label">{{ text(item, 'label') }}</span>
              </KbLink>
            </li>
          </ul>
        </nav>
      </div>
      <p
        v-if="text(fields, 'legal')"
        data-kb-field="legal"
        :class="cn('text-xs text-muted-foreground', variant === 'columns' && 'border-t border-border pt-6')"
      >
        {{ text(fields, 'legal') }}
      </p>
    </div>
  </KbSection>
</template>
