/**
 * The section kit, rendered on its own (no Nuxt: the kit only imports its own files) from
 * `app/content/pages/kit-all.json`, which holds every block type and every variant. Checks what Kanboto's page
 * workshop and search engines rely on: one section per block, one `h1`, complete images.
 */
import { createSSRApp, defineComponent, h } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { describe, expect, it } from 'vitest'
import KbPage from '../app/components/kit/KbPage.vue'
import type { KbPageDocument } from '../app/components/kit/lib/types'
import all from '../app/content/pages/kit-all.json'
import home from '../app/content/pages/home.json'

const CATALOG_TYPES = 20

/** What Nuxt provides in the application: a link inside the site. */
const NuxtLink = defineComponent({
  props: { to: { type: String, required: true } },
  setup: (props, { slots }) => () => h('a', { 'href': props.to, 'data-nuxt-link': '' }, slots.default?.()),
})

function render(page: KbPageDocument, provides: Record<string, unknown> = {}): Promise<string> {
  const app = createSSRApp({ render: () => h(KbPage, { page }) })
  app.component('NuxtLink', NuxtLink)
  for (const [key, value] of Object.entries(provides)) app.provide(key, value)
  return renderToString(app)
}

function count(html: string, pattern: RegExp): number {
  return html.match(pattern)?.length ?? 0
}

describe('every block of the kit', async () => {
  const html = await render(all)

  it('covers every block type of the catalog, and a type the kit does not know', () => {
    const types = new Set(all.blocks.map(block => block.type))
    expect(types.size).toBe(CATALOG_TYPES + 1)
  })

  it('renders each block once, in the order of the document, marked for the workshop', () => {
    const rendered = [...html.matchAll(/data-kb-block="([^"]+)" data-kb-type="([^"]+)"/g)]
    expect(rendered.map(([, id]) => id)).toEqual(all.blocks.map(block => block.id))
    expect(rendered.map(([, , type]) => type)).toEqual(all.blocks.map(block => block.type))
  })

  it('falls back to the first variant, and to the custom block for an unknown type', () => {
    expect(html).toMatch(/data-kb-block="stats-unknown-variant"[^>]* data-kb-variant="row"/)
    expect(html).toMatch(/data-kb-block="unknown-type"[^>]* data-kb-variant="placeholder"/)
    expect(html).toMatch(/data-kb-block="content-empty"[^>]* data-kb-variant="text"/)
  })

  it('has exactly one h1, on the first hero', () => {
    expect(count(html, /<h1[\s>]/g)).toBe(1)
    expect(html).toMatch(/data-kb-block="hero-centered"(?:(?!data-kb-block).)*<h1/s)
  })

  it('marks fields and items', () => {
    expect(html).toMatch(/<h1 data-kb-field="title"/)
    expect(html).toMatch(/<li data-kb-field="items" data-kb-item="2"/)
    expect(html).toMatch(/data-kb-field="links" data-kb-item="0"/)
  })

  it('gives every image an alt, a width and a height, and loads only the hero image first', () => {
    const images = html.match(/<img [^>]*>/g) ?? []
    expect(images.length).toBeGreaterThan(5)
    for (const image of images) {
      expect(image).toMatch(/ alt="[^"]+"/)
      expect(image).toMatch(/ width="\d+"/)
      expect(image).toMatch(/ height="\d+"/)
    }
    const eager = images.filter(image => image.includes('fetchpriority="high"'))
    expect(eager).toHaveLength(4) // one per hero variant; a page has one hero
    expect(images.filter(image => image.includes('loading="lazy"'))).toHaveLength(images.length - eager.length)
  })

  it('shows a captioned placeholder for an image without a file', () => {
    expect(html).toMatch(/<div role="img" aria-label="What the image shows" data-kb-field="image"/)
  })

  it('renders no empty element for a missing field', () => {
    expect(html).not.toMatch(/<(h[1-3]|p|a|li|blockquote|figcaption|dt|dd|label|th|td)(\s[^>]*)?><\/\1>/)
  })

  it('uses native elements: details for questions, a popover for the collapsed navigation, labelled fields', () => {
    expect(html).toMatch(/<details name="kb-faq-faq-accordion"/)
    expect(html).toMatch(/<div id="kb-nav-nav-simple" popover/)
    expect(html).toMatch(/<button[^>]* popovertarget="kb-nav-nav-simple"[^>]* aria-label="Menu"/)
    const controls = html.match(/<(input|textarea|select) [^>]*>/g) ?? []
    for (const control of controls) {
      const id = control.match(/ id="([^"]+)"/)?.[1]
      expect(html, control).toContain(`for="${id}"`)
      expect(control).toMatch(/ name="[^"]+"/)
    }
    expect(html).toMatch(/<input [^>]*type="email"[^>]*autocomplete="email"/)
    expect(html).toMatch(/<div role="region" tabindex="0" aria-label="[^"]+"[^>]*><table/)
  })

  it('links inside the site through the host\'s link component, others plainly', () => {
    expect(html).toMatch(/<a href="\/somewhere" data-nuxt-link[^>]* data-kb-field="primary"/)
  })
})

describe('in the page workshop', () => {
  it('makes links inert', async () => {
    const html = await render(home, { 'kb:editing': true })
    expect(html).not.toContain('data-nuxt-link')
    expect(html).toMatch(/<a href="\/app\/items"[^>]* data-kb-field="primary"/)
  })
})

describe('a page without a hero', () => {
  it('gives the h1 to its first title', async () => {
    const html = await render({
      slug: 'about',
      path: '/about',
      blocks: [
        { id: 'nav-1', type: 'nav', props: { brand: 'My app' } },
        { id: 'content-1', type: 'content', props: { title: 'About' } },
        { id: 'cta-1', type: 'cta', props: { title: 'Get in touch' } },
      ],
    })
    expect(html).toMatch(/<h1[^>]*>About<\/h1>/)
    expect(html).toMatch(/<h2[^>]*>Get in touch<\/h2>/)
  })
})
