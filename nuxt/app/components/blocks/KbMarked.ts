import type { FunctionalComponent } from 'vue'
import { h } from 'vue'
import { marked } from './lib/fields'

/** A title's text, with the words written between asterisks set apart (`.kb-mark`). A title without any is
 * plain text: nothing is added to the markup. */
const KbMarked: FunctionalComponent<{ text: string }> = (props) => {
  if (!props.text.includes('*')) return props.text
  return marked(props.text).map(part => (part.mark ? h('em', { class: 'kb-mark' }, part.text) : part.text))
}
KbMarked.props = ['text']

export default KbMarked
