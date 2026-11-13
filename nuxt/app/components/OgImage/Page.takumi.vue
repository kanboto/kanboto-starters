<script setup lang="ts">
/**
 * The share image of a page (`og:image`), 1200×630: the top of the site in a window, with the page's title and
 * description (filled in from `useSeoMeta`). Colours and fonts come from the design's tokens, like the site's.
 * Takumi lays it out like flexbox: every element with children is a flex container.
 */
import tokens from '~/assets/design/tokens.json'

const { title = '', description = '' } = defineProps<{ title?: string, description?: string }>()

const { appName } = useRuntimeConfig().public
const site = useSiteConfig()
const host = site.url ? new URL(site.url).host : ''

const SYSTEM = /^(serif|sans-serif|monospace|cursive|fantasy|system-ui|ui-\w+|-apple-system|BlinkMacSystemFont)$/
// A system font cannot be drawn: Inter, bundled with the image module, stands in for it.
const family = (stack: string[]) => stack.find(name => !SYSTEM.test(name)) ?? 'Inter'

const c = Object.fromEntries(Object.entries(tokens.color).map(([name, token]) => [name, token.$value]))
const display = family(tokens.font.display.$value)
const body = family(tokens.font.body.$value)
const bold = Number(tokens.fontWeight.bold.$value)
const initial = ([...String(appName).trim()][0] ?? '?').toUpperCase()
const heading = title && title !== appName ? title : description || appName
const text = heading === description ? '' : description
</script>

<template>
  <div
    class="flex w-full h-full"
    :style="{ background: c.action, padding: '56px 64px 0 64px', fontFamily: body, color: c.text }"
  >
    <div
      class="flex flex-col w-full"
      :style="{ background: c.bg, borderRadius: '18px 18px 0 0', overflow: 'hidden' }"
    >
      <div
        class="flex items-center"
        :style="{ height: '64px', padding: '0 24px', gap: '10px', borderBottom: `1px solid ${c.border}` }"
      >
        <div
          v-for="dot in 3"
          :key="dot"
          class="flex"
          :style="{ width: '14px', height: '14px', borderRadius: '7px', background: c.border }"
        />
        <div
          v-if="host"
          class="flex items-center"
          :style="{ marginLeft: '24px', height: '36px', padding: '0 18px', borderRadius: '18px', background: c.surface, fontSize: '20px', color: c.muted }"
        >
          {{ host }}
        </div>
      </div>
      <div
        class="flex items-center"
        :style="{ marginTop: '36px', padding: '0 56px', gap: '14px', fontSize: '26px', fontWeight: bold }"
      >
        <div
          class="flex items-center justify-center"
          :style="{ width: '40px', height: '40px', borderRadius: '10px', background: c.action, color: c['action-text'], fontSize: '22px' }"
        >
          {{ initial }}
        </div>
        {{ appName }}
      </div>
      <div
        class="flex flex-col"
        :style="{ padding: '52px 56px 0 56px', gap: '24px' }"
      >
        <div
          :style="{ fontFamily: display, fontSize: heading.length > 48 ? '56px' : '72px', fontWeight: bold, lineHeight: 1.08, letterSpacing: '-0.02em', maxWidth: '960px', lineClamp: 3 }"
        >
          {{ heading }}
        </div>
        <div
          v-if="text"
          :style="{ fontSize: '28px', lineHeight: 1.4, color: c.muted, maxWidth: '900px', lineClamp: 2 }"
        >
          {{ text }}
        </div>
      </div>
    </div>
  </div>
</template>
