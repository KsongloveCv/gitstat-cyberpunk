import { execSync } from 'child_process'
import { readFileSync, writeFileSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = join(__dirname, '..')

try {
  const tag = execSync('git describe --tags --abbrev=0', {
    encoding: 'utf-8',
    cwd: root
  }).trim().replace(/^v/, '')

  const pkgPath = join(root, 'package.json')
  const pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'))
  pkg.version = tag
  writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n', 'utf-8')

  console.log(`✓ package.json version → ${tag}`)
} catch (e) {
  console.error('✗ failed to sync version:', e.message)
  process.exit(1)
}
