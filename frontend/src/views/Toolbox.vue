<template>
  <div class="toolbox-page">
    <h2 class="page-title">{{ t('toolbox.title') }}</h2>
    <p class="page-subtitle">{{ t('toolbox.subtitle') }}</p>

    <div class="tools-grid">
      <div
        v-for="tool in tools"
        :key="tool.id"
        class="tool-card"
        :class="{ expanded: activeTool === tool.id }"
        @click="toggleTool(tool.id)"
      >
        <div class="card-header">
          <span class="card-icon">{{ tool.icon }}</span>
          <span class="card-title">{{ t(`toolbox.${tool.id}.title`) }}</span>
          <span class="card-arrow">{{ activeTool === tool.id ? '▼' : '▶' }}</span>
        </div>

        <div v-if="activeTool === tool.id" class="card-body" @click.stop>

          <!-- JSON -->
          <template v-if="tool.id === 'json'">
            <textarea v-model="jsonInput" class="tool-input" rows="6" :placeholder="t('toolbox.json.placeholder')" spellcheck="false"></textarea>
            <div class="tool-actions">
              <button @click="formatJson('pretty')" class="tool-btn">{{ t('toolbox.json.format') }}</button>
              <button @click="formatJson('minify')" class="tool-btn">{{ t('toolbox.json.minify') }}</button>
              <button @click="formatJson('validate')" class="tool-btn">{{ t('toolbox.json.validate') }}</button>
              <button @click="copyResult(jsonResult)" class="tool-btn copy-btn">{{ t('toolbox.copy') }}</button>
            </div>
            <div v-if="jsonResult" class="tool-result" :class="{ error: jsonError }">{{ jsonResult }}</div>
          </template>

          <!-- Base64 -->
          <template v-if="tool.id === 'base64'">
            <textarea v-model="base64Input" class="tool-input" rows="4" :placeholder="t('toolbox.base64.placeholder')" spellcheck="false"></textarea>
            <div class="tool-actions">
              <button @click="base64Encode" class="tool-btn">{{ t('toolbox.base64.encode') }}</button>
              <button @click="base64Decode" class="tool-btn">{{ t('toolbox.base64.decode') }}</button>
              <button @click="copyResult(base64Result)" class="tool-btn copy-btn">{{ t('toolbox.copy') }}</button>
            </div>
            <div v-if="base64Result" class="tool-result" :class="{ error: base64Error }">{{ base64Result }}</div>
          </template>

          <!-- Timestamp -->
          <template v-if="tool.id === 'timestamp'">
            <div class="ts-row">
              <input v-model="tsInput" class="tool-input-inline" :placeholder="t('toolbox.timestamp.inputPlaceholder')" />
              <button @click="tsConvert" class="tool-btn">{{ t('toolbox.timestamp.convert') }}</button>
              <button @click="tsNow" class="tool-btn now-btn">{{ t('toolbox.timestamp.now') }}</button>
            </div>
            <div v-if="tsResult" class="tool-result">{{ tsResult }}</div>
          </template>

          <!-- Hash -->
          <template v-if="tool.id === 'hash'">
            <textarea v-model="hashInput" class="tool-input" rows="3" :placeholder="t('toolbox.hash.placeholder')" spellcheck="false"></textarea>
            <div class="tool-actions">
              <button @click="genHash('SHA-256')" class="tool-btn">SHA-256</button>
              <button @click="genHash('SHA-1')" class="tool-btn">SHA-1</button>
              <button @click="copyResult(hashResult)" class="tool-btn copy-btn">{{ t('toolbox.copy') }}</button>
            </div>
            <div v-if="hashResult" class="tool-result hash-result">{{ hashResult }}</div>
          </template>

          <!-- Regex -->
          <template v-if="tool.id === 'regex'">
            <input v-model="regexPattern" class="tool-input-inline regex-pattern" :placeholder="t('toolbox.regex.patternPlaceholder')" />
            <textarea v-model="regexTest" class="tool-input" rows="4" :placeholder="t('toolbox.regex.testPlaceholder')" spellcheck="false"></textarea>
            <div class="tool-actions">
              <button @click="testRegex" class="tool-btn">{{ t('toolbox.regex.test') }}</button>
            </div>
            <div v-if="regexResult" class="tool-result">
              <span v-for="(line, i) in regexResultLines" :key="i" class="regex-line">
                <template v-for="(seg, j) in line" :key="j">
                  <span :class="{ match: seg.match }">{{ seg.text }}</span>
                </template>
              </span>
              <div v-if="regexMatchCount > 0" class="match-count">{{ t('toolbox.regex.matchCount') }}: {{ regexMatchCount }}</div>
            </div>
          </template>

          <!-- Color -->
          <template v-if="tool.id === 'color'">
            <div class="color-row">
              <input v-model="colorInput" class="tool-input-inline" placeholder="#00f5ff / rgb(0,245,255) / hsl(186,100%,50%)" />
              <button @click="convertColor" class="tool-btn">{{ t('toolbox.color.convert') }}</button>
            </div>
            <div v-if="colorResult" class="tool-result color-result">
              <div class="color-preview" :style="{ backgroundColor: colorResult.hex }"></div>
              <div class="color-values">
                <div>HEX: <span class="color-val">{{ colorResult.hex }}</span></div>
                <div>RGB: <span class="color-val">{{ colorResult.rgb }}</span></div>
                <div>HSL: <span class="color-val">{{ colorResult.hsl }}</span></div>
              </div>
            </div>
          </template>

          <!-- JWT -->
          <template v-if="tool.id === 'jwt'">
            <textarea v-model="jwtInput" class="tool-input" rows="3" :placeholder="t('toolbox.jwt.placeholder')" spellcheck="false"></textarea>
            <div class="tool-actions">
              <button @click="parseJwt" class="tool-btn">{{ t('toolbox.jwt.parse') }}</button>
            </div>
            <div v-if="jwtResult" class="tool-result">
              <div v-if="jwtResult.error" class="jwt-error">{{ jwtResult.error }}</div>
              <template v-else>
                <div class="jwt-section">
                  <div class="jwt-label">Header</div>
                  <div class="jwt-json">{{ jwtResult.header }}</div>
                </div>
                <div class="jwt-section">
                  <div class="jwt-label">Payload</div>
                  <div class="jwt-json">{{ jwtResult.payload }}</div>
                  <div v-if="jwtResult.exp" class="jwt-exp" :class="{ expired: jwtResult.isExpired }">{{ jwtResult.isExpired ? t('toolbox.jwt.expired') : t('toolbox.jwt.expiresAt') }}: {{ jwtResult.exp }}</div>
                </div>
              </template>
            </div>
          </template>

          <!-- URL -->
          <template v-if="tool.id === 'url'">
            <textarea v-model="urlInput" class="tool-input" rows="3" :placeholder="t('toolbox.url.placeholder')" spellcheck="false"></textarea>
            <div class="tool-actions">
              <button @click="urlEncode" class="tool-btn">{{ t('toolbox.url.encode') }}</button>
              <button @click="urlDecode" class="tool-btn">{{ t('toolbox.url.decode') }}</button>
              <button @click="parseUrl" class="tool-btn">{{ t('toolbox.url.parse') }}</button>
              <button @click="copyResult(urlResult)" class="tool-btn copy-btn">{{ t('toolbox.copy') }}</button>
            </div>
            <div v-if="urlResult" class="tool-result">{{ urlResult }}</div>
          </template>

          <!-- UUID -->
          <template v-if="tool.id === 'uuid'">
            <div class="tool-actions">
              <button @click="genUuid(1)" class="tool-btn">1x</button>
              <button @click="genUuid(5)" class="tool-btn">5x</button>
              <button @click="genUuid(10)" class="tool-btn">10x</button>
              <button @click="genUuid(50)" class="tool-btn">50x</button>
              <button @click="copyResult(uuidResult)" class="tool-btn copy-btn">{{ t('toolbox.copy') }}</button>
            </div>
            <div v-if="uuidResult" class="tool-result">{{ uuidResult }}</div>
          </template>

          <!-- Text Diff -->
          <template v-if="tool.id === 'diff'">
            <div class="diff-columns">
              <textarea v-model="diffLeft" class="tool-input diff-input" rows="6" :placeholder="t('toolbox.diff.leftPlaceholder')" spellcheck="false"></textarea>
              <textarea v-model="diffRight" class="tool-input diff-input" rows="6" :placeholder="t('toolbox.diff.rightPlaceholder')" spellcheck="false"></textarea>
            </div>
            <div class="tool-actions">
              <button @click="computeDiff" class="tool-btn">{{ t('toolbox.diff.compare') }}</button>
            </div>
            <div v-if="diffResult.length" class="tool-result diff-result">
              <div v-for="(line, i) in diffResult" :key="i" class="diff-line" :class="line.type">{{ line.text }}</div>
            </div>
          </template>

          <!-- Markdown -->
          <template v-if="tool.id === 'markdown'">
            <div class="md-columns">
              <textarea v-model="mdInput" class="tool-input md-input" rows="10" :placeholder="t('toolbox.markdown.placeholder')" spellcheck="false"></textarea>
              <div class="md-preview" v-html="mdHtml"></div>
            </div>
          </template>

          <!-- Cron -->
          <template v-if="tool.id === 'cron'">
            <div class="cron-row">
              <input v-model="cronInput" class="tool-input-inline" :placeholder="t('toolbox.cron.placeholder')" />
              <button @click="parseCron" class="tool-btn">{{ t('toolbox.cron.parse') }}</button>
            </div>
            <div v-if="cronResult" class="tool-result">
              <div>{{ cronResult.description }}</div>
              <div v-if="cronResult.nextRuns.length" class="cron-next">
                {{ t('toolbox.cron.nextRuns') }}:
                <span v-for="(dt, i) in cronResult.nextRuns" :key="i">{{ dt }}<br/></span>
              </div>
            </div>
          </template>

          <!-- Password -->
          <template v-if="tool.id === 'password'">
            <input v-model="pwdInput" class="tool-input-inline pwd-input" type="text" :placeholder="t('toolbox.password.placeholder')" />
            <div v-if="pwdResult" class="tool-result pwd-result">
              <div class="pwd-bar"><div class="pwd-fill" :style="{ width: pwdResult.score + '%', backgroundColor: pwdResult.color }"></div></div>
              <div class="pwd-score" :style="{ color: pwdResult.color }">{{ pwdResult.label }}</div>
              <div class="pwd-details">
                <div>{{ t('toolbox.password.length') }}: {{ pwdResult.length }}</div>
                <div>{{ t('toolbox.password.hasUpper') }}: {{ pwdResult.hasUpper ? 'YES' : 'NO' }}</div>
                <div>{{ t('toolbox.password.hasLower') }}: {{ pwdResult.hasLower ? 'YES' : 'NO' }}</div>
                <div>{{ t('toolbox.password.hasDigit') }}: {{ pwdResult.hasDigit ? 'YES' : 'NO' }}</div>
                <div>{{ t('toolbox.password.hasSpecial') }}: {{ pwdResult.hasSpecial ? 'YES' : 'NO' }}</div>
                <div>{{ t('toolbox.password.crackTime') }}: {{ pwdResult.crackTime }}</div>
              </div>
            </div>
          </template>

          <!-- QR Code -->
          <template v-if="tool.id === 'qrcode'">
            <input v-model="qrInput" class="tool-input-inline" :placeholder="t('toolbox.qrcode.placeholder')" />
            <div class="tool-actions">
              <button @click="genQr" class="tool-btn">{{ t('toolbox.qrcode.generate') }}</button>
              <button v-if="qrDataUrl" @click="downloadQr" class="tool-btn copy-btn">{{ t('toolbox.qrcode.download') }}</button>
            </div>
            <div v-if="qrDataUrl" class="tool-result qr-result">
              <img :src="qrDataUrl" alt="QR Code" class="qr-img" />
            </div>
          </template>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from '../i18n'

