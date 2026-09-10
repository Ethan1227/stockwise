import { scoreBand } from '../../theme'

// 备货评分徽章：≥80 红 / 60~79 橙 / 40~59 灰 / <40 蓝
export function ScoreBadge({ score }: { score: number }) {
  const band = scoreBand(score)
  return (
    <span
      className="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-xs font-semibold text-white min-w-9"
      style={{ backgroundColor: band.bg }}
    >
      {score}
    </span>
  )
}
