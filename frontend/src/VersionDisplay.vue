<template>
  <div class="version">
    Provider {{ providerVersion }} Checker {{ checkerVersion }} Validator {{ validatorVersion }}
  </div>
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
.version {
    color: var(--bs-secondary-color);
    font-size: 0.75em;
}
</style>