import { inject } from 'vue'

/** The few words the block library writes itself (accessible names, mostly). A project in another language provides its
 * own under `kb:labels`: `provide('kb:labels', { menu: 'Menü' })`. */
export const defaultLabels = {
  skip: 'Skip to content',
  menu: 'Menu',
  close: 'Close',
  mainNav: 'Main',
  footerNav: 'Footer',
  back: 'Back',
  previous: 'Previous',
  next: 'Next',
  gallery: 'Gallery',
  slides: 'Slides',
  table: 'Table',
  required: 'required',
  requiredLegend: 'Fields marked * are required.',
  fieldInvalid: 'Check this field.',
  featured: 'Recommended',
  custom: 'Custom block',
}

export type KbLabels = typeof defaultLabels

export function useLabels(): KbLabels {
  return { ...defaultLabels, ...inject<Partial<KbLabels>>('kb:labels', {}) }
}