const { t } = useI18n()

const tools = [
  { id: 'json', icon: '{ }' },
  { id: 'base64', icon: 'B64' },
  { id: 'timestamp', icon: 'CLK' },
  { id: 'hash', icon: '#HZ' },
  { id: 'regex', icon: '.*' },
  { id: 'color', icon: 'RGB' },
  { id: 'jwt', icon: 'JWT' },
  { id: 'url', icon: 'URL' },
  { id: 'uuid', icon: 'UID' },
  { id: 'diff', icon: 'DIFF' },
  { id: 'markdown', icon: 'MD' },
  { id: 'cron', icon: 'CRN' },
  { id: 'password', icon: 'PWD' },
  { id: 'qrcode', icon: 'QR' },
]

const activeTool = ref(null)
function toggleTool(id) {
  activeTool.value = activeTool.value === id ? null : id
}
function copyResult(source) {
  const val = typeof source === 'object' && source?.value ? source.value : source
  if (val) navigator.clipboard.writeText(val)
}

// ── JSON ──
const jsonInput = ref('')
const jsonResult = ref('')
const jsonError = ref(false)
function formatJson(mode) {
  jsonError.value = false
  try {
    const parsed = JSON.parse(jsonInput.value)
    if (mode === 'pretty') jsonResult.value = JSON.stringify(parsed, null, 2)
    else if (mode === 'minify') jsonResult.value = JSON.stringify(parsed)
    else jsonResult.value = t('toolbox.json.valid')
  } catch (e) {
    jsonError.value = true
    jsonResult.value = `${t('toolbox.json.invalid')}: ${e.message}`
  }
}

