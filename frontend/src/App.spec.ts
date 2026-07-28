// SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
// Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
//
// SPDX-License-Identifier: Apache-2.0

import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import App from './App.vue'
import axios from 'axios'

describe("Testing App...", () => {

    let app: any
    beforeEach(()=> {
        vi.spyOn(axios, "get").mockImplementation(
            () => new Promise(resolve => resolve({}))
        )
        app = mount(App)
    })
    afterEach(() => {
        vi.restoreAllMocks()
    })

    test('extractMessages', () => {
        app.vm.extractMessages([{ messages: [{text: "Test1", type: 0}], num: 11}])
        expect(app.vm.messagesList).toStrictEqual([{text: "Test1", type: 0, num:11}])
        app.vm.extractMessages([{messages: undefined}])
        expect(app.vm.messagesList).toStrictEqual([])
    })
    test('extractMessagesFromResultsChecker with requirements null', () => {
        app.vm.extractMessagesFromResultsChecker(
            { "domains": [{"requirements": null}]}
        )
        expect(app.vm.messagesList).toBe(null)
    })
    test('extractMessagesFromResultsChecker with object', () => {
        app.vm.extractMessagesFromResultsChecker(
            { "domains": [{"requirements": [{ "messages": [{"text": "Test1", "type": 0}], "num": 11}]}]}
        )
        expect(app.vm.messagesList).toStrictEqual([{text: "Test1", type: 0, num: 11}])
    })
    test('resultClass', () => {
        const test_oracle = [
            ['ERROR', 'alert-danger'],
            ['UNDEFINED', 'alert-danger'],
            ['DONE_CHECKER', 'alert-success'],
            ['CACHED_CHECKER', 'alert-success'],
            ['DEFAULT', 'alert-info']
        ]
        for (const pair of test_oracle) {
            app.vm.result = { 'status': pair[0]}
            expect(app.vm.resultClass).toBe(pair[1])
        }
    })
    test('backendUrl and apiDocsUrl', () => {
        const protocol = window.location.protocol
        const hostname = window.location.hostname
        vi.stubEnv('VITE_BACKEND_PORT', undefined)
        app = mount(App)
        expect(app.vm.backendUrl).toBe(`${protocol}//${hostname}:48090`)
        expect(app.vm.apiDocsUrl).toBe(`${protocol}//${hostname}:48090/api/docs`)
        vi.stubEnv('VITE_BACKEND_PORT', "33333")
        app = mount(App)
        expect(app.vm.backendUrl).toBe(`${protocol}//${hostname}:33333`)
        expect(app.vm.apiDocsUrl).toBe(`${protocol}//${hostname}:33333/api/docs`)

    })
    test('footerText empty', () => {
        vi.stubEnv('VITE_FOOTER_TEXT', 'FooterTest1')
        app = mount(App)
        expect(app.vm.footerText).toBe('FooterTest1')
        vi.stubEnv('VITE_FOOTER_TEXT', undefined)
        app = mount(App)
        expect(app.vm.footerText).toBe('')

    })
    test('startScan RUNNING', async () => {
        vi.spyOn(axios, 'post').mockImplementation(
            () => new Promise(resolve => resolve({data: {status: "RUNNING" }}))
        );
        app.vm.domain = "Test"
        app.vm.startScan()
        await flushPromises()
        expect(app.vm.loading).toBe(false)
        expect(app.vm.result?.status).toBe('RUNNING')
    })
    test('startScan CACHED_CHECKER', async () => {
        app.vm.domain = "EXAMPLE.com"
        vi.spyOn(axios, 'post').mockImplementation(
            () => new Promise(resolve =>
            {
                return resolve({
                    data: {
                        status: "CACHED_CHECKER",
                        domain: "example.com",
                        results_checker: '{ "domains": [{ "requirements": [{ "messages": [{ "text": "Test1", "type": 0 }], "num": 12 }] }] }'
                    }
                }
            )}
        ))
        app.vm.startScan()
        expect(app.vm.domain).toBe('EXAMPLE.com')
        await flushPromises()
        expect(app.vm.loading).toBe(false)
        expect(app.vm.result?.status).toBe('CACHED_CHECKER')
        expect(app.vm.messagesList).toStrictEqual([{text: 'Test1', type: 0, num: 12}])
        expect(app.vm.domain).toBe('example.com')

    })
    test('startScan DONE_CHECKER not a CSAF provider', async () => {
        vi.spyOn(axios, 'post').mockResolvedValue({
            data: {
                status: "DONE_CHECKER",
                domain: "example.com",
                results_checker: JSON.stringify({
                    domains: [{
                        passed: false,
                        requirements: [{
                            num: 0,
                            description: "Invalid provider metadata",
                            messages: [
                                { type: 1, text: "Fetching provider-metadata.json failed: 404 Not Found" },
                                { type: 2, text: "Could not parse the Provider-Metadata.json of: example.com" }
                            ]
                        }]
                    }],
                    date: "2026-06-24T15:13:40Z"
                })
            }
        })
        app.vm.startScan()
        await flushPromises()
        expect(app.vm.role).toBeNull()
        expect(app.vm.messagesList).toHaveLength(2)
        expect(app.find('.text-warning').exists()).toBe(true)
        expect(app.find('.text-warning').text()).toContain('No CSAF endpoint found')
    })
    test('startScan ERROR', async () => {
        vi.spyOn(axios, 'post').mockImplementation(
            () => new Promise(() =>
            {
                throw new Error("Test error A")
            }
        ))
        app.vm.domain = "Test"
        app.vm.startScan()
        await flushPromises()
        expect(app.vm.loading).toBe(false)
        expect(app.vm.error).toBe('Test error A')

    })
    test('filterMessageListByNums', () => {
        app.vm.messagesList = [{ text: "Test1", type: 0, num: 1 },
                            { text: "Test2", type: 2, num: 2 },
                            { text: "Test2.2", type:2, num: 2 },
                            { text: "Test3", type: 1, num: 3}]
        expect(app.vm.filterMessageListByNums([1, 2])).toStrictEqual([
            { text: "Test1", type: 0, num: 1 },
            { text: "Test2", type: 2, num: 2 },
            { text: "Test2.2", type:2, num: 2 }
        ])
        expect(app.vm.filterMessageListByNums([3])).toStrictEqual([
            { text: "Test3", type: 1, num: 3}
        ])
        expect(app.vm.filterMessageListByNums([4])).toStrictEqual([])
    })
    test('trustedProviderMessages: null messagesList returns null', () => {
        app.vm.messagesList = null
        expect(app.vm.trustedProviderMessages).toBe(null)
    })
    test('trustedProviderMessages: no evaluated_rules trail returns full messagesList', () => {
        app.vm.messagesList = [{ text: "Test1", type: 0, num: 1 }]
        app.vm.relevantRequirementNums = null
        expect(app.vm.trustedProviderMessages).toStrictEqual([{ text: "Test1", type: 0, num: 1 }])
    })
    test('trustedProviderMessages: filters to relevantRequirementNums from trail', () => {
        app.vm.messagesList = [
            { text: "msg8", type: 0, num: 8 },
            { text: "msg9", type: 2, num: 9 },
            { text: "msg15", type: 0, num: 15 },
        ]
        app.vm.relevantRequirementNums = [8, 15]
        expect(app.vm.trustedProviderMessages).toStrictEqual([
            { text: "msg8", type: 0, num: 8 },
            { text: "msg15", type: 0, num: 15 },
        ])
    })
    test('extractMessagesFromResultsChecker: sets relevantRequirementNums from evaluated_rules', () => {
        app.vm.extractMessagesFromResultsChecker({
            date: '2026-06-26T00:00:00Z',
            domains: [{
                passed: true,
                role: 'csaf_trusted_provider',
                requirements: [
                    { num: 8, description: 'security.txt', messages: [{ text: 'ok', type: 0 }] },
                    { num: 9, description: '/.well-known/csaf/provider-metadata.json', messages: [{ text: 'ok', type: 0 }] },
                ],
                evaluated_rules: {
                    condition: 'one',
                    includes: [
                        { condition: 'all', requirement: 8, passed: true },
                        { condition: 'all', requirement: 9, passed: false },
                    ]
                }
            }]
        })
        expect(app.vm.relevantRequirementNums).toStrictEqual([8])
        expect(app.vm.trustedProviderMessages).toStrictEqual([
            { text: 'ok', type: 0, num: 8 }
        ])
    })
    test("groupedTrustedProviderMessages groups messages by requirement", () => {
        app.vm.requirementGroups = [
            { num: 1, description: 'Valid CSAF documents', messages: [] },
            { num: 2, description: 'Filename', messages: [] },
        ]
        app.vm.messagesList = [
            { text: 'msg A', type: 0, num: 1 },
            { text: 'msg B', type: 0, num: 2 },
            { text: 'msg C', type: 2, num: 2 },
        ]
        const groups = app.vm.groupedTrustedProviderMessages
        expect(groups).toHaveLength(2)
        expect(groups[0]).toMatchObject({ num: 1, description: 'Valid CSAF documents' })
        expect(groups[0].messages).toHaveLength(1)
        expect(groups[1]).toMatchObject({ num: 2, description: 'Filename' })
        expect(groups[1].messages).toHaveLength(2)
    })
    test("groupedTrustedProviderMessages excludes groups with no filtered messages", () => {
        app.vm.requirementGroups = [
            { num: 1, description: 'Valid CSAF documents', messages: [] },
            { num: 2, description: 'Filename', messages: [] },
        ]
        app.vm.messagesList = [
            { text: 'msg A', type: 0, num: 1 },
        ]
        const groups = app.vm.groupedTrustedProviderMessages
        expect(groups).toHaveLength(1)
        expect(groups[0].num).toBe(1)
    })
    test("trustedProviderStatus", () => {
        app.vm.passed = true
        expect(app.vm.trustedProviderStatus).toBe('text-green')
        app.vm.passed = false
        expect(app.vm.trustedProviderStatus).toBe('text-red')
    })
    test("setScanTime", () => {
        const data = { passed: true, date:"2026-05-22T08:00:00", requirements: [] }
        app.vm.setScanTime(data)
        expect(app.vm.scanTime).toBe("2026-05-22 08:00:00+00:00")
    })
    test("setPassed", () => {
        const data = { date:"2026-05-22", domains: [{ passed: true }] }
        app.vm.setPassed(data)
        expect(app.vm.passed).toBe(true)
    })
    test("setRole: absent role stays null", () => {
        app.vm.setRole({ date: "2026-06-24", domains: [{ passed: false, requirements: [] }] })
        expect(app.vm.role).toBeNull()
    })
    test("setRole: present role is formatted", () => {
        app.vm.setRole({ date: "2026-06-24", domains: [{ passed: false, role: "csaf_trusted_provider", requirements: [] }] })
        expect(app.vm.role).toBe("CSAF Trusted Provider")
    })
    test("displayAllMessagesTitle", () => {
        expect(app.vm.displayAllMessagesTitle).toBe('Show all messages')
        app.vm.isShowAllMessages = true
        expect(app.vm.displayAllMessagesTitle).toBe('Hide all messages')
    })
    test("displayResultOutputTitle", () => {
        expect(app.vm.displayResultOutputTitle).toBe('Show JSON output')
        app.vm.isShowResultOutput = true
        expect(app.vm.displayResultOutputTitle).toBe('Hide JSON output')
    })
    test("displayLogOutputTitle", () => {
        expect(app.vm.displayLogOutputTitle).toBe('Show log output')
        app.vm.isShowLogOutput = true
        expect(app.vm.displayLogOutputTitle).toBe('Hide log output')
    })
    test("initializeListeners", () => {
        app.vm.initializeListeners()
        expect(app.vm.isShowAllMessages).toBe(false)
        expect(app.vm.isShowResultOutput).toBe(false)
        expect(app.vm.isShowLogOutput).toBe(false)
    })
    test("downloadJson triggers download with correct filename and content", async () => {
        // mock to intercept the click event of the new a element
        const anchor = document.createElement('a')
        vi.spyOn(anchor, 'click').mockImplementation(() => {})
        vi.spyOn(document, 'createElement').mockReturnValue(anchor)
        // required to capture the output
        vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock')

        app.vm.domain = 'https://example.com/.well-known/csaf/provider-metadata.json'
        app.vm.result = { results_checker: '{"version": "3.5.1}' }
        app.vm.downloadJson()

        expect(anchor.download).toBe('example.com_.well-known_csaf_provider-metadata.json-result.json')
        expect(anchor.click).toHaveBeenCalled()
        const blob = vi.mocked(URL.createObjectURL).mock.calls[0][0] as Blob
        expect(await blob.text()).toBe('{"version": "3.5.1}')
    })

    test("sanitizeFilename", () => {
        expect(app.vm.sanitizeFilename('example.com')).toBe('example.com')
        expect(app.vm.sanitizeFilename('https://example.com/.well-known/csaf/provider-metadata.json'))
            .toBe('example.com_.well-known_csaf_provider-metadata.json')
        expect(app.vm.sanitizeFilename('http://example.com/path?foo=bar'))
            .toBe('example.com_path_foo_bar')
    })

    test("formatDuration", () => {
        expect(app.vm.formatDuration(1, 90001)).toBe('1d 1h');
        expect(app.vm.formatDuration(1, 93601)).toBe('1d 2h');
        expect(app.vm.formatDuration(1, 86401)).toBe('1d'); 
        expect(app.vm.formatDuration(1, 1)).toBe('0s');
    })
})
