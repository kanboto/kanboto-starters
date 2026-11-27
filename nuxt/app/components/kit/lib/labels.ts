import { inject } from 'vue'

/** The few words the kit writes itself (accessible names, mostly). A project in another language provides its
 * own under `kb:labels`: `provide('kb:labels', { menu: 'Menü' })`. */
export const defaultLabels = {
  menu: 'Menu',
  close: 'Close',
  mainNav: 'Main',
  footerNav: 'Footer',
  back: 'Back',
  previous: 'Previous',
  next: 'Next',
  gallery: 'Gallery',
  table: 'Table',
  required: 'required',
  custom: 'Custom block',
}

export type KbLabels = typeof defaultLabels

export function useLabels(): KbLabels {
  return { ...defaultLabels, ...inject<Partial<KbLabels>>('kb:labels', {}) }
}