// ── Base64 ──
const base64Input = ref('')
const base64Result = ref('')
const base64Error = ref(false)
function base64Encode() {
  base64Error.value = false
  try { base64Result.value = btoa(unescape(encodeURIComponent(base64Input.value))) }
  catch (e) { base64Error.value = true; base64Result.value = `${t('toolbox.base64.encodeError')}: ${e.message}` }
}
function base64Decode() {
  base64Error.value = false
  try { base64Result.value = decodeURIComponent(escape(atob(base64Input.value))) }
  catch (e) { base64Error.value = true; base64Result.value = `${t('toolbox.base64.decodeError')}: ${e.message}` }
}

// ── Timestamp ──
const tsInput = ref('')
const tsResult = ref('')
function tsConvert() {
  const val = tsInput.value.trim()
  if (!val) return
  const num = Number(val)
  if (isNaN(num)) {
    const d = new Date(val)
    if (d.toString() === 'Invalid Date') { tsResult.value = t('toolbox.timestamp.invalid'); return }
    tsResult.value = `Unix: ${Math.floor(d.getTime() / 1000)}\nUTC: ${d.toISOString()}\nLocal: ${d.toLocaleString()}`
  } else {
    const ts = num > 1e12 ? num : num * 1000
    const d = new Date(ts)
    tsResult.value = `UTC: ${d.toISOString()}\nLocal: ${d.toLocaleString()}\nUnix: ${Math.floor(ts / 1000)}`
  }
}
function tsNow() {
  tsInput.value = String(Math.floor(Date.now() / 1000))
  tsConvert()
}

