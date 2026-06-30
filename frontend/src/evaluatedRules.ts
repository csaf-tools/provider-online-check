// SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
// Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
//
// SPDX-License-Identifier: Apache-2.0

export interface EvaluatedRule {
  condition: 'all' | 'one'
  requirement?: number
  passed?: boolean
  includes?: EvaluatedRule[]
}

function branchPassed(rule: EvaluatedRule): boolean {
  // checks recursively if the branch has passed == true
  if (rule.requirement) {
    return rule.passed === true
  }
  if (rule.condition === 'all') {
    return (rule.includes ?? []).every(branchPassed)
  }
  return (rule.includes ?? []).some(branchPassed)
}

export function relevantRequirements(rule: EvaluatedRule): number[] {
  // returns all the relevant requirements that have lead to the overall passed-result
  if (rule.requirement) {
    return [rule.requirement]
  }

  if (rule.condition === 'all') {
    // include all the requirements under this rule, regardless of their passed-status
    return (rule.includes ?? []).flatMap(relevantRequirements)
  }

  if (rule.condition === 'one') {
    // condition 'one': show the first branch that passed
    const winner = (rule.includes ?? []).find(branchPassed)
    if (winner) {
      return relevantRequirements(winner)
    }
    // else: return all, see below
  }

  // no conditition passed: show all branches so the users see what failed
  return (rule.includes ?? []).flatMap(relevantRequirements)
}
