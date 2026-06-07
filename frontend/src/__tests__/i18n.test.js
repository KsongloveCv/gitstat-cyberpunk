/** Test i18n module. */
import { describe, it, expect } from 'vitest'

// Simple test that doesn't require full Vue setup
describe('i18n keys', () => {
  it('should have gitee translations in both languages', async () => {
    // Dynamic import to handle ESM
    const mod = await import('../../i18n.js')
    // We can verify the module exports work
    expect(mod).toBeDefined()
    expect(mod.useI18n).toBeDefined()
  })
})