// ── Hash ──
const hashInput = ref('')
const hashResult = ref('')
async function genHash(algo) {
  const data = new TextEncoder().encode(hashInput.value)
  try {
    const buf = await crypto.subtle.digest(algo, data)
    hashResult.value = Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('')
  } catch (e) { hashResult.value = `${algo} error: ${e.message}` }
}

// ── Regex ──
const regexPattern = ref('')
const regexTest = ref('')
const regexResultLines = ref([])
const regexMatchCount = ref(0)
const regexResult = ref(false)
function testRegex() {
  regexResultLines.value = []; regexMatchCount.value = 0; regexResult.value = false
  try {
    const re = new RegExp(regexPattern.value, 'g')
    let total = 0
    regexResultLines.value = regexTest.value.split('\n').map(line => {
      const segs = []; let last = 0, m
      while ((m = re.exec(line)) !== null) {
        if (m.index > last) segs.push({ text: line.slice(last, m.index), match: false })
        segs.push({ text: m[0], match: true }); total++; last = m.index + m[0].length
        if (!m[0].length) re.lastIndex++
      }
      if (last < line.length) segs.push({ text: line.slice(last), match: false })
      return segs
    })
    regexMatchCount.value = total; regexResult.value = true
  } catch (e) {
    regexResultLines.value = [[{ text: `${t('toolbox.regex.error')}: ${e.message}`, match: false }]]
    regexResult.value = true
  }
}

