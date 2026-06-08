// SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
// Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
//
// SPDX-License-Identifier: Apache-2.0

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',
    port: 8080,
    allowedHosts: true,
    watch: {
      usePolling: true
    }
  },
  test: {
    globals: true,
    environment: "jsdom",
    coverage: {
      thresholds: {
	      lines: 70
      }
    }
  }
})
