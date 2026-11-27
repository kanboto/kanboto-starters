<script setup lang="ts">
import { computed } from 'vue'
import { Menu, X } from 'lucide-vue-next'
import KbAction from './KbAction.vue'
import KbLink from './KbLink.vue'
import KbSection from './sections/KbSection.vue'
import { containerClass } from './lib/block'
import { items, link, text } from './lib/fields'
import { icon } from './lib/icons'
import { useLabels } from './lib/labels'
import type { KbBlock } from './lib/types'
import { cn, focusRing, touchTarget } from './lib/utils'
import { Button } from './ui/button'

// The bar behind `KbNav` and `KbAppNav`: one compact row and one list of links at every size. When the
// container is too narrow for the links, the same list is a native popover, shown as a drawer; no script.
const props = defineProps<{
  block: KbBlock
  /** `start`: links after the brand; `center`: links centred; `side`: a sidebar in a wide container. */
  layout: 'start' | 'center' | 'side'
}>()

const labels = useLabels()
const panelId = computed(() => `kb-nav-${props.block.id}`)
const brand = computed(() => text(props.block.props, 'brand'))
const links = computed(() => items(props.block.props, 'links').filter(item => text(item, 'label')))
const cta = computed(() => link(props.block.props, 'cta'))

// The popover's own look is undone where the links fit: the list sits in the bar (or the sidebar) again.
const INLINE = {
  bar: '@3xl:static @3xl:flex @3xl:h-auto @3xl:w-auto @3xl:max-w-none @3xl:translate-x-0 @3xl:overflow-visible @3xl:border-0 @3xl:bg-transparent @3xl:p-0 @3xl:shadow-none @3xl:transition-none',
  side: '@5xl:static @5xl:flex @5xl:h-auto @5xl:w-auto @5xl:max-w-none @5xl:translate-x-0 @5xl:overflow-visible @5xl:border-0 @5xl:bg-transparent @5xl:p-0 @5xl:shadow-none @5xl:transition-none',
}
const side = computed(() => props.layout === 'side')
const narrowOnly = computed(() => (side.value ? '@5xl:hidden' : '@3xl:hidden'))
</script>

<template>
  <KbSection
    :block="block"
    as="header"
    bare
    :class="cn('sticky top-0 z-40 border-b border-border', side && '@5xl:h-dvh @5xl:w-60 @5xl:border-r @5xl:border-b-0')"
  >
    <div :class="cn('flex min-h-14 items-center gap-3', containerClass(block), side && '@5xl:h-full @5xl:max-w-none @5xl:flex-col @5xl:items-stretch @5xl:gap-6 @5xl:px-4 @5xl:py-4')">
      <div :class="cn('flex shrink-0 items-center', layout === 'center' && '@3xl:flex-1')">
        <KbLink
          v-if="brand"
          href="/"
          data-kb-field="brand"
          :class="cn('rounded-(--radius-sm) font-(family-name:--font-display) text-lg font-semibold', focusRing, side && '@5xl:px-3')"
        >
          {{ brand }}
        </KbLink>
      </div>
      <nav
        v-if="links.length"
        :aria-label="labels.mainNav"
        :class="cn(layout === 'start' && '@3xl:ml-6 @3xl:flex-1', side && '@5xl:flex-1')"
      >
        <div
          :id="panelId"
          popover
          :class="cn(
            'fixed inset-y-0 right-0 left-auto m-0 h-dvh w-80 max-w-full translate-x-full flex-col gap-4 overflow-y-auto border-0 border-l border-border bg-background p-4 text-foreground shadow-(--shadow-lg) transition-[translate,display,overlay] transition-discrete duration-(--duration-base) ease-(--easing) backdrop:bg-foreground/30 open:flex open:translate-x-0 motion-reduce:transition-none starting:open:translate-x-full',
            side ? INLINE.side : INLINE.bar,
          )"
        >
          <div :class="cn('flex items-center justify-between', narrowOnly)">
            <span class="px-3 text-sm font-medium text-muted-foreground">{{ labels.menu }}</span>
            <Button
              variant="ghost"
              size="icon"
              :popovertarget="panelId"
              popovertargetaction="hide"
              :aria-label="labels.close"
            >
              <X aria-hidden="true" />
            </Button>
          </div>
          <ul :class="cn('flex flex-col gap-1', !side && '@3xl:flex-row @3xl:items-center')">
            <li
              v-for="(item, index) in links"
              :key="index"
              data-kb-field="links"
              :data-kb-item="index"
            >
              <KbLink
                :href="text(item, 'href')"
                :class="cn('flex items-center gap-3 rounded-(--radius-md) px-3 py-2 text-base font-medium text-muted-foreground transition-colors duration-(--duration-fast) ease-(--easing) hover:bg-muted hover:text-foreground aria-[current=page]:bg-muted aria-[current=page]:text-foreground', side ? '@5xl:text-sm' : '@3xl:text-sm', focusRing, touchTarget)"
              >
                <component
                  :is="icon(text(item, 'icon'))"
                  v-if="text(item, 'icon')"
                  class="size-4 shrink-0"
                  aria-hidden="true"
                />
                <span data-kb-field="label">{{ text(item, 'label') }}</span>
              </KbLink>
            </li>
          </ul>
        </div>
      </nav>
      <div :class="cn('ml-auto flex items-center justify-end gap-2', layout === 'center' && '@3xl:ml-0 @3xl:flex-1', side && '@5xl:hidden')">
        <KbAction
          :link="cta"
          field="cta"
          size="sm"
        />
        <Button
          v-if="links.length"
          variant="ghost"
          size="icon"
          :class="narrowOnly"
          :popovertarget="panelId"
          :aria-controls="panelId"
          :aria-label="labels.menu"
        >
          <Menu aria-hidden="true" />
        </Button>
      </div>
    </div>
  </KbSection>
</template>
