<script setup lang="ts">
const { appName } = useRuntimeConfig().public
const site = useSiteConfig()
const route = useRoute()
// The page's address on the site, without its query string.
const canonical = withSiteUrl(computed(() => route.path))

// Each page sets its own title and description (`useSeoMeta`); the root adds what every page shares.
useHead({
  titleTemplate: title => (title && title !== appName ? `${title} · ${appName}` : appName),
  htmlAttrs: { lang: site.defaultLocale },
  link: [
    { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
    { rel: 'canonical', href: canonical },
  ],
})
useSeoMeta({
  ogSiteName: appName,
  ogType: 'website',
  ogUrl: canonical,
  ogLocale: site.defaultLocale,
  twitterCard: 'summary_large_image',
})
// The share image: the page's title and description, drawn in the design's colours and fonts.
defineOgImage('Page')
</script>

<template>
  <NuxtPage />
</template>

<style>
/* Every value comes from `assets/design/tokens.css`: never a colour, font or size written here. */
html,
body {
  margin: 0;
  color: var(--color-text);
  background: var(--color-bg);
  font-family: var(--font-body);
  font-size: var(--text-base);
  line-height: var(--leading-body);
  -webkit-font-smoothing: antialiased;
}
</style>
