<!--
SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
Software-Engineering: 2026 Intevation GmbH <https://intevation.de>

SPDX-License-Identifier: Apache-2.0
-->

<template>
  <div id="app">
    <div class="container pt-4">
      <div class="row justify-content-center">
        <div class="col-md-12">
          <div class="card shadow">
            <div class="card-body">
              <h2 class="card-title mb-4">CSAF Provider Check <span class="badge bg-warning text-dark ms-2">Beta</span></h2>

              <p>Check a CSAF Provider's metadata and all its documents for validity.<br />
                Learn more about CSAF (Common Security Advisory Framework) at <a href="https://csaf.io" target="_blank">csaf.io</a>.</p>

              <form @submit.prevent="startScan" v-if="allowInput">
                <div class="mb-3">
                  <label for="domainInput" class="form-label">Enter a domain name or <a href="https://docs.oasis-open.org/csaf/csaf/v2.1/csaf-v2.1.html#717-requirement-7-provider-metadatajson-" title="Provider Metadata File" target="_blank">PMD</a> to start the check:</label>
                  <input
                    type="text"
                    class="form-control"
                    id="domainInput"
                    v-model="domain"
                    required
                    placeholder="example.com or https://example.com/.well-known/csaf/provider-metadata.json"
                    autofocus
                  >
                </div>

                <button
                  type="submit"
                  class="btn btn-primary"
                >
                  Start Check
                </button>
              </form>

              <div class="alert alert-light mt-4" role="alert" v-else>
                <div class="d-flex gap-2">
                  <span>{{ loading ? 'Running check on target'.replaceAll(' ', '&nbsp;'): 'Completed the check of'.replaceAll(' ', '&nbsp;')}}</span>
                  <span><code>{{ domain }}</code></span>
                  <span v-if="loading" class="spinner-border spinner-border-sm ms-2 me-auto" role="status" aria-hidden="true"></span>
                  <span v-else class="ms-2 me-auto">✓</span>
                  <button class="btn btn-warning btn-sm" @click="reset">{{ loading ? 'Cancel': 'Start a new check'}}</button>
                  <button class="btn btn-danger btn-sm" v-if="!loading" @click="rescan">Rerun without cache</button>
                </div>
                <div v-if="result?.start_time">Duration: {{ formatDuration(result?.start_time, result?.end_time) }}</div>
              </div>

              <!-- display of requirements messages -->
              <div v-if="messagesList" class="alert alert-light mt-4">
                <h3 class="alert-heading d-inline">Check results</h3>
                <button v-if="result?.status === 'CACHED_CHECKER'"
                  class="cache-info-btn ms-2"
                  type="button"
                  @click="isShowCacheInfo = !isShowCacheInfo"
                  :aria-expanded="isShowCacheInfo"
                >Loaded cached result <span class="cache-info-circle">?</span></button>
                <div v-if="result?.status === 'CACHED_CHECKER' && isShowCacheInfo" class="cache-info-box mt-1">
                  This target was checked previously.
                   To reduce load on this service and the targeted CSAF provider, recent results are cached and reused.
                   The result below may not reflect the current state of the provider.
                   For up-to-date results, you can <a href="https://github.com/csaf-tools/provider-online-check/" target="_blank">run your own instance</a> of this service or use the <a href="https://github.com/gocsaf/csaf/blob/main/docs/csaf_checker.md" target="_blank">csaf_checker</a> command-line tool directly.
                </div>

                <div v-show="scanTime">
                  <div>Start time of the check: {{ scanTime }}</div>
                </div>

                <h4 v-if="role" :class="trustedProviderStatus" class="small-margin-top medium-font-size">
                  <span v-if="trustedProviderStatus === 'text-green'">PASSED:</span>
                  <span v-else>FAILED:</span>
                  {{ role }}
                </h4>
                <!-- target is not a CSAF provider -->
                <h4 v-if="!role" class="text-warning small-margin-top medium-font-size">No CSAF endpoint found</h4>
                <p v-if="!role">The target does not appear to be a CSAF publisher or provider. No provider metadata could be found or parsed.</p>
                <MessageGroup
                  v-for="group of groupedTrustedProviderMessages"
                  :key="group.num"
                  :num="group.num"
                  :description="group.description"
                  :messages="group.messages"
                  :passed="group.passed ?? false"
                />

                <p class="small-margin-top">
                    <a class="btn btn-primary" data-bs-toggle="collapse" href="#collapseAllMessages" role="button" aria-expanded="false" aria-controls="collapseAllMessages"
                      :key="displayAllMessagesTitle"
                    >
                      {{  displayAllMessagesTitle }}
                    </a>
                </p>
                <div class="collapse" id="collapseAllMessages" ref="allMessagesRef">
                  <div class="card card-body">
                    <h5 class="card-title">All messages</h5>
                    <div class="card-text log-card-size overflow-scroll">
                      <p>These are all unfiltered messages of <code>csaf_checker</code> and may contain messages that are not relevant for the analysis.</p>
                      <MessageLine v-for="item of messagesList" :key="item.text" :text="item.text" :type="item.type"></MessageLine>
                    </div>
                  </div>
                </div>
                <p class="small-margin-top">
                    <a class="btn btn-primary" data-bs-toggle="collapse" href="#collapseResultOutput" role="button" aria-expanded="false" aria-controls="collapseResultOutput"
                      :key="displayResultOutputTitle"
                    >
                      {{ displayResultOutputTitle }}
                    </a>
                </p>
                <div class="collapse" id="collapseResultOutput" ref="resultOutputRef">
                  <div class="card card-body">
                    <div class="card-title d-flex gap-2 mb-2">
                      <h5 class="me-auto log-header">Complete JSON Result</h5>
                      <button class="btn btn-sm btn-outline-secondary" @click="copyResultToClipboard">Copy to clipboard</button>
                      <button class="btn btn-sm btn-outline-secondary" @click="downloadJson">Download</button>
                    </div>
                    <div class="card-text log-card-size overflow-scroll">
                      <p>This is the complete (stdout) unparsed JSON output of <code>csaf_checker</code>.</p>
                      <pre>{{ result?.results_checker }}</pre>
                    </div>
                  </div>
                </div>
                <p class="small-margin-top">
                    <a class="btn btn-primary" data-bs-toggle="collapse" href="#collapseLogOutput" role="button" aria-expanded="false" aria-controls="collapseLogOutput"
                      :key="displayLogOutputTitle">
                      {{ displayLogOutputTitle }}
                    </a>
                </p>
                <div class="collapse" id="collapseLogOutput" ref="logOutputRef">
                  <div class="card card-body">
                    <div class="cart-title d-flex gap-2 mb-2">
                      <h5 class="me-auto log-header">Log output</h5>
                      <button class="btn btn-sm btn-outline-secondary" @click="copyLogToClipboard">Copy to clipboard
                        <span v-if="fetchLogCBStatus === 'loading'" class="spinner-border spinner-border-sm ms-2" role="status"></span>
                        <span v-if="fetchLogCBStatus === 'done'" role="status">✓</span>
                        <span v-if="fetchLogCBStatus === 'error'">❌</span>
                      </button>
                      <button class="btn btn-sm btn-outline-secondary" @click="downloadLog">Download
                        <span v-if="fetchLogDLStatus === 'loading'" class="spinner-border spinner-border-sm ms-2" role="status"></span>
                        <span v-if="fetchLogDLStatus === 'done'" role="status">✓</span>
                        <span v-if="fetchLogDLStatus === 'error'">❌</span>
                      </button>
                    </div>
                    <div class="card-text log-card-size overflow-scroll">
                      <p v-if="!result?.runtime_output_capped">This is the complete log (stderr)
                        output of <code>csaf_checker</code> ({{ result?.runtime_output_total_lines }} lines).</p>
                      <p v-else>This is <strong>only a portion of</strong> the log (stderr) output of <code>csaf_checker</code>,
                        showing the last {{ result?.runtime_output?.length }} of {{ result?.runtime_output_total_lines }} lines.
                        Use the buttons <em>Copy to clipboard</em> or <em>Download</em> to get the complete log.</p>
                      <p>All timestamps are in UTC.</p>
                      <pre>{{ result?.runtime_output?.join('\n') }}</pre>
                    </div>
                  </div>
                </div>
              </div>
              <div
                v-if="result && ['ERROR', 'UNDEFINED', 'INITIALIZED', 'RUNNING_CHECKER', 'PAUSED'].includes(result?.status)"
                class="mt-4"
              >
                <div :class="['alert', resultClass]" role="alert">
                  <div v-if="result.status === 'ERROR' || result.status === 'UNDEFINED'">
                    <h5 class="alert-heading">Error</h5>
                    <p class="mb-0">{{ result.error }}</p>
                  </div>
                  <div v-if="result.status === 'INITIALIZED'">
                    <h5 class="alert-heading">Check started...</h5>
                  </div>
                  <div v-if="result.status === 'RUNNING_CHECKER'">
                    <h5 class="alert-heading">Check running...</h5>
                    <h6 class="alert-heading">Files checked: {{ result.files_checked }}</h6>
                    <h6 class="alert-heading">Latest file checked: {{ result.latest_file_checked }}</h6>
                  </div>
                  <div v-if="result.status === 'PAUSED'">
                    <h5 class="alert-heading">Check paused</h5>
                  </div>
                </div>
                <div v-if="result.runtime_output" class="mt-4">
                  <div :class="['alert', resultClass]" role="alert">
                    <h5 class="alert-heading">Details</h5>
                    <p v-if="result.runtime_output?.length">All timestamps are in UTC</p>
                    <ul>
                      <li v-for="(item, index) in result.runtime_output" :key="index">{{ item }}</li>
                    </ul>
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

      <div class="row justify-content-center mt-4 pb-4">
        <div class="col-md-12">
          <div class="card">
            <div class="card-body">
              <h5 class="card-title">About</h5>
              <p class="card-text">
                This is an experimental tool that checks a CSAF provider's metadata and documents for validity.
                It uses <a href="https://github.com/gocsaf/csaf/blob/main/docs/csaf_checker.md"><code>csaf_checker</code></a> of the gocsaf toolsuite under the hood.
              </p>
              <p>
                <a href="https://github.com/csaf-tools/provider-online-check/" target="_blank">
                  Website and Source Code
                </a>
                &nbsp;
                <a :href="apiDocsUrl" target="_blank">
                  API Documentation
                </a>
              </p>
              <p v-if="footerText" v-html="footerText"></p>
              <VersionDisplay :checkerVersion="version?.csaf_checker_version"
                                  :provider-version="version?.csaf_provider_version"
                                  :validator-version="version?.csaf_validator_version"
                />
            </div>
          </div>
        </div>
    </div>
    </div>
  </div>
