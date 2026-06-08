// SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
// Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
//
// SPDX-License-Identifier: Apache-2.0

import { describe, expect, test } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageGroup from './MessageGroup.vue'
import MessageLine from './MessageLine.vue'

const makeMessages = (n: number) =>
    Array.from({ length: n }, (_, i) => ({ text: `msg ${i}`, type: 0 }))

describe('MessageGroup', () => {
    test('renders requirement header', () => {
        const wrapper = mount(MessageGroup, {
            props: { num: 15, description: 'ROLIE feed', messages: makeMessages(2) },
        })
        expect(wrapper.text()).toContain('ROLIE feed')
    })

    test('shows all messages when count <= threshold', () => {
        const wrapper = mount(MessageGroup, {
            props: { num: 1, description: 'Test', messages: makeMessages(5) },
        })
        expect(wrapper.findAllComponents(MessageLine)).toHaveLength(5)
        expect(wrapper.text()).not.toContain('more message')
    })

    test('truncates to 5, expands and collapses', async () => {
        const wrapper = mount(MessageGroup, {
            props: { num: 1, description: 'Test', messages: makeMessages(10) },
        })
        expect(wrapper.findAllComponents(MessageLine)).toHaveLength(5)
        expect(wrapper.text()).toContain('5 more messages')

        await wrapper.find('.toggle-btn').trigger('click')
        // flush timers, then wait for Vue to re-render
        await new Promise(resolve => setTimeout(resolve, 0))
        await wrapper.vm.$nextTick()
        expect(wrapper.findAllComponents(MessageLine)).toHaveLength(10)
        expect(wrapper.find('.toggle-btn').text()).toContain('collapse')
        await wrapper.find('.toggle-btn').trigger('click')
        // flush timers, then wait for Vue to re-render
        await new Promise(resolve => setTimeout(resolve, 0))
        await wrapper.vm.$nextTick()
        expect(wrapper.findAllComponents(MessageLine)).toHaveLength(5)
    })

    test('shows count badges', () => {
        const messages = [
            { text: 'a', type: 0 },
            { text: 'b', type: 1 },
            { text: 'c', type: 2 },
        ]
        const wrapper = mount(MessageGroup, {
            props: { num: 1, description: 'Test', messages },
        })
        expect(wrapper.text()).toContain('1 error')
        expect(wrapper.text()).toContain('1 warning')
        // no badge for passing requirements
    })
})