// ── Color ──
const colorInput = ref('')
const colorResult = ref(null)
function convertColor() {
  const val = colorInput.value.trim()
  let r, g, b
  if (val.startsWith('#')) {
    const hex = val.replace('#', '')
    if (hex.length === 3) { r = parseInt(hex[0]+hex[0],16); g = parseInt(hex[1]+hex[1],16); b = parseInt(hex[2]+hex[2],16) }
    else if (hex.length === 6) { r = parseInt(hex.slice(0,2),16); g = parseInt(hex.slice(2,4),16); b = parseInt(hex.slice(4,6),16) }
    else { colorResult.value = null; return }
  } else if (val.startsWith('rgb')) {
    const m = val.match(/(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/)
    if (!m) { colorResult.value = null; return }
    r=parseInt(m[1]); g=parseInt(m[2]); b=parseInt(m[3])
  } else if (val.startsWith('hsl')) {
    const m = val.match(/(\d+)\s*,\s*(\d+)%?\s*,\s*(\d+)%?/)
    if (!m) { colorResult.value = null; return }
    [r,g,b] = hslToRgb(parseInt(m[1])/360, parseInt(m[2])/100, parseInt(m[3])/100)
  } else { colorResult.value = null; return }
  const h = `#${r.toString(16).padStart(2,'0')}${g.toString(16).padStart(2,'0')}${b.toString(16).padStart(2,'0')}`
  const [hue,sat,lit] = rgbToHsl(r,g,b)
  colorResult.value = { hex: h, rgb: `rgb(${r}, ${g}, ${b})`, hsl: `hsl(${hue}, ${sat}%, ${lit}%)` }
}
function rgbToHsl(r,g,b) {
  r/=255;g/=255;b/=255;const mx=Math.max(r,g,b),mn=Math.min(r,g,b);let h,s,l=(mx+mn)/2
  if(mx===mn){h=s=0}else{const d=mx-mn;s=l>0.5?d/(2-mx-mn):d/(mx+mn)
    switch(mx){case r:h=((g-b)/d+(g<b?6:0))/6;break;case g:h=((b-r)/d+2)/6;break;case b:h=((r-g)/d+4)/6;break}}
  return[Math.round(h*360),Math.round(s*100),Math.round(l*100)]
}
function hslToRgb(h,s,l) {
  let r,g,b;if(s===0){r=g=b=l}else{
    const hue2rgb=(p,q,t)=>{if(t<0)t+=1;if(t>1)t-=1;if(t<1/6)return p+(q-p)*6*t;if(t<1/2)return q;if(t<2/3)return p+(q-p)*(2/3-t)*6;return p}
    const q=l<0.5?l*(1+s):l+s-l*s,p=2*l-q;r=hue2rgb(p,q,h+1/3);g=hue2rgb(p,q,h);b=hue2rgb(p,q,h-1/3)}
  return[Math.round(r*255),Math.round(g*255),Math.round(b*255)]
}

// ── JWT ──
const jwtInput = ref('')
const jwtResult = ref(null)
function parseJwt() {
  const token = jwtInput.value.trim()
  if (!token) return
  const parts = token.split('.')
  if (parts.length !== 3) { jwtResult.value = { error: t('toolbox.jwt.invalid') }; return }
  try {
    const header = JSON.parse(atob(parts[0].replace(/-/g,'+').replace(/_/g,'/')))
    const payload = JSON.parse(atob(parts[1].replace(/-/g,'+').replace(/_/g,'/')))
    const exp = payload.exp ? new Date(payload.exp * 1000).toLocaleString() : null
    const isExpired = payload.exp ? Date.now() > payload.exp * 1000 : false
    jwtResult.value = {
      header: JSON.stringify(header, null, 2),
      payload: JSON.stringify(payload, null, 2),
      exp, isExpired
    }
  } catch (e) { jwtResult.value = { error: `${t('toolbox.jwt.invalid')}: ${e.message}` } }
}

// ── URL ──
const urlInput = ref('')
const urlResult = ref('')
function urlEncode() { urlResult.value = encodeURIComponent(urlInput.value) }
function urlDecode() { urlResult.value = decodeURIComponent(urlInput.value) }
function parseUrl() {
  try {
    const u = new URL(urlInput.value)
    const params = Array.from(u.searchParams.entries()).map(([k,v]) => `${k} = ${v}`).join('\n')
    urlResult.value = `Protocol: ${u.protocol}\nHost: ${u.host}\nPath: ${u.pathname}\nPort: ${u.port || '(default)'}\n${params ? 'Query:\n' + params : 'No query params'}`
  } catch (e) { urlResult.value = `${t('toolbox.url.parseError')}: ${e.message}` }
}

// ── UUID ──
const uuidResult = ref('')
function genUuid(count) {
  const uuids = []
  for (let i = 0; i < count; i++) {
    uuids.push('xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = Math.random() * 16 | 0
      return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16)
    }))
  }
  uuidResult.value = uuids.join('\n')
}

// ── Text Diff ──
const diffLeft = ref('')
const diffRight = ref('')
const diffResult = ref([])
function computeDiff() {
  const leftLines = diffLeft.value.split('\n')
  const rightLines = diffRight.value.split('\n')
  const maxLen = Math.max(leftLines.length, rightLines.length)
  const result = []
  for (let i = 0; i < maxLen; i++) {
    const l = leftLines[i] || ''
    const r = rightLines[i] || ''
    if (l === r) result.push({ type: 'same', text: `  ${l}` })
    else {
      if (l && !leftLines[i] === undefined) result.push({ type: 'removed', text: `- ${l}` })
      if (r || rightLines[i] !== undefined) result.push({ type: 'added', text: `+ ${r}` })
    }
  }
  diffResult.value = result
}

// ── Markdown ──
const mdInput = ref('')
const mdHtml = computed(() => {
  let html = mdInput.value
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
    .replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank">$1</a>')
    .replace(/^---$/gm, '<hr/>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>')
  return html
})

// ── Cron ──
const cronInput = ref('')
const cronResult = ref(null)
const cronFields = [
  { name: 'minute', values: { '*': 'every minute', '0': 'at minute 0' } },
  { name: 'hour', values: { '*': 'every hour', '0': 'at hour 0 (midnight)' } },
  { name: 'dom', values: { '*': 'every day' } },
  { name: 'month', values: { '*': 'every month' } },
  { name: 'dow', values: { '*': 'every day of week', '0': 'on Sunday', '1': 'on Monday', '2': 'on Tuesday', '3': 'on Wednesday', '4': 'on Thursday', '5': 'on Friday', '6': 'on Saturday' } },
]
function parseCron() {
  const parts = cronInput.value.trim().split(/\s+/)
  if (parts.length < 5) { cronResult.value = { description: t('toolbox.cron.invalid'), nextRuns: [] }; return }
  const desc = []
  const fieldNames = ['minute','hour','day of month','month','day of week']
  for (let i = 0; i < 5; i++) {
    const p = parts[i]
    if (p === '*') desc.push(`${fieldNames[i]}: every`)
    else desc.push(`${fieldNames[i]}: ${p}`)
  }
  const nextRuns = []
  try {
    for (let i = 0; i < 5; i++) {
      const d = new Date(Date.now() + i * 60000)
      nextRuns.push(d.toLocaleString())
    }
  } catch {}
  cronResult.value = { description: desc.join(', '), nextRuns }
}

