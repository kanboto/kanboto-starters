<script setup lang="ts">
import type { Ref } from 'vue'
import { computed, inject, unref } from 'vue'
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
// The site's logo, provided by the application (`kb:logo`: the SVG as text, drawn inline so that it takes the
// colour of the text and the site's typeface). A logo that does not write the name gets it beside.
const provided = inject<string | Ref<string>>('kb:logo', '')
const logo = computed(() => (props.block.options?.brand === 'text' ? '' : unref(provided) || ''))
const named = computed(() => logo.value.includes('<text'))
const links = computed(() => items(props.block.props, 'links').filter(item => text(item, 'label')))
const cta = computed(() => link(props.block.props, 'cta'))

// The popover's own look is undone where the links fit: the list sits in the bar (or the sidebar) again. Only
// while it is closed: a drawer left open when the container widens stays a drawer, with its close button.
const INLINE = {
  bar: '@3xl:not-open:static @3xl:not-open:flex @3xl:not-open:h-auto @3xl:not-open:w-auto @3xl:not-open:max-w-none @3xl:not-open:translate-x-0 @3xl:not-open:overflow-visible @3xl:not-open:border-0 @3xl:not-open:bg-transparent @3xl:not-open:p-0 @3xl:not-open:shadow-none @3xl:not-open:transition-none',
  side: '@5xl:not-open:static @5xl:not-open:flex @5xl:not-open:h-auto @5xl:not-open:w-auto @5xl:not-open:max-w-none @5xl:not-open:translate-x-0 @5xl:not-open:overflow-visible @5xl:not-open:border-0 @5xl:not-open:bg-transparent @5xl:not-open:p-0 @5xl:not-open:shadow-none @5xl:not-open:transition-none',
}
const CLOSE_ROW = {
  bar: '@3xl:[:not(:popover-open)>&]:hidden',
  side: '@5xl:[:not(:popover-open)>&]:hidden',
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
      <div :class="cn('flex min-w-0 items-center', layout === 'center' && '@3xl:flex-1')">
        <KbLink
          v-if="brand"
          href="/"
          data-kb-field="brand"
          :aria-label="logo && named ? brand : undefined"
          :class="cn('rounded-(--radius-sm) font-(family-name:--font-display) text-lg font-semibold pointer-coarse:py-2', logo ? 'flex items-center gap-2.5' : 'block truncate', focusRing, side && '@5xl:px-3')"
        >
          <!-- eslint-disable vue/no-v-html -- the project's own logo file, a cleaned SVG -->
          <span
            v-if="logo"
            class="kb-logo block h-7 shrink-0"
            aria-hidden="true"
            v-html="logo"
          />
          <!-- eslint-enable vue/no-v-html -->
          <span
            v-if="!logo || !named"
            class="truncate"
          >{{ brand }}</span>
        </KbLink>
      </div>
      <nav
        v-if="links.length"
        :aria-label="labels.mainNav"
        :class="cn('min-w-0', layout === 'start' && '@3xl:ms-6 @3xl:flex-1', side && '@5xl:flex-1')"
      >
        <div
          :id="panelId"
          popover
          :class="cn(
            'kb-nav-panel fixed inset-y-0 right-0 left-auto m-0 h-svh w-80 max-w-[80%] translate-x-full flex-col gap-4 overflow-y-auto border-0 border-l border-border bg-background p-4 text-foreground shadow-(--shadow-lg) transition-[translate,display,overlay] transition-discrete duration-(--duration-base) ease-(--easing) backdrop:bg-foreground/30 open:flex open:translate-x-0 motion-reduce:transition-none starting:open:translate-x-full',
            side ? INLINE.side : INLINE.bar,
          )"
        >
          <div :class="cn('kb-nav-toggle flex items-center justify-between', side ? CLOSE_ROW.side : CLOSE_ROW.bar)">
            <span class="px-3 text-sm font-medium text-muted-foreground">{{ labels.menu }}</span>
            <Button
              variant="ghost"
              size="icon"
              :popovertarget="panelId"
              popovertargetaction="hide"
              autofocus
              :aria-label="labels.close"
            >
              <X aria-hidden="true" />
            </Button>
          </div>
          <ul :class="cn('flex flex-col gap-1', !side && '@3xl:flex-row @3xl:flex-wrap @3xl:items-center')">
            <li
              v-for="(item, index) in links"
              :key="index"
              data-kb-field="links"
              :data-kb-item="index"
            >
              <KbLink
                :href="text(item, 'href')"
                :class="cn('flex items-center gap-3 rounded-(--radius-md) px-3 py-2 text-base font-medium text-muted-foreground transition-colors duration-(--duration-fast) ease-(--easing) hover:bg-muted hover:text-foreground active:bg-muted/70 aria-[current=page]:bg-muted aria-[current=page]:font-semibold aria-[current=page]:text-foreground aria-[current=page]:underline aria-[current=page]:underline-offset-4', side ? '@5xl:text-sm' : '@3xl:text-sm', focusRing, touchTarget)"
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
      <div :class="cn('ms-auto flex shrink-0 items-center justify-end gap-2', layout === 'center' && '@3xl:ms-0 @3xl:flex-1', side && '@5xl:hidden')">
        <KbAction
          :link="cta"
          field="cta"
          size="sm"
          compact
        />
        <Button
          v-if="links.length"
          variant="ghost"
          size="icon"
          :class="cn('kb-nav-toggle', narrowOnly)"
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
