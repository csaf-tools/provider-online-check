<!--
SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
Software-Engineering: 2026 Intevation GmbH <https://intevation.de>

SPDX-License-Identifier: Apache-2.0
-->

<template>
  <div id="app">
    <nav class="navbar navbar-dark bg-dark">
      <div class="container-fluid">
        <span class="navbar-brand mb-0 h1">CSAF Provider Scan <span class="badge bg-warning text-dark ms-2">Beta</span></span>
      </div>
    </nav>

    <div class="container mt-5">
      <div class="row justify-content-center">
        <div class="col-md-12">
          <div class="card shadow">
            <div class="card-body">
              <h2 class="card-title mb-4">Scan a Domain or PMD<span class="badge bg-warning ms-2" style="font-size: 0.4em; vertical-align: middle;">Experimental</span></h2>

              <form @submit.prevent="startScan">
                <div class="mb-3">
                  <input
                    type="text"
                    class="form-control"
                    id="domainInput"
                    v-model="domain"
                    placeholder="example.com"
                    required
                  >
                  <div class="form-text">Enter a domain to scan a CSAF provider</div>
                  <VersionDisplay :checkerVersion="version?.csaf_checker_version"
                                  :provider-version="version?.csaf_provider_version"
                                  :validator-version="version?.csaf_validator_version"
                  />
                </div>

                <button
                  type="submit"
                  class="btn btn-primary"
                >
                  Start Scan
                </button>
              </form>

              <div class="alert alert-light mt-4" role="alert" v-show="domainRescan">
                  {{ loading ? 'Scanning': 'Done'}} domain or PMD: {{ domainRescan }}
                  <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                  <span v-else>✔</span>
              </div>

              <!-- display of requirements messages -->
              <div v-if="messagesList" class="alert alert-light mt-4">
                <div v-if="result?.status === 'DONE_CHECKER'">
                  <h3 class="alert-heading">Scan Done</h3>
                </div>
                <div v-else-if="result?.status === 'CACHED_CHECKER'">
                  <h3 class="alert-heading">Scan found in cache</h3>
                </div>

                <div v-show="scanTime">
                  Scan Time: {{ scanTime }}
                </div>

                <h4 :class="trustedProviderStatus" class="small-margin-top medium-font-size">
                  <span v-if="trustedProviderStatus === 'text-green'">PASSED:</span>
                  <span v-else>FAILED:</span>
                  {{ role }}
                </h4>
                <MessageGroup
                  v-for="group of groupedTrustedProviderMessages"
                  :key="group.num"
                  :num="group.num"
                  :description="group.description"
                  :messages="group.messages"
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
                    <h5 class="card-title">All messages:</h5>
                    <div class="card-text log-card-size overflow-scroll">
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
                      <h5 class="me-auto log-header">Result of the checker:</h5>
                      <button class="btn btn-sm btn-outline-secondary" @click="copyResultToClipboard">Copy to clipboard</button>
                      <button class="btn btn-sm btn-outline-secondary" @click="downloadJson">Download</button>
                    </div>
                    <div class="card-text log-card-size overflow-scroll">
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
                      <h5 class="me-auto log-header">Log output:</h5>
                      <button class="btn btn-sm btn-outline-secondary" @click="copyLogToClipboard">Copy to clipboard</button>
                      <button class="btn btn-sm btn-outline-secondary" @click="downloadLog">Download</button>
                    </div>
                    <div class="card-text log-card-size overflow-scroll">
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
                    <h5 class="alert-heading">Scan started...</h5>
                    <pre>{{ result.results_checker }}</pre>
                  </div>
                  <div v-if="result.status === 'RUNNING_CHECKER'">
                    <h5 class="alert-heading">Scan Running...</h5>
                    <h6 class="alert-heading">Files scanned - {{ result.files_checked }}</h6>
                    <h6 class="alert-heading">Latest file scanned - {{ result.latest_file_checked }}</h6>
                    <pre>{{ result.results_checker }}</pre>
                  </div>
                  <div v-if="result.status === 'PAUSED'">
                    <h5 class="alert-heading">Scan paused</h5>
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
        <div class="col-md-12">
          <div class="card">
            <div class="card-body">
              <h5 class="card-title">About</h5>
              <p class="card-text">
                This is an experimental tool that scans domains for <a href="https://www.csaf.io" target="_blank">CSAF</a> (Common Security Advisory Framework)
                provider metadata and checks its validity. Results may vary.
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
import VersionDisplay from './VersionDisplay.vue';

