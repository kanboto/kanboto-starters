/**
 * Search engines, as in production: every page of the sitemap is indexable and describes itself (title,
 * description, canonical address, one heading, structured data, share image); the signed-in area stays out.
 * A new public page is checked as soon as the sitemap lists it.
 */
import { fileURLToPath } from 'node:url'
import { $fetch, fetch, setup } from '@nuxt/test-utils/e2e'
import { describe, expect, it } from 'vitest'

const SITE = 'https://acme.example.com'

await setup({
  rootDir: fileURLToPath(new URL('..', import.meta.url)),
  env: {
    NUXT_PUBLIC_APP_NAME: 'Acme Console',
    NUXT_PUBLIC_SITE_URL: SITE,
    NUXT_PUBLIC_SITE_INDEXABLE: 'true',
    NUXT_APP_SECRET: 'a-test-secret-of-at-least-32-characters',
    DRAIN_DELAY_S: '0',
  },
})

async function pages(): Promise<string[]> {
  const sitemap = await $fetch<string>('/sitemap.xml', { responseType: 'text' })
  return [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map(([, loc]) => loc!)
}

/** Width and height of a PNG, read from its header. */
function size(png: Uint8Array): [number, number] {
  const view = new DataView(png.buffer, png.byteOffset)
  return [view.getUint32(16), view.getUint32(20)]
}

function meta(html: string, attribute: string, name: string): string | undefined {
  return html.match(new RegExp(`<meta ${attribute}="${name}" content="([^"]*)"`))?.[1]
}

describe('robots.txt', () => {
  it('lets search engines in and points them to the sitemap', async () => {
    const robots = await $fetch<string>('/robots.txt')
    expect(robots).not.toMatch(/^Disallow: \/$/m)
    expect(robots).toContain(`Sitemap: ${SITE}/sitemap.xml`)
  })
})

describe('sitemap', () => {
  it('lists the public pages on the public address', async () => {
    const urls = await pages()
    expect(urls).toContain(`${SITE}/`)
    expect(urls.every(url => url.startsWith(`${SITE}/`) && !url.startsWith(`${SITE}/app/`))).toBe(true)
  })

  it('describes each of its pages', async () => {
    for (const url of await pages()) {
      const path = url.slice(SITE.length)
      const response = await fetch(path)
      expect(response.status, path).toBe(200)
      expect(response.headers.get('x-robots-tag'), path).not.toContain('noindex')
      const html = await response.text()
      expect(html.match(/<title>([^<]+)<\/title>/)?.[1], path).toBeTruthy()
      expect(meta(html, 'name', 'description'), path).toBeTruthy()
      expect(meta(html, 'property', 'og:title'), path).toBeTruthy()
      expect(html, path).toContain(`<link rel="canonical" href="${url}">`)
      expect(html.match(/<h1[\s>]/g), path).toHaveLength(1)
      expect(html, path).toMatch(/<html[^>]* lang="en"/)
      expect(html, path).toContain('"@type":"WebSite","name":"Acme Console"')
    }
  })

  it('gives each of its pages a share image', async () => {
    for (const url of await pages()) {
      const path = url.slice(SITE.length)
      const image = meta(await $fetch<string>(path), 'property', 'og:image')
      expect(image, path).toMatch(new RegExp(`^${SITE}/_og/`))
      const response = await fetch(image!.slice(SITE.length))
      expect(response.status, path).toBe(200)
      expect(response.headers.get('content-type'), path).toBe('image/png')
      expect(size(new Uint8Array(await response.arrayBuffer())), path).toEqual([1200, 630])
    }
  })

  it('refuses to draw a share image it did not sign', async () => {
    expect((await fetch('/_og/d/c_Page,title_Anything.png')).status).toBe(403)
  })
})

describe('signed-in area', () => {
  it('is never indexed', async () => {
    const response = await fetch('/app/settings')
    expect(response.headers.get('x-robots-tag')).toBe('noindex, nofollow')
  })
})
