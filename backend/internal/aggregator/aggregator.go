package aggregator

import (
	"cmp"
	"fmt"
	"math"
	"slices"
	"strconv"
	"strings"
	"time"

	"gitstat/internal/model"
)

func AggregateOverview(repos []model.Repository, userEmail string, startDate, endDate time.Time) model.OverviewStats {
	var totalAdditions, totalDeletions int
	var commitCount int
	authorMap := make(map[string]*model.AuthorRankItem)
	repoSet := make(map[string]bool)

	for _, repo := range repos {
		repoSet[repo.Path] = true
		for _, c := range repo.Commits {
			if userEmail != "" && c.Email != userEmail {
				continue
			}
			if !startDate.IsZero() && c.Date.Before(startDate) {
				continue
			}
			if !endDate.IsZero() && c.Date.After(endDate) {
				continue
			}
			commitCount++
			totalAdditions += c.Additions
			totalDeletions += c.Deletions

			key := c.Email
			if _, exists := authorMap[key]; !exists {
				authorMap[key] = &model.AuthorRankItem{
					Author: c.Author,
					Email:  c.Email,
					IsMe:   c.Email == userEmail,
				}
			}
			stats := authorMap[key]
			stats.Commits++
			stats.Additions += c.Additions
			stats.Deletions += c.Deletions
			stats.NetChange = stats.Additions - stats.Deletions
		}
	}

	var authorList []model.AuthorRankItem
	for _, item := range authorMap {
		if item.Commits > 0 {
			item.AvgCommitSize = float64(item.Additions+item.Deletions) / float64(item.Commits)
		}
		authorList = append(authorList, *item)
	}
	slices.SortFunc(authorList, func(a, b model.AuthorRankItem) int {
		return cmp.Compare(b.Commits, a.Commits)
	})

	return model.OverviewStats{
		TotalCommits:    commitCount,
		TotalAdditions:  totalAdditions,
		TotalDeletions:  totalDeletions,
		ActiveAuthors:   len(authorMap),
		RepositoryCount: len(repoSet),
		Authors:         authorList,
	}
}

func AggregateDailyStatsWithRange(repos []model.Repository, userEmail string, startDate time.Time, endDate time.Time) []model.RepositoryDailyStats {
	var result []model.RepositoryDailyStats

	for _, repo := range repos {
		authorMap := make(map[string]*model.AuthorDailyStats)
		dailyDataMap := make(map[string]map[string]*model.DayCommitData) // email -> date -> data

		for _, commit := range repo.Commits {
			commitDate := commit.Date.Format("2006-01-02")

			// 过滤时间范围
			if !startDate.IsZero() && commit.Date.Before(startDate) {
				continue
			}
			if !endDate.IsZero() && commit.Date.After(endDate) {
				continue
			}

			key := commit.Email
			if _, exists := authorMap[key]; !exists {
				authorMap[key] = &model.AuthorDailyStats{
					Author: commit.Author,
					Email:  commit.Email,
					IsMe:   commit.Email == userEmail,
				}
				if dailyDataMap[key] == nil {
					dailyDataMap[key] = make(map[string]*model.DayCommitData)
				}
			}

			stats := authorMap[key]
			stats.Commits++
			stats.Additions += commit.Additions
			stats.Deletions += commit.Deletions

			// 收集每日数据
			if _, exists := dailyDataMap[key][commitDate]; !exists {
				dailyDataMap[key][commitDate] = &model.DayCommitData{
					Date: commitDate,
				}
			}
			dayData := dailyDataMap[key][commitDate]
			dayData.Commits++
			dayData.Additions += commit.Additions
			dayData.Deletions += commit.Deletions
		}

		if len(authorMap) > 0 {
			var authors []model.AuthorDailyStats
			for email, stats := range authorMap {
				// 转换每日数据为数组并排序
				var dailyData []model.DayCommitData
				for _, dayData := range dailyDataMap[email] {
					dailyData = append(dailyData, *dayData)
				}
				slices.SortFunc(dailyData, func(a, b model.DayCommitData) int {
					return cmp.Compare(a.Date, b.Date)
				})
				stats.DailyData = dailyData

				authors = append(authors, *stats)
			}

			// 按提交数排序
			slices.SortFunc(authors, func(a, b model.AuthorDailyStats) int {
				return cmp.Compare(b.Commits, a.Commits)
			})

			result = append(result, model.RepositoryDailyStats{
				RepoName:       repo.Name,
				RepoPath:       repo.Path,
				CurrentBranch:  repo.CurrentBranch,
				LastCommitTime: repo.LastCommitTime,
				Authors:        authors,
			})
		}
	}

	return result
}

