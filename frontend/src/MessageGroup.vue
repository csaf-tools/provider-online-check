<!--
SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
Software-Engineering: 2026 Intevation GmbH <https://intevation.de>

SPDX-License-Identifier: Apache-2.0
-->

<template>
  <div class="message-group small-margin-top">
    <div class="message-group-header">
      <span class="requirement-desc">{{ description }}</span>
      <span v-if="messages.length > 0" class="message-counts ms-2">
        <span v-if="errorCount > 0" class="badge bg-danger me-1">{{ errorCount }} error{{ errorCount !== 1 ? 's' : '' }}</span>
        <span v-if="warnCount > 0" class="badge bg-warning text-dark me-1">{{ warnCount }} warning{{ warnCount !== 1 ? 's' : '' }}</span>
      </span>
      <button
        v-if="messages.length > COLLAPSE_THRESHOLD"
        class="toggle-btn ms-2"
        @click="expanded ? collapse() : expand()"
      >
        <span v-if="expanding" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
        {{ expanding ? (expanded ? 'collapse' : 'show all ' + messages.length + ' messages') : (expanded ? '▼ collapse' : '▶ show all ' + messages.length + ' messages') }}
      </button>
    </div>
    <div class="message-group-body">
      <MessageLine
        v-for="(msg, idx) of visibleMessages"
        :key="idx"
        :text="msg.text"
        :type="msg.type"
      />
      <div v-if="messages.length > COLLAPSE_THRESHOLD" class="show-more-hint text-muted">
        <span v-if="expanding" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
        <span v-if="!expanded && !expanding" role="button" @click="expand" class="toggle-btn">...</span>
        <span v-if="expanded && !expanding" role="button" @click="collapse" class="toggle-btn">collapse</span>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import MessageLine from './MessageLine.vue'

const COLLAPSE_THRESHOLD = 5

export default defineComponent({
  name: 'MessageGroup',
  components: { MessageLine },
  props: {
    num: { type: Number, required: true },
    description: { type: String, required: true },
    messages: { type: Array as () => { text: string; type: number }[], required: true },
  },
  data() {
    return {
      expanded: false,
      expanding: false,
      COLLAPSE_THRESHOLD,
    }
  },
  computed: {
    visibleMessages(): { text: string; type: number }[] {
      if (this.expanded || this.messages.length <= COLLAPSE_THRESHOLD) {
        return this.messages
      }
      return this.messages.slice(0, COLLAPSE_THRESHOLD)
    },
    errorCount(): number {
      return this.messages.filter(m => m.type === 2).length
    },
    warnCount(): number {
      return this.messages.filter(m => m.type === 1).length
    },
  },
  methods: {
    expand() {
      this.expanding = true
      setTimeout(() => {
        this.expanded = true
        this.expanding = false
      }, 0)
    },
    collapse() {
      this.expanding = true
      setTimeout(() => {
        this.expanded = false
        this.expanding = false
      }, 0)
    },
  },
})
</script>

<style scoped>
.message-group {
  border-left: 3px solid var(--bs-secondary);
  padding-left: 0.75rem;
  margin-bottom: 0.75rem;
}
.message-group-header {
  font-weight: 600;
  margin-bottom: 0.25rem;
}
.show-more-hint {
  font-size: 0.875rem;
  margin-top: 0.25rem;
}
.toggle-btn {
  font-size: 0.8rem;
  font-weight: normal;
  background: none;
  border: none;
  padding: 0;
  color: var(--bs-secondary);
  cursor: pointer;
}
.toggle-btn:hover {
  text-decoration: underline;
}
</style>