interface ResultCheckerData {
  domains: {
    requirements: {num: number, description: string, messages: {text: string, type: number}[]}[],
    passed: boolean;
    role: string;
  }[];
  date: string;
}

interface RequirementGroup {
  num: number;
  description: string;
  messages: { text: string; type: number }[];
}

interface AppData {
  session_id: string;
  domain: string;
  domainRescan: string | null;
  loading: boolean;
  initializedListeners: boolean;
  result: any;
  error: any;
  messagesList: null | MessageData[];
  requirementGroups: RequirementGroup[];
  scanTime: null | string;
  passed: boolean;
  role: string | null;
  isShowAllMessages: boolean;
  isShowResultOutput: boolean;
  isShowLogOutput: boolean;
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
      domainRescan: null,
      loading: false,
      initializedListeners: false,
      result: null,
      error: null,
      messagesList: null,
      requirementGroups: [],
      scanTime: null,
      passed: false,
      role: null,
      version: null,
      isShowAllMessages: false,
      isShowResultOutput: false,
      isShowLogOutput: false
    } as AppData
  },
  async mounted() {
    axios
      .get(`${this.backendUrl}/api/information/`)
      .then(response => this.version = response.data)
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
    trustedProviderMessages() {
      if (this.messagesList) {
        const trustedProviderMessages = []

        // requirements 1 (Valid CSAF document), 2 (Filename), 3 (TLS), 4 (TLP:WHITE)
        // Show all messages
        trustedProviderMessages.push(...this.filterMessageListByNums([1, 2, 3, 4]))

        // requirements 5 (TLP:AMBER and TLP:RED), 6 (Redirects) and 7 (provider-metadata.json)
        // Show all messages
        trustedProviderMessages.push(...this.filterMessageListByNums([5, 6, 7]))

        // requirements min one of 8 (security.txt), 9 (Well-known URL for provider-metadata.json), 10 (DNS path)
        // One must succeed, then show that message, else show all messages
        const req8Messages = this.filterMessageListByNums([8])
        const req9Messages = this.filterMessageListByNums([9])
        const req10Messages = this.filterMessageListByNums([10])
        if (req8Messages.length > 0  && req8Messages.filter((msg:MessageData) => msg.type === 2).length === 0) {
          trustedProviderMessages.push(...req8Messages)
        } else if (req9Messages.length > 0  && req9Messages.filter((msg:MessageData) => msg.type === 2).length === 0) {
          trustedProviderMessages.push(...req9Messages)
        } else if (req10Messages.length > 0  && req10Messages.filter((msg:MessageData) => msg.type === 2).length === 0) {
          trustedProviderMessages.push(...req10Messages)
        } else {
          trustedProviderMessages.push(...req8Messages, ...req9Messages, ...req10Messages)
        }

        // requirements dir based 11 (One folder per year), 12 (index.txt), 13 (changes.csv), 14 (Directory listings)
        //           or ROLIE based 15 (ROLIE feed), 16 (ROLIE service document), 17 (ROLIE category document)
        // Show the dir-based messages or show the ROLIE based messages
        const dirBaseMessages = this.filterMessageListByNums([11, 12, 13, 14])
        const rolieBaseMessages = this.filterMessageListByNums([15, 16, 17])
        if (rolieBaseMessages.filter((msg:MessageData) => msg.type === 2).length
            <= dirBaseMessages.filter((msg: MessageData) => msg.type === 2).length) {
          trustedProviderMessages.push(...rolieBaseMessages)
        } else {
          trustedProviderMessages.push(...dirBaseMessages)
        }

        // requirements 18 (Integrity), 19 (Signatures), 20 (Public OpenPGP Key)
        // Show all messages
        trustedProviderMessages.push(...this.filterMessageListByNums([18, 19, 20]))
        return trustedProviderMessages
      }
      return null
    },
    groupedTrustedProviderMessages(): RequirementGroup[] {
      const flatMessages = this.trustedProviderMessages
      if (!flatMessages) return []
      const groupMap = new Map<number, RequirementGroup>()
      for (const g of this.requirementGroups) {
        groupMap.set(g.num, { num: g.num, description: g.description, messages: [] })
      }
      for (const msg of flatMessages) {
        const group = groupMap.get(msg.num)
        if (group) {
          group.messages.push({ text: msg.text, type: msg.type })
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
    async startScan() {
      this.domainRescan = null
      this.scanWork()
    },
    async scanWork() {
      if (!this.domainRescan) {
        this.domainRescan = this.domain
        this.domain = ''
        this.loading = true
        this.result = null
        this.messagesList = null
        this.error = null
        this.clearFields()
      }

      try {
        const response = await axios.post(`${this.backendUrl}/api/scan/start`, {
          domain: this.domainRescan,
          session_id: this.session_id
        })
        this.result = response.data
        if (['DONE_CHECKER', 'CACHED_CHECKER'].includes(this.result?.status)) {
          const parsedResultsChecker = this.parseResultsChecker(this.result.results_checker)
          this.extractMessagesFromResultsChecker(parsedResultsChecker)
          this.setScanTime(parsedResultsChecker)
          this.setPassed(parsedResultsChecker)
          this.setRole(parsedResultsChecker)
          if (!this.initializedListeners) {
            setTimeout(() => {
              this.initializeListeners()
            })
          }
        } else {
          this.clearFields()
        }
      } catch (err: any) {
        this.clearFields()
        this.error = err.response?.data?.detail || err.message || 'An error occurred while starting the scan'
        if (err.response?.data?.detail[0]?.msg) {
          this.error = `${err.response?.data?.detail[0]?.input}: ${err.response?.data?.detail[0]?.msg}`
        }
      } finally {
        if (['INITIALIZED', 'RUNNING_CHECKER'].includes(this.result?.status) ) {
          setTimeout(this.scanWork, 3000)
        } else {
          this.loading = false
        }
      }
    },
    clearFields() {
      this.messagesList = null
      this.requirementGroups = []
      this.scanTime = null
      this.passed = false
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
      this.passed = parsedResultsChecker?.domains?.[0]?.passed ?? false;
    },
    setRole(parsedResultsChecker: ResultCheckerData) {
      this.role = parsedResultsChecker?.domains?.[0]?.role ?? "Unknown Role";
      this.role = this.role.replace('csaf', 'CSAF').replaceAll('_', ' ');
      this.role = this.role.replace(/\b\w/g, (c: string) => c.toUpperCase());
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
      this.initializedListeners = true
    },
    extractMessagesFromResultsChecker(results_checker: ResultCheckerData) {
      if (results_checker.domains?.[0]?.requirements) {
        this.extractMessages(results_checker.domains[0].requirements)
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
    copyLogToClipboard() {
      // runtime_output is a list, join it by newlines
      this.copyToClipboard(this.result?.runtime_output?.join('\n') ?? '')
    },
    downloadJson() {
      const blob = new Blob([this.result?.results_checker ?? ''], { type: 'application/json' })
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `${this.domainRescan}-result.json`
      a.click()
      URL.revokeObjectURL(a.href)
    },
    downloadLog() {
      const blob = new Blob([this.result?.runtime_output?.join('\n') ?? ''], { type: 'text/plain' })
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `${this.domainRescan}-log.txt`
      a.click()
      URL.revokeObjectURL(a.href)
    },
    formatTime(ts: number) {
      return new Date(ts * 1000).toLocaleString()
    }
  }
})
</script>

<style scoped>
#app {
  min-height: 100vh;
  background-color: #f8f9fa;
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