func getWeekKey(t time.Time) string {
	year, week := t.ISOWeek()
	return fmt.Sprintf("%d-W%02d", year, week)
}

func getMonthKey(t time.Time) string {
	return t.Format("2006-01")
}

func getYearKey(t time.Time) string {
	return t.Format("2006")
}

func aggregatePeriodStats(repos []model.Repository, userEmail string, startDate, endDate time.Time, periodKeyFn func(time.Time) string) []model.RepositoryPeriodStats {
	var result []model.RepositoryPeriodStats

	for _, repo := range repos {
		authorMap := make(map[string]*model.AuthorPeriodStats)
		periodDataMap := make(map[string]map[string]*model.PeriodCommitData)

		for _, commit := range repo.Commits {
			if !startDate.IsZero() && commit.Date.Before(startDate) {
				continue
			}
			if !endDate.IsZero() && commit.Date.After(endDate) {
				continue
			}

			key := commit.Email
			if _, exists := authorMap[key]; !exists {
				authorMap[key] = &model.AuthorPeriodStats{
					Author: commit.Author,
					Email:  commit.Email,
					IsMe:   commit.Email == userEmail,
				}
				if periodDataMap[key] == nil {
					periodDataMap[key] = make(map[string]*model.PeriodCommitData)
				}
			}

			stats := authorMap[key]
			stats.Commits++
			stats.Additions += commit.Additions
			stats.Deletions += commit.Deletions

			periodKey := periodKeyFn(commit.Date)
			if _, exists := periodDataMap[key][periodKey]; !exists {
				periodDataMap[key][periodKey] = &model.PeriodCommitData{
					Period: periodKey,
				}
			}
			pd := periodDataMap[key][periodKey]
			pd.Commits++
			pd.Additions += commit.Additions
			pd.Deletions += commit.Deletions
		}

		if len(authorMap) > 0 {
			var authors []model.AuthorPeriodStats
			for email, stats := range authorMap {
				var periodData []model.PeriodCommitData
				for _, pd := range periodDataMap[email] {
					periodData = append(periodData, *pd)
				}
				slices.SortFunc(periodData, func(a, b model.PeriodCommitData) int {
					return cmp.Compare(a.Period, b.Period)
				})
				stats.PeriodData = periodData
				authors = append(authors, *stats)
			}

			slices.SortFunc(authors, func(a, b model.AuthorPeriodStats) int {
				return cmp.Compare(b.Commits, a.Commits)
			})

			result = append(result, model.RepositoryPeriodStats{
				RepoName:       repo.Name,
				RepoPath:       repo.Path,
				CurrentBranch:  repo.CurrentBranch,
				LastCommitTime: repo.LastCommitTime,
				Authors:        authors,
			})
		}
	}

	return result
}

func AggregateWeeklyStatsWithRange(repos []model.Repository, userEmail string, startDate, endDate time.Time) []model.RepositoryPeriodStats {
	return aggregatePeriodStats(repos, userEmail, startDate, endDate, getWeekKey)
}

func AggregateMonthlyStatsWithRange(repos []model.Repository, userEmail string, startDate, endDate time.Time) []model.RepositoryPeriodStats {
	return aggregatePeriodStats(repos, userEmail, startDate, endDate, getMonthKey)
}

func AggregateYearlyStatsWithRange(repos []model.Repository, userEmail string, startDate, endDate time.Time) []model.RepositoryPeriodStats {
	return aggregatePeriodStats(repos, userEmail, startDate, endDate, getYearKey)
}

