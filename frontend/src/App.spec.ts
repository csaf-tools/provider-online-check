// SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
// Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
//
// SPDX-License-Identifier: Apache-2.0

import { beforeEach, describe, expect, test, vi } from 'vitest'
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
        vi.spyOn(axios, 'post').mockImplementation(
            () => new Promise(resolve =>
            {
                return resolve({
                    data: {
                        status: "CACHED_CHECKER",
                        results_checker: '{ "domains": [{ "requirements": [{ "messages": [{ "text": "Test1", "type": 0 }], "num": 12 }] }] }'
                    }
                }
            )}
        ))
        app.vm.domain = "Test"
        app.vm.startScan()
        await flushPromises()
        expect(app.vm.loading).toBe(false)
        expect(app.vm.result?.status).toBe('CACHED_CHECKER')
        expect(app.vm.messagesList).toStrictEqual([{text: 'Test1', type: 0, num: 12}])

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
    test('trustedProviderMessages with one message', () => {
        app.vm.messagesList = [{ text: "Test1", type: 0, num: 1}]
        expect(app.vm.trustedProviderMessages).toStrictEqual([
            { text: "Test1", type: 0, num: 1}
        ])
    })
    test('trustedProviderMessages req 8-10', () => {
        app.vm.messagesList = [
            { text: "Test8", type: 0, num: 8 },
            { text: "Test9", type: 2, num: 9 },
            { text: "Test10", type: 2, num: 10 }
        ]
        expect(app.vm.trustedProviderMessages).toStrictEqual([
            { text: "Test8", type: 0, num: 8 }
        ])
        app.vm.messagesList = [
            { text: "Test8", type: 2, num: 8 },
            { text: "Test9", type: 0, num: 9 },
            { text: "Test10", type: 2, num: 10 }
        ]
        expect(app.vm.trustedProviderMessages).toStrictEqual([
            { text: "Test9", type: 0, num: 9 }
        ])
        app.vm.messagesList = [
            { text: "Test8", type: 2, num: 8 },
            { text: "Test9", type: 2, num: 9 },
            { text: "Test10", type: 0, num: 10 }
        ]
        expect(app.vm.trustedProviderMessages).toStrictEqual([
            { text: "Test10", type: 0, num: 10 }
        ])
        app.vm.messagesList = [
            { text: "Test8", type: 2, num: 8 },
            { text: "Test9", type: 2, num: 9 },
            { text: "Test10", type: 2, num: 10 }
        ]
        expect(app.vm.trustedProviderMessages).toStrictEqual([
            { text: "Test8", type: 2, num: 8 },
            { text: "Test9", type: 2, num: 9 },
            { text: "Test10", type: 2, num: 10 }
        ])
    })
    test("trustedProviderMessages dir-based vs ROLIE", () => {
        app.vm.messagesList = [
            { text: "Test11", type: 0, num: 11 },
            { text: "Test15", type: 2, num: 15 }
        ]
        expect(app.vm.trustedProviderMessages).toStrictEqual([
            { text: "Test11", type: 0, num: 11 }
        ])
        app.vm.messagesList = [
            { text: "Test11", type: 2, num: 11 },
            { text: "Test15", type: 0, num: 15 }
        ]
        expect(app.vm.trustedProviderMessages).toStrictEqual([
            { text: "Test15", type: 0, num: 15 }
        ])
        app.vm.messagesList = null;
        expect(app.vm.trustedProviderMessages).toBe(null)
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
        expect(app.vm.initializedListeners).toBe(true)
    })
    test("downloadJson triggers download with correct filename and content", async () => {
        // mock to intercept the click event of the new a element
        const anchor = document.createElement('a')
        vi.spyOn(anchor, 'click').mockImplementation(() => {})
        vi.spyOn(document, 'createElement').mockReturnValue(anchor)
        // required to capture the output
        vi.spyOn(URL, 'createObjectURL').mockReturnValue('blob:mock')

        app.vm.domainRescan = 'example.com'
        app.vm.result = { results_checker: '{"version": "3.5.1}' }
        app.vm.downloadJson()

        expect(anchor.download).toBe('example.com-result.json')
        expect(anchor.click).toHaveBeenCalled()
        const blob = vi.mocked(URL.createObjectURL).mock.calls[0][0] as Blob
        expect(await blob.text()).toBe('{"version": "3.5.1}')
    })
})
