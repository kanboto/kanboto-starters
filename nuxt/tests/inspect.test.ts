/**
 * Kanboto's page workshop shows the running site in a frame, outside production: when its origin is
 * configured, that origin and no other may frame the site. Without it, nobody may (see `server.test.ts`).
 */
import { fileURLToPath } from 'node:url'
import { fetch, setup } from '@nuxt/test-utils/e2e'
import { describe, expect, it } from 'vitest'

const WORKSHOP = 'https://workshop.example.com'

await setup({
  rootDir: fileURLToPath(new URL('..', import.meta.url)),
  env: {
    NUXT_PUBLIC_APP_NAME: 'Acme Console',
    NUXT_PUBLIC_KANBOTO_INSPECT_ORIGIN: `${WORKSHOP}/some/path`,
    NUXT_APP_SECRET: 'a-test-secret-of-at-least-32-characters',
    DRAIN_DELAY_S: '0',
  },
})

describe('with the workshop\'s origin', () => {
  it('lets that origin, and no other, frame the pages', async () => {
    for (const path of ['/', '/app/items']) {
      const response = await fetch(path)
      expect(response.headers.get('content-security-policy'), path).toBe(`frame-ancestors ${WORKSHOP}`)
      expect(response.headers.get('x-frame-options'), path).toBeNull()
    }
  })

  it('hands the origin to the inspector, in the page', async () => {
    expect(await (await fetch('/')).text()).toContain(`kanbotoInspectOrigin:"${WORKSHOP}/some/path"`)
  })
})