</template>

<script lang="ts">
import axios from 'axios'
import { defineComponent } from 'vue'
import MessageLine from './MessageLine.vue'
import MessageGroup from './MessageGroup.vue'
import VersionDisplay from './VersionDisplay.vue'
import { relevantRequirements, type EvaluatedRule } from './evaluatedRules'

interface ResultCheckerData {
  domains: {
    requirements: {num: number, description: string, messages: {text: string, type: number}[]}[],
    passed: boolean;
    role: string;
    evaluated_rules?: EvaluatedRule;
  }[];
  date: string;
}

interface RequirementGroup {
  num: number;
  description: string;
  messages: { text: string; type: number }[];
  passed?: boolean;
}

interface AppData {
  session_id: string;
  domain: string;
  loading: boolean;
  allowInput: boolean;
  result: any;
  error: any;
  messagesList: null | MessageData[];
  requirementGroups: RequirementGroup[];
  relevantRequirementNums: number[] | null;
  scanTime: null | string;
  passed: boolean;
  role: string | null;
  isShowAllMessages: boolean;
  isShowResultOutput: boolean;
  isShowLogOutput: boolean;
  isShowCacheInfo: boolean;
  fetchLogCBStatus: string;
  fetchLogDLStatus: string;
  observe_rerun: boolean;
  version: {
    csaf_checker_version: string;
    csaf_validator_version: string;
    csaf_provider_version: string;
  } | null
}

