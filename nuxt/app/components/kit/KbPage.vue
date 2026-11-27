<script setup lang="ts">
import type { Component } from 'vue'
import { computed, provide } from 'vue'
import { H1_BLOCK, PAGE_PATH } from './lib/block'
import { text } from './lib/fields'
import type { KbBlock, KbPageDocument } from './lib/types'
import KbAppNav from './sections/KbAppNav.vue'
import KbContent from './sections/KbContent.vue'
import KbCta from './sections/KbCta.vue'
import KbCustom from './sections/KbCustom.vue'
import KbDetail from './sections/KbDetail.vue'
import KbEmptyState from './sections/KbEmptyState.vue'
import KbFaq from './sections/KbFaq.vue'
import KbFeatures from './sections/KbFeatures.vue'
import KbFooter from './sections/KbFooter.vue'
import KbForm from './sections/KbForm.vue'
import KbGallery from './sections/KbGallery.vue'
import KbHero from './sections/KbHero.vue'
import KbList from './sections/KbList.vue'
import KbNav from './sections/KbNav.vue'
import KbPageHeader from './sections/KbPageHeader.vue'
import KbPricing from './sections/KbPricing.vue'
import KbStats from './sections/KbStats.vue'
import KbSteps from './sections/KbSteps.vue'
import KbTable from './sections/KbTable.vue'
import KbTestimonials from './sections/KbTestimonials.vue'

// A page document, rendered block by block in the order of the document. The root is the size container
// every section adapts to: the same page lays out for a phone inside a narrow frame as on a phone.
const props = defineProps<{
  page: KbPageDocument
}>()

/** Block type → section. A project's own block replaces `KbCustom` here, under its type. */
const SECTIONS: Record<string, Component> = {
  'nav': KbNav,
  'hero': KbHero,
  'stats': KbStats,
  'features': KbFeatures,
  'steps': KbSteps,
  'content': KbContent,
  'testimonials': KbTestimonials,
  'pricing': KbPricing,
  'faq': KbFaq,
  'gallery': KbGallery,
  'cta': KbCta,
  'form': KbForm,
  'footer': KbFooter,
  'app-nav': KbAppNav,
  'page-header': KbPageHeader,
  'list': KbList,
  'table': KbTable,
  'detail': KbDetail,
  'empty-state': KbEmptyState,
  'custom': KbCustom,
}
const TOP = ['nav', 'app-nav']
const TITLES = ['hero', 'page-header']

const blocks = computed(() => props.page.blocks ?? [])
const titled = (block: KbBlock) => text(block.props, 'title') !== ''

// Exactly one `h1`: the hero's or the page header's title, else the first title of the page.
provide(H1_BLOCK, computed(() =>
  (blocks.value.find(block => TITLES.includes(block.type) && titled(block)) ?? blocks.value.find(titled))?.id,
))
provide(PAGE_PATH, computed(() => props.page.path))

// Landmarks, without changing the order: the leading navigation, the trailing footer, `main` between them.
const start = computed(() => {
  const index = blocks.value.findIndex(block => !TOP.includes(block.type))
  return index === -1 ? blocks.value.length : index
})
const end = computed(() => {
  let index = blocks.value.length
  while (index > start.value && blocks.value[index - 1]!.type === 'footer') index--
  return index
})
const top = computed(() => blocks.value.slice(0, start.value))
const main = computed(() => blocks.value.slice(start.value, end.value))
const bottom = computed(() => blocks.value.slice(end.value))
const sidebar = computed(() => top.value.some(block => block.type === 'app-nav' && block.variant !== 'topbar'))

const section = (block: KbBlock) => SECTIONS[block.type] ?? KbCustom
</script>

<template>
  <div
    class="kb-root @container"
    :data-kb-page="page.slug"
  >
    <div :class="sidebar && '@5xl:grid @5xl:grid-cols-[auto_minmax(0,1fr)] @5xl:items-start'">
      <component
        :is="section(block)"
        v-for="block in top"
        :key="block.id"
        :block="block"
      />
      <div class="min-w-0">
        <main v-if="main.length">
          <component
            :is="section(block)"
            v-for="block in main"
            :key="block.id"
            :block="block"
          />
        </main>
        <component
          :is="section(block)"
          v-for="block in bottom"
          :key="block.id"
          :block="block"
        />
      </div>
    </div>
  </div>
</template>
