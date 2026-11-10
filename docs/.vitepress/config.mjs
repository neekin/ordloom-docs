import fs from 'node:fs'
import path from 'node:path'
import { defineConfig } from 'vitepress'

// 从 GitBook 的 SUMMARY.md 生成侧边栏,保持两套发布方式的导航一致
function sidebarFromSummary() {
  const summary = fs.readFileSync(path.resolve(__dirname, '../SUMMARY.md'), 'utf8')
  const groups = []
  let current = null
  for (const line of summary.split('\n')) {
    const heading = line.match(/^## (.+)$/)
    if (heading) { current = { text: heading[1], items: [] }; groups.push(current); continue }
    const entry = line.match(/^\s*\*\s*\[([^\]]+)\]\(([^)]+\.md)\)/)
    if (entry && current) {
      const [, text, link] = entry
      const clean = link.replace(/README\.md$/, '').replace(/\.md$/, '')
      current.items.push({ text: text.trim(), link: clean ? '/' + clean : '/' })
    }
  }
  return groups.filter(group => group.items.length)
}

const sidebar = sidebarFromSummary()

export default defineConfig({
  lang: 'zh-CN',
  title: '序衡 Ordloom 使用手册',
  head: [['link', { rel: 'stylesheet', href: 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css', crossorigin: 'anonymous', referrerpolicy: 'no-referrer' }]],
  description: '可配置的 Django Admin 工作台:可视化页面搭建、数字大屏、业务报表、表单问卷、数据订阅与企业级安全。',
  base: '/ordloom-docs/',
  srcDir: '.',
  ignoreDeadLinks: false,
  head: [['link', { rel: 'icon', type: 'image/svg+xml', href: '/ordloom-docs/.gitbook/assets/ordloom-cover.svg' }]],
  themeConfig: {
    logo: '/logo.png',
    siteTitle: '序衡 Ordloom 使用手册',
    nav: [
      { text: '手册首页', link: '/' },
      { text: '安装与接入', link: '/getting-started/installation' },
      { text: '配置参考', link: '/reference/settings' },
      { text: 'GitHub', link: 'https://github.com/neekin/ordloom-docs' },
    ],
    sidebar,
    socialLinks: [{ icon: 'github', link: 'https://github.com/neekin/ordloom-docs' }],
    outline: { level: [2, 3], label: '本页目录' },
    docFooter: { prev: '上一页', next: '下一页' },
    search: { provider: 'local', options: { translations: { button: { buttonText: '搜索文档' }, modal: { noResultsText: '没有找到结果' } } } },
    lastUpdated: { text: '最后更新' },
  },
  lastUpdated: true,
})