// ── Password ──
const pwdInput = ref('')
const pwdResult = computed(() => {
  const pwd = pwdInput.value
  if (!pwd) return null
  const len = pwd.length
  const hasUpper = /[A-Z]/.test(pwd)
  const hasLower = /[a-z]/.test(pwd)
  const hasDigit = /[0-9]/.test(pwd)
  const hasSpecial = /[^A-Za-z0-9]/.test(pwd)
  const types = [hasUpper, hasLower, hasDigit, hasSpecial].filter(Boolean).length
  let score = 0
  if (len >= 8) score += 25
  if (len >= 12) score += 15
  if (len >= 16) score += 10
  score += types * 15
  score = Math.min(score, 100)
  const color = score < 30 ? '#ef4444' : score < 60 ? '#f59e0b' : score < 80 ? '#22c55e' : '#00ff88'
  const label = score < 30 ? t('toolbox.password.weak') : score < 60 ? t('toolbox.password.medium') : score < 80 ? t('toolbox.password.strong') : t('toolbox.password.veryStrong')
  const combinations = types === 1 ? 26 : types === 2 ? 62 : types === 3 ? 68 : 94
  const entropy = len * Math.log2(combinations)
  const seconds = Math.pow(2, entropy) / 1e10
  const crackTime = seconds < 1 ? t('toolbox.password.instant') : seconds < 3600 ? `${Math.ceil(seconds)}s` : seconds < 86400 ? `${Math.ceil(seconds/3600)}h` : seconds < 86400*365 ? `${Math.ceil(seconds/86400)}d` : `${Math.ceil(seconds/86400/365)}y`
  return { length: len, hasUpper, hasLower, hasDigit, hasSpecial, score, color, label, crackTime }
})

// ── QR Code ──
const qrInput = ref('')
const qrDataUrl = ref('')
function genQr() {
  const text = qrInput.value.trim()
  if (!text) return
  const size = 256
  const canvas = document.createElement('canvas')
  canvas.width = size; canvas.height = size
  const ctx = canvas.getContext('2d')
  const modules = qrEncode(text)
  const cellSize = size / modules.length
  ctx.fillStyle = '#0a0a1a'; ctx.fillRect(0, 0, size, size)
  ctx.fillStyle = '#00f5ff'
  for (let r = 0; r < modules.length; r++) {
    for (let c = 0; c < modules.length; c++) {
      if (modules[r][c]) ctx.fillRect(c * cellSize, r * cellSize, cellSize, cellSize)
    }
  }
  qrDataUrl.value = canvas.toDataURL('image/png')
}
function downloadQr() {
  const a = document.createElement('a')
  a.href = qrDataUrl.value; a.download = 'qrcode.png'; a.click()
}
function qrEncode(data) {
  const version = 2, size = 25
  const modules = Array.from({length: size}, () => Array(size).fill(false))
  // finder patterns
  const fp = [[0,0],[0,size-7],[size-7,0]]
  for (const [fr,fc] of fp) {
    for (let r=0;r<7;r++) for(let c=0;c<7;c++) {
      const on = r===0||r===6||c===0||c===6||(r>=2&&r<=4&&c>=2&&c<=4)
      modules[fr+r][fc+c] = on
    }
  }
  // alignment pattern at [18,18]
  for(let r=-2;r<=2;r++) for(let c=-2;c<=2;c++) modules[18+r][18+c] = r===0||c===0||(Math.abs(r)===2&&Math.abs(c)===2)
  // timing
  for(let i=8;i<size-8;i++) { modules[6][i] = i%2===0; modules[i][6] = i%2===0 }
  // encode data bits
  const bytes = new TextEncoder().encode(data)
  const bits = []
  bits.push(0,1,0,0) // byte mode
  for(let i=7;i>=0;i--) bits.push((bytes.length>>i)&1)
  for(const b of bytes) for(let i=7;i>=0;i--) bits.push((b>>i)&1)
  // pad to capacity
  while(bits.length<152) bits.push(0)
  // fill data modules zigzag
  const reserved = Array.from({length:size},()=>Array(size).fill(false))
  for(const [fr,fc] of fp) for(let r=0;r<7;r++) for(let c=0;c<7;c++) reserved[fr+r][fc+c]=true
  for(let r=-2;r<=2;r++) for(let c=-2;c<=2;c++) reserved[18+r][18+c]=true
  for(let i=8;i<size-8;i++) { reserved[6][i]=true; reserved[i][6]=true }
  reserved.forEach(row=>row[8]=true)
  reserved[8].forEach((_,c)=>reserved[8][c]=true)
  let bitIdx=0, col=size-1, upward=true
  while(col>=0) {
    if(col===6) col--;
    for(let row=upward?size-1:0; upward?row>=0:row<size; row+=upward?-1:1) {
      for(let c=col;c>=col-1&&c>=0;c--) {
        if(reserved[row][c]) continue
        if(bitIdx<bits.length) modules[row][c] = bits[bitIdx]===1
        bitIdx++
      }
    }
    col-=2; upward=!upward
  }
  return modules
}
</script>