// 开发者排行榜聚合
func AggregateAuthorRank(repos []model.Repository, userEmail string, startDate time.Time, endDate time.Time) []model.AuthorRankItem {
	authorMap := make(map[string]*model.AuthorRankItem)
	lastTimes := make(map[string]time.Time)

	for _, repo := range repos {
		for _, commit := range repo.Commits {
			if !startDate.IsZero() && commit.Date.Before(startDate) {
				continue
			}
			if !endDate.IsZero() && commit.Date.After(endDate) {
				continue
			}

			key := commit.Email
			if _, exists := authorMap[key]; !exists {
				authorMap[key] = &model.AuthorRankItem{
					Author: commit.Author,
					Email:  commit.Email,
					IsMe:   commit.Email == userEmail,
				}
			}

			stats := authorMap[key]
			stats.Commits++
			stats.Additions += commit.Additions
			stats.Deletions += commit.Deletions
			stats.NetChange = stats.Additions - stats.Deletions
			if commit.Date.After(lastTimes[key]) {
				lastTimes[key] = commit.Date
				stats.LastCommitDate = commit.Date.Format("2006-01-02 15:04:05")
			}
		}
	}

	// 计算平均提交大小并转换为数组
	var result []model.AuthorRankItem
	for _, item := range authorMap {
		if item.Commits > 0 {
			item.AvgCommitSize = float64(item.Additions+item.Deletions) / float64(item.Commits)
		}
		result = append(result, *item)
	}

	// 按提交数排序
	slices.SortFunc(result, func(a, b model.AuthorRankItem) int {
		return cmp.Compare(b.Commits, a.Commits)
	})

	return result
}

// 活动热力图聚合
func AggregateActivityHeatmap(repos []model.Repository, userEmail string, startDate time.Time, endDate time.Time) []model.ActivityHeatmapPoint {
	heatmap := make(map[string]int) // "dayOfWeek-hour" -> count

	for _, repo := range repos {
		for _, commit := range repo.Commits {
			// 邮箱过滤
			if userEmail != "" && commit.Email != userEmail {
				continue
			}
			// 时间过滤
			if !startDate.IsZero() && commit.Date.Before(startDate) {
				continue
			}
			if !endDate.IsZero() && commit.Date.After(endDate) {
				continue
			}

			key := fmt.Sprintf("%d-%d", commit.Date.Weekday(), commit.Date.Hour())
			heatmap[key]++
		}
	}

	// 转换为数组
	var result []model.ActivityHeatmapPoint
	for key, count := range heatmap {
		parts := strings.Split(key, "-")
		dayOfWeek, _ := strconv.Atoi(parts[0])
		hour, _ := strconv.Atoi(parts[1])
		result = append(result, model.ActivityHeatmapPoint{
			DayOfWeek:   dayOfWeek,
			Hour:        hour,
			CommitCount: count,
		})
	}

	// 排序
	slices.SortFunc(result, func(a, b model.ActivityHeatmapPoint) int {
		if a.DayOfWeek != b.DayOfWeek {
			return cmp.Compare(a.DayOfWeek, b.DayOfWeek)
		}
		return cmp.Compare(a.Hour, b.Hour)
	})

	return result
}

// 仓库对比聚合
func AggregateRepoComparison(repos []model.Repository, userEmail string, startDate time.Time, endDate time.Time) []model.RepoComparison {
	var result []model.RepoComparison

	for _, repo := range repos {
		commitSet := make(map[string]bool) // 用于计算活跃天数
		authorSet := make(map[string]bool)
		var commits, additions, deletions int

		for _, commit := range repo.Commits {
			// 邮箱过滤
			if userEmail != "" && commit.Email != userEmail {
				continue
			}
			// 时间过滤
			if !startDate.IsZero() && commit.Date.Before(startDate) {
				continue
			}
			if !endDate.IsZero() && commit.Date.After(endDate) {
				continue
			}

			commits++
			additions += commit.Additions
			deletions += commit.Deletions
			authorSet[commit.Email] = true
			commitSet[commit.Date.Format("2006-01-02")] = true
		}

		if commits > 0 {
			activeDays := len(commitSet)
			avgCommitsPerDay := float64(commits) / float64(activeDays)
			// 保留1位小数
			avgCommitsPerDay = math.Round(avgCommitsPerDay*10) / 10

			result = append(result, model.RepoComparison{
				RepoName:         repo.Name,
				RepoPath:         repo.Path,
				Commits:          commits,
				Authors:          len(authorSet),
				Additions:        additions,
				Deletions:        deletions,
				LastCommitTime:   repo.LastCommitTime,
				ActiveDays:       activeDays,
				AvgCommitsPerDay: avgCommitsPerDay,
			})
		}
	}

	// 按提交数排序
	slices.SortFunc(result, func(a, b model.RepoComparison) int {
		return cmp.Compare(b.Commits, a.Commits)
	})

	return result
}
