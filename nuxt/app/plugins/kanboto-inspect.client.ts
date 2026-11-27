/**
 * Inspector for Kanboto's page workshop, which shows the running site in a frame and lets a human point at a
 * block. Off unless `NUXT_PUBLIC_KANBOTO_INSPECT_ORIGIN` is set (Kanboto sets it outside production only) and
 * the page is framed; it talks to that origin and to no other.
 *
 * Sent: `ready` (on load and on each route change, with the blocks in page order), then, in selection mode,
 * `hover` and `select` with the block, the field and the item under the pointer.
 * Received: `highlight` (outline a block) and `mode` (selection on or off; off, the site behaves normally).
 */
interface Target {
  block: string
  blockType: string | null
  field: string | null
  item: number | null
  text: string
  rect: { x: number, y: number, width: number, height: number }
}

const TEXT_MAX = 200

function describe(target: EventTarget | null): Target | undefined {
  const element = target instanceof Element ? target : undefined
  const block = element?.closest<HTMLElement>('[data-kb-block]')
  if (!element || !block) return undefined
  const field = element.closest<HTMLElement>('[data-kb-field]')
  const item = element.closest<HTMLElement>('[data-kb-item]')
  const inside = (candidate: HTMLElement | null | undefined) => (candidate && block.contains(candidate) ? candidate : undefined)
  const shown = inside(field) ?? block
  const { x, y, width, height } = shown.getBoundingClientRect()
  return {
    block: block.dataset.kbBlock!,
    blockType: block.dataset.kbType ?? null,
    field: inside(field)?.dataset.kbField ?? null,
    item: inside(item) ? Number(inside(item)!.dataset.kbItem) : null,
    text: (shown.textContent ?? '').trim().replace(/\s+/g, ' ').slice(0, TEXT_MAX),
    rect: { x, y, width, height },
  }
}

export default defineNuxtPlugin((nuxtApp) => {
  const origin = useRuntimeConfig().public.kanbotoInspectOrigin
  if (!origin || window.parent === window) return

  let selecting = false
  let hovered = ''
  let highlighted: HTMLElement | undefined
  let announced = ''

  const post = (message: Record<string, unknown>) =>
    window.parent.postMessage({ source: 'kanboto-inspect', path: location.pathname, ...message }, origin)

  function ready(): void {
    const blocks = [...document.querySelectorAll<HTMLElement>('[data-kb-block]')]
      .map(block => ({ id: block.dataset.kbBlock, type: block.dataset.kbType }))
    // Mounting and the end of a navigation both end here: the same page is announced once.
    const key = JSON.stringify([location.pathname, blocks])
    if (key === announced) return
    announced = key
    post({ type: 'ready', blocks })
  }

  function highlight(id: unknown): void {
    highlighted?.style.removeProperty('outline')
    highlighted?.style.removeProperty('outline-offset')
    highlighted = typeof id === 'string'
      ? document.querySelector<HTMLElement>(`[data-kb-block="${CSS.escape(id)}"]`) ?? undefined
      : undefined
    highlighted?.style.setProperty('outline', 'calc(var(--border-width) * 2) solid var(--color-focus)')
    highlighted?.style.setProperty('outline-offset', 'calc(var(--border-width) * -2)')
  }

  window.addEventListener('pointerover', (event) => {
    const target = selecting ? describe(event.target) : undefined
    const key = target ? `${target.block}/${target.field}/${target.item}` : ''
    if (key === hovered) return
    hovered = key
    if (target) post({ type: 'hover', ...target })
  })

  // Capture phase: the click selects before any link or button of the page reacts to it.
  window.addEventListener('click', (event) => {
    const target = selecting ? describe(event.target) : undefined
    if (!target) return
    event.preventDefault()
    event.stopPropagation()
    post({ type: 'select', ...target })
  }, true)

  window.addEventListener('message', (event) => {
    if (event.origin !== origin || event.data?.source !== 'kanboto-atelier') return
    if (event.data.type === 'highlight') highlight(event.data.block)
    if (event.data.type === 'mode') {
      selecting = event.data.select === true
      hovered = ''
    }
  })

  nuxtApp.hook('app:mounted', ready)
  nuxtApp.hook('page:finish', () => nextTick(ready))
})