<style scoped>
.toolbox-page { max-width: 960px; margin: 0 auto; }
.page-title { font-family: 'Orbitron', sans-serif; font-weight: 700; font-size: 1.6rem; color: var(--neon-cyan); letter-spacing: 2px; margin-bottom: 0.25rem; }
.page-subtitle { font-family: 'Share Tech Mono', monospace; color: var(--text-muted); font-size: 0.75rem; margin-bottom: 2rem; letter-spacing: 1px; }

.tools-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
.tool-card { background: var(--bg-panel); border: 1px solid var(--border-dim); border-radius: 8px; cursor: pointer; transition: all 0.3s; position: relative; overflow: hidden; }
.tool-card:hover { border-color: var(--border-strong); box-shadow: 0 0 20px rgba(0,245,255,0.1); }
.tool-card.expanded { grid-column: 1 / -1; border-color: var(--neon-cyan); box-shadow: 0 0 30px rgba(0,245,255,0.15); }
.tool-card::before, .tool-card::after { content:''; position:absolute; width:12px; height:12px; border-color:var(--neon-cyan); opacity:0; transition:opacity 0.3s; }
.tool-card::before { top:4px; left:4px; border-top:2px solid; border-left:2px solid; }
.tool-card::after { bottom:4px; right:4px; border-bottom:2px solid; border-right:2px solid; }
.tool-card:hover::before, .tool-card:hover::after, .tool-card.expanded::before, .tool-card.expanded::after { opacity: 0.8; }

.card-header { padding: 1rem 1.25rem; display: flex; align-items: center; gap: 0.75rem; font-family: 'Orbitron', sans-serif; font-weight: 600; font-size: 0.85rem; color: var(--text-secondary); }
.card-icon { font-family: 'Share Tech Mono', monospace; font-size: 0.9rem; color: var(--neon-cyan); background: rgba(0,245,255,0.08); padding: 0.3rem 0.5rem; border-radius: 4px; border: 1px solid rgba(0,245,255,0.2); }
.card-title { flex: 1; }
.card-arrow { font-size: 0.7rem; color: var(--text-dim); transition: transform 0.2s; }
.tool-card.expanded .card-arrow { color: var(--neon-cyan); }
.card-body { padding: 1rem 1.25rem 1.5rem; border-top: 1px solid var(--border-dim); }

.tool-input { width:100%; background:rgba(0,0,0,0.4); border:1px solid var(--border-dim); border-radius:6px; padding:0.75rem; font-family:'Share Tech Mono',monospace; font-size:0.8rem; color:var(--text-primary); resize:vertical; line-height:1.5; }
.tool-input:focus { border-color:var(--neon-cyan); box-shadow:0 0 8px rgba(0,245,255,0.15); outline:none; }
.tool-input-inline { background:rgba(0,0,0,0.4); border:1px solid var(--border-dim); border-radius:6px; padding:0.6rem 0.75rem; font-family:'Share Tech Mono',monospace; font-size:0.8rem; color:var(--text-primary); flex:1; }
.tool-input-inline:focus { border-color:var(--neon-cyan); outline:none; }

.tool-actions { display:flex; gap:0.5rem; margin-top:0.75rem; flex-wrap:wrap; }
.tool-btn { font-family:'Orbitron',sans-serif; font-size:0.7rem; font-weight:500; padding:0.4rem 0.8rem; border:1px solid rgba(0,245,255,0.3); border-radius:4px; background:rgba(0,245,255,0.05); color:var(--neon-cyan); cursor:pointer; transition:all 0.2s; letter-spacing:1px; }
.tool-btn:hover { background:rgba(0,245,255,0.15); box-shadow:0 0 10px rgba(0,245,255,0.2); }
.tool-btn.now-btn { background:rgba(0,255,136,0.08); border-color:rgba(0,255,136,0.3); color:var(--accent-green); }
.tool-btn.now-btn:hover { background:rgba(0,255,136,0.15); box-shadow:0 0 10px rgba(0,255,136,0.2); }
.copy-btn { background:rgba(255,215,0,0.05); border-color:rgba(255,215,0,0.3); color:var(--accent-gold); }
.copy-btn:hover { background:rgba(255,215,0,0.15); box-shadow:0 0 10px rgba(255,215,0,0.2); }

