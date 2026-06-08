// SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
// Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
//
// SPDX-License-Identifier: Apache-2.0

import { beforeEach, describe, expect, test } from 'vitest'
import { mount } from '@vue/test-utils'
import MessageLine from './MessageLine.vue'

describe("Testing MessageLine...", () => {
    let message = mount(MessageLine , {props: { type: 0}})
    beforeEach(()=> {
        message = mount(MessageLine , {props: { type: 0}})
    })
    test('messageClass', () => {
        expect(message.vm.messageClass).toBe('text-green')
        message = mount(MessageLine , {props: { type: 1 }})
        expect(message.vm.messageClass).toBe('text-orange') 
        message = mount(MessageLine , {props: { type: 2 }})
        expect(message.vm.messageClass).toBe('text-red')
        message = mount(MessageLine , {props: { type: -1 }})
        expect(message.vm.messageClass).toBe('')
    })
})