interface MessageData {
  text: string;
  type: number;
  num: number;
}

export default defineComponent({
  name: 'App',
  components: { MessageLine, MessageGroup, VersionDisplay },
  data() {
    return {
      session_id: '1',
      domain: '',
      loading: false,
      allowInput: true,
      result: null,
      error: null,
      messagesList: null,
      requirementGroups: [],
      relevantRequirementNums: null,
      scanTime: null,
      passed: false,
      role: null,
      version: null,
      isShowAllMessages: false,
      isShowResultOutput: false,
      isShowLogOutput: false,
      isShowCacheInfo: false,
      fetchLogCBStatus: '',
      fetchLogDLStatus: '',
      observe_rerun: false,
    } as AppData
  },
  async mounted() {
    axios
      .get(`${this.backendUrl}/api/information/`)
      .then(response => this.version = response.data)
    const params = new URLSearchParams(window.location.search)
    const domainParam = params.get('domain')
    if (domainParam) {
      this.domain = domainParam
      this.observe_rerun = params.get('observe_rerun') === 'true'
      this.startScan()
    }
  },
  computed: {
    resultClass() {
      switch(this.result?.status) {
        case 'ERROR':
          return 'alert-danger'
        case 'UNDEFINED':
          return 'alert-danger'
        case 'DONE_CHECKER':
          return 'alert-success'
        case 'CACHED_CHECKER':
          return 'alert-success'
        default:
          return 'alert-info'
      }
    },
    backendUrl() {
      // Use the same protocol and host as the client, but with backend port
      const protocol = window.location.protocol
      const hostname = window.location.hostname
      const backendPort = import.meta.env.VITE_BACKEND_PORT || 48090
      return `${protocol}//${hostname}:${backendPort}`
    },
    apiDocsUrl() {
      return `${this.backendUrl}/api/docs`
    },
    footerText() {
      return import.meta.env.VITE_FOOTER_TEXT || ''
    },
    trustedProviderMessages(): null | MessageData[] {
      if (!this.messagesList) return null
      if (!this.relevantRequirementNums) return this.messagesList
      return this.filterMessageListByNums(this.relevantRequirementNums)
    },
    groupedTrustedProviderMessages(): RequirementGroup[] {
      const flatMessages = this.trustedProviderMessages
      if (!flatMessages) return []
      const groupMap = new Map<number, RequirementGroup>()
      for (const g of this.requirementGroups) {
        groupMap.set(g.num, { num: g.num, description: g.description, messages: [], passed: true })
      }
      for (const msg of flatMessages) {
        const group = groupMap.get(msg.num)
        if (group) {
          group.messages.push({ text: msg.text, type: msg.type })
          if (msg.type === 2) group.passed = false
        }
      }
      return [...groupMap.values()].filter(g => g.messages.length > 0)
    },
    trustedProviderStatus() {
      return this.passed ? 'text-green': 'text-red'
    },
    displayAllMessagesTitle(): string {
      return this.isShowAllMessages ? 'Hide all messages' : 'Show all messages'
    },
    displayResultOutputTitle(): string {
      return this.isShowResultOutput ? 'Hide JSON output' : 'Show JSON output'
    },
    displayLogOutputTitle(): string {
      return this.isShowLogOutput ? 'Hide log output' : 'Show log output'
    }
  },
  methods: {
    async startScan(skip_cache = false) {
      this.loading = true
      this.allowInput = false
      this.result = null
      this.messagesList = null
      this.error = null
      this.clearFields()
      this.scanWork(skip_cache)
    },
    async scanWork(skip_cache = false) {
      try {
        let skipCache = false
        if (typeof skip_cache === 'boolean') {
          skipCache = skip_cache
        }

        this.error = null
        const url = `?domain=${encodeURIComponent(this.domain)}` + (this.observe_rerun ? '&observe_rerun=true' : '')
        history.replaceState(null, '', url)
        const response = await axios.post(`${this.backendUrl}/api/scan/start`, {
          domain: this.domain,
          session_id: this.session_id,
          skip_cache: skipCache,
          observe_rerun: this.observe_rerun,
        })

        if ( skipCache ) {
          this.observe_rerun = true
        }

        this.result = this.loading ? response.data: null
        if (this.result?.domain) {
          this.domain = this.result.domain
        }
        if (['DONE_CHECKER', 'CACHED_CHECKER'].includes(this.result?.status)) {
          this.observe_rerun = false
          const parsedResultsChecker = this.parseResultsChecker(this.result.results_checker)
          this.extractMessagesFromResultsChecker(parsedResultsChecker)
          this.setScanTime(parsedResultsChecker)
          this.setPassed(parsedResultsChecker)
          this.setRole(parsedResultsChecker)
          setTimeout(() => {
            this.initializeListeners()
          })
        } else {
          this.clearFields()
        }
      } catch (err: any) {
        this.clearFields()
        this.result = null
        this.error = err.response?.data?.detail || err.message || 'An error occurred while starting the scan'
        if (err.response?.data?.detail[0]?.msg) {
          this.error = `${err.response?.data?.detail[0]?.input}: ${err.response?.data?.detail[0]?.msg}`
        }
      } finally {
        if (['INITIALIZED', 'RUNNING_CHECKER'].includes(this.result?.status) ) {
          if (this.loading) {
            setTimeout(this.scanWork, 3000)
          }
        } else {
          this.loading = false
        }
      }
    },
    rescan() {
      this.startScan(true)
    },
    reset() {
      this.observe_rerun = false
      this.loading = false
      this.allowInput = true
      this.result = null
      this.error = null
      this.clearFields()
      history.replaceState(null, '', window.location.pathname)
    },
    clearFields() {
      this.messagesList = null
      this.requirementGroups = []
      this.relevantRequirementNums = null
      this.scanTime = null
      this.passed = false
      this.isShowAllMessages = false
      this.isShowResultOutput = false
      this.isShowLogOutput = false
      this.isShowCacheInfo = false
      this.fetchLogCBStatus = ''
      this.fetchLogDLStatus = ''
    },
    parseResultsChecker(results_checker: string): ResultCheckerData {
      return JSON.parse(results_checker)
    },
    setScanTime(parsedResultsChecker: ResultCheckerData) {
      if (parsedResultsChecker?.date) {
        // toISOString always return UTC, but that is not well readable for anyone not living close to UTC
        // the use-case is: user starts a scan or gets it from the cache and wants to recognize if thats the result of a scan just started, or how old it is
        // d.toLocaleString('sv') results an ISO format string in the local time zone (a widely used method)
        const d = new Date(parsedResultsChecker.date)
        this.scanTime = d.toLocaleString('sv', {timeZoneName: 'longOffset'}).replace(' GMT', '')
      }
    },
    setPassed(parsedResultsChecker: ResultCheckerData) {
      this.passed = parsedResultsChecker?.domains?.[0]?.passed ?? false
    },
    setRole(parsedResultsChecker: ResultCheckerData) {
      const rawRole = parsedResultsChecker?.domains?.[0]?.role ?? null
      if (!rawRole) {
        // not a CSAF provider
        this.role = null
        return
      }
      let role = rawRole.replace('csaf', 'CSAF').replaceAll('_', ' ')
      role = role.replace(/\b\w/g, (c: string) => c.toUpperCase())
      this.role = role
    },
    initializeListeners() {
      const allMessagesRef = this.$refs.allMessagesRef as HTMLElement
      allMessagesRef?.addEventListener('show.bs.collapse', () => { this.isShowAllMessages = true })
      allMessagesRef?.addEventListener('hide.bs.collapse', () => { this.isShowAllMessages = false })
      allMessagesRef?.addEventListener('shown.bs.collapse', () => { allMessagesRef.scrollIntoView({ behavior: 'smooth', block: 'nearest' }) })
      const resultOutputRef = this.$refs.resultOutputRef as HTMLElement
      resultOutputRef?.addEventListener('show.bs.collapse', () => { this.isShowResultOutput = true })
      resultOutputRef?.addEventListener('hide.bs.collapse', () => { this.isShowResultOutput = false })
      resultOutputRef?.addEventListener('shown.bs.collapse', () => { resultOutputRef.scrollIntoView({ behavior: 'smooth', block: 'nearest' }) })
      const logOutputRef = this.$refs.logOutputRef as HTMLElement
      logOutputRef?.addEventListener('show.bs.collapse', () => { this.isShowLogOutput = true })
      logOutputRef?.addEventListener('hide.bs.collapse', () => { this.isShowLogOutput = false })
      logOutputRef?.addEventListener('shown.bs.collapse', () => { logOutputRef.scrollIntoView({ behavior: 'smooth', block: 'nearest' }) })
    },
    extractMessagesFromResultsChecker(results_checker: ResultCheckerData) {
      const domain = results_checker.domains?.[0]
      if (domain?.requirements) {
        this.extractMessages(domain.requirements)
        const evaluatedRules = domain.evaluated_rules
        if (evaluatedRules) {
          this.relevantRequirementNums = relevantRequirements(evaluatedRules)
        }
      } else {
        this.messagesList = null
      }
    },
    extractMessages(requirements: {num: number, description: string, messages: {text: string, type: number}[]}[]) {
      this.messagesList = []
      this.requirementGroups = []
      for (const req of requirements) {
        const msgs = req.messages ?? []
        this.requirementGroups.push({ num: req.num, description: req.description ?? '', messages: msgs })
        for (const msg2 of msgs) {
          this.messagesList.push({type: msg2.type, text: msg2.text, num: req.num })
        }
      }
    },
    filterMessageListByNums(nums: number[]): MessageData[] {
      return this.messagesList?.filter((msg: MessageData) => nums.includes(msg.num)) ?? []
    },
    async fetchLog(): Promise<string> {
      let output = this.result?.runtime_output
      if (this.result?.runtime_output_capped) {
        const response = await axios.post(`${this.backendUrl}/api/scan/start`, {
          domain: this.domain,
          session_id: this.session_id,
          max_lines: -1
        }, { timeout: 20000 })
        output = response?.data?.runtime_output
      }
      // runtime_output is a list, join it by newlines
      return output?.join('\n') ?? ''
    },
    copyToClipboard(text: string) {
      if (navigator.clipboard) {
        // This is the "normal" modern method, but does not work with HTTP (development setups)
        navigator.clipboard.writeText(text)
      } else {
        // Fallback to old method for development setups using HTTP
        const el = document.createElement('textarea')
        el.value = text
        document.body.appendChild(el)
        el.select()
        document.execCommand('copy')
        document.body.removeChild(el)
      }
    },
    copyResultToClipboard() {
      // results_checker is a string (not a JSON object), pass it directly
      this.copyToClipboard(this.result?.results_checker ?? '')
    },
    async copyLogToClipboard() {
      this.fetchLogCBStatus = 'loading'
      try {
        const output = await this.fetchLog()
        this.copyToClipboard(output)
        this.fetchLogCBStatus = 'done'
      } catch (err: any) {
        this.fetchLogCBStatus = 'error'
        console.error(err)
      }
    },
    sanitizeFilename(name: string): string {
      return name.replace(/^https?:\/\//, '').replace(/[^a-zA-Z0-9._-]/g, '_')
    },
    downloadJson() {
      const blob = new Blob([this.result?.results_checker ?? ''], { type: 'application/json' })
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `${this.sanitizeFilename(this.domain ?? '')}-result.json`
      a.click()
      URL.revokeObjectURL(a.href)
    },
    async downloadLog() {
      this.fetchLogDLStatus = 'loading'
      try {
        const output = await this.fetchLog()
        const blob = new Blob([output], { type: 'text/plain' })
        const a = document.createElement('a')
        a.href = URL.createObjectURL(blob)
        a.download = `${this.sanitizeFilename(this.domain ?? '')}-log.txt`
        a.click()
        URL.revokeObjectURL(a.href)
        this.fetchLogDLStatus = 'done'
      } catch (err: any) {
        this.fetchLogDLStatus = 'error'
        console.error(err)
      }
    },
    formatTime(ts: number) {
      return new Date(ts * 1000).toLocaleString()
    },
    formatDuration(startTime: number, endTime: number) {
      if (endTime === 0) {
        endTime = Date.now() / 1000
      }
      const duration = endTime - startTime
      const days = Math.floor(duration / 86400);
      const hours = Math.floor((duration % 86400) / 3600)
      const minutes = Math.floor((duration % 3600) / 60)
      const seconds = Math.floor((duration % 60))

      return [
          days && `${days}d`,
          hours && `${hours}h`,
          minutes && `${minutes}m`,
          seconds && `${seconds}s`,
          !days && !hours && !minutes && !seconds && '0s'
      ]
          .filter(Boolean)
          .join(' ')
    }
  }
})
</script>

<style scoped>
  #app {
    background-color: #f1f1f1;
    min-height: 100vh;
  }
.text-green {
  color: var(--bs-success);
}
.text-red {
  color: var(--bs-danger);
}
.small-margin-top {
  margin-top: 15px;
}
.cache-info-btn {
  background: none;
  border: none;
  padding: 0;
  font-size: 0.8rem;
  color: var(--bs-secondary);
  cursor: pointer;
  vertical-align: middle;
}
.cache-info-btn:hover {
  color: var(--bs-primary);
}
.cache-info-circle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2ex;
  height: 2ex;
  border-radius: 1ex;
  border: thin solid;
  font-size: 0.8rem;
  vertical-align: middle;
}
.cache-info-box {
  font-size: 0.875rem;
  color: var(--bs-secondary);
  border-left: 3px solid var(--bs-secondary);
  padding-left: 0.75rem;
}
.log-header {
  margin-top: 7px;
}
.medium-font-size {
  font-size: 1.3rem;
}
.log-card-size {
  max-height: 510px;
}
</style>