.tool-result { margin-top:0.75rem; background:rgba(0,0,0,0.3); border:1px solid var(--border-dim); border-radius:6px; padding:0.75rem; font-family:'Share Tech Mono',monospace; font-size:0.78rem; color:var(--neon-cyan); white-space:pre-wrap; word-break:break-all; line-height:1.6; max-height:300px; overflow-y:auto; }
.tool-result.error { color:var(--accent-red); border-color:rgba(239,68,68,0.3); }
.hash-result { letter-spacing:1px; }

.ts-row, .color-row, .cron-row { display:flex; gap:0.5rem; align-items:center; }
.regex-pattern { margin-bottom:0.5rem; width:100%; display:block; }
.regex-line { display:block; }
.regex-line .match { background:rgba(0,245,255,0.2); color:var(--neon-cyan); border-radius:2px; padding:0 2px; }
.match-count { margin-top:0.5rem; font-family:'Orbitron',sans-serif; font-size:0.7rem; color:var(--accent-green); }

.color-result { display:flex; align-items:center; gap:1rem; }
.color-preview { width:48px; height:48px; border-radius:6px; border:2px solid var(--border-strong); box-shadow:0 0 12px rgba(0,245,255,0.2); }
.color-values div { font-family:'Share Tech Mono',monospace; font-size:0.78rem; color:var(--text-secondary); margin-bottom:0.25rem; }
.color-val { color:var(--neon-cyan); }

/* JWT */
.jwt-section { margin-bottom:0.75rem; }
.jwt-label { font-family:'Orbitron',sans-serif; font-size:0.7rem; color:var(--accent-gold); margin-bottom:0.25rem; letter-spacing:1px; }
.jwt-json { font-size:0.75rem; }
.jwt-exp { font-family:'Orbitron',sans-serif; font-size:0.7rem; margin-top:0.5rem; }
.jwt-exp.expired { color:var(--accent-red); }
.jwt-error { color:var(--accent-red); }

/* Diff */
.diff-columns { display:flex; gap:0.75rem; }
.diff-input { flex:1; }
.diff-result .diff-line { line-height:1.5; }
.diff-line.same { color:var(--text-secondary); }
.diff-line.removed { color:var(--accent-red); background:rgba(239,68,68,0.08); }
.diff-line.added { color:var(--accent-green); background:rgba(0,255,136,0.08); }

/* Markdown */
.md-columns { display:flex; gap:0.75rem; }
.md-input { flex:1; }
.md-preview { flex:1; background:rgba(0,0,0,0.3); border:1px solid var(--border-dim); border-radius:6px; padding:0.75rem; color:var(--text-primary); font-size:0.85rem; line-height:1.6; overflow-y:auto; max-height:400px; }
.md-preview h1 { font-size:1.2rem; color:var(--neon-cyan); }
.md-preview h2 { font-size:1rem; color:var(--neon-cyan); }
.md-preview h3 { font-size:0.9rem; color:var(--neon-cyan); }
.md-preview code { background:rgba(0,245,255,0.1); padding:2px 4px; border-radius:3px; font-family:'Share Tech Mono',monospace; color:var(--accent-gold); }
.md-preview blockquote { border-left:3px solid var(--neon-magenta); padding-left:0.75rem; color:var(--text-muted); }
.md-preview a { color:var(--neon-cyan); }
.md-preview hr { border-color:var(--border-dim); }
.md-preview li { margin-left:1rem; }

/* Cron */
.cron-next { margin-top:0.5rem; font-size:0.75rem; color:var(--accent-green); }

/* Password */
.pwd-input { width:100%; margin-bottom:0.75rem; display:block; }
.pwd-bar { height:6px; background:rgba(255,255,255,0.1); border-radius:3px; margin-bottom:0.5rem; }
.pwd-fill { height:100%; border-radius:3px; transition:width 0.3s; }
.pwd-score { font-family:'Orbitron',sans-serif; font-size:0.8rem; font-weight:600; }
.pwd-details { margin-top:0.5rem; font-size:0.75rem; color:var(--text-secondary); }
.pwd-details div { margin-bottom:0.15rem; }

/* QR */
.qr-result { text-align:center; }
.qr-img { width:200px; height:200px; border:2px solid var(--border-strong); border-radius:8px; box-shadow:0 0 20px rgba(0,245,255,0.2); }

@media(max-width:768px) {
  .diff-columns, .md-columns { flex-direction:column; }
}
</style>