/**
 * The block library, rendered on its own (no Nuxt: the block library only imports its own files) from
 * `app/content/pages/all-blocks.json`, which holds every block type and every variant. Checks what Kanboto's page
 * workshop and search engines rely on: one section per block, one `h1`, complete images.
 */
import { createSSRApp, defineComponent, h } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { describe, expect, it } from 'vitest'
import KbPage from '../app/components/blocks/KbPage.vue'
import type { KbPageDocument } from '../app/components/blocks/lib/types'
import all from '../app/content/pages/all-blocks.json'
import stored from '../app/content/pages/home.json'
import shared from '../app/content/shared.json'
import { resolvePage } from '../app/components/blocks/lib/shared'

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

describe('every block of the block library', async () => {
  const html = await render(all)

  it('covers every block type of the catalog, and a type the block library does not know', () => {
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
    // Answers open independently: no exclusive accordion.
    expect(html).toMatch(/<details data-kb-field="items"/)
    expect(html).not.toMatch(/<details name=/)
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

const home = resolvePage(stored, shared)

describe('keyboard and assistive technology', async () => {
  const html = await render(all)

  it('draws a focus ring: no class cancels the outline of the focused state', () => {
    expect(html).toContain('focus-visible:outline-2')
    expect(html).not.toMatch(/class="[^"]*\boutline-none\b[^"]*focus-visible:outline-2/)
  })

  it('offers a skip link to the content, before the navigation', () => {
    expect(html.indexOf('href="#kb-main"')).toBeGreaterThan(-1)
    expect(html.indexOf('href="#kb-main"')).toBeLessThan(html.indexOf('<header'))
    expect(html).toMatch(/<main id="kb-main" tabindex="-1"/)
  })

  it('keeps list semantics on lists laid out as grids', () => {
    expect(html).not.toMatch(/<(ul|ol)(?![^>]*role="list")[^>]*class="[^"]*\bgrid\b/)
  })

  it('says an invalid field in words and explains the asterisk once', () => {
    expect(html).toMatch(/peer-user-invalid:block/)
    expect(html.match(/Fields marked \* are required\./g)?.length).toBeGreaterThan(0)
  })
})

describe('shared blocks', () => {
  it('are written once and put in place of each reference', () => {
    expect(stored.blocks[0]).toEqual({ ref: 'nav' })
    expect(home.blocks[0]).toBe(shared.blocks.nav)
    expect(home.blocks.at(-1)).toBe(shared.blocks.footer)
    expect(JSON.stringify(stored)).not.toContain('"brand"')
  })

  it('render nothing for a reference to a block that is gone', () => {
    const page = resolvePage({ ...stored, blocks: [{ ref: 'missing' }, ...stored.blocks] }, shared)
    expect(page.blocks).toHaveLength(stored.blocks.length)
  })
})

describe('dressing a block', () => {
  const hero = home.blocks.find(block => block.type === 'hero')!
  const dressed = (settings: Record<string, string>, props: Record<string, unknown> = {}) =>
    render({ ...home, blocks: [{ ...hero, settings: { ...hero.settings, ...settings }, props: { ...hero.props, ...props } }] })

  it('offers the accent colour of the charter as a ground, and decorations drawn from its colours', async () => {
    const html = await dressed({ tone: 'accent', backdrop: 'glow' })
    expect(html).toMatch(/<section[^>]*class="[^"]*kb-tone-accent[^"]*kb-backdrop kb-backdrop-glow/)
    expect(await dressed({ backdrop: 'unknown' })).not.toContain('kb-backdrop')
  })

  it('lays a background image under a veil of the ground colour, hidden from assistive technology', async () => {
    const html = await dressed({}, { background: { src: '/images/steel.jpg', alt: 'A steel counter', ratio: '21:9' } })
    expect(html).toMatch(/<img[^>]*src="\/images\/steel\.jpg"[^>]*alt(="")?[ >][^>]*data-kb-field="background"/)
    expect(html).toMatch(/<span class="[^"]*bg-background\/80[^"]*" aria-hidden="true">/)
  })

  it('sets apart the words of a title written between asterisks, and adds nothing to a plain title', async () => {
    const html = await dressed({}, { title: 'Keep *every item* on track' })
    expect(html).toMatch(/Keep <em class="kb-mark">every item<\/em> on track/)
    expect(await dressed({})).not.toContain('kb-mark')
  })

  it('lets the author centre or left-align the head of a section', async () => {
    const features = home.blocks.find(block => block.type === 'features')!
    const page = (align: string) => render({ ...home, blocks: [{ ...features, settings: { align } }] })
    expect(await page('start')).not.toMatch(/<header class="[^"]*text-center/)
    expect(await page('center')).toMatch(/<header class="[^"]*text-center/)
  })
})

describe('the buttons of a bar', () => {
  it('fold into a square with their icon in a narrow container, and keep their label as their name', async () => {
    const html = await render(home)
    const cta = html.match(/<a[^>]*data-kb-field="cta"[^>]*>[\s\S]*?<\/a>/)?.[0] ?? ''
    expect(cta).toMatch(/class="[^"]*@max-xl:aspect-square[^"]*@max-xl:px-0/)
    expect(cta).toMatch(/<svg[^>]*aria-hidden="true"/)
    expect(cta).toMatch(/<span class="@max-xl:sr-only">Open the app<\/span>/)
  })

  it('stay in full words without an icon, and never fold in the content of a page', async () => {
    const nav = { ...shared.blocks.nav, props: { ...shared.blocks.nav.props, cta: { label: 'Open the app', href: '/app/items' } } }
    const html = await render({ ...home, blocks: [nav, ...home.blocks.slice(1)] })
    expect(html.match(/<a[^>]*data-kb-field="cta"[^>]*>[\s\S]*?<\/a>/)?.[0]).not.toContain('@max-xl')
    expect(html.match(/<a[^>]*data-kb-field="primary"[^>]*>[\s\S]*?<\/a>/)?.[0]).not.toContain('@max-xl')
  })
})

describe('the logo of the site', () => {
  const mark = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256"><circle cx="128" cy="128" r="96" fill="currentColor"/></svg>'
  const lockup = mark.replace('</svg>', '<text x="280" y="160">My app</text></svg>')

  it('is drawn inline in the navigation, with the name beside a mark that does not write it', async () => {
    const html = await render(home, { 'kb:logo': mark })
    expect(html).toMatch(/<span class="kb-logo[^"]*" aria-hidden="true"><svg/)
    expect(html).toMatch(/<\/svg><\/span>[\s\S]{0,240}<span class="truncate">My app<\/span>/)
  })

  it('stands alone when it writes the name, which stays the accessible name of the link', async () => {
    const html = await render(home, { 'kb:logo': lockup })
    expect(html).toMatch(/aria-label="My app"[^>]*>[\s\S]{0,240}<span class="kb-logo/)
    expect(html).not.toMatch(/<span class="truncate">My app<\/span>/)
  })

  it('gives way to the name in text when the block asks for it, or when the site has no logo', async () => {
    const nav = { ...shared.blocks.nav, options: { brand: 'text' } }
    const page = { ...home, blocks: [nav, ...home.blocks.slice(1)] }
    expect(await render(page, { 'kb:logo': mark })).not.toContain('kb-logo')
    expect(await render(home)).not.toContain('kb-logo')
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
