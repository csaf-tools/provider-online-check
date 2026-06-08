<!--
SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
Software-Engineering: 2026 Intevation GmbH <https://intevation.de>

SPDX-License-Identifier: Apache-2.0
-->

<template>
    <div class="small-bottom-margin">
        <span v-if="type === 2" :class="messageClass">ERROR</span>
        <span v-else-if="type === 1" :class="messageClass">WARN</span>
        <span v-else :class="messageClass">PASS</span>
        {{ text }}
    </div>
</template>
<script lang="ts">
import { defineComponent } from 'vue'
export default defineComponent({
    props: {
        type: Number,
        text: String
    },
    computed: {
        messageClass() {
            switch (this.type) {
                case 0:
                    return 'text-green'
                case 1:
                    return 'text-orange'
                case 2:
                    return 'text-red'
                default:
                    return ''
            }
        }
    }
})
</script>

<style scoped>

.text-green {
color: var(--bs-success);
}
.text-orange {
color: var(--bs-warning);
}
.text-red {
color: var(--bs-danger);
}
.small-bottom-margin {
    margin-bottom: 12px;
}
</style>

