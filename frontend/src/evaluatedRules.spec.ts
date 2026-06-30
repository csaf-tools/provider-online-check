// SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
// Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
//
// SPDX-License-Identifier: Apache-2.0

import { describe, expect, test } from 'vitest'
import { relevantRequirements, type EvaluatedRule } from './evaluatedRules'
import intevation from '../tests/assets/intevation.de-result.json'
import innomic from '../tests/assets/www.innomic.com-result.json'
import isduba from '../tests/assets/isduba.github.io-result.json'
import exampleCom from '../tests/assets/example.com-result.json'

describe('relevantRequirements', () => {
  test('leaf node: passed true returns requirement number', () => {
    let rule: EvaluatedRule = { condition: 'all', requirement: 3, passed: true }
    expect(relevantRequirements(rule)).toStrictEqual([3])
    rule.condition = 'one'
    expect(relevantRequirements(rule)).toStrictEqual([3])
  })

  test('leaf node: passed false returns requirement number', () => {
    let rule: EvaluatedRule = { condition: 'all', requirement: 5, passed: false }
    expect(relevantRequirements(rule)).toStrictEqual([5])
    rule.condition = 'one'
    expect(relevantRequirements(rule)).toStrictEqual([5])
  })

  test('condition all: returns all requirement numbers regardless of passed', () => {
    const rule: EvaluatedRule = {
      condition: 'all',
      includes: [
        { condition: 'all', requirement: 1, passed: true },
        { condition: 'all', requirement: 2, passed: false },
        { condition: 'all', requirement: 3, passed: true },
      ]
    }
    expect(relevantRequirements(rule)).toStrictEqual([1, 2, 3])
  })

  test('condition one: returns only the first passing branch', () => {
    const rule: EvaluatedRule = {
      condition: 'one',
      includes: [
        { condition: 'all', requirement: 8, passed: false },
        { condition: 'all', requirement: 9, passed: true },
        { condition: 'all', requirement: 10, passed: false },
      ]
    }
    expect(relevantRequirements(rule)).toStrictEqual([9])
  })

  test('condition one: picks first branch when multiple pass', () => {
    const rule: EvaluatedRule = {
      condition: 'one',
      includes: [
        { condition: 'all', requirement: 8, passed: true },
        { condition: 'all', requirement: 9, passed: true },
        { condition: 'all', requirement: 10, passed: false },
      ]
    }
    expect(relevantRequirements(rule)).toStrictEqual([8])
  })

  test('condition one: returns all branches when none pass', () => {
    const rule: EvaluatedRule = {
      condition: 'one',
      includes: [
        { condition: 'all', requirement: 8, passed: false },
        { condition: 'all', requirement: 9, passed: false },
        { condition: 'all', requirement: 10, passed: false },
      ]
    }
    expect(relevantRequirements(rule)).toStrictEqual([8, 9, 10])
  })

  test('condition one: multi-leaf branch must have all leaves passing to count as passed', () => {
    const rule: EvaluatedRule = {
      condition: 'one',
      includes: [
        {
          condition: 'all',
          includes: [
            { condition: 'all', requirement: 11, passed: true },
            { condition: 'all', requirement: 12, passed: false }, // whole branch fails
          ]
        },
        {
          condition: 'all',
          includes: [
            { condition: 'all', requirement: 15, passed: true },
            { condition: 'all', requirement: 16, passed: true },
          ]
        },
      ]
    }
    expect(relevantRequirements(rule)).toStrictEqual([15, 16])
  })

  test('example.com: no evaluated_rules when target is not a CSAF provider', () => {
      expect((exampleCom.domains[0] as any).evaluated_rules).toBeUndefined()
    })

  test('intevation.de trail: req 8 wins, ROLIE wins -> [1-8,15-20]', () => {
    const rule = intevation.domains[0].evaluated_rules as EvaluatedRule
    expect(relevantRequirements(rule)).toStrictEqual([1, 2, 3, 4, 5, 6, 7, 8, 15, 16, 17, 18, 19, 20])
  })

  test('www.innomic.com trail: req 8 wins, dir-based wins -> [1-8,11-14]', () => {
    const rule = innomic.domains[0].evaluated_rules as EvaluatedRule
    expect(relevantRequirements(rule)).toStrictEqual([1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 14])
  })

  test('isduba.github.io trail: req 9 wins, ROLIE wins -> [1-7,9,15-20], 8 fails -> overall fail', () => {
    const rule = isduba.domains[0].evaluated_rules as EvaluatedRule
    expect(relevantRequirements(rule)).toStrictEqual([1, 2, 3, 4, 5, 6, 7, 9, 15, 16, 17, 18, 19, 20])
  })
})
