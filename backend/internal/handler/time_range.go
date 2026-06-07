package handler

import (
	"time"
)

// ParseTimeRange 解析预设时间范围，返回起止时间
// timeRange: today/week/lastWeek/month/year/all
func ParseTimeRange(timeRange string) (startDate, endDate time.Time) {
	now := time.Now()

	switch timeRange {
	case "today": // 今日
		startDate = time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, now.Location())
		endDate = now
	case "week": // 本周（从周一开始）
		weekday := int(now.Weekday())
		if weekday == 0 { // 周日
			weekday = 7
		}
		daysFromMonday := weekday - 1
		startDate = now.AddDate(0, 0, -daysFromMonday)
		startDate = time.Date(startDate.Year(), startDate.Month(), startDate.Day(), 0, 0, 0, 0, startDate.Location())
		endDate = now
	case "lastWeek": // 上周
		weekday := int(now.Weekday())
		if weekday == 0 {
			weekday = 7
		}
		daysFromMonday := weekday + 6
		lastMonday := now.AddDate(0, 0, -daysFromMonday)
		startDate = time.Date(lastMonday.Year(), lastMonday.Month(), lastMonday.Day(), 0, 0, 0, 0, lastMonday.Location())
		endDate = startDate.AddDate(0, 0, 6).Add(24*time.Hour - time.Second)
	case "month": // 本月
		startDate = time.Date(now.Year(), now.Month(), 1, 0, 0, 0, 0, now.Location())
		endDate = now
	case "year": // 本年
		startDate = time.Date(now.Year(), 1, 1, 0, 0, 0, 0, now.Location())
		endDate = now
	default: // all 或其他
		startDate = time.Time{} // 零值表示不限制
		endDate = now
	}

	return startDate, endDate
}
