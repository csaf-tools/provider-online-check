<template>
  <div id="app">
    <nav class="navbar navbar-dark bg-dark">
      <div class="container-fluid">
        <span class="navbar-brand mb-0 h1">CSAF Provider Scan</span>
      </div>
    </nav>

    <div class="container mt-5">
      <div class="row justify-content-center">
        <div class="col-md-8">
          <div class="card shadow">
            <div class="card-body">
              <h2 class="card-title mb-4">Scan a Domain</h2>

              <form @submit.prevent="startScan">
                <div class="mb-3">
                  <label for="domainInput" class="form-label">Domain</label>
                  <input
                    type="text"
                    class="form-control"
                    id="domainInput"
                    v-model="domain"
                    placeholder="example.com"
                    required
                  >
                  <div class="form-text">Enter a domain to scan a CSAF provider</div>
                </div>

                <button
                  type="submit"
                  class="btn btn-primary"
                  :disabled="loading"
                >
                  <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  {{ loading ? 'Scanning...' : 'Start Scan' }}
                </button>
              </form>

              <div v-if="result" class="mt-4">
                <div :class="['alert', resultClass]" role="alert">
                  <div v-if="result.status === 'ERROR'">
                    <h5 class="alert-heading">Error</h5>
                    <p class="mb-0">{{ result.error }}</p>
                  </div>
                  <div v-if="result.status != 'ERROR'">
                    <h5 class="alert-heading">Scan Done</h5>
                    <pre>{{ result.results_checker }}</pre>
                  </div>
                </div>
                <div v-if="result.runtime_output" class="mt-4">
                  <div :class="['alert', resultClass]" role="alert">
                    <h5 class="alert-heading">Details</h5>
                    <li v-for="(item, index) in result.runtime_output" :key="index">
                    <p class="mb-0">{{ item }}</p>
                    </li>
                  </div>
                </div>
              </div>

              <div v-if="error" class="mt-4">
                <div class="alert alert-danger" role="alert">
                  <h5 class="alert-heading">Error</h5>
                  <p class="mb-0">{{ error }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="row justify-content-center mt-4">
        <div class="col-md-8">
          <div class="card">
            <div class="card-body">
              <h5 class="card-title">About</h5>
              <p class="card-text">
                This tool scans domains for <a href="https://www.csaf.io" target="_blank">CSAF</a> (Common Security Advisory Framework)
                provider metadata and check it's validity.
              </p>
              <p>
                <a href="https://github.com/Intevation/csaf-provider-scan/" target="_blank">
                  Website and Source Code
                </a>
                <a :href="apiDocsUrl" target="_blank">
                  API Documentation
                </a>
              </p>
              <p>
                This is a project of the <a href="https://www.bsi.bund.de">German Federal Office for Information Security (BSI)</a><br />
                Software-Engineering: <a href="https://intevation.de">Intevation GmbH</a><br />
                Software License: Apache-2.0
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      session_id: '1',
      domain: '',
      loading: false,
      result: null,
      error: null
    }
  },
  computed: {
    resultClass() {
      return this.result?.status != 'ERROR' ? 'alert-success' : 'alert-danger'
    },
    backendUrl() {
      // Use the same protocol and host as the client, but with backend port
      const protocol = window.location.protocol
      const hostname = window.location.hostname
      const backendPort = 48090
      return `${protocol}//${hostname}:${backendPort}`
    },
    apiDocsUrl() {
      return `${this.backendUrl}/docs`
    }
  },
  methods: {
    async startScan() {
      this.loading = true
      this.result = null
      this.error = null

      try {
        const response = await axios.post(`${this.backendUrl}/scan/start`, {
          domain: this.domain,
          session_id: this.session_id
        })
        this.result = response.data
      } catch (err) {
        this.error = err.response?.data?.detail || err.message || 'An error occurred while starting the scan'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
#app {
  min-height: 100vh;
  background-color: #f8f9fa;
}
</style>
