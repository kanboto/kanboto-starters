<script setup lang="ts">
import { computed } from 'vue'
import KbSectionHeader from '../KbSectionHeader.vue'
import { useVariant } from '../lib/block'
import { flag, items, text } from '../lib/fields'
import { useLabels } from '../lib/labels'
import type { KbBlock, KbItem } from '../lib/types'
import { cn } from '../lib/utils'
import { Button } from '../ui/button'
import { Card } from '../ui/card'
import { Checkbox } from '../ui/checkbox'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { NativeSelect } from '../ui/native-select'
import { Textarea } from '../ui/textarea'
import KbSection from './KbSection.vue'

// Native controls and native validation: each field has a visible label, a `name`, what the browser needs to
// fill it, and is only marked invalid once the user has touched it (`:user-invalid`). The form sends nothing
// by itself: the page that uses it handles `submit`.
const props = defineProps<{
  block: KbBlock
}>()

const INPUTS = ['text', 'email', 'tel', 'password', 'number', 'date']
/** What the browser may fill, and the keyboard a phone shows, by type of field. */
const HINTS: Record<string, { autocomplete: string, inputmode?: 'email' | 'tel' | 'decimal', plain?: boolean }> = {
  text: { autocomplete: 'on' },
  email: { autocomplete: 'email', inputmode: 'email', plain: true },
  tel: { autocomplete: 'tel', inputmode: 'tel' },
  password: { autocomplete: 'current-password', plain: true },
  number: { autocomplete: 'off', inputmode: 'decimal' },
  date: { autocomplete: 'on' },
}

const labels = useLabels()
const variant = useVariant(() => props.block, ['card', 'split', 'plain'])
const fields = computed(() => items(props.block.props, 'fields').filter(item => text(item, 'label')).map(field))
const submit = computed(() => text(props.block.props, 'submit'))

function field(item: KbItem, index: number) {
  const type = text(item, 'type') || 'text'
  const label = text(item, 'label')
  return {
    index,
    id: `${props.block.id}-field-${index}`,
    name: label.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '_').replace(/^_|_$/g, '') || `field_${index}`,
    label,
    type: INPUTS.includes(type) || type === 'textarea' || type === 'select' || type === 'checkbox' ? type : 'text',
    required: flag(item, 'required'),
    hint: HINTS[type] ?? HINTS.text!,
  }
}
</script>

<template>
  <KbSection
    :block="block"
    :data-kb-variant="variant"
  >
    <div :class="variant === 'split' ? 'grid gap-10 @4xl:grid-cols-2 @4xl:gap-16' : cn('flex flex-col gap-8', variant === 'card' ? 'mx-auto max-w-xl' : 'max-w-xl')">
      <KbSectionHeader
        :block="block"
        lead="text"
      />
      <component
        :is="variant === 'plain' ? 'form' : Card"
        v-if="fields.length || submit"
        as="form"
        method="post"
        :class="cn('flex flex-col gap-5', variant !== 'plain' && '@3xl:p-8')"
        @submit.prevent
      >
        <div
          v-for="entry in fields"
          :key="entry.index"
          data-kb-field="fields"
          :data-kb-item="entry.index"
          :class="entry.type === 'checkbox' ? 'flex items-center gap-3 pointer-coarse:min-h-11' : 'flex flex-col gap-2'"
        >
          <Checkbox
            v-if="entry.type === 'checkbox'"
            :id="entry.id"
            :name="entry.name"
            :required="entry.required"
          />
          <Label
            :for="entry.id"
            data-kb-field="label"
          >
            {{ entry.label }}
            <span
              v-if="entry.required"
              class="text-muted-foreground"
              :title="labels.required"
              aria-hidden="true"
            >*</span>
          </Label>
          <Textarea
            v-if="entry.type === 'textarea'"
            :id="entry.id"
            :name="entry.name"
            :required="entry.required"
          />
          <NativeSelect
            v-else-if="entry.type === 'select'"
            :id="entry.id"
            :name="entry.name"
            :required="entry.required"
          >
            <option value="" />
          </NativeSelect>
          <Input
            v-else-if="entry.type !== 'checkbox'"
            :id="entry.id"
            :name="entry.name"
            :type="entry.type"
            :required="entry.required"
            :autocomplete="entry.hint.autocomplete"
            :inputmode="entry.hint.inputmode"
            :autocapitalize="entry.hint.plain ? 'none' : undefined"
            :spellcheck="entry.hint.plain ? false : undefined"
          />
        </div>
        <Button
          v-if="submit"
          type="submit"
          size="lg"
          data-kb-field="submit"
          class="mt-2 w-full @xl:w-fit"
        >
          {{ submit }}
        </Button>
      </component>
    </div>
  </KbSection>
</template>
