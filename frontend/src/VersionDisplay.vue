<!--
SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
Software-Engineering: 2026 Intevation GmbH <https://intevation.de>

SPDX-License-Identifier: Apache-2.0
-->

<template>
    <small class="text-muted version">
        Version Information: CSAF Provider Online Check {{ providerVersion }} •
        <a href="https://github.com/gocsaf/csaf/releases/" target="_blank">CSAF Checker</a> {{ checkerVersion }} •
        <a href="https://github.com/secvisogram/csaf-validator-service" target="_blank">Secvisogram Validator</a> {{ validatorVersion }}
    </small>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

export default defineComponent({
    props: {
        providerVersion: String,
        checkerVersion: String,
        validatorVersion: String
    }
})
</script>

<style scoped>
.version a {
    color: inherit;
}
</style>
