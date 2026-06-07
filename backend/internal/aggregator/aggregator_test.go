package aggregator

import (
	"testing"
	"time"

	"gitstat/internal/model"
)

func TestGetWeekKey(t *testing.T) {
	tests := []struct {
		date string
		want string
	}{
		{"2026-01-01", "2026-W01"},
		{"2026-05-26", "2026-W22"},
		{"2026-12-31", "2026-W53"},
	}
	for _, tt := range tests {
		tm, _ := time.Parse("2006-01-02", tt.date)
		got := getWeekKey(tm)
		if got != tt.want {
			t.Errorf("getWeekKey(%s) = %s, want %s", tt.date, got, tt.want)
		}
	}
}

func TestGetMonthKey(t *testing.T) {
	tm, _ := time.Parse("2006-01-02", "2026-05-26")
	if got := getMonthKey(tm); got != "2026-05" {
		t.Errorf("getMonthKey = %s, want 2026-05", got)
	}
}

func TestGetYearKey(t *testing.T) {
	tm, _ := time.Parse("2006-01-02", "2026-05-26")
	if got := getYearKey(tm); got != "2026" {
		t.Errorf("getYearKey = %s, want 2026", got)
	}
}

func TestAggregateWeeklyStatsWithRange(t *testing.T) {
	// Mon May 25 2026
	d1 := time.Date(2026, 5, 25, 0, 0, 0, 0, time.UTC)
	// Tue May 26 2026
	d2 := time.Date(2026, 5, 26, 0, 0, 0, 0, time.UTC)
	// Mon Jun 1 2026 (W23)
	d3 := time.Date(2026, 6, 1, 0, 0, 0, 0, time.UTC)

	repos := []model.Repository{
		{
			Name:  "test-repo",
			Path:  "/test",
			Commits: []model.Commit{
				{Author: "Alice", Email: "a@x", Date: d1, Additions: 10, Deletions: 2},
				{Author: "Alice", Email: "a@x", Date: d2, Additions: 20, Deletions: 5},
				{Author: "Alice", Email: "a@x", Date: d3, Additions: 30, Deletions: 3},
			},
		},
	}

	stats := AggregateWeeklyStatsWithRange(repos, "", time.Time{}, time.Time{})
	if len(stats) != 1 {
		t.Fatalf("Expected 1 repo, got %d", len(stats))
	}
	if len(stats[0].Authors) != 1 {
		t.Fatalf("Expected 1 author, got %d", len(stats[0].Authors))
	}
	author := stats[0].Authors[0]
	if author.Commits != 3 {
		t.Errorf("Expected 3 commits, got %d", author.Commits)
	}
	if len(author.PeriodData) != 2 {
		t.Errorf("Expected 2 weeks (W22, W23), got %d: %v", len(author.PeriodData), author.PeriodData)
	}
}

func TestAggregateMonthlyStatsWithRange(t *testing.T) {
	d1 := time.Date(2026, 5, 15, 0, 0, 0, 0, time.UTC)
	d2 := time.Date(2026, 6, 1, 0, 0, 0, 0, time.UTC)

	repos := []model.Repository{
		{
			Name:  "test-repo",
			Path:  "/test",
			Commits: []model.Commit{
				{Author: "Bob", Email: "b@x", Date: d1, Additions: 5, Deletions: 1},
				{Author: "Bob", Email: "b@x", Date: d2, Additions: 15, Deletions: 4},
			},
		},
	}

	stats := AggregateMonthlyStatsWithRange(repos, "", time.Time{}, time.Time{})
	if len(stats) != 1 {
		t.Fatalf("Expected 1 repo, got %d", len(stats))
	}
	author := stats[0].Authors[0]
	if len(author.PeriodData) != 2 {
		t.Errorf("Expected 2 months (2026-05, 2026-06), got %d: %v", len(author.PeriodData), author.PeriodData)
	}
}

func TestAggregateYearlyStatsWithRange(t *testing.T) {
	d1 := time.Date(2025, 6, 1, 0, 0, 0, 0, time.UTC)
	d2 := time.Date(2026, 5, 26, 0, 0, 0, 0, time.UTC)

	repos := []model.Repository{
		{
			Name:  "test-repo",
			Path:  "/test",
			Commits: []model.Commit{
				{Author: "Charlie", Email: "c@x", Date: d1, Additions: 100, Deletions: 10},
				{Author: "Charlie", Email: "c@x", Date: d2, Additions: 200, Deletions: 20},
			},
		},
	}

	stats := AggregateYearlyStatsWithRange(repos, "", time.Time{}, time.Time{})
	if len(stats) != 1 {
		t.Fatalf("Expected 1 repo, got %d", len(stats))
	}
	author := stats[0].Authors[0]
	if len(author.PeriodData) != 2 {
		t.Errorf("Expected 2 years (2025, 2026), got %d: %v", len(author.PeriodData), author.PeriodData)
	}
}

func TestAggregateOverview(t *testing.T) {
	repos := []model.Repository{
		{
			Path: "/test",
			Commits: []model.Commit{
				{Author: "Alice", Email: "a@x", Additions: 10, Deletions: 5},
				{Author: "Bob", Email: "b@x", Additions: 20, Deletions: 10},
			},
		},
	}

	stats := AggregateOverview(repos, "", time.Time{}, time.Time{})

	if stats.TotalCommits != 2 {
		t.Errorf("Expected 2 commits, got %d", stats.TotalCommits)
	}

	if stats.ActiveAuthors != 2 {
		t.Errorf("Expected 2 authors, got %d", stats.ActiveAuthors)
	}

	if stats.TotalAdditions != 30 {
		t.Errorf("Expected 30 additions, got %d", stats.TotalAdditions)
	}
}

