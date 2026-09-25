/* ------------------------------------------------------------------
 * 时区相关小工具 —— 依赖  luxon 2.x
 * ----------------------------------------------------------------- */
import { DateTime } from 'luxon'

/**
 * 将 ISO 日期（如 "2025-07-14"）转换为玩家时区下的 00:00
 * @param isoDate   仅日期部分即可，也接受完整 ISODateTime
 * @param zoneIANA  "Asia/Shanghai" 等 IANA 名称
 */
export function localStartOfDay(isoDate: string, zoneIANA: string) {
  // 用 utc 解析，再切到 zone
  const base = DateTime.fromISO(isoDate, { zone: 'utc' })
  return base.setZone(zoneIANA).startOf('day')
}

/**
 * 把毫秒差值拆成 d / h / m，便于倒计时显示
 */
export function diffBreakdown(ms: number) {
  const d = Math.floor(ms / 86_400_000)
  const h = Math.floor((ms % 86_400_000) / 3_600_000)
  const m = Math.floor((ms %   3_600_000) /     60_000)
  return { d, h, m }
}
