// 设计规范常量（CLAUDE.md 第 5 节），与 index.css 的 @theme 保持一致
export const colors = {
  bg: '#F4F6FB',
  card: '#FFFFFF',
  cardBorder: '#E6E9F2',
  sidebar: '#1B1C3B',
  sidebarActive: '#2A2C52',
  primary: '#6366F1',
  primaryLight: '#EEF0FE',
  danger: '#EF4444',
  warning: '#F59E0B',
  success: '#10B981',
  info: '#3B82F6',
  ink: '#1F2430',
  sub: '#8A90A6',
}

// 评分徽章分档：≥80 红 / 60~79 橙 / 40~59 灰 / <40 蓝
export function scoreBand(score: number) {
  if (score >= 80) return { label: '立即补货', bg: colors.danger, fg: '#fff' }
  if (score >= 60) return { label: '常规', bg: colors.warning, fg: '#fff' }
  if (score >= 40) return { label: '观望', bg: '#9CA3AF', fg: '#fff' }
  return { label: '停止补货', bg: colors.info, fg: '#fff' }
}

// 侧边导航菜单（7 项）
export const menuItems = [
  { key: 'dashboard', label: '工作台总览', path: '/' },
  { key: 'datacenter', label: '数据中心', path: '/datacenter' },
  { key: 'suggestions', label: '备货建议表', path: '/suggestions' },
  { key: 'alerts', label: '预警中心', path: '/alerts' },
  { key: 'purchase', label: '采购计划', path: '/purchase' },
  { key: 'chat', label: 'AI问答助手', path: '/chat' },
  { key: 'settings', label: '系统设置', path: '/settings' },
]
